"""Tests for scripts/check_skill_language.py (FB-078)."""

from pathlib import Path

from check_skill_language import check_file, main


def _write_skill(tmp_path: Path, body: str, name: str = "demo") -> Path:
    skill_dir = tmp_path / "skills" / "misc" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / "SKILL.md"
    skill_path.write_text(
        f"---\nname: {name}\ndescription: Demo skill.\n---\n\n{body.lstrip()}",
        encoding="utf-8",
    )
    return skill_path


def test_chinese_body_fails(tmp_path: Path, capsys) -> None:
    skill_path = _write_skill(
        tmp_path,
        """
# 示例技能

只在明确要求时运行这个流程。
核心原则是不直接执行原任务。
第一步先读取全部原始材料。
""",
    )
    count, first_line = check_file(skill_path)
    assert count == 3
    assert first_line == 8

    exit_code = main([str(skill_path)])
    assert exit_code == 1
    out = capsys.readouterr().out
    assert "(FB-078)" in out
    assert "Write skill bodies in English" in out
    assert "3 lines of Chinese/Japanese prose (first: line 8)" in out


def test_english_body_with_quotes_code_and_examples_passes(tmp_path: Path, capsys) -> None:
    skill_path = _write_skill(
        tmp_path,
        """
# Demo Skill

Run when the user says "磨一下这个需求", “帮我换个说法”, 「找术语」, or 『记录到错题本』 （包括语音输入）.

Show inline examples like `今天学到的` in backticks.

```text
这是一段纯中文的代码块示例
第二行也是纯中文示例
第三行依然不应该触发报错
```

Follow all steps in plain English.
""",
    )
    count, first_line = check_file(skill_path)
    assert (count, first_line) == (0, None)
    assert main([str(skill_path)]) == 0
    assert capsys.readouterr().out == ""


def test_verbatim_line_with_three_ascii_words_passes(tmp_path: Path, capsys) -> None:
    skill_path = _write_skill(
        tmp_path,
        """
# Blog Rules

1. **Tone (Eric, verbatim):** 除非有特定指向性，否则请尽量不要使用网络流行用语
2. **Drafting (Eric, note):** 默认先写中文，最后定稿了以后再去输出英文
3. **Detail (Eric, style):** 在一个章节内，优先重点讲最重要的部分
""",
    )
    count, first_line = check_file(skill_path)
    assert (count, first_line) == (0, None)
    assert main([str(skill_path)]) == 0
    assert capsys.readouterr().out == ""


def test_threshold_under_three_lines_passes(tmp_path: Path, capsys) -> None:
    skill_path = _write_skill(
        tmp_path,
        """
# Mostly English

Keep instructions concise and direct.
这一行是超过八个汉字的中文说明。
第二行也是超过八个汉字的中文说明。
""",
    )
    count, first_line = check_file(skill_path)
    assert (count, first_line) == (2, 9)
    assert main([str(skill_path)]) == 0
    assert capsys.readouterr().out == ""
