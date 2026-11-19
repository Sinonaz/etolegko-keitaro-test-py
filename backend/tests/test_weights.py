from app.services.weights import OfferShare, redistribute


def test_equal_split_three() -> None:
    offers = [
        OfferShare(1, 0),
        OfferShare(2, 0),
        OfferShare(3, 0),
    ]
    redistribute(offers)
    assert [o.share for o in offers] == [34, 33, 33]
    assert sum(o.share for o in offers) == 100


def test_equal_split_four() -> None:
    offers = [OfferShare(i, 0) for i in range(4)]
    redistribute(offers)
    assert [o.share for o in offers] == [25, 25, 25, 25]


def test_pin_locks_share() -> None:
    offers = [
        OfferShare(1, 25, pinned=True),
        OfferShare(2, 0),
        OfferShare(3, 0),
    ]
    redistribute(offers)
    assert offers[0].share == 25
    assert sorted(o.share for o in offers[1:]) == [37, 38]
    assert sum(o.share for o in offers) == 100


def test_removed_zero() -> None:
    offers = [
        OfferShare(1, 50),
        OfferShare(2, 50),
        OfferShare(3, 0, removed=True),
    ]
    redistribute(offers)
    assert offers[2].share == 0
    assert sum(o.share for o in offers if not o.removed) == 100
