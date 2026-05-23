from dataclasses import dataclass


@dataclass(frozen=True)
class Founder:
    name: str
    role: str | None = None
