from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "cyber-shell" / "config.yaml"
DEFAULT_STATE_DIR = Path.home() / ".local" / "state" / "cyber-shell"


@dataclass(slots=True)
class AppConfig:
    endpoint_url: str | None = None
    api_key: str | None = None
    timeout_ms: int = 3000
    retry_max: int = 3
    retry_backoff_ms: int = 1000
    max_output_bytes: int = 262144
    queue_size: int = 256
    shell_path: str = "/bin/bash"
    user_id: str | None = None
    lab_id: str | None = None
    target_id: str | None = None
    state_dir: Path = DEFAULT_STATE_DIR
    config_path: Path = DEFAULT_CONFIG_PATH
    hostname: str = field(default_factory=socket.gethostname)
    metadata: dict[str, str] = field(default_factory=dict)

    def ensure_state_dir(self) -> Path:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir


def load_config(path: str | Path | None = None) -> AppConfig:
    config_path = Path(
        path
        or os.environ.get("CYBER_SHELL_CONFIG")
        or DEFAULT_CONFIG_PATH
    ).expanduser()
    data: dict[str, object] = {}
    if config_path.exists():
        data = _parse_simple_yaml(config_path.read_text(encoding="utf-8"))

    config = AppConfig(
        endpoint_url=_env_or_data("CYBER_SHELL_ENDPOINT_URL", data, "endpoint_url"),
        api_key=_env_or_data("CYBER_SHELL_API_KEY", data, "api_key"),
        timeout_ms=_coerce_int(
            _env_or_data("CYBER_SHELL_TIMEOUT_MS", data, "timeout_ms"), 3000
        ),
        retry_max=_coerce_int(
            _env_or_data("CYBER_SHELL_RETRY_MAX", data, "retry_max"), 3
        ),
        retry_backoff_ms=_coerce_int(
            _env_or_data("CYBER_SHELL_RETRY_BACKOFF_MS", data, "retry_backoff_ms"),
            1000,
        ),
        max_output_bytes=_coerce_int(
            _env_or_data("CYBER_SHELL_MAX_OUTPUT_BYTES", data, "max_output_bytes"),
            262144,
        ),
        queue_size=_coerce_int(
            _env_or_data("CYBER_SHELL_QUEUE_SIZE", data, "queue_size"), 256
        ),
        shell_path=str(
            _env_or_data("CYBER_SHELL_SHELL_PATH", data, "shell_path") or "/bin/bash"
        ),
        user_id=_as_optional_str(
            _env_or_data("CYBER_SHELL_USER_ID", data, "user_id")
        ),
        lab_id=_as_optional_str(_env_or_data("CYBER_SHELL_LAB_ID", data, "lab_id")),
        target_id=_as_optional_str(
            _env_or_data("CYBER_SHELL_TARGET_ID", data, "target_id")
        ),
        state_dir=Path(
            _env_or_data("CYBER_SHELL_STATE_DIR", data, "state_dir")
            or DEFAULT_STATE_DIR
        ).expanduser(),
        config_path=config_path,
        hostname=str(
            _env_or_data("CYBER_SHELL_HOSTNAME", data, "hostname")
            or socket.gethostname()
        ),
        metadata=_coerce_metadata(data.get("metadata")),
    )
    config.ensure_state_dir()
    return config


def default_config_text() -> str:
    return """endpoint_url: "http://127.0.0.1:8080/api/terminal-events"
api_key: "replace-me"
timeout_ms: 3000
retry_max: 3
retry_backoff_ms: 1000
max_output_bytes: 262144
queue_size: 256
shell_path: "/bin/bash"
user_id: "student-01"
lab_id: "lab-web-02"
target_id: "target-a"
metadata:
  hostname_group: "kali-lab"
"""


def _env_or_data(env_name: str, data: dict[str, object], key: str) -> object:
    if env_name in os.environ:
        return os.environ[env_name]
    return data.get(key)


def _coerce_int(value: object, default: int) -> int:
    if value in (None, ""):
        return default
    try:
        return int(str(value))
    except ValueError:
        return default


def _as_optional_str(value: object) -> str | None:
    if value in (None, "", "null", "None"):
        return None
    return str(value)


def _coerce_metadata(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(inner) for key, inner in value.items()}


def _parse_simple_yaml(text: str) -> dict[str, object]:
    result: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, result)]

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        stripped = raw_line.lstrip()
        if stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(stripped)
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()

        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        parent = stack[-1][1]
        if not value:
            child: dict[str, object] = {}
            parent[key] = child
            stack.append((indent, child))
            continue

        parent[key] = _parse_scalar(value)

    return result


def _parse_scalar(value: str) -> object:
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) >= 2:
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value
