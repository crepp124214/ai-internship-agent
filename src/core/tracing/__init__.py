"""OpenTelemetry tracing入口 for the core infrastructure."""

# Lightweight global holder for the tracer provider to be accessible from
# the rest of the application without relying on global opentelemetry state.
_tracer_provider = None

def setup_tracing():
    """Initialize tracing using environment configuration.

    Returns the TracerProvider instance so middleware can attach to it.
    """
    from .config import init_tracing
    global _tracer_provider
    _tracer_provider = init_tracing()
    _instrument_llm_calls(_tracer_provider)
    return _tracer_provider

def get_tracer(name: str):
    """Return a tracer for the given name using the initialized provider."""
    if _tracer_provider is None:
        raise RuntimeError("Tracing has not been initialized. Call setup_tracing() first.")
    return _tracer_provider.get_tracer(name)

def _instrument_llm_calls(provider):
    """Attach lightweight spans around LLM adapter calls by monkey-patching.

    This avoids modifying adapter implementations directly and keeps tracing
    awareness at the adapter call sites.
    """
    try:
        tracer = provider.get_tracer("llm")
        # Try to patch common adapters if present on the project
        for mod_path in [
            "src.core.llm.openai_adapter",
            "src.core.llm.mock_adapter",
        ]:
            try:
                mod = __import__(mod_path, fromlist=["*"])
            except Exception:
                continue
            for func_name in ("generate", "chat", "get_embedding"):
                if hasattr(mod, func_name):
                    orig = getattr(mod, func_name)
                    def make_wrapped(f, name, provider_tracer):
                        def wrapper(*args, **kwargs):
                            with provider_tracer.start_as_current_span("llm.call") as span:
                                # Populate a few helpful attributes if available
                                try:
                                    span.set_attribute("llm.provider", "openai" if "openai" in mod_path else "mock")
                                except Exception:
                                    pass
                                try:
                                    if "model" in kwargs:
                                        span.set_attribute("llm.model", str(kwargs["model"]))
                                    elif len(args) > 0 and isinstance(args[0], dict) and "model" in args[0]:
                                        span.set_attribute("llm.model", str(args[0]["model"]))
                                except Exception:
                                    pass
                                return f(*args, **kwargs)
                        return wrapper
                    wrapped = make_wrapped(orig, func_name, tracer)
                    setattr(mod, func_name, wrapped)
            
    except Exception:
        # Best-effort instrumentation; non-fatal for environments without OT
        pass

__all__ = ["setup_tracing", "get_tracer"]
