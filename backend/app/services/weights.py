"""Share % redistribution for stream offers (equal split + pin)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OfferShare:
    offer_id: int
    share: int
    pinned: bool = False
    removed: bool = False


def redistribute(offers: list[OfferShare]) -> list[OfferShare]:
    """Mutate and return shares so active offers sum to 100%.

    Rules (from assignment demo video):
    - removed → always 0%, ignored in split
    - no pins → equal split (remainder to the first items: 3 → 34/33/33)
    - pinned keep their %; remainder split equally among unpinned
    """
    for offer in offers:
        if offer.removed:
            offer.share = 0
            offer.pinned = False

    active = [o for o in offers if not o.removed]
    if not active:
        return offers

    pinned = [o for o in active if o.pinned]
    unpinned = [o for o in active if not o.pinned]

    if not pinned:
        _equal_split(active)
        return offers

    pinned_total = sum(max(0, o.share) for o in pinned)
    if pinned_total > 100:
        # Defensive: scale pinned down proportionally
        scale = 100 / pinned_total
        allocated = 0
        for i, offer in enumerate(pinned):
            if i == len(pinned) - 1:
                offer.share = 100 - allocated
            else:
                offer.share = int(offer.share * scale)
                allocated += offer.share
        pinned_total = sum(o.share for o in pinned)

    remaining = 100 - pinned_total
    if not unpinned:
        return offers

    if remaining <= 0:
        for offer in unpinned:
            offer.share = 0
        return offers

    _equal_split(unpinned, total=remaining)
    return offers


def _equal_split(items: list[OfferShare], *, total: int = 100) -> None:
    n = len(items)
    if n == 0:
        return
    base, rem = divmod(total, n)
    for i, offer in enumerate(items):
        offer.share = base + (1 if i < rem else 0)
