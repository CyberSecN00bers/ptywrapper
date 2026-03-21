from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class ShellEvent:
    session_id: str
    user_id: str | None
    lab_id: str | None
    target_id: str | None
    hostname: str
    shell: str
    seq: int
    cwd: str
    cmd: str
    exit_code: int
    output: str
    output_truncated: bool
    started_at: str
    finished_at: str
    is_interactive: bool
    metadata: dict[str, str] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        return asdict(self)
