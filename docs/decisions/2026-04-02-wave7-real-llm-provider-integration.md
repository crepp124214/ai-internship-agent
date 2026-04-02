# Wave 7: Real LLM Provider Integration

## Background

The shared LLM runtime already had a mock path and an OpenAI adapter skeleton, but provider/runtime resolution was still too loose for a stable real-provider baseline.

## Stage Goal

Strengthen the OpenAI runtime path while preserving mock-first local development:

- stabilize provider/runtime precedence
- make environment fallback behavior explicit
- make mixed config/env/settings behavior predictable in deployment-style setups
- keep ownership inside `src/core/llm`

## Core Decisions

### D7.1 Lock provider/runtime precedence with tests

Provider selection and OpenAI runtime option resolution are now covered by dedicated unit tests so future changes cannot silently drift.

### D7.2 Resolve key OpenAI runtime options through one consistent path

`api_key`, `model`, and `base_url` now follow the same precedence:

1. top-level config
2. nested `llm` config
3. environment fallback

### D7.3 Treat blank-string config values as unset

Empty string values should not override better nested or environment-provided configuration.

### D7.4 Fall through invalid numeric config values instead of defaulting too early

If a top-level numeric runtime option is present but unusable, the adapter should still consider nested `llm` config and then environment values before settling on a default.

### D7.5 Blank provider strings should not block fallback resolution

An empty provider string should behave like missing configuration so `LLMFactory` can still use nested config, environment, or settings defaults.

## Impact Scope

### Code

- `src/core/llm/openai_adapter.py`
- `src/core/llm/factory.py`
- `tests/unit/core/test_llm_factory.py`
- `tests/unit/core/test_openai_adapter_runtime.py`

### Stage Docs

- `.sisyphus/plans/PLAN.md`
- `.sisyphus/plans/progress.md`
- `docs/decisions/README.md`
- `PROJECT_MEMORY.md`

## Verification Result

- `python -m pytest tests/unit/core/test_llm_factory.py tests/unit/core/test_openai_adapter_runtime.py --no-cov`
  - passed
  - current result: `25` tests passed
- `python -m pytest tests/unit/core/test_llm_factory.py tests/unit/core/test_openai_adapter_runtime.py tests/unit/core/test_resume_agent.py tests/unit/core/test_job_agent.py tests/unit/core/test_interview_agent.py tests/unit/core/test_tracker_agent.py --no-cov`
  - passed
  - current result: `51` tests passed

## Current Judgment

Wave 7 is now in progress with four stable provider-runtime milestones:

- the OpenAI path is more predictable because key runtime fields have explicit fallback behavior
- `LLMFactory` can now resolve a default provider even when the caller does not pre-merge config, while still preserving mock-first local behavior when defaults are blank
- OpenAI runtime request parameters now have consistent parsing and coercion rules, including instance-default reuse when callers omit overrides
- mixed deployment-style config is now safer because invalid top-level numeric values can still fall through to nested `llm` config or environment values, and blank provider strings no longer block fallback resolution

## Next Recommended Task

Continue Wave 7 with the next deployment-driven verification step and only expand the runtime surface where real deployment needs justify it.
