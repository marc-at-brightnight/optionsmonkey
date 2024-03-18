import datetime as dt
from typing import Literal, Any

import pandas as pd
from humps import decamelize
from pydantic import BaseModel, Field, field_validator, ConfigDict

OptionType = Literal["call", "put"]
Range = tuple[float, float]
Country = Literal[
    "US",
    "Canada",
    "Mexico",
    "Brazil",
    "China",
    "India",
    "India",
    "South Korea",
    "Russia",
    "Japan",
    "UK",
    "France",
    "Germany",
    "Italy",
    "Australia",
]


class BaseStrategy(BaseModel):
    action: Literal["buy", "sell"]
    prev_pos: float | None = None


class StockStrategy(BaseStrategy):
    """
    "type" : string
        It must be 'stock'. It is mandatory.
    "n" : int
        Number of shares. It is mandatory.
    "action" : string
        Either 'buy' or 'sell'. It is mandatory.
    "prev_pos" : float
        Stock price effectively paid or received in a previously
        opened position. If positive, it means that the position
        remains open and the payoff calculation takes this price
        into account, not the current price of the stock. If
        negative, it means that the position is closed and the
        difference between this price and the current price is
        considered in the payoff calculation.
    """

    type: Literal["stock"] = "stock"
    n: int = Field(gt=0)
    premium: float | None = None


class OptionStrategy(BaseStrategy):
    """
    "type" : string
        Either 'call' or 'put'. It is mandatory.
    "strike" : float
        Option strike price. It is mandatory.
    "premium" : float
        Option premium. It is mandatory.
    "n" : int
        Number of options. It is mandatory
    "action" : string
        Either 'buy' or 'sell'. It is mandatory.
    "prev_pos" : float
        Premium effectively paid or received in a previously opened
        position. If positive, it means that the position remains
        open and the payoff calculation takes this price into
        account, not the current price of the option. If negative,
        it means that the position is closed and the difference
        between this price and the current price is considered in
        the payoff calculation.
    "expiration" : string | int
        Expiration date.
    """

    type: OptionType
    strike: float = Field(gt=0)
    premium: float = Field(gt=0)
    n: int = Field(gt=0)
    expiration: dt.date


class ClosedPosition(BaseModel):
    """
    "type" : string
        It must be 'closed'. It is mandatory.
    "prev_pos" : float
        The total value of the position to be closed, which can be
        positive if it made a profit or negative if it is a loss.
        It is mandatory.
    """

    type: Literal["closed"] = "closed"
    prev_pos: float


Strategy = StockStrategy | OptionStrategy | ClosedPosition


class Inputs(BaseModel):
    """
    stock_price : float
            Spot price of the underlying.
    volatility : float
        Annualized volatility.
    interest_rate : float
        Annualized risk-free interest rate.
    min_stock : float
        Minimum value of the stock in the stock price domain.
    max_stock : float
        Maximum value of the stock in the stock price domain.
    strategy : list
        A list of `Strategy`
    dividend_yield : float, optional
        Annualized dividend yield. Default is 0.0.
    profit_target : float, optional
        Target profit level. Default is None, which means it is not
        calculated.
    loss_limit : float, optional
        Limit loss level. Default is None, which means it is not calculated.
    opt_commission : float
        Broker commission for options transactions. Default is 0.0.
    stock_commission : float
        Broker commission for stocks transactions. Default is 0.0.
    compute_expectation : logical, optional
        Whether or not the strategy's average profit and loss must be
        computed from a numpy array of random terminal prices generated from
        the chosen distribution. Default is False.
    discard_nonbusinessdays : logical, optional
        Whether to discard Saturdays and Sundays (and maybe holidays) when
        counting the number of days between two dates. Default is True.
    country : string, optional
        Country for which the holidays will be considered if 'discard_nonbusinessdyas'
        is True. Default is 'US'.
    start_date : dt.date, optional
        Start date in the calculations (today if not provided).
    target_date : dt.date, optional
        Start date in the calculations (today if not provided).
    distribution : string, optional
        Statistical distribution used to compute probabilities. It can be
        'black-scholes', 'normal', 'laplace' or 'array'. Default is 'black-scholes'.
    nmc_prices : int, optional
        Number of random terminal prices to be generated when calculationg
        the average profit and loss of a strategy. Default is 100,000.
    """

    stock_price: float = Field(gt=0)
    volatility: float
    interest_rate: float = Field(gt=0, le=0.2)
    min_stock: float
    max_stock: float
    strategy: list[Strategy] = Field(..., discriminator="type")
    dividend_yield: float = 0.0
    profit_target: float | None = None
    loss_limit: float | None = None
    opt_commission: float = 0.0
    stock_commission: float = 0.0
    compute_expectation: bool = False
    discard_nonbusiness_days: bool = True
    country: Country = "US"
    start_date: dt.date = Field(default_factory=dt.date.today)
    target_date: dt.date = Field(default_factory=dt.date.today)
    distribution: Literal["black-scholes", "normal", "laplace", "array"] = (
        "black-scholes"
    )
    nmc_prices: float = 100000


class BlackScholesInfo(BaseModel):
    call_price: float
    put_price: float
    call_delta: float
    put_delta: float
    call_theta: float
    put_theta: float
    gamma: float
    vega: float
    call_itm_prob: float
    put_itm_prob: float


