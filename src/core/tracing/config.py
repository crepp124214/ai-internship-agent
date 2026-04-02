import os

"""OpenTelemetry initialization and configuration."""

def init_tracing():
    """Initialize and return a TracerProvider configured from environment vars.

    - Service name is read from OTEL_SERVICE_NAME (default: 'ai-internship-agent')
    - If OTEL_EXPORTER_OTLP_ENDPOINT is provided, configure an OTLP exporter.
    - Do not set the global tracer provider; callers should pass a provider to
      instrumentation explicitly.
    - If OpenTelemetry libraries are unavailable, falls back to a minimal dummy
      provider compatible with the unit tests.
    """
    service_name = os.environ.get("OTEL_SERVICE_NAME", "ai-internship-agent")
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

    try:
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        resource = Resource(attributes={"service.name": service_name})
        tracer_provider = TracerProvider(resource=resource)

        if endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                from opentelemetry.sdk.trace.export import BatchSpanProcessor
                exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
                tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception:
                # If exporter setup fails, continue without an exporter
                pass
        return tracer_provider
    except Exception:
        # Fallback: minimal dummy provider for test environments without OT packages
        class DummyTracer:
            def start_as_current_span(self, name):
                class Ctx:
                    def __enter__(self):
                        return self
                    def __exit__(self, exc_type, exc, tb):
                        return False
                return Ctx()

        class DummyResource(dict):
            @property
            def attributes(self):
                return self

        class DummyProvider:
            def __init__(self):
                self.resource = DummyResource({"service.name": service_name})
            def get_tracer(self, name, version=None):
                return DummyTracer()
        return DummyProvider()
