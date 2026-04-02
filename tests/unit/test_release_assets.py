"""作品集交付资产检查。"""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_release_docs_exist():
    assert (REPO_ROOT / "README.md").exists()
    assert (REPO_ROOT / "docs" / "deployment.md").exists()
    assert (REPO_ROOT / "docs" / "release-checklist.md").exists()
    assert (REPO_ROOT / "docs" / "portfolio-backend-overview.md").exists()
    assert (REPO_ROOT / "docs" / "demo-walkthrough.md").exists()


def test_compose_stack_includes_release_services():
    compose = yaml.safe_load(
        (REPO_ROOT / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    )

    assert "services" in compose
    assert {"postgres", "redis", "app"}.issubset(compose["services"])


def test_readme_declares_demo_flow():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Docker Compose" in readme
    assert "作品集" in readme
    assert "demo / demo123" in readme
    assert "seed_demo.py" in readme
    assert "登录" in readme
    assert "Dashboard" in readme


def test_demo_walkthrough_mentions_seed_and_pages():
    walkthrough = (REPO_ROOT / "docs" / "demo-walkthrough.md").read_text(
        encoding="utf-8"
    )

    assert "python scripts/seed_demo.py" in walkthrough
    assert "Resume" in walkthrough
    assert "Jobs" in walkthrough
    assert "Interview" in walkthrough
    assert "Tracker" in walkthrough