class UnderlyingAsset(BaseModel):
    symbol: str
    region: str
    quote_type: Literal["EQUITY"]
    quote_source_name: Literal["Delayed Quote"]
    triggerable: bool
    currency: Literal["USD"]
    market_state: Literal["CLOSED", "OPEN"]
    regular_market_change_percent: float
    regular_market_price: float
    exchange: str
    short_name: str
    long_name: str
    exchange_timezone_name: str
    exchange_timezone_short_name: str
    gmt_off_set_milliseconds: int
    market: Literal["us_market"]
    esg_populated: bool
    first_trade_date_milliseconds: int
    post_market_change_percent: float
    post_market_time: int
    post_market_price: float
    post_market_change: float
    regular_market_change: float
    regular_market_time: int
    regular_market_day_high: float
    regular_market_day_range: tuple[float, float]
    regular_market_day_low: float
    regular_market_volume: float
    regular_market_previous_close: float
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    full_exchange_name: str
    financial_currency: Literal["USD"]
    regular_market_open: float
    average_daily_volume3_month: int
    average_daily_volume10_day: int
    fifty_two_week_low_change: float
    fifty_two_week_low_change_percent: float
    fifty_two_week_range: tuple[float, float]
    fifty_two_week_high_change: float
    fifty_two_week_high_change_percent: float
    fifty_two_week_low: float
    fifty_two_week_high: float
    fifty_two_week_change_percent: float
    dividend_date: int
    earnings_timestamp: int
    earnings_timestamp_start: int
    earnings_timestamp_end: int
    trailing_annual_dividend_rate: float
    trailing_pe: float
    dividend_rate: float
    trailing_annual_dividend_yield: float
    dividend_yield: float
    eps_trailing_twelve_months: float
    eps_forward: float
    eps_current_year: float
    price_eps_current_year: float
    shares_outstanding: int
    book_value: float
    fifty_day_average: float
    fifty_day_average_change: float
    fifty_day_average_change_percent: float
    two_hundred_day_average: float
    two_hundred_day_average_change: float
    two_hundred_day_average_change_percent: float
    market_cap: int
    forward_pe: float
    price_to_book: float
    source_interval: int
    exchange_data_delayed_by: int
    average_analyst_rating: str
    tradeable: bool
    crypto_tradeable: bool
    display_name: str


class OptionsChain(BaseModel):
    calls: pd.DataFrame
    puts: pd.DataFrame
    underlying: UnderlyingAsset
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("underlying", mode="before")
    @classmethod
    def validate_underlying(cls, v: dict[str, Any]) -> UnderlyingAsset:
        day_range_split = v["regularMarketDayRange"].split(" - ")
        fifty_two_week_range_split = v["fiftyTwoWeekRange"].split(" - ")
        return UnderlyingAsset.model_validate(
            decamelize(v)
            | {
                "regular_market_day_range": (
                    float(day_range_split[0]),
                    float(day_range_split[1]),
                ),
                "fifty_two_week_range": (
                    float(fifty_two_week_range_split[0]),
                    float(fifty_two_week_range_split[1]),
                ),
            }
        )


class Outputs(BaseModel):
    """
    probability_of_profit : float
        Probability of the strategy yielding at least $0.01.
    profit_ranges : list
        A Python list of minimum and maximum stock prices defining
        ranges in which the strategy makes at least $0.01.
    strategy_cost : float
        Total strategy cost.
    per_leg_cost : list
        A Python list of costs, one per strategy leg.
    implied_volatility : list
        A Python list of implied volatilities, one per strategy leg.
    in_the_money_probability : list
        A Python list of ITM probabilities, one per strategy leg.
    delta : list
        A Python list of Delta values, one per strategy leg.
    gamma : list
        A Python list of Gamma values, one per strategy leg.
    theta : list
        A Python list of Theta values, one per strategy leg.
    vega : list
        A Python list of Vega values, one per strategy leg.
    minimum_return_in_the_domain : float
        Minimum return of the strategy within the stock price domain.
    maximum_return_in_the_domain : float
        Maximum return of the strategy within the stock price domain.
    probability_of_profit_target : float
        Probability of the strategy yielding at least the profit target.
    project_target_ranges : list
        A Python list of minimum and maximum stock prices defining
        ranges in which the strategy makes at least the profit
        target.
    probability_of_loss_limit : float
        Probability of the strategy losing at least the loss limit.
    average_profit_from_mc : float
        Average profit as calculated from Monte Carlo-created terminal
        stock prices for which the strategy is profitable.
    average_loss_from_mc : float
        Average loss as calculated from Monte Carlo-created terminal
        stock prices for which the strategy ends in loss.
    probability_of_profit_from_mc : float
        Probability of the strategy yielding at least $0.01 as calculated
        from Monte Carlo-created terminal stock prices.
    """

    probability_of_profit: float
    profit_ranges: list[Range]
    per_leg_cost: Range
    strategy_cost: float
    minimum_return_in_the_domain: float
    maximum_return_in_the_domain: float
    implied_volatility: Range
    in_the_money_probability: Range
    delta: Range
    gamma: Range
    theta: Range
    vega: Range
    probability_of_profit_target: float | None = None
    project_target_ranges: Range | None = None
    probability_of_loss_limit: float | None = None
    average_profit_from_mc: float | None = None
    average_loss_from_mc: float | None = None
    probability_of_profit_from_mc: float | None = None
