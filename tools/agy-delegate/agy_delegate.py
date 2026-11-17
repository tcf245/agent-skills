"""Hand one well-scoped task to agy (Gemini through Google's official Antigravity CLI); Claude judges and verifies.

The limits live in this code, not in the model (skill: skills/coding/agy-delegation.md):
- A repo task runs in a fresh git worktree on branch `agy/<run-id>`; the original working tree is never touched.
  A task without a repo runs in its own folder with copies of its input files.
- agy always runs with `--sandbox`, a JSON schema for its answer, a time limit and an allowed model.
  Argon (and the Orchestrator) have their own quota in agy: on a quota error the task continues on 3.8 Flash.
- Changed files are read from git / the folder, not from the model. This script runs outside the caller's sandbox,
  so it never runs arbitrary commands: the caller re-runs the verify command in its own sandbox.
- `wiki: read|write` adds Eric's LLM Wiki and the llm-wiki skill; wiki edits are listed after the run.
- Inside Rex, a pane opens on the right that shows agy working live (`watch`).

Usage:
  agy-delegate run <task.json> [--no-panel]   run a task; prints a JSON result
  agy-delegate watch <run-id>                 follow a run's progress (what the Rex pane shows)
  agy-delegate cleanup <run-id>               remove a run's worktree/branch or folder
  agy-delegate quota                          Claude's last known quota use and the mode it implies
  agy-delegate statusline                     Claude Code statusLine command: shows quota use and records it
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
HOME = Path.home()
SCRIPT = Path(__file__).resolve()
MODELS = {f"gemini-4-{m}-{e}" for m in ("argon", "hydrogen") for e in ("low", "medium", "high")} | {
    "gemini-4-hydrogen-xhigh", "gemini-3.8-flash-low", "gemini-3.8-flash-medium", "gemini-3.8-flash-high"}
ORCHESTRATOR = "gemini-pro-orchestrator-g1-pro"  # agy's Orchestrator (Argon): plans and runs sub-agents; big multi-part tasks only
MODELS.add(ORCHESTRATOR)
ARGON = {f"gemini-4-argon-{e}" for e in ("low", "medium", "high")} | {ORCHESTRATOR}  # Argon's own quota
DEFAULT_MODEL = "gemini-4-argon-high"  # Eric 2026-11-17: argon first; 3.8 Flash only for bulk text where speed matters
FALLBACK_MODEL = "gemini-3.8-flash-high"
QUOTA_ERROR = re.compile(r"quota|exhaust|rate.?limit|limit (reached|exceeded)|\b429\b", re.IGNORECASE)
DEFAULT_MINUTES, MAX_MINUTES = 30, 60
SECRET_PARTS = (".env", ".ssh", "credentials", ".pem", ".key", ".p12", "id_rsa", "token", "secret")
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules", ".agy-runs"}

# Claude quota: Claude stays the gateway even when agy does the work, so its 5-hour window must not reach 100%.
CONSERVE, RESERVE, STOP = 0.5, 0.8, 0.95

SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["done", "failed", "needs_input"]},
        "summary": {"type": "string"},
        "verification": {"type": "string"},
        "questions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "summary"],
}

GROUND_RULES = """规则（必须遵守）：
- 只在当前目录里工作。不要 git commit、git push，不要 deploy，不要安装全局软件。
- 不要读取或打印密钥：.env、令牌、证书、SSH 私钥、登录文件。
- 做完后自己检查结果；给了验收命令就运行它，在 verification 里写命令和结果。
- 信息不够或需要决定时不要猜：status 写 needs_input，在 questions 里写问题。
- summary 简短：做了什么、没做什么、要注意什么。"""


class TaskError(ValueError):
    """The task asks for something this script does not allow; nothing was run."""


@dataclass(frozen=True)
class Paths:
    workspace: Path = HOME / "workspace"
    runs: Path = HOME / "workspace" / ".agy-runs"
    wiki: Path = Path(os.environ.get("CREW_WIKI_DIR", HOME / "Library/Mobile Documents/iCloud~md~obsidian/Documents/LLM-Wiki"))
    wiki_skill: Path = HOME / ".agents/skills/llm-wiki/SKILL.md"
    quota: Path = Path(os.environ.get("CREW_QUOTA_FILE", HOME / ".local/share/agent-crew/quota.json"))


# runner(command, cwd, timeout, log) -> (returncode, stdout, stderr); the real one streams stdout into `log` as it comes.
Runner = Callable[[list[str], Path, int, Path], tuple[int, str, str]]
Opener = Callable[[str], None]


def _run_agy(command: list[str], cwd: Path, timeout: int, log: Path) -> tuple[int, str, str]:
    lines = []
    with log.open("a") as out, subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE, text=True) as proc:
        deadline = time.monotonic() + timeout
        for line in proc.stdout:
            out.write(line)
            out.flush()
            lines.append(line)
            if time.monotonic() > deadline:
                proc.kill()
                raise subprocess.TimeoutExpired(command, timeout)
        stderr = proc.stderr.read()
        proc.wait()
    return proc.returncode, "".join(lines), stderr


def _open_panel(run_id: str) -> None:
    """Inside Rex, show the run live in a pane to the right of the caller's pane; silently skip otherwise."""
    session, block = os.environ.get("REX_SESSION"), os.environ.get("REX_BLOCK")
    rex = shutil.which("rex")
    if not (session and block and rex):
        return
    subprocess.run([rex, "split", "-s", session, "-b", block, "--split=right", "--ratio", "45", "--focus=false",
                    "--keep-open", "--", sys.executable, str(SCRIPT), "watch", run_id],
                   capture_output=True, timeout=20, check=False)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def _inside(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def _check(task: dict, paths: Paths) -> dict:
    if not isinstance(task.get("goal"), str) or not task["goal"].strip():
        raise TaskError("goal 不能为空")
    model = task.get("model", DEFAULT_MODEL)
    if model not in MODELS:
        raise TaskError(f"不允许的模型 {model}；可选：{', '.join(sorted(MODELS))}")
    minutes = int(task.get("timeout_min", DEFAULT_MINUTES))
    if not 1 <= minutes <= MAX_MINUTES:
        raise TaskError(f"timeout_min 要在 1 到 {MAX_MINUTES} 之间")
    if task.get("wiki") not in (None, "read", "write"):
        raise TaskError("wiki 只能是 read 或 write")
    repo = None
    if task.get("repo"):
        repo = Path(task["repo"]).expanduser()
        if not repo.is_absolute() or not _inside(repo, paths.workspace) or _inside(repo, paths.runs):
            raise TaskError(f"repo 必须是 {paths.workspace} 下的绝对路径")
        if not (repo / ".git").exists():
            raise TaskError(f"{repo} 不是 git 仓库")
    files = []
    for name in task.get("files", []):
        file = Path(name).expanduser()
        if any(part in file.name.lower() or part in str(file).lower().split("/") for part in SECRET_PARTS):
            raise TaskError(f"不复制可能含密钥的文件：{file}")
        if not file.is_absolute() or not file.is_file() or not (_inside(file, paths.workspace) or _inside(file, paths.wiki)):
            raise TaskError(f"files 只能是 {paths.workspace} 或 wiki 下已存在的文件：{file}")
        files.append(file)
    rules = task.get("rules", [])
    if not isinstance(rules, list) or not all(isinstance(r, str) for r in rules):
        raise TaskError("rules 必须是字符串列表")
    return {"goal": task["goal"].strip(), "model": model, "minutes": minutes, "wiki": task.get("wiki"), "repo": repo,
            "files": files, "rules": rules, "verify": task.get("verify"), "requester": task.get("requester", "")}


def _prepare(spec: dict, run_id: str, paths: Paths) -> tuple[Path, str | None]:
    workdir = paths.runs / run_id
    paths.runs.mkdir(parents=True, exist_ok=True)
    if spec["repo"]:
        branch = f"agy/{run_id}"
        _git(spec["repo"], "worktree", "add", "-q", "-b", branch, str(workdir), "HEAD")
        return workdir, branch
    (workdir / "inputs").mkdir(parents=True)
    for file in spec["files"]:
        shutil.copy2(file, workdir / "inputs" / file.name)
    return workdir, None


def _prompt(spec: dict, paths: Paths) -> str:
    parts = [f"任务：{spec['goal']}"]
    if spec["files"] and not spec["repo"]:
        parts.append("输入文件在 inputs/ 里；产出写在当前目录。")
    if spec["rules"]:
        parts.append("这个任务的约束：\n" + "\n".join(f"- {r}" for r in spec["rules"]))
    if spec["verify"]:
        parts.append(f"验收命令：`{spec['verify']}`")
    if spec["wiki"]:
        mode = "可以按 skill 的规则新建或修改页面" if spec["wiki"] == "write" else "只读，不要修改 wiki 里的任何文件"
        parts.append(f"这个任务要用到 Eric 的 LLM Wiki（{paths.wiki}）：先完整读 {paths.wiki_skill}，按里面的规则查找。wiki 权限：{mode}。")
    parts.append(GROUND_RULES)
    return "\n\n".join(parts)


def _command(spec: dict, prompt: str, paths: Paths) -> list[str]:
    command = ["agy", "-p", prompt, "--model", spec["model"], "--sandbox", "--output-format", "stream-json",
               "--json-schema", json.dumps(SCHEMA), "--print-timeout", f"{spec['minutes'] * 60}s"]
    if spec["wiki"]:
        command += ["--add-dir", str(paths.wiki), "--add-dir", str(paths.wiki_skill.parent)]
    return command


def _snapshot(root: Path) -> dict[str, tuple[int, int]]:
    seen = {}
    for folder, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            file = Path(folder) / name
            try:
                stat = file.stat()
            except OSError:
                continue
            seen[str(file.relative_to(root))] = (stat.st_mtime_ns, stat.st_size)
    return seen


def _changed(before: dict, after: dict) -> list[str]:
    return sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))


