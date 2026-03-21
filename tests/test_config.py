from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from cyber_shell.config import load_config


class ConfigTests(unittest.TestCase):
    def test_loads_simple_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(
                textwrap.dedent(
                    """
                    endpoint_url: "http://127.0.0.1:8080/api/terminal-events"
                    api_key: "secret"
                    timeout_ms: 1234
                    retry_max: 5
                    metadata:
                      role: "student"
                    """
                ).strip(),
                encoding="utf-8",
            )

            config = load_config(config_path)

        self.assertEqual(
            config.endpoint_url,
            "http://127.0.0.1:8080/api/terminal-events",
        )
        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.timeout_ms, 1234)
        self.assertEqual(config.retry_max, 5)
        self.assertEqual(config.metadata, {"role": "student"})


if __name__ == "__main__":
    unittest.main()
