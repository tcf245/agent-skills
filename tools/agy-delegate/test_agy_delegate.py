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
                     quota=tmp_path / "quota.json", agy_quota=tmp_path / "agy-quota.json")


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


def test_the_command_is_sandboxed_skips_permissions_streamed_structured_and_on_orchestrator_neon_by_default(env):
    fake = FakeAgy()
    go({"goal": "x", "repo": repo(env)}, env, fake)
    command = fake.calls[0]["command"]
    assert command[0] == "agy" and "--sandbox" in command and "--dangerously-skip-permissions" in command
    assert command.index("--dangerously-skip-permissions") == command.index("--sandbox") + 1
    assert model_of(fake.calls[0]) == "gemini-pro-orchestrator-neon"
    assert command[command.index("--output-format") + 1] == "stream-json"
    assert json.loads(command[command.index("--json-schema") + 1])["required"] == ["status", "summary"]


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
    assert "沙箱外" in agy.GROUND_RULES
    for rule in ("commit", "push", "deploy", ".env", "沙箱外"):
        assert rule in prompt


def test_the_prompt_carries_the_efficiency_rules(env):
    fake = FakeAgy()
    go({"goal": "改一个函数", "repo": repo(env)}, env, fake)
    prompt = fake.calls[0]["command"][fake.calls[0]["command"].index("-p") + 1]
    for rule in ("一条命令", "一次写入", "不要重复读", "只跑一次", "ask_permission", "子代理"):
        assert rule in prompt, rule


def test_wiki_tasks_get_the_wiki_and_the_llm_wiki_skill(env):
    fake = FakeAgy()
    go({"goal": "查一下", "wiki": "read"}, env, fake)
    command = fake.calls[0]["command"]
    added = [command[i + 1] for i, a in enumerate(command) if a == "--add-dir"]
    assert str(env.wiki) in added and str(env.wiki_skill.parent) in added
    assert str(env.wiki_skill) in command[command.index("-p") + 1]


def test_agy_delegate_prompt_includes_workdir_path(env):
    """反馈 FB-074"""
    fake_wiki = FakeAgy()
    res_wiki = go({"goal": "查一下", "wiki": "read"}, env, fake_wiki)
    cmd_wiki = fake_wiki.calls[0]["command"]
    prompt_wiki = cmd_wiki[cmd_wiki.index("-p") + 1]
    assert Path(res_wiki["workdir"]).is_absolute()
    assert res_wiki["workdir"] in prompt_wiki
    assert "产出" in prompt_wiki and "写在这个目录" in prompt_wiki

    fake_repo = FakeAgy()
    res_repo = go({"goal": "改 a.txt", "repo": repo(env)}, env, fake_repo)
    cmd_repo = fake_repo.calls[0]["command"]
    prompt_repo = cmd_repo[cmd_repo.index("-p") + 1]
    assert Path(res_repo["workdir"]).is_absolute()
    assert res_repo["workdir"] in prompt_repo
    assert "产出" in prompt_repo and "写在这个目录" in prompt_repo


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
def test_when_argon_is_out_of_quota_the_task_falls_back_to_orchestrator_neon_in_the_same_folder(env, first):
    fake = ArgonOutOfQuota()
    result = go({"goal": "x", "repo": repo(env), "model": first}, env, fake)
    assert [model_of(c) for c in fake.calls] == [first, "gemini-pro-orchestrator-neon"]
    assert fake.calls[0]["cwd"] == fake.calls[1]["cwd"]
    assert result["status"] == "done" and result["model"] == "gemini-pro-orchestrator-neon" and result["fallback_from"] == first


def test_other_failures_do_not_fall_back(env):
    fake = FakeAgy(returncode=1, result={"status": "ERROR", "error": "syntax error"})
    result = go({"goal": "x", "repo": repo(env)}, env, fake)
    assert len(fake.calls) == 1 and "fallback_from" not in result


