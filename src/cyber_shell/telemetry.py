from __future__ import annotations

import json
import logging
import queue
import threading
import time
import urllib.error
import urllib.request

from .config import AppConfig
from .models import ShellEvent


class TelemetryClient:
    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self._config = config
        self._logger = logger
        self._queue: queue.Queue[ShellEvent | None] = queue.Queue(
            maxsize=config.queue_size
        )
        self._worker = threading.Thread(
            target=self._run,
            name="cyber-shell-telemetry",
            daemon=True,
        )
        self._worker.start()

    def enqueue(self, event: ShellEvent) -> None:
        if not self._config.endpoint_url:
            self._logger.debug(
                "Skipping telemetry because endpoint_url is not configured."
            )
            return
        try:
            self._queue.put_nowait(event)
        except queue.Full:
            self._logger.warning("Telemetry queue is full; dropping seq=%s", event.seq)

    def close(self, grace_period: float = 2.0) -> None:
        deadline = time.monotonic() + max(grace_period, 0.0)
        while True:
            try:
                self._queue.put(None, timeout=0.1)
                break
            except queue.Full:
                if time.monotonic() >= deadline:
                    break
        while time.monotonic() < deadline:
            if self._queue.unfinished_tasks == 0:
                break
            time.sleep(0.05)
        self._worker.join(timeout=max(deadline - time.monotonic(), 0.1))

    def _run(self) -> None:
        while True:
            try:
                item = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue

            if item is None:
                self._queue.task_done()
                break

            try:
                self._send_with_retry(item)
            except Exception:
                self._logger.exception(
                    "Unexpected telemetry worker failure for seq=%s",
                    item.seq,
                )
            finally:
                self._queue.task_done()

    def _send_with_retry(self, event: ShellEvent) -> None:
        for attempt in range(1, self._config.retry_max + 2):
            try:
                self._post(event)
                return
            except Exception as exc:
                if attempt > self._config.retry_max:
                    self._logger.warning(
                        "Giving up telemetry seq=%s after %s attempt(s): %s",
                        event.seq,
                        attempt,
                        exc,
                    )
                    return
                backoff = (self._config.retry_backoff_ms / 1000.0) * attempt
                self._logger.warning(
                    "Telemetry seq=%s attempt %s failed: %s; retrying in %.2fs",
                    event.seq,
                    attempt,
                    exc,
                    backoff,
                )
                time.sleep(backoff)

    def _post(self, event: ShellEvent) -> None:
        if not self._config.endpoint_url:
            return

        payload = json.dumps(event.to_payload()).encode("utf-8")
        request = urllib.request.Request(
            self._config.endpoint_url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.api_key or ''}",
            },
        )
        timeout = max(self._config.timeout_ms / 1000.0, 0.1)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                _ = response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"http {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"url error: {exc.reason}") from exc
