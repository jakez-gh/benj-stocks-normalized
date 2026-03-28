from datetime import date

import pytest

from daily_bars_alpha_vantage import parse_alpha_vantage_daily_json


def test_parse_alpha_vantage_daily_json_note_payload_raises():
    payload = '{"Note": "Thank you for using Alpha Vantage..."}'
    with pytest.raises(ValueError, match="Alpha Vantage"):
        parse_alpha_vantage_daily_json(payload)


def test_parse_alpha_vantage_daily_json_scales_ohlc_to_adjusted_close():
    payload = """
{
  "Meta Data": {"1. Information": "Daily adjusted prices"},
  "Time Series (Daily)": {
    "2024-01-03": {
      "1. open": "6.0", "2. high": "6.0", "3. low": "6.0", "4. close": "6.0",
      "5. adjusted close": "3.0", "6. volume": "60", "7. dividend amount": "0.0000", "8. split coefficient": "1.0"
    },
    "2024-01-01": {
      "1. open": "2.0", "2. high": "2.0", "3. low": "2.0", "4. close": "2.0",
      "5. adjusted close": "1.0", "6. volume": "20", "7. dividend amount": "0.0000", "8. split coefficient": "1.0"
    }
  }
}
"""
    bars = parse_alpha_vantage_daily_json(payload)
    assert [b.trade_date for b in bars] == [date(2024, 1, 1), date(2024, 1, 3)]
    assert bars[0].open == 1.0 and bars[0].close == 1.0 and bars[0].volume == 20
    assert bars[1].open == 3.0 and bars[1].close == 3.0 and bars[1].volume == 60