def test_every_run_is_written_to_the_ledger(env):
    go({"goal": "x", "repo": repo(env)}, env)
    line = json.loads((env.runs / "ledger.jsonl").read_text().splitlines()[-1])
    assert line["model"] == "gemini-pro-orchestrator-neon" and line["status"] == "done" and line["tokens"] == 1234


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


def test_cleanup_refuses_to_delete_uncommitted_work(env):
    """2026-11-19: cleanup ran after a failed `git add` (chained with `;`) and force-removed 17 changed files.
    Uncommitted changes in the worktree now stop cleanup; throwing them away takes an explicit discard."""
    result = go({"goal": "x", "repo": repo(env)}, env, FakeAgy(edit=lambda cwd: (cwd / "a.txt").write_text("n")))
    with pytest.raises(agy.TaskError, match="--discard"):
        agy.cleanup(result["run_id"], paths=env)
    assert (Path(result["workdir"]) / "a.txt").read_text() == "n"
    agy.cleanup(result["run_id"], paths=env, discard=True)
    assert not Path(result["workdir"]).exists()


def test_cleanup_closes_the_runs_panel(env):
    result = go({"goal": "x", "repo": repo(env)}, env, opener=lambda run_id: "block:pane-1")
    closed = []
    agy.cleanup(result["run_id"], paths=env, closer=closed.append)
    assert closed == ["block:pane-1"]
    assert not list(env.runs.glob("*.panel"))


def test_cleanup_without_a_panel_closes_nothing(env):
    result = go({"goal": "x", "repo": repo(env), "panel": False}, env)
    closed = []
    agy.cleanup(result["run_id"], paths=env, closer=closed.append)
    assert closed == []


def test_a_broken_closer_never_fails_cleanup(env):
    result = go({"goal": "x", "repo": repo(env)}, env, opener=lambda run_id: "block:pane-1")
    def broken(block_id):
        raise RuntimeError("rex is gone")
    agy.cleanup(result["run_id"], paths=env, closer=broken)
    assert not Path(result["workdir"]).exists()


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


# ---- agy quota: protect a model once less than half of its quota is left (Eric 2026-11-18) ----------------------------
# agy quota page: Neon (+ Orchestrator Neon, since 2026-11-19), Hydrogen and 3.8 Flash share the "gemini" bucket; Argon (+ Orchestrator Argon) has its own.

class OutOfQuota(FakeAgy):
    """Every model of the given buckets answers with a quota error."""

    def __init__(self, *buckets):
        super().__init__()
        self.buckets = buckets

    def __call__(self, command, cwd, timeout, log):
        if agy.bucket(model_of({"command": command})) in self.buckets:
            self.calls.append({"command": command, "cwd": Path(cwd), "timeout": timeout})
            return 1, _stream({"status": "ERROR", "error": "RESOURCE_EXHAUSTED: quota exceeded"}), ""
        return super().__call__(command, cwd, timeout, log)


def test_neon_hydrogen_and_flash_share_the_gemini_bucket():
    assert {agy.bucket(m) for m in ("gemini-pro-orchestrator-neon", "gemini-4-neon-high", "gemini-4-hydrogen-high", "gemini-3.8-flash-low")} == {"gemini"}
    assert {agy.bucket(m) for m in ("gemini-4-argon-low", agy.ORCHESTRATOR)} == {"argon"}


def test_a_model_with_less_than_half_its_quota_left_is_swapped_for_one_with_more(env):
    """Eric 2026-11-18: Argon's weekly quota was down to 19%; below 50% a model is protected, not used up."""
    agy.record_agy_quota("argon", 18.74, env)
    fake = FakeAgy()
    result = go({"goal": "x", "repo": repo(env), "model": agy.ORCHESTRATOR}, env, fake)
    assert model_of(fake.calls[0]) == "gemini-pro-orchestrator-neon"
    assert result["model_swapped_from"] == agy.ORCHESTRATOR


def test_a_model_with_half_or_more_left_is_used_as_asked(env):
    agy.record_agy_quota("argon", 50, env)
    fake = FakeAgy()
    result = go({"goal": "x", "repo": repo(env), "model": "gemini-4-argon-high"}, env, fake)
    assert model_of(fake.calls[0]) == "gemini-4-argon-high" and "model_swapped_from" not in result


