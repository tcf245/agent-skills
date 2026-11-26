"""Hand one well-scoped task to agy (Gemini through Google's official Antigravity CLI); Claude judges and verifies.

The limits live in this code, not in the model (skill: skills/coding/agy-delegation/SKILL.md):
- A repo task runs in a fresh git worktree on branch `agy/<run-id>`; the original working tree is never touched.
  A task without a repo runs in its own folder with copies of its input files.
- agy always runs with `--sandbox`, a JSON schema for its answer, a time limit and an allowed model.
  agy has two quota buckets: "gemini" (Neon + Orchestrator Neon + Hydrogen + 3.8 Flash) and "argon" (Argon +
  Orchestrator Argon), each with a weekly
  and a 5-hour limit. Below 50% left (recorded with `agy-quota`) a bucket is protected: the task moves to the other one.
  On a quota error the task continues on the other bucket in the same folder; the empty one is skipped for 5 hours.
- Changed files are read from git / the folder, not from the model. This script runs outside the caller's sandbox,
  so it never runs arbitrary commands: the caller re-runs the verify command in its own sandbox.
- `wiki: read|write` adds Eric's LLM Wiki and the llm-wiki skill; wiki edits are listed after the run.
- `extra_files` writes per-run relative files (e.g. a plugin under `.agents/plugins/`) into the run folder before agy starts, without reporting them in `files_changed` or copying their contents into logs.
- Inside Rex, a pane opens on the right that shows agy working live (`watch`).

Usage:
  agy-delegate run <task.json> [--no-panel]   run a task; prints a JSON result
  agy-delegate watch <run-id>                 follow a run's progress (what the Rex pane shows)
  agy-delegate cleanup <run-id> [--discard]   remove a run's worktree/branch or folder and close its pane;
                                              refuses while the worktree has uncommitted changes unless --discard
  agy-delegate quota                          Claude's last known quota use and the mode it implies
  agy-delegate agy-quota [<bucket> <left%> [<refresh-hours>]]
                                              show or record how much of a bucket's weekly agy quota is left
  agy-delegate statusline                     Claude Code statusLine command: shows quota use and records it
"""
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
HOME = Path.home()
SCRIPT = Path(__file__).resolve()
MODELS = {f"gemini-4-{m}-{e}" for m in ("argon", "hydrogen", "neon") for e in ("low", "medium", "high")} | {
    "gemini-4-hydrogen-xhigh", "gemini-4-neon-xhigh", "gemini-3.8-flash-low", "gemini-3.8-flash-medium", "gemini-3.8-flash-high"}
ORCHESTRATOR = "gemini-pro-orchestrator-g1-pro"  # Orchestrator (Argon): Argon plans, sub-agents run; Argon's quota
ORCHESTRATOR_NEON = "gemini-pro-orchestrator-neon"  # Orchestrator (Neon): Neon plans, Hydrogen executes; shared gemini quota
MODELS |= {ORCHESTRATOR, ORCHESTRATOR_NEON}
ARGON = {f"gemini-4-argon-{e}" for e in ("low", "medium", "high")} | {ORCHESTRATOR}  # Argon's own quota
DEFAULT_MODEL = ORCHESTRATOR_NEON  # Eric 2026-11-19: Neon replaced Argon and joined the shared 5-hour + weekly pool
CHAIN = (ORCHESTRATOR_NEON, "gemini-4-argon-high")  # one model per quota bucket, in order of preference
PROTECT = 0.5  # Eric 2026-11-18: below half of a weekly quota left, protect that bucket instead of using it up
WEEK, FIVE_HOURS = 7 * 86400, 5 * 3600
QUOTA_ERROR = re.compile(r"quota|exhaust|rate.?limit|limit (reached|exceeded)|\b429\b", re.IGNORECASE)
DEFAULT_MINUTES, MAX_BASE_MINUTES = 30, 180
DEFAULT_CAP_MINUTES, MAX_CAP_MINUTES = 120, 240
STALL_MIN, EXTEND_MIN, WATCHDOG_POLL_S = 10, 15, 5
SECRET_PARTS = (".env", ".ssh", "credentials", ".pem", ".key", ".p12", "id_rsa", "token", "secret")
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules", ".agy-runs", ".agy"}
DECISIONS_HEADER = ["ts", "phase", "decision", "why", "evidence", "result"]
MAX_EXTRA_FILES = 20
MAX_EXTRA_BYTES = 200 * 1024

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
- 改仓库代码前，先读仓库根目录的 AGENTS.md（没有则读 CLAUDE.md）并遵守其中的规范；若任务目标与它冲突，按仓库规范执行，并在 summary/questions 里说明冲突。
- 不要读取或打印密钥：.env、令牌、证书、SSH 私钥、登录文件。
- 命令被 hook 拦下（“被硬规则 … 拦下”）时照报错里的改法做；觉得规则不对就写进 questions，不要换个写法绕过。
- 命令在沙箱里跑不了（缺网络、写不了缓存等）可以直接在沙箱外重跑，会自动批准；但不要 git commit/push、不要部署（kubectl、deploy.sh）、不要删当前目录以外的文件、不要往外部服务写数据（发消息、发 PR、改线上数据）。这些由 hook 硬拦。
- 做完后自己检查结果；给了验收命令就运行它，在 verification 里写命令和结果。
- 信息不够或需要决定时不要猜：status 写 needs_input，在 questions 里写问题。
- summary 简短：做了什么、没做什么、要注意什么。
- 改动超过 3 步时，在当前目录的 .agy/decisions.tsv 维护决策日志：第一行表头 ts\\tphase\\tdecision\\twhy\\tevidence\\tresult 六列，制表符分隔；每做一个决定追加一行（ts 用 ISO 时间；phase 如 read/plan/edit/verify；evidence 写证据指针，如 文件:行号、命令和它的结果摘要；result 写 ok/failed/superseded 等）；只追加，发现之前的决定错了就加一行新的写明覆盖哪一行，不改不删旧行。

