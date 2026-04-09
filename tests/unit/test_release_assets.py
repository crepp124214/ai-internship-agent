"""Release and documentation contract checks."""

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_core_docs_exist():
    assert (REPO_ROOT / "README.md").exists()
    assert (REPO_ROOT / ".env.local.example").exists()


def test_legacy_docs_removed():
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
    assert app["environment"]["SEED_DEMO_ON_BOOT"] == "${SEED_DEMO_ON_BOOT:-false}"

    frontend = compose["services"]["frontend"]
    assert frontend["depends_on"]["app"]["condition"] == "service_healthy"
    assert "3000:80" in frontend["ports"]
    assert frontend["build"]["args"]["VITE_API_BASE_URL"] == ""


def test_readme_declares_demo_flow():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "用户名" in readme
    assert "`demo`" in readme
    assert "密码" in readme
    assert "`demo123`" in readme
    assert "docker compose" in readme
    assert "FastAPI" in readme
    assert "React" in readme
    assert "MIT" in readme
    assert "CONTRIBUTING.md" in readme


def test_readme_contains_demo_walkthrough():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "pip install" in readme
    assert "npm install" in readme
    assert "python scripts/seed_demo.py" in readme
    assert "Agent 运行时" in readme
    assert "License" in readme