def test_flash_asked_for_bulk_text_stays_flash_while_gemini_is_fine(env):
    fake = FakeAgy()
    go({"goal": "x", "repo": repo(env), "model": "gemini-3.8-flash-high"}, env, fake)
    assert model_of(fake.calls[0]) == "gemini-3.8-flash-high"


def test_when_every_bucket_is_low_the_one_with_most_left_is_used(env):
    agy.record_agy_quota("gemini", 30, env)
    agy.record_agy_quota("argon", 40, env)
    fake = FakeAgy()
    go({"goal": "x", "repo": repo(env)}, env, fake)
    assert model_of(fake.calls[0]) == "gemini-4-argon-high"


def test_a_reading_expires_when_its_quota_refreshes(env):
    """The quota page says when each bucket refreshes; after that the reading says nothing."""
    agy.record_agy_quota("argon", 18.74, env, refresh_hours=157, now=0)
    assert agy.agy_quota_left(env, now=156 * 3600) == {"argon": 0.1874}
    assert agy.agy_quota_left(env, now=158 * 3600) == {}


def test_a_reading_without_a_refresh_time_lasts_a_week(env):
    agy.record_agy_quota("gemini", 10, env, now=0)
    assert agy.agy_quota_left(env, now=8 * 86400) == {}


def test_running_out_mid_task_moves_to_the_other_bucket_and_marks_it_empty_for_five_hours(env):
    """A quota error may be the 5-hour limit, so the bucket is only marked empty for 5 hours."""
    fake = OutOfQuota("gemini")
    result = go({"goal": "x", "repo": repo(env)}, env, fake)
    assert [model_of(c) for c in fake.calls] == ["gemini-pro-orchestrator-neon", "gemini-4-argon-high"]
    assert fake.calls[0]["cwd"] == fake.calls[1]["cwd"]
    assert result["status"] == "done" and result["fallback_from"] == "gemini-pro-orchestrator-neon"
    import time
    assert agy.agy_quota_left(env)["gemini"] == 0
    assert agy.agy_quota_left(env, now=time.time() + 6 * 3600) == {}


def test_when_both_buckets_are_out_the_error_is_returned(env):
    fake = OutOfQuota("gemini", "argon")
    result = go({"goal": "x", "repo": repo(env)}, env, fake)
    assert len(fake.calls) == 2 and result["status"] == "error"


def test_agy_quota_can_be_recorded_from_the_command_line(env, monkeypatch, capsys):
    monkeypatch.setattr(agy, "Paths", lambda: env)
    assert agy.main(["agy-quota", "argon", "18.74", "157"]) == 0
    assert json.loads(capsys.readouterr().out)["argon"]["left"] == 0.1874
    assert agy.main(["agy-quota", "hydrogen", "99"]) == 0  # Hydrogen and Flash are names of the gemini bucket
    assert "gemini" in json.loads(capsys.readouterr().out)


# ---- 2026-11-22: speed (effort), tests runnable inside agy's sandbox, timing in the ledger ----

def test_no_effort_flag_because_agy_rejects_it_for_every_allowed_model(env):
    """Live 2026-11-22: Orchestrator says '--effort is not supported', suffixed models ('-low', '-high') say it conflicts.
    Effort is chosen by the model suffix instead, e.g. gemini-4-neon-medium."""
    fake = FakeAgy()
    go({"goal": "x", "repo": repo(env)}, env, fake)
    assert "--effort" not in fake.calls[0]["command"]


def test_agy_gets_a_path_without_asdf_because_its_sandbox_cannot_read_asdf():
    """Probe 2026-11-22: inside `agy --sandbox`, ~/.asdf is unreadable, so the uv shim fails with 'operation not permitted'."""
    env = agy.agy_env({"PATH": "/Users/e/.asdf/shims:/Users/e/.asdf/bin:/opt/homebrew/bin:/usr/bin", "HOME": "/Users/e"})
    assert env["PATH"] == "/opt/homebrew/bin:/usr/bin" and env["HOME"] == "/Users/e"


