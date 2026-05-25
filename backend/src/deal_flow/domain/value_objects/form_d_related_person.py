from dataclasses import dataclass


@dataclass(frozen=True)
class FormDRelatedPerson:
    first_name: str
    last_name: str
    relationships: tuple[str, ...]
    relationship_clarification: str | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
