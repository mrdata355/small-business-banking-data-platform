from __future__ import annotations

from prometheus_client import Gauge, start_http_server
from pyspark.sql.streaming import StreamingQueryListener

INPUT_RATE = Gauge("spark_stream_input_rows_per_second", "Streaming input rows/sec", ["query"])
PROCESSED_RATE = Gauge("spark_stream_processed_rows_per_second", "Streaming processed rows/sec", ["query"])
BATCH_DURATION = Gauge("spark_stream_batch_duration_ms", "Streaming trigger duration in ms", ["query"])
STATE_ROWS = Gauge("spark_stream_state_rows_total", "Rows held in state", ["query"])


class PrometheusStreamingListener(StreamingQueryListener):
    def onQueryStarted(self, event):
        pass

    def onQueryProgress(self, event):
        progress = event.progress
        name = progress.name or progress.id
        INPUT_RATE.labels(query=name).set(float(progress.inputRowsPerSecond or 0.0))
        PROCESSED_RATE.labels(query=name).set(float(progress.processedRowsPerSecond or 0.0))
        BATCH_DURATION.labels(query=name).set(float(progress.durationMs.get("triggerExecution", 0)))
        state_rows = sum(int(x.numRowsTotal) for x in progress.stateOperators)
        STATE_ROWS.labels(query=name).set(state_rows)

    def onQueryTerminated(self, event):
        pass

    def onQueryIdle(self, event):
        pass


def install_streaming_metrics(spark, port: int = 9108) -> None:
    start_http_server(port)
    spark.streams.addListener(PrometheusStreamingListener())