效率（每多一步就多等一轮模型，按这些做）：
- 任务给了方案或文件就照做、只读这些；够用就停，不要通读仓库，同一个文件不要重复读。
- 合并步骤：几个文件用一条命令一起读（cat、sed -n），几项检查放进一条命令；同一个文件的多处改动合成一次写入，不要连着小改。
- 测试自己跑：和改动相关的用例与全量，哪个快跑哪个（整套一分钟内跑完就直接跑全量）；最后只跑一次完整的验收命令，不要重复跑整套，也不要加跑任务没要求的检查。
- Python 项目用 uv（/opt/homebrew/bin/uv），锁定的依赖已经装好，直接 uv run。沙箱读不了 ~/.asdf，那里的 python、uv 都用不了，不要去找。
- 沙箱里 git 用不了（worktree 的 .git 在沙箱外），不要跑 git；改了哪些文件由外面从 git 读。
- 环境问题（缺依赖、路径、版本）先用约束里给的办法；还不行就停下，写进 questions，不要反复试。
- 不要用 ask_permission、浏览器工具或子代理，任务明确要求时除外。
- verification 只写命令和结果，不贴长日志。"""


class TaskError(ValueError):
    """The task asks for something this script does not allow; nothing was run."""


@dataclass(frozen=True)
class Paths:
    workspace: Path = HOME / "workspace"
    runs: Path = HOME / "workspace" / ".agy-runs"
    wiki: Path = Path(os.environ.get("CREW_WIKI_DIR", HOME / "Library/Mobile Documents/iCloud~md~obsidian/Documents/LLM-Wiki"))
    wiki_skill: Path = HOME / ".agents/skills/llm-wiki/SKILL.md"
    quota: Path = Path(os.environ.get("CREW_QUOTA_FILE", HOME / ".local/share/agent-crew/quota.json"))
    agy_quota: Path = Path(os.environ.get("AGY_QUOTA_FILE", HOME / ".local/share/agent-crew/agy-quota.json"))


@dataclass(frozen=True)
class Budget:
    base_min: int = DEFAULT_MINUTES
    max_min: int = DEFAULT_CAP_MINUTES
    stall_min: float | None = None
    extend_min: int = EXTEND_MIN


class BudgetExceeded(Exception):
    def __init__(self, reason: str, elapsed_min: int, extended_min: int, stall_min: float, max_min: int,
                 stdout: str = "", stderr: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.elapsed_min = elapsed_min
        self.extended_min = extended_min
        self.stall_min = stall_min
        self.max_min = max_min
        self.stdout = stdout
        self.stderr = stderr


# runner(command, cwd, timeout, log) -> (returncode, stdout, stderr); the real one streams stdout into `log` as it comes.
Runner = Callable[[list[str], Path, int | Budget, Path], tuple[int, str, str]]
Opener = Callable[[str], "str | None"]  # returns the Rex block id of the pane it opened
Closer = Callable[[str], None]
Setup = Callable[[Path], dict]  # prepares a worktree's dependencies before agy starts; returns what it did
UV = "/opt/homebrew/bin/uv"  # agy's sandbox cannot read ~/.asdf, where the other uv lives


def agy_env(environ: dict | None = None) -> dict:
    """agy's environment without ~/.asdf on PATH: its sandbox cannot read ~/.asdf (probe 2026-11-22), so an asdf shim
    found first fails with 'operation not permitted' instead of falling through to /opt/homebrew/bin."""
    env = dict(os.environ if environ is None else environ)
    env["PATH"] = ":".join(p for p in env.get("PATH", "").split(":") if p and "/.asdf/" not in p + "/")
    return env


def _stamped(line: str) -> str:
    """The log line with the time it arrived (agy's events carry none), so slow turns can be found afterwards."""
    try:
        event = json.loads(line)
    except ValueError:
        return line
    if not isinstance(event, dict):
        return line
    return json.dumps({"at": datetime.now(JST).isoformat(timespec="milliseconds"), **event}, ensure_ascii=False) + "\n"


def _stall_minutes() -> float:
    raw = os.environ.get("AGY_STALL_MIN", "").strip()
    return float(raw) if raw else float(STALL_MIN)


def _decisions_stat(workdir: Path) -> tuple[int, int] | None:
    try:
        st = (workdir / ".agy" / "decisions.tsv").stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def _decisions_rows(workdir: Path) -> int:
    try:
        lines = (workdir / ".agy" / "decisions.tsv").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0
    return max(0, len(lines) - 1)


def budget_decision(now: float, started: float, base_s: float, cap_s: float, last_progress: float, deadline: float,
                    stall_s: float = STALL_MIN * 60, extend_s: float = EXTEND_MIN * 60) -> str:
    """Decide what the watchdog should do: 'continue', 'extend', 'kill-stalled', or 'kill-cap'."""
    if now - started >= cap_s:
        return "kill-cap"
    if now - last_progress >= stall_s:
        return "kill-stalled"
    if now >= deadline:
        return "extend"
    return "continue"


def _unpack_budget(timeout: int | Budget) -> tuple[float, float, float, float, int]:
    if isinstance(timeout, Budget):
        stall_m = timeout.stall_min if timeout.stall_min is not None else _stall_minutes()
        return (timeout.base_min * 60.0, timeout.max_min * 60.0, stall_m * 60.0,
                timeout.extend_min * 60.0, timeout.max_min)
    cap_s = float(timeout)
    return cap_s, cap_s, _stall_minutes() * 60.0, EXTEND_MIN * 60.0, round(cap_s / 60)


def _run_agy(command: list[str], cwd: Path, timeout: int | Budget, log: Path, *,
             clock: Callable[[], float] = time.monotonic, poll_s: float = WATCHDOG_POLL_S,
             popen: Callable[..., subprocess.Popen] = subprocess.Popen) -> tuple[int, str, str]:
    base_s, cap_s, stall_s, extend_s, max_min = _unpack_budget(timeout)
    lines: list[str] = []
    stderr_chunks: list[str] = []
    lock = threading.Lock()
    started = clock()
    progress = {"last": started}

    with log.open("a") as out, popen(command, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True, env=agy_env()) as proc:
        def read_stdout() -> None:
            if proc.stdout is None:
                return
            for line in proc.stdout:
                now_line = clock()
                stamped = _stamped(line)
                with lock:
                    out.write(stamped)
                    out.flush()
                    lines.append(line)
                    progress["last"] = now_line

        def read_stderr() -> None:
            if proc.stderr is not None:
                stderr_chunks.append(proc.stderr.read())

        reader = threading.Thread(target=read_stdout, daemon=True)
        err_reader = threading.Thread(target=read_stderr, daemon=True)
        reader.start()
        err_reader.start()

        deadline = started + base_s
        last_tsv = _decisions_stat(cwd)
        extended_min = 0
        while True:
            try:
                proc.wait(timeout=poll_s)
                break
            except subprocess.TimeoutExpired:
                pass
            now = clock()
            cur_tsv = _decisions_stat(cwd)
            with lock:
                if cur_tsv is not None and cur_tsv != last_tsv:
                    last_tsv = cur_tsv
                    progress["last"] = now
                last_prog = progress["last"]
            action = budget_decision(now, started, base_s, cap_s, last_prog, deadline, stall_s, extend_s)
            if action == "extend":
                new_deadline = min(deadline + extend_s, started + cap_s)
                by_min = round((new_deadline - deadline) / 60)
                deadline = new_deadline
                extended_min += by_min
                event = {"event": "extended", "by_min": by_min, "elapsed_min": round((now - started) / 60),
                         "decisions_rows": _decisions_rows(cwd)}
                with lock:
                    out.write(_stamped(json.dumps(event, ensure_ascii=False)))
                    out.flush()
            elif action in ("kill-stalled", "kill-cap"):
                proc.kill()
                proc.wait()
                reader.join(timeout=2)
                err_reader.join(timeout=2)
                reason = "stalled" if action == "kill-stalled" else "cap"
                raise BudgetExceeded(reason=reason, elapsed_min=round((now - started) / 60),
                                     extended_min=extended_min, stall_min=stall_s / 60, max_min=max_min,
                                     stdout="".join(lines), stderr="".join(stderr_chunks))
        reader.join()
        err_reader.join()
    return proc.returncode, "".join(lines), "".join(stderr_chunks)


def _open_panel(run_id: str) -> str | None:
    """Inside Rex, show the run live in a pane to the right of the caller's pane; silently skip otherwise.
    Returns the new pane's block id so cleanup can close it."""
    session, block = os.environ.get("REX_SESSION"), os.environ.get("REX_BLOCK")
    rex = shutil.which("rex")
    if not (session and block and rex):
        return None
    proc = subprocess.run([rex, "split", "-s", session, "-b", block, "--split=right", "--ratio", "45", "--focus=false",
                           "--keep-open", "--json", "--", sys.executable, str(SCRIPT), "watch", run_id],
                          capture_output=True, text=True, timeout=20, check=False)
    try:
        return json.loads(proc.stdout)["block_ids"][0]
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def _close_panel(block_id: str) -> None:
    rex = shutil.which("rex")
    if rex:
        subprocess.run([rex, "block", "close", block_id], capture_output=True, timeout=20, check=False)


def _sync_uv(workdir: Path) -> dict:
    """Install the repo's locked Python deps into the worktree, outside agy's sandbox: inside it, new package versions
    are blocked (403 'in cooldown'), so `uv run` there must find everything already synced. A fixed command, never the
    task's. Failing is reported, not fatal: agy can still read and edit."""
    command = [UV, "sync", "--frozen", "--quiet"]
    started = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=workdir, capture_output=True, text=True, timeout=300, env=agy_env(), check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": " ".join(command[1:]), "ok": False, "error": str(error)[-300:]}
    out = {"command": " ".join(command[1:]), "ok": proc.returncode == 0, "seconds": round(time.monotonic() - started)}
    return out if out["ok"] else out | {"error": (proc.stderr or proc.stdout).strip()[-300:]}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def _inside(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def _check_extra_files(raw: object, runs_dir: Path) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in raw.items()):
        raise TaskError("extra_files 必须是 路径→内容 的字符串字典")
    if len(raw) > MAX_EXTRA_FILES:
        raise TaskError(f"extra_files 最多 {MAX_EXTRA_FILES} 个文件")
    if sum(len(v.encode("utf-8")) for v in raw.values()) > MAX_EXTRA_BYTES:
        raise TaskError(f"extra_files 总大小不能超过 {MAX_EXTRA_BYTES // 1024} KB")
    probe = runs_dir.resolve()
    cleaned: dict[str, str] = {}
    for rel, content in raw.items():
        segs = rel.replace("\\", "/").split("/")
        if not rel or "\x00" in rel or rel.endswith(("/", "\\")) or segs[-1] in ("", "."):
            raise TaskError(f"extra_files 路径必须是相对文件路径：{rel!r}")
        p = Path(rel)
        if p.is_absolute() or rel.startswith("\\"):
            raise TaskError(f"extra_files 路径不能是绝对路径：{rel}")
        if ".." in p.parts or ".." in segs:
            raise TaskError(f"extra_files 路径不能包含 ..：{rel}")
        resolved = (probe / p).resolve()
        if not resolved.is_relative_to(probe) or resolved == probe:
            raise TaskError(f"extra_files 路径必须落在运行目录内：{rel}")
        norm = resolved.relative_to(probe).as_posix()
        if norm in cleaned:
            raise TaskError(f"extra_files 路径重复：{rel}")
        cleaned[norm] = content
    return cleaned


def _check(task: dict, paths: Paths) -> dict:
    if not isinstance(task.get("goal"), str) or not task["goal"].strip():
        raise TaskError("goal 不能为空")
    model = task.get("model", DEFAULT_MODEL)
    if model not in MODELS:
        raise TaskError(f"不允许的模型 {model}；可选：{', '.join(sorted(MODELS))}")
    minutes = int(task.get("timeout_min", DEFAULT_MINUTES))
    if not 1 <= minutes <= MAX_BASE_MINUTES:
        raise TaskError(f"timeout_min 要在 1 到 {MAX_BASE_MINUTES} 之间")
    raw_max = task.get("max_min")
    max_min = max(DEFAULT_CAP_MINUTES, minutes) if raw_max is None else int(raw_max)
    if not minutes <= max_min <= MAX_CAP_MINUTES:
        raise TaskError(f"max_min 要在 {minutes} 到 {MAX_CAP_MINUTES} 之间")
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
    extra_files = _check_extra_files(task.get("extra_files"), paths.runs)
    return {"goal": task["goal"].strip(), "model": model, "minutes": minutes, "max_min": max_min,
            "wiki": task.get("wiki"), "repo": repo, "files": files, "extra_files": extra_files,
            "rules": rules, "verify": task.get("verify"), "requester": task.get("requester", "")}


def _write_extra_files(workdir: Path, extra_files: dict[str, str]) -> None:
    root = workdir.resolve()
    for rel, content in extra_files.items():
        target = workdir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.parent.resolve().is_relative_to(root):
            raise TaskError(f"extra_files 路径必须落在运行目录内：{rel}")
        if target.is_symlink():
            raise TaskError(f"extra_files 目标不能是符号链接：{rel}")
        target.write_text(content, encoding="utf-8")
        if rel.endswith((".sh", ".py")):
            target.chmod(target.stat().st_mode | 0o111)


def _prepare(spec: dict, run_id: str, paths: Paths) -> tuple[Path, str | None]:
    workdir = paths.runs / run_id
    paths.runs.mkdir(parents=True, exist_ok=True)
    if spec["repo"]:
        branch = f"agy/{run_id}"
        _git(spec["repo"], "worktree", "add", "-q", "-b", branch, str(workdir), "HEAD")
    else:
        branch = None
        (workdir / "inputs").mkdir(parents=True)
        for file in spec["files"]:
            shutil.copy2(file, workdir / "inputs" / file.name)
    if spec["extra_files"]:
        _write_extra_files(workdir, spec["extra_files"])
    return workdir, branch


def _prompt(spec: dict, paths: Paths, workdir: Path) -> str:
    parts = [
        f"任务：{spec['goal']}",
        f"运行目录（绝对路径）：{workdir}。产出文件都写在这个目录里，用绝对路径写；终端的当前目录可能不是它。",
    ]
    if spec["files"] and not spec["repo"]:
        parts.append(f"输入文件在 {workdir / 'inputs'}（运行目录下的 inputs/）里；产出写在运行目录 {workdir}。")
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
    command = ["agy", "-p", prompt, "--model", spec["model"], "--sandbox", "--dangerously-skip-permissions",
               "--output-format", "stream-json", "--json-schema", json.dumps(SCHEMA),
               "--print-timeout", f"{spec['max_min'] * 60}s"]
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
    files = (line[3:].split(" -> ")[-1] for line in _git(workdir, "status", "--porcelain", "--untracked-files=all").splitlines())
    return sorted(f for f in files if f != ".agy" and not f.startswith(".agy/"))


def _collect_decisions(workdir: Path, dest: Path) -> dict | None:
    """Copy workdir/.agy/decisions.tsv to `dest` (beside the run log, kept across cleanup), count rows/bad rows, delete workdir/.agy."""
    agy_dir = workdir / ".agy"
    tsv = agy_dir / "decisions.tsv"
    decisions = None
    if tsv.is_file():
        shutil.copy2(tsv, dest)
        lines = dest.read_text(encoding="utf-8", errors="replace").splitlines()
        bad_rows = [1] if not lines or lines[0].split("\t") != DECISIONS_HEADER else []
        for lineno, line in enumerate(lines[1:], start=2):
            if len(line.split("\t")) != len(DECISIONS_HEADER):
                bad_rows.append(lineno)
        decisions = {"path": str(dest.resolve()), "rows": max(0, len(lines) - 1), "bad_rows": bad_rows}
    if agy_dir.is_dir() and not agy_dir.is_symlink():
        shutil.rmtree(agy_dir)
    elif agy_dir.exists() or agy_dir.is_symlink():
        agy_dir.unlink()
    return decisions


def _events(text: str):
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            yield event


def timing(stdout: str) -> dict:
    """Where a run's time went, from agy's own step durations: model turns vs tool calls."""
    turns, tools = [], []
    thinking = 0
    for event in _events(stdout):
        step = event.get("step_update") or {}
        if event.get("event") != "step_update" or step.get("state") != "DONE":
            continue
        if step.get("step_type") == "agent_response":
            turns.append(float(step.get("duration_seconds") or 0))
            thinking += int((step.get("usage") or {}).get("thinking_tokens") or 0)
        elif step.get("step_type") == "tool":
            tools.append(float(step.get("duration_seconds") or 0))
    return {"turns": len(turns), "model_seconds": round(sum(turns)), "longest_turn_seconds": round(max(turns, default=0)),
            "tool_calls": len(tools), "tool_seconds": round(sum(tools)), "thinking_tokens": thinking}


def _extended_minutes(log: Path) -> int:
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(int(e.get("by_min", 0)) for e in _events(text) if e.get("event") == "extended")


def _call(spec: dict, prompt: str, workdir: Path, paths: Paths, runner: Runner, log: Path) -> dict:
    """One agy run; returns the fields it decides (status, summary or error, model, tokens)."""
    out = {"model": spec["model"]}
    try:
        code, stdout, stderr = runner(_command(spec, prompt, paths), workdir, Budget(spec["minutes"], spec["max_min"]), log)
    except BudgetExceeded as err:
        if err.reason == "stalled":
            msg = f"停滞 {err.stall_min:g} 分钟没有进展，已中止（共跑了 {err.elapsed_min} 分钟）"
        else:
            msg = f"到了上限 {err.max_min} 分钟，已中止（续期 {err.extended_min} 分钟）"
        return out | {"status": "error", "error": msg, "extended_min": err.extended_min, "timing": timing(err.stdout)}
    except subprocess.TimeoutExpired:
        return out | {"status": "error", "error": f"agy 超过 {spec['minutes']} 分钟没有结束，已中止",
                      "extended_min": _extended_minutes(log)}
    payload = next((e["result"] for e in _events(stdout) if e.get("event") == "result" and isinstance(e.get("result"), dict)), None)
    if payload is None:
        payload = {"status": "ERROR", "error": (stderr or stdout).strip()[-500:]}
    answer = payload.get("structured_output") or {}
    out |= {"conversation_id": payload.get("conversation_id"), "tokens": (payload.get("usage") or {}).get("total_tokens"),
            "timing": timing(stdout), "extended_min": _extended_minutes(log)}
    if code != 0 or payload.get("status") != "SUCCESS" or not answer:
        return out | {"status": "error", "error": payload.get("error") or (stderr or "agy 没有返回结构化结果").strip()[-500:]}
    return out | {"status": answer.get("status", "done"), "summary": answer.get("summary", ""),
                  "verification_claimed": answer.get("verification", ""), "questions": answer.get("questions", [])}


def run(task: dict, paths: Paths = Paths(), runner: Runner = _run_agy, opener: Opener = _open_panel,
        setup: Setup = _sync_uv) -> dict:
    spec = _check(task, paths)
    run_id = datetime.now(JST).strftime("%Y%m%d-%H%M%S-") + os.urandom(2).hex()
    workdir, branch = _prepare(spec, run_id, paths)
    log = paths.runs / f"{run_id}.log.jsonl"
    log.write_text(json.dumps({"event": "task", "goal": spec["goal"], "model": spec["model"], "workdir": str(workdir)},
                              ensure_ascii=False) + "\n")
    if task.get("panel", True):
        try:
            pane = opener(run_id)
            if isinstance(pane, str) and pane:
                (paths.runs / f"{run_id}.panel").write_text(pane)
        except Exception:  # the panel is a convenience; never fail the task over it
            pass
    before = _snapshot(workdir) if not branch else {}
    wiki_before = _snapshot(paths.wiki) if spec["wiki"] else {}
    started = time.monotonic()
    result = {"run_id": run_id, "workdir": str(workdir), "branch": branch, "repo": str(spec["repo"]) if spec["repo"] else None,
              "verify": spec["verify"], "log": str(log), "extra_files": sorted(spec["extra_files"])}
    if branch and (workdir / "uv.lock").is_file():
        result["setup"] = setup(workdir)
        _log(log, {"event": "setup", **result["setup"]})
    prompt = _prompt(spec, paths, workdir)
    chosen = choose_model(spec["model"], agy_quota_left(paths))
    if chosen != spec["model"]:
        _log(log, {"event": "protected", "from": spec["model"], "to": chosen})
        result["model_swapped_from"] = spec["model"]
        spec = {**spec, "model": chosen}
    result |= _call(spec, prompt, workdir, paths, runner, log)
    first, tried = spec["model"], {bucket(spec["model"])}
    while result["status"] == "error" and QUOTA_ERROR.search(result.get("error", "")):
        record_agy_quota(bucket(spec["model"]), 0, paths, refresh_hours=FIVE_HOURS / 3600)  # may be the 5-hour limit
        nxt = _next_model(tried, agy_quota_left(paths))
        if nxt is None:
            break
        tried.add(bucket(nxt))
        _log(log, {"event": "fallback", "from": spec["model"], "to": nxt})
        spec = {**spec, "model": nxt}
        if "（换了模型接着做" not in prompt:
            prompt += "\n\n（换了模型接着做：这个目录里可能已有上一次没做完的改动，先看一下现状再继续。）"
        result |= _call(spec, prompt, workdir, paths, runner, log) | {"fallback_from": first}
    result["seconds"] = round(time.monotonic() - started)
    if decisions := _collect_decisions(workdir, paths.runs / f"{run_id}.decisions.tsv"):
        result["decisions"] = decisions
    extra_paths = set(spec["extra_files"])
    result["files_changed"] = (
        [f for f in _git_changed(workdir) if f not in extra_paths]
        if branch
        else [n for n in _changed(before, _snapshot(workdir)) if not n.startswith("inputs/") and n not in extra_paths]
    )
    warnings = []
    if spec["wiki"]:
        result["wiki_changed"] = _changed(wiki_before, _snapshot(paths.wiki))
        if spec["wiki"] == "read" and result["wiki_changed"]:
            warnings.append("只读任务却改了 wiki 文件，请检查 wiki_changed")
    if "decisions" not in result and len(result["files_changed"]) > 3:
        warnings.append(f"改了 {len(result['files_changed'])} 个文件但没有 decisions.tsv")
    if warnings:
        result["warning"] = "；".join(warnings)
    _log(log, {"event": "finished", "status": result["status"], "files_changed": result["files_changed"]})
    _ledger(paths, spec, result)
    return result


def _log(log: Path, event: dict) -> None:
    with log.open("a") as out:
        out.write(json.dumps(event, ensure_ascii=False) + "\n")


def _ledger(paths: Paths, spec: dict, result: dict) -> None:
    line = {"at": datetime.now(JST).isoformat(timespec="seconds"), "run_id": result["run_id"], "requester": spec["requester"],
            "goal": spec["goal"][:200], "model": result["model"],
            "conversation_id": result.get("conversation_id"), "timing": result.get("timing"), "fallback_from": result.get("fallback_from"), "repo": result["repo"], "wiki": spec["wiki"],
            "status": result["status"], "seconds": result["seconds"], "tokens": result.get("tokens"),
            "files_changed": len(result["files_changed"])}
    _log(paths.runs / "ledger.jsonl", line)


def cleanup(run_id: str, paths: Paths = Paths(), closer: Closer = _close_panel, discard: bool = False) -> None:
    """Remove a finished run: its worktree and branch, or its folder, and close its Rex pane. Merge what you want to keep first.
    A worktree with uncommitted changes is kept unless `discard` (2026-11-19: a chained cleanup deleted 17 unlanded files)."""
    if not run_id or "/" in run_id or run_id.startswith("."):
        raise TaskError("run_id 不对")
    workdir = paths.runs / run_id
    if (workdir / ".git").is_file():  # a worktree: find its repo from the .git pointer
        changed = _git(workdir, "status", "--porcelain").splitlines()
        if changed and not discard:
            raise TaskError(f"{run_id} 还有 {len(changed)} 个未提交的改动，没删。先 git add -A、提交并合到目标分支再清理；"
                            f"确定不要这些改动，就加 --discard：agy-delegate cleanup {run_id} --discard")
        repo = Path(_git(workdir, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()).parent
        _git(repo, "worktree", "remove", "--force", str(workdir))
        _git(repo, "branch", "-D", f"agy/{run_id}")
    elif workdir.is_dir():
        shutil.rmtree(workdir)
    (paths.runs / f"{run_id}.log.jsonl").unlink(missing_ok=True)
    panel = paths.runs / f"{run_id}.panel"
    if panel.is_file():
        try:
            closer(panel.read_text().strip())
        except Exception:  # the pane is a convenience; never fail cleanup over it
            pass
        panel.unlink()


# ---- live view -------------------------------------------------------------------------------------------------------

def describe(event: dict) -> str | None:
    """One readable line per agy event, for the Rex pane. None: nothing worth showing."""
    kind = event.get("event")
    if kind == "task":
        return f"📋 任务：{event.get('goal', '')}\n   模型 {event.get('model')} · 目录 {event.get('workdir')}"
    if kind == "setup":
        return f"📦 {event.get('command')}：{'好了' if event.get('ok') else '失败 ' + str(event.get('error', ''))}"
    if kind == "init":
        return "▶ agy 开始"
    if kind == "fallback":
        return f"⚠️ {event['from']} 额度用完，换 {event['to']} 接着做"
    if kind == "protected":
        return f"🛡️ {event['from']} 的额度剩不到一半，留着；改用 {event['to']}"
    if kind == "extended":
        return f"⏱️ 有进展，续期 {event.get('by_min')} 分钟（已跑 {event.get('elapsed_min')} 分钟）"
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
        if idle > (MAX_CAP_MINUTES + 10) * 60:
            return


# ---- agy quota (per bucket, as agy's quota page groups them) ---------------------------------------------------------

BUCKETS = {"gemini": "gemini", "hydrogen": "gemini", "flash": "gemini", "argon": "argon"}  # names accepted -> bucket


def bucket(model: str) -> str:
    return "argon" if model in ARGON else "gemini"


def agy_quota_left(paths: Paths = Paths(), now: float | None = None) -> dict[str, float]:
    """Share of each bucket's quota left, from readings that have not expired. Unknown buckets are absent."""
    try:
        data = json.loads(paths.agy_quota.read_text())
    except (OSError, ValueError):
        return {}
    now = time.time() if now is None else now
    return {name: float(v["left"]) for name, v in data.items()
            if isinstance(v, dict) and now < v.get("expires_at", v.get("seen_at", 0) + WEEK)}


def record_agy_quota(name: str, left_percent: float, paths: Paths = Paths(), refresh_hours: float | None = None,
                     now: float | None = None) -> dict:
    """Record what agy's quota page shows; the reading expires when the page says the bucket refreshes (default a week)."""
    if name not in BUCKETS or not 0 <= float(left_percent) <= 100:
        raise TaskError("用法：agy-quota <gemini|argon> <剩余百分比 0-100> [几小时后刷新]（hydrogen、flash 都算 gemini）")
    try:
        data = json.loads(paths.agy_quota.read_text())
    except (OSError, ValueError):
        data = {}
    now = time.time() if now is None else now
    expires = now + (float(refresh_hours) * 3600 if refresh_hours is not None else WEEK)
    data[BUCKETS[name]] = {"left": round(float(left_percent) / 100, 4), "seen_at": int(now), "expires_at": int(expires)}
    paths.agy_quota.parent.mkdir(parents=True, exist_ok=True)
    tmp = paths.agy_quota.with_name(f".{paths.agy_quota.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(data))
    os.replace(tmp, paths.agy_quota)
    return data


def _ok(name: str, left: dict[str, float]) -> bool:
    return left.get(name, 1.0) >= PROTECT  # never recorded: assume plenty


def choose_model(model: str, left: dict[str, float]) -> str:
    """The asked model if its bucket has half or more left; else the first in CHAIN that has; else the one with most left."""
    if _ok(bucket(model), left):
        return model
    return next((m for m in CHAIN if _ok(bucket(m), left)), max(CHAIN, key=lambda m: left.get(bucket(m), 1.0)))


def _next_model(tried: set[str], left: dict[str, float]) -> str | None:
    """After a quota error: the model of a bucket not tried yet that still has something left, protected ones last."""
    rest = [m for m in CHAIN if bucket(m) not in tried and left.get(bucket(m), 1.0) > 0]
    return next((m for m in rest if _ok(bucket(m), left)), rest[-1] if rest else None)


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
    commands = {"run", "watch", "cleanup", "quota", "agy-quota", "statusline"}
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
        if argv[0] == "agy-quota":
            paths = Paths()
            if len(argv) > 1:
                record_agy_quota(argv[1], float(argv[2]), paths, float(argv[3]) if len(argv) > 3 else None)
            print(json.dumps({name: {"left": left} for name, left in agy_quota_left(paths).items()}, ensure_ascii=False))
            return 0
        if argv[0] == "watch":
            watch(argv[1])
            return 0
        if argv[0] == "cleanup":
            cleanup(argv[1], discard="--discard" in argv)
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