def test_the_prompt_says_to_run_whichever_tests_are_faster_itself(env):
    fake = FakeAgy()
    go({"goal": "改一个函数", "repo": repo(env)}, env, fake)
    prompt = fake.calls[0]["command"][fake.calls[0]["command"].index("-p") + 1]
    assert "哪个快跑哪个" in prompt and "~/.asdf" in prompt and "git 用不了" in prompt


TIMED = [
    {"event": "step_update", "step_update": {"state": "DONE", "step_type": "agent_response", "duration_seconds": 180.4,
                                             "usage": {"thinking_tokens": 21000, "total_tokens": 25000}}},
    {"event": "step_update", "step_update": {"state": "DONE", "step_type": "tool", "tool_name": "read_file", "duration_seconds": 2.0}},
    {"event": "step_update", "step_update": {"state": "DONE", "step_type": "tool", "tool_name": "edit_file", "duration_seconds": 3.5}},
    {"event": "step_update", "step_update": {"state": "DONE", "step_type": "agent_response", "duration_seconds": 20.0,
                                             "usage": {"thinking_tokens": 500, "total_tokens": 3000}}},
    {"event": "result", "result": OK},
]


class TimedAgy(FakeAgy):
    def __call__(self, command, cwd, timeout, log):
        self.calls.append({"command": command, "cwd": Path(cwd), "timeout": timeout})
        out = "\n".join(json.dumps(e) for e in TIMED) + "\n"
        with log.open("a") as f:
            f.write(out)
        return 0, out, ""


def test_the_ledger_keeps_goal_and_where_the_time_went_after_the_log_is_cleaned(env):
    result = go({"goal": "改 a.txt 的第一行" * 30, "repo": repo(env)}, env, TimedAgy())
    agy.cleanup(result["run_id"], paths=env, closer=lambda b: None)
    line = json.loads((env.runs / "ledger.jsonl").read_text().splitlines()[-1])
    assert line["goal"].startswith("改 a.txt 的第一行") and len(line["goal"]) <= 200
    assert line["conversation_id"] == "c1"
    assert line["timing"] == {"turns": 2, "model_seconds": 200, "longest_turn_seconds": 180, "tool_calls": 2,
                              "tool_seconds": 6, "thinking_tokens": 21500}
    assert result["timing"] == line["timing"]


def test_log_lines_get_a_timestamp(tmp_path):
    log = tmp_path / "x.log.jsonl"
    code, out, _ = agy._run_agy([sys.executable, "-c", "print('{\"event\": \"init\"}'); print('plain')"], tmp_path, 30, log)
    lines = log.read_text().splitlines()
    assert code == 0 and "at" in json.loads(lines[0]) and lines[1] == "plain"
    assert json.loads(out.splitlines()[0]) == {"event": "init"}  # stdout itself is unchanged


def test_a_uv_repo_gets_its_locked_deps_synced_before_agy_starts(env):
    """agy's sandbox blocks new package versions (403 'in cooldown' from files.pythonhosted.org, 2026-11-22),
    so the tool syncs the lockfile outside the sandbox first and agy's `uv run` needs no network."""
    (env.workspace / "proj" / "uv.lock").write_text("")
    _git(env.workspace / "proj", "add", "-A")
    _git(env.workspace / "proj", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "lock")
    synced = []
    result = agy.run({"goal": "x", "repo": repo(env)}, paths=env, runner=FakeAgy(), opener=no_panel,
                     setup=lambda workdir: synced.append(workdir) or {"command": "uv sync --frozen", "ok": True, "seconds": 2})
    assert synced == [Path(result["workdir"])] and result["setup"]["ok"]


def test_no_setup_without_a_lockfile(env):
    synced = []
    result = agy.run({"goal": "x", "repo": repo(env)}, paths=env, runner=FakeAgy(), opener=no_panel,
                     setup=lambda workdir: synced.append(workdir) or {})
    assert synced == [] and "setup" not in result


