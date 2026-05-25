from dataclasses import dataclass, replace
from urllib.parse import urljoin

from deal_flow.application.dtos.team_url import TeamUrl
from deal_flow.application.ports.services.web_extractor import WebExtractor
from deal_flow.domain.entities.partner import Partner


@dataclass(frozen=True)
class ExtractFirmPartnersInput:
    """Two listing strategies; pick one per firm:

    - ``team_urls``: one or more team pages we scrape via Firecrawl LLM
      extraction. Each ``TeamUrl`` may carry ``focus_areas`` tags — those
      are propagated onto every partner discovered on that URL, then
      unioned when the same partner appears under multiple URLs (e.g.
      a Sequoia partner on both the Seed/Early and Growth tabs).
    - ``payload_url`` + ``payload_attribute`` + ``payload_role_filter``:
      the team page embeds the whole roster as JSON in a data-* attribute
      (e.g. a16z). The JSON already carries focus areas + socials.

    ``limit`` is applied after merge/dedupe. ``None`` means no cap.
    """

    team_urls: tuple[TeamUrl, ...] = ()
    payload_url: str | None = None
    payload_attribute: str | None = None
    payload_role_filter: str | None = None
    limit: int | None = None
    firm_name: str | None = None  # when set, missing x_urls are searched for


class ExtractFirmPartners:
    """Resolve a listing (multi-URL or payload) → batch profile detail → Partners.

    When ``input.firm_name`` is set, partners whose listing+profile didn't
    surface an X link get one filled in via the extractor's web-search
    fallback. The fallback fires one search per missing partner — leave
    ``firm_name=None`` for the cheap path.
    """

    def __init__(self, extractor: WebExtractor) -> None:
        self._extractor = extractor

    def execute(self, input: ExtractFirmPartnersInput) -> list[Partner]:
        listings = self._collect_listings(input)
        if input.limit is not None:
            listings = listings[: input.limit]

        detail_urls = [item["profile_url"] for item in listings if item.get("profile_url")]
        details_by_url: dict[str, dict] = (
            self._extractor.scrape_partner_details(detail_urls) if detail_urls else {}
        )

        partners = [
            _to_partner(item, details_by_url.get(item.get("profile_url") or ""))
            for item in listings
        ]
        if input.firm_name:
            partners = [self._fill_x_url(p, input.firm_name) for p in partners]
        return partners

    def _collect_listings(self, input: ExtractFirmPartnersInput) -> list[dict]:
        """Run the chosen listing strategy and return deduped listing dicts.

        Dedupe key is the absolute profile URL — fallback to lowercased name
        when a listing item has no profile URL (rare). When a partner is
        seen on multiple ``TeamUrl``s, focus_areas are unioned across appearances.
        """
        if input.payload_url:
            return self._extractor.discover_partners_from_payload(
                input.payload_url,
                input.payload_attribute or "data-payload",
                input.payload_role_filter,
            )

        by_key: dict[str, dict] = {}
        order: list[str] = []
        for team_url in input.team_urls:
            for item in self._extractor.scrape_partner_listing(team_url.url):
                if item.get("profile_url"):
                    item["profile_url"] = urljoin(team_url.url, item["profile_url"])
                key = (item.get("profile_url") or (item.get("name") or "").lower()).strip()
                if not key:
                    continue
                existing = by_key.get(key)
                if existing is None:
                    item = {**item, "focus_areas": tuple(team_url.focus_areas)}
                    by_key[key] = item
                    order.append(key)
                else:
                    merged: list[str] = list(existing.get("focus_areas") or ())
                    for fa in team_url.focus_areas:
                        if fa not in merged:
                            merged.append(fa)
                    existing["focus_areas"] = tuple(merged)
        return [by_key[k] for k in order]

    def _fill_x_url(self, partner: Partner, firm_name: str) -> Partner:
        if partner.x_url or not partner.name:
            return partner
        found = self._extractor.search_x_profile(firm_name, partner.name)
        return replace(partner, x_url=found) if found else partner


def _to_partner(listing: dict, detail: dict | None) -> Partner:
    detail = detail or {}
    return Partner(
        name=listing.get("name") or "",
        profile_url=listing.get("profile_url") or "",
        role=detail.get("role") or listing.get("role"),
        bio=detail.get("bio"),
        linkedin_url=detail.get("linkedin_url") or listing.get("linkedin_url"),
        x_url=detail.get("x_url") or listing.get("x_url"),
        farcaster_url=listing.get("farcaster_url"),
        email=detail.get("email"),
        photo_url=detail.get("photo_url") or listing.get("photo_url"),
        focus_areas=tuple(listing.get("focus_areas") or ()),
        education=tuple(detail.get("education") or ()),
        prior_experience=tuple(detail.get("prior_experience") or ()),
    )