def _git_changed(workdir: Path) -> list[str]:
    return sorted(line[3:].split(" -> ")[-1] for line in _git(workdir, "status", "--porcelain", "--untracked-files=all").splitlines())


def _events(text: str):
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            yield event


def _call(spec: dict, prompt: str, workdir: Path, paths: Paths, runner: Runner, log: Path) -> dict:
    """One agy run; returns the fields it decides (status, summary or error, model, tokens)."""
    out = {"model": spec["model"]}
    try:
        code, stdout, stderr = runner(_command(spec, prompt, paths), workdir, spec["minutes"] * 60 + 60, log)
    except subprocess.TimeoutExpired:
        return out | {"status": "error", "error": f"agy 超过 {spec['minutes']} 分钟没有结束，已中止"}
    payload = next((e["result"] for e in _events(stdout) if e.get("event") == "result" and isinstance(e.get("result"), dict)), None)
    if payload is None:
        payload = {"status": "ERROR", "error": (stderr or stdout).strip()[-500:]}
    answer = payload.get("structured_output") or {}
    out |= {"conversation_id": payload.get("conversation_id"), "tokens": (payload.get("usage") or {}).get("total_tokens")}
    if code != 0 or payload.get("status") != "SUCCESS" or not answer:
        return out | {"status": "error", "error": payload.get("error") or (stderr or "agy 没有返回结构化结果").strip()[-500:]}
    return out | {"status": answer.get("status", "done"), "summary": answer.get("summary", ""),
                  "verification_claimed": answer.get("verification", ""), "questions": answer.get("questions", [])}


