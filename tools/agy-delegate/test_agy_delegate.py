"""Run: uv run --with pytest pytest -q tools/agy-delegate"""
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import agy_delegate as agy  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def env(tmp_path):
    workspace = tmp_path / "workspace"
    repo = workspace / "proj"
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    (repo / "a.txt").write_text("old\n")
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init")
    wiki = tmp_path / "wiki"
    (wiki / "wiki").mkdir(parents=True)
    (wiki / "wiki" / "page.md").write_text("hello\n")
    skill = tmp_path / "skills" / "llm-wiki"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: llm-wiki\n---\n")
    return agy.Paths(workspace=workspace, runs=workspace / ".agy-runs", wiki=wiki, wiki_skill=skill / "SKILL.md",
                     quota=tmp_path / "quota.json")


def _stream(result: dict) -> str:
    events = [{"event": "init", "init": {"model": "x"}},
              {"event": "step_update", "step_update": {"state": "ACTIVE", "step_type": "tool", "tool_name": "read_file",
                                                       "tool_info": {"parameters": {"Path": "/x/a.txt"}}}},
              {"event": "result", "result": result}]
    return "\n".join(json.dumps(e) for e in events) + "\n"


OK = {"status": "SUCCESS", "conversation_id": "c1", "structured_output": {"status": "done", "summary": "改好了"},
      "usage": {"total_tokens": 1234}}


class FakeAgy:
    """Stands in for the agy CLI: records the command, optionally edits files, streams like `--output-format stream-json`."""

    def __init__(self, edit=None, result=None, returncode=0):
        self.edit, self.returncode, self.calls = edit, returncode, []
        self.result = result or OK

    def __call__(self, command, cwd, timeout, log):
        self.calls.append({"command": command, "cwd": Path(cwd), "timeout": timeout})
        if self.edit:
            self.edit(Path(cwd))
        out = _stream(self.result)
        with log.open("a") as f:
            f.write(out)
        return self.returncode, out, ""


def no_panel(run_id):
    pass


def go(task, env, fake=None, opener=no_panel):
    return agy.run(task, paths=env, runner=fake or FakeAgy(), opener=opener)


def repo(env):
    return str(env.workspace / "proj")


def model_of(call):
    return call["command"][call["command"].index("--model") + 1]


def test_a_repo_task_runs_in_its_own_worktree_and_leaves_the_original_untouched(env):
    result = go({"goal": "改 a.txt", "repo": repo(env)}, env, FakeAgy(edit=lambda cwd: (cwd / "a.txt").write_text("new\n")))
    workdir = Path(result["workdir"])
    assert workdir.is_relative_to(env.runs)
    assert (env.workspace / "proj" / "a.txt").read_text() == "old\n"
    assert (workdir / "a.txt").read_text() == "new\n"
    assert result["branch"] == f"agy/{result['run_id']}"
    assert result["files_changed"] == ["a.txt"]  # taken from git, not from the model
    assert result["status"] == "done" and result["summary"] == "改好了"


def test_the_command_is_sandboxed_streamed_structured_and_on_argon_by_default(env):
    fake = FakeAgy()
    go({"goal": "x", "repo": repo(env)}, env, fake)
    command = fake.calls[0]["command"]
    assert command[0] == "agy" and "--sandbox" in command and model_of(fake.calls[0]) == "gemini-4-argon-high"
    assert command[command.index("--output-format") + 1] == "stream-json"
    assert json.loads(command[command.index("--json-schema") + 1])["required"] == ["status", "summary"]
    assert "--dangerously-skip-permissions" not in command


@pytest.mark.parametrize("model", ["claude-opus-5-5-high", "claude-sonnet-5-5-high"])
def test_claude_inside_agy_is_not_allowed(env, model):
    """Eric 2026-11-17: hard to use, and its quota is gone after a hello."""
    with pytest.raises(agy.TaskError):
        go({"goal": "x", "repo": repo(env), "model": model}, env)


@pytest.mark.parametrize("path", ["/etc", "../outside"])
def test_repos_outside_the_workspace_are_refused(env, path):
    with pytest.raises(agy.TaskError):
        go({"goal": "x", "repo": path}, env)


def test_secret_files_are_never_copied_in(env):
    (env.workspace / "proj" / ".env").write_text("TOKEN=1")
    with pytest.raises(agy.TaskError):
        go({"goal": "x", "files": [str(env.workspace / "proj" / ".env")]}, env)


def test_a_task_without_a_repo_gets_a_run_folder_with_copies_of_its_inputs(env):
    result = go({"goal": "翻译", "files": [str(env.workspace / "proj" / "a.txt")]}, env,
                FakeAgy(edit=lambda cwd: (cwd / "out.md").write_text("draft")))
    assert (Path(result["workdir"]) / "inputs" / "a.txt").read_text() == "old\n"
    assert result["branch"] is None and result["files_changed"] == ["out.md"]


def test_the_prompt_carries_goal_rules_and_the_ground_rules(env):
    fake = FakeAgy()
    go({"goal": "把文案翻成日语", "rules": ["键名不改"], "repo": repo(env)}, env, fake)
    prompt = fake.calls[0]["command"][fake.calls[0]["command"].index("-p") + 1]
    assert "把文案翻成日语" in prompt and "键名不改" in prompt
    for rule in ("commit", "push", "deploy", ".env"):
        assert rule in prompt


def test_wiki_tasks_get_the_wiki_and_the_llm_wiki_skill(env):
    fake = FakeAgy()
    go({"goal": "查一下", "wiki": "read"}, env, fake)
    command = fake.calls[0]["command"]
    added = [command[i + 1] for i, a in enumerate(command) if a == "--add-dir"]
    assert str(env.wiki) in added and str(env.wiki_skill.parent) in added
    assert str(env.wiki_skill) in command[command.index("-p") + 1]