def test_a_failed_sync_does_not_stop_the_run(env):
    (env.workspace / "proj" / "uv.lock").write_text("")
    _git(env.workspace / "proj", "add", "-A")
    _git(env.workspace / "proj", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "lock")
    result = agy.run({"goal": "x", "repo": repo(env)}, paths=env, runner=FakeAgy(), opener=no_panel,
                     setup=lambda workdir: {"command": "uv sync --frozen", "ok": False, "error": "boom"})
    assert result["status"] == "done" and result["setup"]["error"] == "boom"


# ---- decision log (decisions.tsv) ----

VALID_HEADER = "ts\tphase\tdecision\twhy\tevidence\tresult"


def _write_decisions(cwd: Path, lines: list[str]) -> None:
    (cwd / ".agy").mkdir(exist_ok=True)
    (cwd / ".agy" / "decisions.tsv").write_text("\n".join(lines) + "\n")


def test_decisions_tsv_is_copied_counted_and_agy_dir_is_removed_from_workdir(env):
    def edit(cwd: Path):
        (cwd / "a.txt").write_text("new\n")
        _write_decisions(cwd, [
            VALID_HEADER,
            "2026-11-25T10:00:00+09:00\tread\tInspect a.txt\tNeed baseline\ta.txt:1\tok",
            "2026-11-25T10:01:00+09:00\tedit\tUpdate a.txt\tRequested change\ta.txt:1\tok",
        ])

    result = go({"goal": "改 a.txt", "repo": repo(env)}, env, FakeAgy(edit=edit))
    copied = Path(result["decisions"]["path"])
    assert copied.is_absolute() and copied == (env.runs / f"{result['run_id']}.decisions.tsv").resolve()
    assert result["decisions"]["rows"] == 2 and result["decisions"]["bad_rows"] == []
    assert not (Path(result["workdir"]) / ".agy").exists()
    assert result["files_changed"] == ["a.txt"]

    agy.cleanup(result["run_id"], paths=env, closer=no_panel, discard=True)
    assert not Path(result["workdir"]).exists()
    assert copied.is_file() and len(copied.read_text().splitlines()) == 3


def test_decisions_tsv_is_copied_even_when_agy_fails(env):
    def edit(cwd: Path):
        _write_decisions(cwd, [VALID_HEADER, "2026-11-25T10:00:00+09:00\tverify\tRun check\tCheck fails\tpytest:1 failed\tfailed"])

    result = go({"goal": "x", "repo": repo(env)}, env, FakeAgy(edit=edit, returncode=1, result={"status": "ERROR", "error": "boom"}))
    assert result["status"] == "error"
    assert result["decisions"]["rows"] == 1 and result["decisions"]["bad_rows"] == []
    assert Path(result["decisions"]["path"]).is_file()
    assert not (Path(result["workdir"]) / ".agy").exists()


def test_decisions_tsv_reports_bad_rows_for_five_columns_and_bad_header(env):
    def edit_five_cols(cwd: Path):
        _write_decisions(cwd, [
            VALID_HEADER,
            "2026-11-25T10:00:00+09:00\tread\tInspect a.txt\tBaseline\ta.txt:1\tok",
            "2026-11-25T10:01:00+09:00\tedit\tOnly five cols\tMissing result\ta.txt:1",
        ])

    res1 = go({"goal": "x", "repo": repo(env)}, env, FakeAgy(edit=edit_five_cols))
    assert res1["decisions"]["rows"] == 2 and res1["decisions"]["bad_rows"] == [3]

    def edit_bad_header(cwd: Path):
        _write_decisions(cwd, [
            "ts\tphase\tdecision\twhy\tevidence",
            "2026-11-25T10:00:00+09:00\tread\tInspect a.txt\tBaseline\ta.txt:1\tok",
        ])

    res2 = go({"goal": "x", "repo": repo(env)}, env, FakeAgy(edit=edit_bad_header))
    assert res2["decisions"]["rows"] == 1 and res2["decisions"]["bad_rows"] == [1]


