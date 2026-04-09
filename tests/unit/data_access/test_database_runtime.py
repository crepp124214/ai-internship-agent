from src.data_access.database import _engine_options_for_url, _import_all_entities


def test_engine_options_skip_pool_args_for_sqlite():
    options = _engine_options_for_url("sqlite:///./data/app.db", echo=False)

    assert options == {"echo": False}


def test_engine_options_include_pool_args_for_postgres():
    options = _engine_options_for_url(
        "postgresql://agent_user:agent_password@localhost:5432/internship_agent",
        echo=False,
    )

    assert options["echo"] is False
    assert options["pool_size"] == 20
    assert options["max_overflow"] == 10
    assert options["pool_recycle"] == 3600