def test_no_wiki_access_unless_asked(env):
    fake = FakeAgy()
    go({"goal": "x", "repo": repo(env)}, env, fake)
    assert str(env.wiki) not in fake.calls[0]["command"]


def test_wiki_edits_are_listed_and_flagged_on_a_read_only_task(env):
    result = go({"goal": "查一下", "wiki": "read"}, env, FakeAgy(edit=lambda cwd: (env.wiki / "wiki" / "page.md").write_text("x\n")))
    assert result["wiki_changed"] == ["wiki/page.md"] and "wiki" in result["warning"]


def test_agy_failing_is_reported_not_hidden(env):
    result = go({"goal": "x", "repo": repo(env)}, env, FakeAgy(returncode=1, result={"status": "ERROR", "error": "boom"}))
    assert result["status"] == "error" and "boom" in result["error"]


class ArgonOutOfQuota(FakeAgy):
    def __call__(self, command, cwd, timeout, log):
        model = command[command.index("--model") + 1]
        if model in agy.ARGON:
            self.calls.append({"command": command, "cwd": Path(cwd), "timeout": timeout})
            out = _stream({"status": "ERROR", "error": "RESOURCE_EXHAUSTED: quota exceeded for Gemini 4 Argon weekly limit"})
            return 1, out, ""
        return super().__call__(command, cwd, timeout, log)


@pytest.mark.parametrize("first", ["gemini-4-argon-high", agy.ORCHESTRATOR])
def test_when_argon_is_out_of_quota_the_task_falls_back_to_flash_in_the_same_folder(env, first):
    fake = ArgonOutOfQuota()
    result = go({"goal": "x", "repo": repo(env), "model": first}, env, fake)
    assert [model_of(c) for c in fake.calls] == [first, "gemini-3.8-flash-high"]
    assert fake.calls[0]["cwd"] == fake.calls[1]["cwd"]
    assert result["status"] == "done" and result["model"] == "gemini-3.8-flash-high" and result["fallback_from"] == first


def test_other_failures_do_not_fall_back(env):
    fake = FakeAgy(returncode=1, result={"status": "ERROR", "error": "syntax error"})
    result = go({"goal": "x", "repo": repo(env)}, env, fake)
    assert len(fake.calls) == 1 and "fallback_from" not in result


def test_every_run_is_written_to_the_ledger(env):
    go({"goal": "x", "repo": repo(env)}, env)
    line = json.loads((env.runs / "ledger.jsonl").read_text().splitlines()[-1])
    assert line["model"] == "gemini-4-argon-high" and line["status"] == "done" and line["tokens"] == 1234


def test_cleanup_removes_the_worktree_branch_and_log(env):
    result = go({"goal": "x", "repo": repo(env)}, env)
    agy.cleanup(result["run_id"], paths=env)
    assert not Path(result["workdir"]).exists() and not Path(result["log"]).exists()
    assert result["branch"] not in _git(env.workspace / "proj", "branch", "--list")


# ---- the Rex pane ----

def test_the_panel_is_opened_for_the_run_and_can_be_turned_off(env):
    opened = []
    result = go({"goal": "x", "repo": repo(env)}, env, opener=opened.append)
    assert opened == [result["run_id"]]
    opened.clear()
    go({"goal": "x", "repo": repo(env), "panel": False}, env, opener=opened.append)
    assert opened == []


def test_a_broken_panel_never_fails_the_task(env):
    def broken(run_id):
        raise RuntimeError("rex is gone")
    assert go({"goal": "x", "repo": repo(env)}, env, opener=broken)["status"] == "done"


def test_watch_shows_the_task_the_tools_and_the_answer(env):
    result = go({"goal": "改 a.txt", "repo": repo(env)}, env, FakeAgy(edit=lambda cwd: (cwd / "a.txt").write_text("n")))
    out = io.StringIO()
    agy.watch(result["run_id"], paths=env, follow=False, out=out)
    text = out.getvalue()
    assert "改 a.txt" in text and "read_file /x/a.txt" in text and "改好了" in text and "a.txt" in text.splitlines()[-1]


# ---- Claude quota ----

def test_the_statusline_records_claudes_quota_and_shows_it(env):
    stdin = json.dumps({"model": {"display_name": "Opus"}, "workspace": {"current_dir": "/x"},
                        "rate_limits": {"five_hour": {"used_percentage": 62.4, "resets_at": 4102444800},
                                        "seven_day": {"used_percentage": 30, "resets_at": 4102444800}}})
    assert agy.statusline(stdin, paths=env, now=1000) == "Opus · /x · 5h 62%"
    quota = agy.read_quota(env, now=1000)
    assert quota["five_hour"] == pytest.approx(0.624) and quota["mode"] == "conserve"


def test_a_statusline_without_limits_leaves_the_record_alone(env):
    env.quota.write_text(json.dumps({"five_hour": 0.9, "five_hour_resets": 4102444800, "seen_at": 0}))
    assert agy.statusline(json.dumps({"model": {"display_name": "Opus"}}), paths=env) == "Opus"
    assert agy.read_quota(env, now=10)["mode"] == "reserve"


def test_a_bad_statusline_input_still_prints_something(env):
    assert agy.statusline("not json", paths=env) == ""


def test_quota_resets_with_the_window(env):
    env.quota.write_text(json.dumps({"five_hour": 0.97, "five_hour_resets": 2000, "seen_at": 0}))
    assert agy.read_quota(env, now=1000)["mode"] == "stop"
    assert agy.read_quota(env, now=2001)["mode"] == "normal"
