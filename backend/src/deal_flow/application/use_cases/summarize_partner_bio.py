from dataclasses import dataclass

from deal_flow.application.ports.services.llm_structured_output import (
    LlmStructuredOutput,
)

_PROMPT_TEMPLATE = (
    "You are condensing a VC partner's biography for a deal-flow dashboard. "
    "Write 1-2 sentences that capture (a) what the partner invests in and "
    "(b) one or two most-relevant prior roles or notable investments. "
    "No marketing language, no personal trivia, no 'is a general partner at "
    "X' restatement. Plain text, no markdown.\n\nBiography:\n{bio}"
)

_RESPONSE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "about_short": {
            "type": "string",
            "description": "1-2 sentence summary of the partner's investing focus and key prior experience.",
        }
    },
    "required": ["about_short"],
}


@dataclass(frozen=True)
class SummarizePartnerBioInput:
    bio: str


@dataclass(frozen=True)
class SummarizedBio:
    about_short: str


class SummarizePartnerBio:
    """Reduce a long scraped partner bio to a 1-2 sentence ``about`` line."""

    def __init__(self, llm: LlmStructuredOutput) -> None:
        self._llm = llm

    def execute(self, input: SummarizePartnerBioInput) -> SummarizedBio:
        result = self._llm.generate(
            prompt=_PROMPT_TEMPLATE.format(bio=input.bio.strip()),
            response_schema=_RESPONSE_SCHEMA,
            schema_name="partner_bio_summary_v1",
        )
        return SummarizedBio(about_short=(result.get("about_short") or "").strip())