def test_changing_four_files_without_decisions_tsv_sets_warning(env):
    def edit_four(cwd: Path):
        for name in ("f1.txt", "f2.txt", "f3.txt", "f4.txt"):
            (cwd / name).write_text("x\n")

    result = go({"goal": "批量改四个文件", "repo": repo(env)}, env, FakeAgy(edit=edit_four))
    assert "decisions" not in result
    assert len(result["files_changed"]) == 4
    assert "改了 4 个文件但没有 decisions.tsv" in result["warning"]

    def edit_three(cwd: Path):
        for name in ("f1.txt", "f2.txt", "f3.txt"):
            (cwd / name).write_text("x\n")

    ok_three = go({"goal": "改三个文件", "repo": repo(env)}, env, FakeAgy(edit=edit_three))
    assert "warning" not in ok_three


def test_the_prompt_carries_the_decisions_log_rule(env):
    fake = FakeAgy()
    go({"goal": "改多个文件", "repo": repo(env)}, env, fake)
    prompt = fake.calls[0]["command"][fake.calls[0]["command"].index("-p") + 1]
    assert ".agy/decisions.tsv" in prompt
    assert "ts\\tphase\\tdecision\\twhy\\tevidence\\tresult" in prompt
    assert "只追加" in prompt


# ---- 2026-11-26: progress-based time budget ----

def test_timeout_min_and_max_min_validation_and_defaults(env):
    spec = agy._check({"goal": "x", "repo": repo(env)}, env)
    assert spec["minutes"] == 30 and spec["max_min"] == 120

    spec_large_base = agy._check({"goal": "x", "repo": repo(env), "timeout_min": 150}, env)
    assert spec_large_base["minutes"] == 150 and spec_large_base["max_min"] == 150

    spec_explicit = agy._check({"goal": "x", "repo": repo(env), "timeout_min": 45, "max_min": 240}, env)
    assert spec_explicit["minutes"] == 45 and spec_explicit["max_min"] == 240

    for bad in (0, 181):
        with pytest.raises(agy.TaskError, match="timeout_min 要在 1 到 180 之间"):
            agy._check({"goal": "x", "repo": repo(env), "timeout_min": bad}, env)

    with pytest.raises(agy.TaskError, match="max_min 要在 60 到 240 之间"):
        agy._check({"goal": "x", "repo": repo(env), "timeout_min": 60, "max_min": 59}, env)
    with pytest.raises(agy.TaskError, match="max_min 要在 30 到 240 之间"):
        agy._check({"goal": "x", "repo": repo(env), "max_min": 241}, env)


def test_print_timeout_uses_max_min(env):
    fake = FakeAgy()
    go({"goal": "x", "repo": repo(env)}, env, fake)
    cmd = fake.calls[0]["command"]
    assert cmd[cmd.index("--print-timeout") + 1] == "7200s"

    fake2 = FakeAgy()
    go({"goal": "x", "repo": repo(env), "timeout_min": 30, "max_min": 180}, env, fake2)
    cmd2 = fake2.calls[0]["command"]
    assert cmd2[cmd2.index("--print-timeout") + 1] == "10800s"

    fake3 = FakeAgy()
    go({"goal": "x", "repo": repo(env), "timeout_min": 150}, env, fake3)
    cmd3 = fake3.calls[0]["command"]
    assert cmd3[cmd3.index("--print-timeout") + 1] == "9000s"


