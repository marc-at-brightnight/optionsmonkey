import pandas as pd

from optionsmonkey.api import get_options_chain, get_stock_history
from optionsmonkey.models import UnderlyingAsset
from optionsmonkey.utils import get_fridays_date


def test_get_options_chain():

    next_friday_date = get_fridays_date()

    options = get_options_chain("MSFT", next_friday_date)

    assert isinstance(options.calls, pd.DataFrame)
    assert isinstance(options.puts, pd.DataFrame)
    assert isinstance(options.underlying, UnderlyingAsset)


def test_get_stock_history():

    hist_df = get_stock_history("MSFT", 1)

    assert isinstance(hist_df, pd.DataFrame)
