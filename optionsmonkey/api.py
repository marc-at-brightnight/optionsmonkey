from dataclasses import dataclass
from typing import Any

import pandas as pd
from yfinance import Ticker

@dataclass
class OptionsChain:
    calls: pd.DataFrame
    puts: pd.DataFrame
    underlying: dict[str, Any]


def get_options_chain(ticker: str, expiration_date: str) -> OptionsChain:
    stock = Ticker(ticker)
    return stock.option_chain(expiration_date)


def get_stock_history(ticker: str, num_of_months: int) -> pd.DataFrame:
    stock = Ticker(ticker)
    return stock.history(period=f"{num_of_months}mo")
