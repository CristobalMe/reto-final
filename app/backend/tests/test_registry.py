from metrics.registry import all_historical, all_local, catalog


def test_all_local_metrics_registered():
    ids = {m.meta.id for m in all_local()}
    expected = {"R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10", "R11"}
    assert expected.issubset(ids), f"missing locals: {expected - ids}"


def test_all_historical_metrics_registered():
    ids = {m.meta.id for m in all_historical()}
    expected = {"H01", "H02", "H03", "H04"}
    assert expected.issubset(ids), f"missing historicals: {expected - ids}"


def test_catalog_entries_have_required_fields():
    for entry in catalog():
        assert entry.id
        assert entry.name
        assert entry.description
        assert entry.scope in ("LOCAL", "HISTORICAL")
        assert entry.category
