import datetime as dt
from typing import Literal

from optionsmonkey.models import Strategy, StockStrategy, OptionStrategy

NamedStrategy = Literal["covered-call", "married-put", "bull-call", "protective-collar"]


def generate_strategies(
    named_strat: NamedStrategy,
    strike: float,
    premium: float,
    expiration: dt.date,
    n: int = 100,
    prev_pos: float | None = None,
    higher_strike: float | None = None,
) -> list[Strategy]:
    """Generate common option strategies
    Source: https://www.investopedia.com/trading/options-strategies/
    """

    match named_strat:
        case "covered-call":
            return _generate_covered_call_strategy(
                strike, premium, n, expiration, prev_pos
            )
        case "married-put":
            return _generate_married_put_strategy(
                strike, premium, n, expiration, prev_pos
            )
        case "bull-call":
            return _generate_bull_call_strategy(
                strike, premium, n, expiration, prev_pos, higher_strike
            )
        case "protective-collar":
            return _generate_protective_collar_strategy(
                strike, premium, n, expiration, prev_pos, higher_strike
            )
        case _:
            raise ValueError("Strategy not defined")


def _generate_covered_call_strategy(
    strike: float, premium: float, n: int, expiration: dt.date, prev_pos: float | None
) -> list[Strategy]:

    return [
        StockStrategy(n=n, prev_pos=prev_pos, action="buy"),
        OptionStrategy(
            n=n,
            prev_pos=prev_pos,
            strike=strike,
            premium=premium,
            type="call",
            action="sell",
            expiration=expiration,
        ),
    ]


def _generate_married_put_strategy(
    strike: float, premium: float, n: int, expiration: dt.date, prev_pos: float | None
) -> list[Strategy]:

    return [
        StockStrategy(n=n, prev_pos=prev_pos, action="buy"),
        OptionStrategy(
            n=n,
            prev_pos=prev_pos,
            strike=strike,
            premium=premium,
            type="put",
            action="buy",
            expiration=expiration,
        ),
    ]


def _generate_bull_call_strategy(
    strike: float,
    premium: float,
    n: int,
    expiration: dt.date,
    prev_pos: float | None,
    higher_strike: float | None,
) -> list[Strategy]:

    if higher_strike is None or higher_strike < strike:
        raise ValueError("Higher strike price must be provided for bull call strategy")

    return [
        OptionStrategy(
            n=n,
            prev_pos=prev_pos,
            strike=strike,
            premium=premium,
            type="call",
            action="buy",
            expiration=expiration,
        ),
        OptionStrategy(
            n=n,
            prev_pos=prev_pos,
            strike=higher_strike,
            premium=premium,
            type="call",
            action="sell",
            expiration=expiration,
        ),
    ]


def _generate_protective_collar_strategy(
    strike: float,
    premium: float,
    n: int,
    expiration: dt.date,
    prev_pos: float | None,
    higher_strike: float | None,
) -> list[Strategy]:

    if higher_strike is None or higher_strike < strike:
        raise ValueError(
            "Higher strike price must be provided for protective caller strategy"
        )

    return [
        OptionStrategy(
            n=n,
            prev_pos=prev_pos,
            strike=strike,
            premium=premium,
            type="put",
            action="buy",
            expiration=expiration,
        ),
        OptionStrategy(
            n=n,
            prev_pos=prev_pos,
            strike=higher_strike,
            premium=premium,
            type="call",
            action="sell",
            expiration=expiration,
        ),
    ]
