from __future__ import print_function, division

from numpy import array, zeros

from optionsmonkey.black_scholes import get_bs_info, get_implied_vol
from optionsmonkey.models import Inputs, Strategy, Outputs, OptionStrategy
from optionsmonkey.support import (
    getPLprofile,
    getPLprofilestock,
    getPLprofileBS,
    getprofitrange,
    getnonbusinessdays,
    createpriceseq,
    createpricesamples,
    getPoP,
)


class StrategyEngine:
    def __init__(self, inputs: Inputs):
        """
        getdata -> provides input data to performs calculations for a strategy.

        Parameters
        ----------
        inputs: Inputs

        Returns
        -------
        None.
        """
        if len(inputs.strategy) == 0:
            raise ValueError("No strategy provided!")

        self.s = array([])
        self.s_mc = array([])
        self.strike = []
        self.premium = []
        self.n = []
        self.action: list[str] = []
        self.type = []
        self.expiration = []
        self.prev_pos = []
        self.use_bs = []
        self.profit_ranges: list[float] = []
        self.profit_target_range: list[float] = []
        self.loss_limit_ranges: list[float] = []
        self.days_to_maturity: list[float] = []
        self.start_date = inputs.start_date
        self.country = "US"
        self.days_to_target = 30
        self.discard_nonbusinessdays = True
        self.days_in_year = 252
        self.impvol: list[float] = []
        self.itmprob: list[float] = []
        self.delta: list[float] = []
        self.gamma: list[float] = []
        self.vega: list[float] = []
        self.theta: list[float] = []
        self.cost: list[float] = []
        self.profitprob = 0.0
        self.profittargprob = 0.0
        self.losslimitprob = 0.0
        self.distribution = inputs.distribution
        self.stock_price = inputs.stock_price
        self.volatility = inputs.volatility
        self.r = inputs.interest_rate
        self.y = inputs.dividend_yield
        self.min_stock = inputs.min_stock
        self.max_stock = inputs.max_stock
        self.profit_target = inputs.profit_target
        self.loss_limit = inputs.loss_limit
        self.opt_commission = inputs.opt_commission
        self.stock_commission = inputs.stock_commission
        self.nmc_prices = inputs.nmc_prices
        self.compute_expectation = inputs.compute_expectation
        self.discard_nonbusinessdays = inputs.discard_nonbusiness_days

        self.days_in_year = 252 if self.discard_nonbusinessdays else 365

        self.country = inputs.country

        if inputs.target_date > inputs.start_date:
            self.start_date = inputs.start_date
            self.target_date = inputs.target_date

            if self.discard_nonbusinessdays:
                ndiscardeddays = getnonbusinessdays(
                    self.start_date, self.target_date, self.country
                )
            else:
                ndiscardeddays = 0

            self.days_to_target = (
                self.target_date - self.start_date
            ).days - ndiscardeddays
        else:
            raise ValueError(
                "Start date cannot be after the target date!"
            )  # TODO: move validation to pydantic

        for i, strat in enumerate(inputs.strategy):
            strategy: Strategy = strat
            self.type.append(strategy.type)

            if type(strategy) is OptionStrategy:
                self.strike.append(strategy.strike)  # type: ignore
                self.premium.append(strategy.premium)  # type: ignore
                self.n.append(strategy.n)  # type: ignore
                self.action.append(strategy.action)  # type: ignore
                self.prev_pos.append(strategy.prev_pos or 0.0)

                if strategy.expiration >= self.target_date:
                    self.expiration.append(strategy.expiration)

                    if self.discard_nonbusinessdays:
                        ndiscardeddays = getnonbusinessdays(
                            self.start_date, strategy.expiration, self.country
                        )
                    else:
                        ndiscardeddays = 0

                    self.days_to_maturity.append(
                        (strategy.expiration - self.start_date).days - ndiscardeddays
                    )

                    self.use_bs.append(strategy.expiration != self.target_date)
                else:
                    raise ValueError(
                        "Expiration date must be after or equal to the target date!"
                    )

            elif strategy.type == "stock":
                self.n.append(strategy.n)
                self.action.append(strategy.action)
                self.prev_pos.append(strategy.prev_pos or 0.0)

                self.strike.append(0.0)
                self.premium.append(0.0)
                self.use_bs.append(False)
                self.days_to_maturity.append(-1)
                self.expiration.append(self.target_date)

            elif strategy.type == "closed":
                self.prev_pos.append(strategy.prev_pos)
                self.strike.append(0.0)
                self.n.append(0)
                self.premium.append(0.0)
                self.action.append("n/a")
                self.use_bs.append(False)
                self.days_to_maturity.append(-1)
                self.expiration.append(self.target_date)
            else:
                raise ValueError("Type must be 'call', 'put', 'stock' or 'closed'!")


    def run(self):
        """
        run -> runs calculations for an options strategy.

        Returns
        -------
        outputs : Outputs
        """
        if len(self.type) == 0:
            raise RuntimeError("No legs in the strategy! Nothing to do!")
        elif self.type.count("closed") > 1:
            raise RuntimeError("Only one position of type 'closed' is allowed!")
        elif self.distribution == "array" and self.s_mc.shape[0] == 0:
            raise RuntimeError(
                "No terminal stock prices from Monte Carlo simulations! Nothing to do!"
            )

        time2target = self.days_to_target / self.days_in_year
        self.cost = [0.0 for _ in range(len(self.type))]
        self.impvol = []
        self.itmprob = []
        self.delta = []
        self.gamma = []
        self.vega = []
        self.theta = []

        if self.s.shape[0] == 0:
            self.s = createpriceseq(self.min_stock, self.max_stock)

        self.profit = zeros((len(self.type), self.s.shape[0]))
        self.strategyprofit = zeros(self.s.shape[0])

        if self.compute_expectation and self.s_mc.shape[0] == 0:
            self.s_mc = createpricesamples(
                self.stock_price,
                self.volatility,
                time2target,
                self.r,
                self.distribution,
                self.y,
                self.nmc_prices,
            )

        if self.s_mc.shape[0] > 0:
            self.profit_mc = zeros((len(self.type), self.s_mc.shape[0]))
            self.strategyprofit_mc = zeros(self.s_mc.shape[0])

        for i, type in enumerate(self.type):
            if type in ("call", "put"):
                if self.prev_pos[i] >= 0.0:
                    time2maturity = self.days_to_maturity[i] / self.days_in_year
                    bs = get_bs_info(
                        self.stock_price,
                        self.strike[i],
                        self.r,
                        self.volatility,
                        time2maturity,
                        self.y,
                    )

                    self.gamma.append(bs.gamma)
                    self.vega.append(bs.vega)

                    if type == "call":
                        self.impvol.append(
                            get_implied_vol(
                                "call",
                                self.premium[i],
                                self.stock_price,
                                self.strike[i],
                                self.r,
                                time2maturity,
                                self.y,
                            )
                        )
                        self.itmprob.append(bs.call_itm_prob)

                        if self.action[i] == "buy":
                            self.delta.append(bs.call_delta)
                            self.theta.append(bs.call_theta / self.days_in_year)
                        else:
                            self.delta.append(-bs.call_delta)
                            self.theta.append(-bs.call_theta / self.days_in_year)
                    else:
                        self.impvol.append(
                            get_implied_vol(
                                "put",
                                self.premium[i],
                                self.stock_price,
                                self.strike[i],
                                self.r,
                                time2maturity,
                                self.y,
                            )
                        )
                        self.itmprob.append(bs.putitmprob)

                        if self.action[i] == "buy":
                            self.delta.append(bs.put_delta)
                            self.theta.append(bs.put_theta / self.days_in_year)
                        else:
                            self.delta.append(-bs.put_delta)
                            self.theta.append(-bs.put_theta / self.days_in_year)
                else:
                    self.impvol.append(0.0)
                    self.itmprob.append(0.0)
                    self.delta.append(0.0)
                    self.gamma.append(0.0)
                    self.vega.append(0.0)
                    self.theta.append(0.0)

                if self.prev_pos[i] < 0.0:  # Previous position is closed
                    costtmp = (self.premium[i] + self.prev_pos[i]) * self.n[i]

                    if self.action[i] == "buy":
                        costtmp *= -1.0

                    self.cost[i] = costtmp
                    self.profit[i] += costtmp

                    if self.compute_expectation or self.distribution == "array":
                        self.profit_mc[i] += costtmp
                else:
                    if self.prev_pos[i] > 0.0:  # Premium of the open position
                        opval = self.prev_pos[i]
                    else:  # Current premium
                        opval = self.premium[i]

                    if self.use_bs[i]:
                        self.profit[i], self.cost[i] = getPLprofileBS(
                            type,
                            self.action[i],
                            self.strike[i],
                            opval,
                            self.r,
                            (self.days_to_maturity[i] - self.days_to_target)
                            / self.days_in_year,
                            self.volatility,
                            self.n[i],
                            self.s,
                            self.y,
                            self.opt_commission,
                        )

                        if self.compute_expectation or self.distribution == "array":
                            self.profit_mc[i] = getPLprofileBS(
                                type,
                                self.action[i],
                                self.strike[i],
                                opval,
                                self.r,
                                (self.days_to_maturity[i] - self.days_to_target)
                                / self.days_in_year,
                                self.volatility,
                                self.n[i],
                                self.s_mc,
                                self.y,
                                self.opt_commission,
                            )[0]
                    else:
                        self.profit[i], self.cost[i] = getPLprofile(
                            type,
                            self.action[i],
                            self.strike[i],
                            opval,
                            self.n[i],
                            self.s,
                            self.opt_commission,
                        )

                        if self.compute_expectation or self.distribution == "array":
                            self.profit_mc[i] = getPLprofile(
                                type,
                                self.action[i],
                                self.strike[i],
                                opval,
                                self.n[i],
                                self.s_mc,
                                self.opt_commission,
                            )[0]
            elif type == "stock":
                self.impvol.append(0.0)
                self.itmprob.append(1.0)
                self.delta.append(1.0)
                self.gamma.append(0.0)
                self.vega.append(0.0)
                self.theta.append(0.0)

                if self.prev_pos[i] < 0.0:  # Previous position is closed
                    costtmp = (self.stock_price + self.prev_pos[i]) * self.n[i]

                    if self.action[i] == "buy":
                        costtmp *= -1.0

                    self.cost[i] = costtmp
                    self.profit[i] += costtmp

                    if self.compute_expectation or self.distribution == "array":
                        self.profit_mc[i] += costtmp
                else:
                    if self.prev_pos[i] > 0.0:  # Stock price at previous position
                        stockpos = self.prev_pos[i]
                    else:  # Spot price of the stock at start date
                        stockpos = self.stock_price

                    self.profit[i], self.cost[i] = getPLprofilestock(
                        stockpos,
                        self.action[i],
                        self.n[i],
                        self.s,
                        self.stock_commission,
                    )

                    if self.compute_expectation or self.distribution == "array":
                        self.profit_mc[i] = getPLprofilestock(
                            stockpos,
                            self.action[i],
                            self.n[i],
                            self.s_mc,
                            self.stock_commission,
                        )[0]
            elif type == "closed":
                self.impvol.append(0.0)
                self.itmprob.append(0.0)
                self.delta.append(0.0)
                self.gamma.append(0.0)
                self.vega.append(0.0)
                self.theta.append(0.0)

                self.cost[i] = self.prev_pos[i]
                self.profit[i] += self.prev_pos[i]

                if self.compute_expectation or self.distribution == "array":
                    self.profit_mc[i] += self.prev_pos[i]

            self.strategyprofit += self.profit[i]

            if self.compute_expectation or self.distribution == "array":
                self.strategyprofit_mc += self.profit_mc[i]

        self.profit_ranges = getprofitrange(self.s, self.strategyprofit)

        if self.profit_ranges:
            if self.distribution in ("normal", "laplace", "black-scholes"):
                self.profitprob = getPoP(
                    self.profit_ranges,
                    self.distribution,
                    stockprice=self.stock_price,
                    volatility=self.volatility,
                    time2maturity=time2target,
                    interestrate=self.r,
                    dividendyield=self.y,
                )
            elif self.distribution == "array":
                self.profitprob = getPoP(
                    self.profit_ranges, self.distribution, array=self.s_mc
                )

        if self.profit_target is not None:
            self.profit_target_range = getprofitrange(
                self.s, self.strategyprofit, self.profit_target
            )

            if self.profit_target_range:
                if self.distribution in ("normal", "laplace", "black-scholes"):
                    self.profittargprob = getPoP(
                        self.profit_target_range,
                        self.distribution,
                        stockprice=self.stock_price,
                        volatility=self.volatility,
                        time2maturity=time2target,
                        interestrate=self.r,
                        dividendyield=self.y,
                    )
                elif self.distribution == "array":
                    self.profittargprob = getPoP(
                        self.profit_target_range, self.distribution, array=self.s_mc
                    )

        if self.loss_limit is not None:
            self.loss_limit_ranges = getprofitrange(
                self.s, self.strategyprofit, self.loss_limit + 0.01
            )

            if self.loss_limit_ranges:
                if self.distribution in ("normal", "laplace", "black-scholes"):
                    self.losslimitprob = 1.0 - getPoP(
                        self.loss_limit_ranges,
                        self.distribution,
                        stockprice=self.stock_price,
                        volatility=self.volatility,
                        time2maturity=time2target,
                        interestrate=self.r,
                        dividendyield=self.y,
                    )
                elif self.distribution == "array":
                    self.losslimitprob = 1.0 - getPoP(
                        self.loss_limit_ranges, self.distribution, array=self.s_mc
                    )

        opt_outputs = {}

        if self.profit_target is not None:
            opt_outputs["probability_of_profit_target"] = self.profittargprob
            opt_outputs["project_target_ranges"] = self.profit_target_range

        if self.loss_limit is not None:
            opt_outputs["probability_of_loss_limit"] = self.losslimitprob

        if (
            self.compute_expectation or self.distribution == "array"
        ) and self.s_mc.shape[0] > 0:
            tmpprof = self.strategyprofit_mc[self.strategyprofit_mc >= 0.01]
            tmploss = self.strategyprofit_mc[self.strategyprofit_mc < 0.0]
            opt_outputs["average_profit_from_mc"] = (
                tmpprof.mean() if tmpprof.shape[0] > 0 else 0.0
            )
            opt_outputs["average_loss_from_mc"] = (
                tmploss.mean() if tmploss.shape[0] > 0 else 0.0
            )

            opt_outputs["probability_of_profit_from_mc"] = (
                self.strategyprofit_mc >= 0.01
            ).sum() / self.strategyprofit_mc.shape[0]

        return Outputs.model_validate(
            opt_outputs
            | {
                "probability_of_profit": self.profitprob,
                "strategy_cost": sum(self.cost),
                "per_leg_cost": self.cost,
                "profit_ranges": self.profit_ranges,
                "minimum_return_in_the_domain": self.strategyprofit.min(),
                "maximum_return_in_the_domain": self.strategyprofit.max(),
                "implied_volatility": self.impvol,
                "in_the_money_probability": self.itmprob,
                "delta": self.delta,
                "gamma": self.gamma,
                "theta": self.theta,
                "vega": self.vega,
            }
        )

    def get_pl(self, leg=-1):
        """
        get_pl -> returns the profit/loss profile of either a leg or the whole
        strategy.

        Parameters
        ----------
        leg : int, optional
            Index of the leg. Default is -1 (whole strategy).

        Returns
        -------
        stock prices : numpy array
            Sequence of stock prices within the bounds of the stock price domain.
        P/L profile : numpy array
            Profit/loss profile of either a leg or the whole strategy.
        """
        if self.profit.size > 0 and leg >= 0 and leg < self.profit.shape[0]:
            return self.s, self.profit[leg]
        else:
            return self.s, self.strategyprofit

    """
    Properties
    ----------
    days2target : int, readonly
        Number of days remaining to the target date from the start date.
    stockpricearray : array
        A Numpy array of consecutive stock prices, from the minimum price up to 
        the maximum price in the stock price domain. It is used to compute the 
        strategy's P/L profile.
    terminalstockprices : array
        A Numpy array or terminal stock prices typically generated by Monte Carlo 
        simulations. It is used to compute strategy's expected profit and loss. 
    """

    @property
    def days2target(self):
        return self.days_to_target

    @property
    def stockpricearray(self):
        return self.s

    @property
    def terminalstockprices(self):
        return self.s_mc
