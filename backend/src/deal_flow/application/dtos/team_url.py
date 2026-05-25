from dataclasses import dataclass, field


@dataclass(frozen=True)
class TeamUrl:
    """One team-listing URL the partner extractor will scrape.

    Some firms publish a single team page; others split by tab/filter
    (e.g. Sequoia's Seed/Early vs Growth). ``focus_areas`` carries the
    firm's own label for what this URL contains — propagated onto every
    partner discovered on this URL so a partner appearing in multiple
    URLs gets the union of focus areas after dedupe.
    """

    url: str
    focus_areas: tuple[str, ...] = field(default_factory=tuple)
