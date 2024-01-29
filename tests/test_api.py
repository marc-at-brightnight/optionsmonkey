import pandas as pd

from optionsmonkey.api import get_options_chain, get_stock_history
from datetime import datetime, timedelta


def test_get_options_chain():

    # Current date
    current_date = datetime.now()

    days_until_friday = 4 - current_date.weekday() + 7
    next_friday_date = current_date + timedelta(days=days_until_friday)

    assert next_friday_date.weekday() == 4

    options = get_options_chain('MSFT', next_friday_date.strftime("%Y-%m-%d"))

    assert isinstance(options.calls, pd.DataFrame)
    assert isinstance(options.puts, pd.DataFrame)
    assert isinstance(options.underlying, dict)


def test_get_stock_history():

    hist_df = get_stock_history('MSFT', 1)

    assert isinstance(hist_df, pd.DataFrame)
