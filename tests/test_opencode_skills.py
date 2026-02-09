"""Tests for Opencode skills loading."""

from pathlib import Path

from nanobot.agent.skills import SkillsLoader


def test_opencode_skills_loading():
    """Test that opencode skills are loaded correctly."""
    loader = SkillsLoader(Path("/tmp/test_workspace"), opencode_config={"enabled": True})
    skills = loader.list_skills()

    opencode_skills = [s for s in skills if s["source"] == "opencode"]
    assert len(opencode_skills) >= 2

    skill_names = [s["name"] for s in opencode_skills]
    assert "code-review" in skill_names
    assert "code-refactoring" in skill_names


def test_load_code_review_skill():
    """Test loading code review skill."""
    loader = SkillsLoader(Path("/tmp/test_workspace"), opencode_config={"enabled": True})
    content = loader.load_skill("code-review")
    assert content is not None
    assert "security" in content.lower()