def test_budget_decision_pure_cases():
    started = 1000.0
    base_s = 30 * 60
    cap_s = 60 * 60
    stall_s = 10 * 60
    extend_s = 15 * 60

    # Before base with recent progress -> continue
    assert agy.budget_decision(started + 20 * 60, started, base_s, cap_s, started + 19 * 60, started + base_s, stall_s, extend_s) == "continue"
    # Before base with no progress for 10 min -> kill-stalled
    assert agy.budget_decision(started + 10 * 60, started, base_s, cap_s, started, started + base_s, stall_s, extend_s) == "kill-stalled"
    # Steady progress past base -> extend in 15-min steps up to cap
    assert agy.budget_decision(started + 30 * 60, started, base_s, cap_s, started + 28 * 60, started + 30 * 60, stall_s, extend_s) == "extend"
    assert agy.budget_decision(started + 45 * 60, started, base_s, cap_s, started + 43 * 60, started + 45 * 60, stall_s, extend_s) == "extend"
    # Past base with no progress for 10 min -> kill-stalled
    assert agy.budget_decision(started + 40 * 60, started, base_s, cap_s, started + 30 * 60, started + 45 * 60, stall_s, extend_s) == "kill-stalled"
    # At cap -> kill-cap
    assert agy.budget_decision(started + 60 * 60, started, base_s, cap_s, started + 59 * 60, started + 60 * 60, stall_s, extend_s) == "kill-cap"
    # When base == cap -> kill-cap at cap, never extend
    assert agy.budget_decision(started + 30 * 60, started, base_s, base_s, started + 29 * 60, started + base_s, stall_s, extend_s) == "kill-cap"


class FakeClock:
    def __init__(self, start: float = 0.0):
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class ScriptedPipe:
    def __init__(self):
        self._items = []
        self._cond = __import__("threading").Condition()
        self._closed = False

    def push(self, line: str) -> None:
        with self._cond:
            self._items.append(line)
            self._cond.notify_all()

    def close(self) -> None:
        with self._cond:
            self._closed = True
            self._cond.notify_all()

    def __iter__(self):
        return self

    def __next__(self) -> str:
        with self._cond:
            while not self._items and not self._closed:
                self._cond.wait()
            if self._items:
                return self._items.pop(0)
            raise StopIteration

    def read(self) -> str:
        return "".join(self)


class FakePopen:
    def __init__(self, clock: FakeClock, on_tick):
        self.clock = clock
        self.on_tick = on_tick
        self.stdout = ScriptedPipe()
        self.stderr = ScriptedPipe()
        self.returncode = None
        self.killed = False
        self._step = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stdout.close()
        self.stderr.close()

    def wait(self, timeout=None):
        if self.killed:
            self.returncode = -9
            return -9
        if self.returncode is not None:
            return self.returncode
        self._step += 1
        done = self.on_tick(self, self._step)
        if done:
            self.stdout.close()
            self.stderr.close()
            self.returncode = 0
            return 0
        raise subprocess.TimeoutExpired("agy", timeout)

    def kill(self):
        self.killed = True
        self.returncode = -9
        self.stdout.close()
        self.stderr.close()


def test_watchdog_extends_on_stdout_progress_and_reports_extended_min(env):
    clock = FakeClock()

    def on_tick(proc: FakePopen, step: int) -> bool:
        # Advance 5 minutes per tick with stdout activity; finish at 40 min (> 30 min base, < 60 min cap)
        clock.advance(5 * 60)
        if step < 8:
            proc.stdout.push(json.dumps({"event": "init"}) + "\n")
            __import__("time").sleep(0.01)
            return False
        for line in _stream(OK).splitlines(keepends=True):
            proc.stdout.push(line)
        __import__("time").sleep(0.01)
        return True

    def runner(command, cwd, budget, log):
        return agy._run_agy(command, cwd, budget, log, clock=clock, poll_s=0.01,
                             popen=lambda *a, **kw: FakePopen(clock, on_tick))

    result = go({"goal": "long task", "repo": repo(env), "timeout_min": 30, "max_min": 60}, env, runner)
    assert result["status"] == "done"
    assert result["extended_min"] == 15
    ext_events = [e for e in agy._events(Path(result["log"]).read_text()) if e.get("event") == "extended"]
    assert len(ext_events) == 1
    assert ext_events[0]["by_min"] == 15
    assert ext_events[0]["elapsed_min"] == 30
    assert ext_events[0]["decisions_rows"] == 0
    assert "at" in ext_events[0]


