from src.paper_tracker import PaperTrade, summarize_paper_trades


def test_buy_trade_pnl_and_win():
    trade = PaperTrade("EURUSD", "BUY", 100, 105, 0.8)
    assert round(trade.pnl_pct, 2) == 5.0
    assert trade.win


def test_sell_trade_pnl():
    trade = PaperTrade("EURUSD", "SELL", 100, 95, 0.7)
    assert round(trade.pnl_pct, 2) == 5.0


def test_summary():
    trades = [PaperTrade("A", "BUY", 100, 105, 0.8), PaperTrade("B", "BUY", 100, 98, 0.6)]
    result = summarize_paper_trades(trades)
    assert result["trades"] == 2
    assert result["wins"] == 1
    assert result["losses"] == 1
    assert result["total_return_pct"] == -0.1
    assert result["average_confidence"] == 0.7
