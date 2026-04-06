"""Docker runtime contract checks for local release flows."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_entrypoint_supports_optional_demo_seed():
    entrypoint = (REPO_ROOT / "docker" / "entrypoint.sh").read_text(encoding="utf-8")

    assert "SEED_DEMO_ON_BOOT" in entrypoint
    assert "python scripts/seed_demo.py" in entrypoint


def test_frontend_runtime_assets_exist():
    assert (REPO_ROOT / "docker" / "frontend.Dockerfile").exists()
    assert (REPO_ROOT / "docker" / "nginx.conf").exists()
    assert (REPO_ROOT / ".env.compose.example").exists()


def test_compose_example_contains_demo_stack_defaults():
    compose_env = (REPO_ROOT / ".env.compose.example").read_text(encoding="utf-8")

    assert "DATABASE_URL=postgresql://agent_user:agent_password@postgres:5432/internship_agent" in compose_env
    assert "REDIS_URL=redis://redis:6379/0" in compose_env
    assert "SEED_DEMO_ON_BOOT=false" in compose_env


def test_nginx_proxies_backend_routes():
    nginx_conf = (REPO_ROOT / "docker" / "nginx.conf").read_text(encoding="utf-8")

    assert "location /api/" in nginx_conf
    assert "proxy_pass http://app:8000/api/" in nginx_conf
    assert "location = /health" in nginx_conf
    assert "proxy_pass http://app:8000/health" in nginx_conf