def test_watchdog_kills_silent_hang_before_base_and_respects_env_stall(env, monkeypatch):
    clock = FakeClock()

    def on_tick(proc: FakePopen, step: int) -> bool:
        proc.clock.advance(5 * 60)  # the proc's own clock, so the second run's clock moves too
        return False

    def runner(command, cwd, budget, log):
        return agy._run_agy(command, cwd, budget, log, clock=clock, poll_s=0.01,
                             popen=lambda *a, **kw: FakePopen(clock, on_tick))

    result = go({"goal": "hang", "repo": repo(env), "timeout_min": 30, "max_min": 60}, env, runner)
    assert result["status"] == "error"
    assert result["error"] == "停滞 10 分钟没有进展，已中止（共跑了 10 分钟）"
    assert result["extended_min"] == 0

    monkeypatch.setenv("AGY_STALL_MIN", "5")
    clock2 = FakeClock()
    def runner2(command, cwd, budget, log):
        return agy._run_agy(command, cwd, budget, log, clock=clock2, poll_s=0.01,
                             popen=lambda *a, **kw: FakePopen(clock2, on_tick))
    result2 = go({"goal": "hang2", "repo": repo(env), "timeout_min": 30, "max_min": 60}, env, runner2)
    assert result2["status"] == "error"
    assert result2["error"] == "停滞 5 分钟没有进展，已中止（共跑了 5 分钟）"


def test_watchdog_kills_at_hard_cap(env):
    clock = FakeClock()

    def on_tick(proc: FakePopen, step: int) -> bool:
        clock.advance(5 * 60)
        proc.stdout.push(json.dumps({"event": "step_update", "step_update": {"state": "DONE", "step_type": "tool", "duration_seconds": 1}}) + "\n")
        __import__("time").sleep(0.01)
        return False

    def runner(command, cwd, budget, log):
        return agy._run_agy(command, cwd, budget, log, clock=clock, poll_s=0.01,
                             popen=lambda *a, **kw: FakePopen(clock, on_tick))

    result = go({"goal": "too long", "repo": repo(env), "timeout_min": 30, "max_min": 60}, env, runner)
    assert result["status"] == "error"
    assert result["error"] == "到了上限 60 分钟，已中止（续期 30 分钟）"
    assert result["extended_min"] == 30
    assert result["timing"]["tool_calls"] >= 1


def test_watchdog_counts_decisions_tsv_only_as_progress(env):
    clock = FakeClock()

    def runner(command, cwd, budget, log):
        def on_tick(proc: FakePopen, step: int) -> bool:
            clock.advance(5 * 60)
            # No stdout lines at all until finish; progress only via .agy/decisions.tsv
            if step in (1, 3, 5, 7):
                rows = [VALID_HEADER] + [
                    f"2026-11-26T12:0{i}:00+09:00\tedit\tstep {i}\treason\tf:1\tok"
                    for i in range(1, step + 1)
                ]
                _write_decisions(cwd, rows)
                return False
            if step == 8:
                for line in _stream(OK).splitlines(keepends=True):
                    proc.stdout.push(line)
                __import__("time").sleep(0.01)
                return True
            return False

        return agy._run_agy(command, cwd, budget, log, clock=clock, poll_s=0.01,
                             popen=lambda *a, **kw: FakePopen(clock, on_tick))

    result = go({"goal": "tsv progress", "repo": repo(env), "timeout_min": 30, "max_min": 60}, env, runner)
    assert result["status"] == "done"
    assert result["extended_min"] == 15
    ext_events = [e for e in agy._events(Path(result["log"]).read_text()) if e.get("event") == "extended"]
    assert len(ext_events) == 1
    assert ext_events[0]["decisions_rows"] == 5  # extended at 30 min (tick 6); tick 5 wrote 5 rows


def test_normal_run_includes_zero_extended_min_and_timing(env):
    result = go({"goal": "x", "repo": repo(env)}, env, TimedAgy())
    assert result["extended_min"] == 0
    assert result["timing"] == {"turns": 2, "model_seconds": 200, "longest_turn_seconds": 180,
                                "tool_calls": 2, "tool_seconds": 6, "thinking_tokens": 21500}