def run(task: dict, paths: Paths = Paths(), runner: Runner = _run_agy, opener: Opener = _open_panel) -> dict:
    spec = _check(task, paths)
    run_id = datetime.now(JST).strftime("%Y%m%d-%H%M%S-") + os.urandom(2).hex()
    workdir, branch = _prepare(spec, run_id, paths)
    log = paths.runs / f"{run_id}.log.jsonl"
    log.write_text(json.dumps({"event": "task", "goal": spec["goal"], "model": spec["model"], "workdir": str(workdir)},
                              ensure_ascii=False) + "\n")
    if task.get("panel", True):
        try:
            opener(run_id)
        except Exception:  # the panel is a convenience; never fail the task over it
            pass
    before = _snapshot(workdir) if not branch else {}
    wiki_before = _snapshot(paths.wiki) if spec["wiki"] else {}
    started = time.monotonic()
    result = {"run_id": run_id, "workdir": str(workdir), "branch": branch, "repo": str(spec["repo"]) if spec["repo"] else None,
              "verify": spec["verify"], "log": str(log)}
    prompt = _prompt(spec, paths)
    result |= _call(spec, prompt, workdir, paths, runner, log)
    if result["status"] == "error" and spec["model"] in ARGON and QUOTA_ERROR.search(result.get("error", "")):
        first = spec["model"]
        spec = {**spec, "model": FALLBACK_MODEL}
        prompt += "\n\n（换了模型接着做：这个目录里可能已有上一次没做完的改动，先看一下现状再继续。）"
        _log(log, {"event": "fallback", "from": first, "to": FALLBACK_MODEL})
        result |= _call(spec, prompt, workdir, paths, runner, log) | {"fallback_from": first}
    result["seconds"] = round(time.monotonic() - started)
    result["files_changed"] = _git_changed(workdir) if branch else [n for n in _changed(before, _snapshot(workdir)) if not n.startswith("inputs/")]
    if spec["wiki"]:
        result["wiki_changed"] = _changed(wiki_before, _snapshot(paths.wiki))
        if spec["wiki"] == "read" and result["wiki_changed"]:
            result["warning"] = "只读任务却改了 wiki 文件，请检查 wiki_changed"
    _log(log, {"event": "finished", "status": result["status"], "files_changed": result["files_changed"]})
    _ledger(paths, spec, result)
    return result


