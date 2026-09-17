from src.trade_journal import append_entry, make_entry, read_entries


def test_trade_journal_round_trip(tmp_path):
    path = tmp_path / "trades.jsonl"
    entry = make_entry(
        "signal",
        "EURUSD",
        action="BUY",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        reason="strategy signal",
    )
    append_entry(path, entry)
    entries = read_entries(path)
    assert len(entries) == 1
    assert entries[0].symbol == "EURUSD"
    assert entries[0].action == "BUY"
    assert entries[0].stop_loss == 1.09


def test_missing_journal_is_empty(tmp_path):
    assert read_entries(tmp_path / "missing.jsonl") == []
