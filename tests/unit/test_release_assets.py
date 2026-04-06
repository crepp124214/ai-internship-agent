"""Release and documentation contract checks."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_core_docs_exist():
    assert (REPO_ROOT / "README.md").exists()
    assert (REPO_ROOT / "AGENTS.md").exists()
    assert (REPO_ROOT / ".env.compose.example").exists()
    assert (REPO_ROOT / ".sisyphus" / "plans" / "PLAN.md").exists()
    assert (REPO_ROOT / "docs" / "internal" / "decisions" / "README.md").exists()
    assert (REPO_ROOT / "docs" / "internal" / "prompts" / "agent_team_bootstrap.md").exists()
    assert (REPO_ROOT / "docs" / "internal" / "runbooks" / "incident-response.md").exists()


def test_legacy_docs_removed():
    assert not (REPO_ROOT / "CLAUDE.md").exists()
    assert not (REPO_ROOT / "AGENT_TEAM.md").exists()
    assert not (REPO_ROOT / "PROJECT_MEMORY.md").exists()
    assert not (REPO_ROOT / "docs" / "README.md").exists()
    assert not (REPO_ROOT / "docs" / "architecture.md").exists()
    assert not (REPO_ROOT / "docs" / "developer-guide.md").exists()
    assert not (REPO_ROOT / "docs" / "deployment.md").exists()
    assert not (REPO_ROOT / "docs" / "product.md").exists()
    assert not (REPO_ROOT / "docs" / "demo-walkthrough.md").exists()
    assert not (REPO_ROOT / "docs" / "api-reference.md").exists()
    assert not (REPO_ROOT / "docs" / "three-tier-architecture.md").exists()
    assert not (REPO_ROOT / "docs" / "release-checklist.md").exists()
    assert not (REPO_ROOT / "docs" / "runbooks" / "deployment.md").exists()
    assert not (REPO_ROOT / "docs" / "product-design-spec.md").exists()
    assert not (REPO_ROOT / "docs" / "portfolio-backend-overview.md").exists()
    assert not (REPO_ROOT / "docs" / "portfolio-ui-copydeck.md").exists()
    assert not (REPO_ROOT / "docs" / "figma-backend-capability-map.md").exists()
    assert not (REPO_ROOT / "frontend" / "README.md").exists()
    assert not (REPO_ROOT / "tests" / "README.md").exists()
    assert not (REPO_ROOT / ".sisyphus" / "plans" / "progress.md").exists()


def test_compose_stack_includes_release_services():
    compose = yaml.safe_load(
        (REPO_ROOT / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    )
    assert "services" in compose
    assert {"postgres", "redis", "app", "frontend"}.issubset(compose["services"])

    app = compose["services"]["app"]
    assert "../.env.compose" in app["env_file"]
    assert app["environment"]["SEED_DEMO_ON_BOOT"] == "${SEED_DEMO_ON_BOOT:-false}"

    frontend = compose["services"]["frontend"]
    assert frontend["depends_on"]["app"]["condition"] == "service_healthy"
    assert "3000:80" in frontend["ports"]
    assert frontend["build"]["args"]["VITE_API_BASE_URL"] == ""


def test_readme_declares_demo_flow():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "demo / demo123" in readme
    assert "seed_demo.py" in readme
    assert "make dev" in readme
    assert "AGENTS.md" in readme
    assert "/resume" in readme
    assert "/jobs" in readme
    assert "/interview" in readme
    assert "/tracker" in readme


def test_readme_contains_demo_walkthrough():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "python scripts/seed_demo.py" in readme
    assert "Resume" in readme
    assert "Jobs" in readme
    assert "Interview" in readme
    assert "Tracker" in readme