def _log(log: Path, event: dict) -> None:
    with log.open("a") as out:
        out.write(json.dumps(event, ensure_ascii=False) + "\n")


def _ledger(paths: Paths, spec: dict, result: dict) -> None:
    line = {"at": datetime.now(JST).isoformat(timespec="seconds"), "run_id": result["run_id"], "requester": spec["requester"],
            "model": result["model"], "fallback_from": result.get("fallback_from"), "repo": result["repo"], "wiki": spec["wiki"],
            "status": result["status"], "seconds": result["seconds"], "tokens": result.get("tokens"),
            "files_changed": len(result["files_changed"])}
    _log(paths.runs / "ledger.jsonl", line)


def cleanup(run_id: str, paths: Paths = Paths()) -> None:
    """Remove a finished run: its worktree and branch, or its folder. Merge what you want to keep first."""
    if not run_id or "/" in run_id or run_id.startswith("."):
        raise TaskError("run_id 不对")
    workdir = paths.runs / run_id
    if (workdir / ".git").is_file():  # a worktree: find its repo from the .git pointer
        repo = Path(_git(workdir, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()).parent
        _git(repo, "worktree", "remove", "--force", str(workdir))
        _git(repo, "branch", "-D", f"agy/{run_id}")
    elif workdir.is_dir():
        shutil.rmtree(workdir)
    (paths.runs / f"{run_id}.log.jsonl").unlink(missing_ok=True)


# ---- live view -------------------------------------------------------------------------------------------------------

def describe(event: dict) -> str | None:
    """One readable line per agy event, for the Rex pane. None: nothing worth showing."""
    kind = event.get("event")
    if kind == "task":
        return f"📋 任务：{event.get('goal', '')}\n   模型 {event.get('model')} · 目录 {event.get('workdir')}"
    if kind == "init":
        return "▶ agy 开始"
    if kind == "fallback":
        return f"⚠️ {event['from']} 额度用完，换 {event['to']} 接着做"
    if kind == "finished":
        files = ", ".join(event.get("files_changed") or []) or "无"
        return f"🏁 结束：{event.get('status')} · 改动文件：{files}"
    if kind == "result":
        result = event.get("result") or {}
        answer = result.get("structured_output") or {}
        tokens = (result.get("usage") or {}).get("total_tokens")
        return f"{'✅' if result.get('status') == 'SUCCESS' else '❌'} agy 交卷（{tokens} tokens）：{answer.get('summary') or result.get('error', '')}"
    step = event.get("step_update") or {}
    if kind == "step_update" and step.get("state") == "ACTIVE" and step.get("step_type") == "tool":
        params = (step.get("tool_info") or {}).get("parameters") or {}
        shown = next((str(v) for k, v in params.items() if k.lower() in ("commandline", "command", "path", "absolutepath", "targetfile", "query")), "")
        return f"🔧 {step.get('tool_name')} {shown[:120]}".rstrip()
    if kind == "step_update" and step.get("state") == "DONE" and step.get("step_type") == "agent_response":
        tokens = (step.get("usage") or {}).get("total_tokens")
        return f"💭 思考了一轮（{tokens} tokens，{step.get('duration_seconds', 0):.0f} 秒）"
    return None


def watch(run_id: str, paths: Paths = Paths(), follow: bool = True, out=sys.stdout) -> None:
    log = paths.runs / f"{run_id}.log.jsonl"
    print(f"agy 委托 {run_id}（Claude 分派，agy 执行）\n", file=out, flush=True)
    position, idle = 0, 0
    while True:
        lines = log.read_text().splitlines() if log.exists() else []
        for line in lines[position:]:
            for event in _events(line):
                if text := describe(event):
                    print(text, file=out, flush=True)
                if event.get("event") == "finished":
                    return
        position = len(lines)
        if not follow:
            return
        time.sleep(1)
        idle += 1
        if idle > (MAX_MINUTES + 10) * 60:
            return


# ---- Claude quota ----------------------------------------------------------------------------------------------------

def quota_mode(used: float) -> str:
    return "stop" if used >= STOP else "reserve" if used >= RESERVE else "conserve" if used >= CONSERVE else "normal"


def read_quota(paths: Paths = Paths(), now: float | None = None) -> dict:
    try:
        info = json.loads(paths.quota.read_text())
    except (OSError, ValueError):
        return {"known": False}
    now = time.time() if now is None else now
    resets = info.get("five_hour_resets")
    used = 0.0 if resets and now >= resets else float(info.get("five_hour", 0.0))
    return {"known": True, "five_hour": used, "seven_day": info.get("seven_day"), "mode": quota_mode(used),
            "age_minutes": round((now - info.get("seen_at", now)) / 60), "resets_at": resets}


def statusline(stdin: str, paths: Paths = Paths(), now: float | None = None) -> str:
    """Claude Code statusLine: record the 5-hour/7-day use it is given, and show it next to model and folder."""
    try:
        data = json.loads(stdin or "{}")
    except ValueError:
        return ""  # a status line must never crash the UI
    limits = data.get("rate_limits") or {}
    five, seven = limits.get("five_hour") or {}, limits.get("seven_day") or {}
    if "used_percentage" in five:
        info = {"five_hour": float(five["used_percentage"]) / 100, "five_hour_resets": five.get("resets_at"),
                "seven_day": float(seven.get("used_percentage", 0)) / 100, "seven_day_resets": seven.get("resets_at"),
                "seen_at": int(time.time() if now is None else now)}
        try:
            paths.quota.parent.mkdir(parents=True, exist_ok=True)
            tmp = paths.quota.with_name(f".{paths.quota.name}.{os.getpid()}.tmp")
            tmp.write_text(json.dumps(info))
            os.replace(tmp, paths.quota)
        except OSError:
            pass
    model = (data.get("model") or {}).get("display_name", "")
    folder = str((data.get("workspace") or {}).get("current_dir", "")).replace(str(HOME), "~", 1)
    parts = [model, folder]
    if "used_percentage" in five:
        parts.append(f"5h {float(five['used_percentage']):.0f}%")
    return " · ".join(p for p in parts if p)


def main(argv: list[str]) -> int:
    commands = {"run", "watch", "cleanup", "quota", "statusline"}
    if not argv or argv[0] not in commands:
        print(__doc__.split("Usage:")[1].strip(), file=sys.stderr)
        return 2
    try:
        if argv[0] == "statusline":
            print(statusline(sys.stdin.read()))
            return 0
        if argv[0] == "quota":
            print(json.dumps(read_quota(), ensure_ascii=False))
            return 0
        if argv[0] == "watch":
            watch(argv[1])
            return 0
        if argv[0] == "cleanup":
            cleanup(argv[1])
            print(json.dumps({"cleaned": argv[1]}))
            return 0
        task = json.loads(Path(argv[1]).read_text())
        if "--no-panel" in argv:
            task["panel"] = False
        result = run(task)
    except (TaskError, ValueError, OSError, IndexError, subprocess.CalledProcessError) as error:
        print(json.dumps({"status": "refused", "error": str(error)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
