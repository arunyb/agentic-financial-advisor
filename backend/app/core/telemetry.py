"""
Observability wiring: OpenTelemetry tracing + Prometheus metrics.

- Traces export via OTLP/HTTP if OTEL_EXPORTER_OTLP_ENDPOINT is set (e.g. to
  Jaeger, Tempo, or an OTel Collector). Falls back to console export so
  tracing is still visible with zero extra infra.
- Prometheus metrics are exposed at /metrics via prometheus-fastapi-instrumentator.
"""
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings


def setup_tracing() -> None:
    resource = Resource(attributes={SERVICE_NAME: settings.APP_NAME})
    provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)


def instrument_app(app: FastAPI) -> None:
    setup_tracing()
    FastAPIInstrumentor.instrument_app(app)

    if settings.ENABLE_PROMETHEUS:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


def get_tracer(name: str = "app"):
    return trace.get_tracer(name)
