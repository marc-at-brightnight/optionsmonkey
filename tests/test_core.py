from optionsmonkey.engine import StrategyEngine

from optionsmonkey.models import Inputs, Outputs


def test_covered_call(nvidia):
    # https://medium.com/@rgaveiga/python-for-options-trading-2-mixing-options-and-stocks-1e9f59f388f

    inputs = Inputs.model_validate(
        nvidia
        | dict(
            # The covered call strategy is defined
            strategy=[
                {"type": "stock", "n": 100, "action": "buy"},
                {
                    "type": "call",
                    "strike": 185.0,
                    "premium": 4.1,
                    "n": 100,
                    "action": "sell",
                    "expiration": nvidia["target_date"],
                },
            ],
        )
    )

    st = StrategyEngine(inputs)
    outputs = st.run()

    # Print useful information on screen
    assert isinstance(outputs, Outputs)
    assert outputs.model_dump(exclude_none=True) == {
        "probability_of_profit": 0.5489826392738772,
        "profit_ranges": [(164.9, float("inf"))],
        "per_leg_cost": (-16899.0, 409.99999999999994),
        "strategy_cost": -16489.0,
        "minimum_return_in_the_domain": -9590.000000000002,
        "maximum_return_in_the_domain": 2011.0,
        "implied_volatility": (0.0, 0.466),
        "in_the_money_probability": (1.0, 0.2529827985340476),
        "delta": (1.0, -0.30180572515271814),
        "gamma": (0.0, 0.01413835937607837),
        "theta": (0.0, 0.19521264859629808),
        "vega": (0.0, 0.1779899391089498),
    }


def test_covered_call_w_prev_position(nvidia):
    # https://medium.com/@rgaveiga/python-for-options-trading-2-mixing-options-and-stocks-1e9f59f388f

    inputs = Inputs.model_validate(
        nvidia
        | dict(
            # The covered call strategy is defined
            strategy=[
                {"type": "stock", "n": 100, "action": "buy", "prev_pos": 158.99},
                {
                    "type": "call",
                    "strike": 185.0,
                    "premium": 4.1,
                    "n": 100,
                    "action": "sell",
                    "expiration": nvidia["target_date"],
                },
            ]
        )
    )

    st = StrategyEngine(inputs)
    outputs = st.run()

    # Print useful information on screen
    assert outputs.model_dump(exclude_none=True) == {
        "probability_of_profit": 0.7094641281976972,
        "profit_ranges": [(154.9, float("inf"))],
        "per_leg_cost": (-15899.0, 409.99999999999994),
        "strategy_cost": -15489.0,
        "minimum_return_in_the_domain": -8590.000000000002,
        "maximum_return_in_the_domain": 3011.0,
        "implied_volatility": (0.0, 0.466),
        "in_the_money_probability": (1.0, 0.2529827985340476),
        "delta": (1.0, -0.30180572515271814),
        "gamma": (0.0, 0.01413835937607837),
        "theta": (0.0, 0.19521264859629808),
        "vega": (0.0, 0.1779899391089498),
    }


def test_100_perc_itm(nvidia):
    # https://medium.com/@rgaveiga/python-for-options-trading-3-a-trade-with-100-probability-of-profit-886e934addbf

    inputs = Inputs.model_validate(
        nvidia
        | dict(
            # The covered call strategy is defined
            strategy=[
                {
                    "type": "call",
                    "strike": 165.0,
                    "premium": 12.65,
                    "n": 100,
                    "action": "buy",
                    "prev_pos": 7.5,
                    "expiration": nvidia["target_date"],
                },
                {
                    "type": "call",
                    "strike": 170.0,
                    "premium": 9.9,
                    "n": 100,
                    "action": "sell",
                    "expiration": nvidia["target_date"],
                },
            ]
        )
    )

    st = StrategyEngine(inputs)
    outputs = st.run()

    # Print useful information on screen
    assert outputs.model_dump(exclude_none=True) == {
        "probability_of_profit": 1.0,
        "profit_ranges": [(0.0, float("inf"))],
        "per_leg_cost": (-750.0, 990.0),
        "strategy_cost": 240.0,
        "minimum_return_in_the_domain": 240.0,
        "maximum_return_in_the_domain": 740.0000000000018,
        "implied_volatility": (0.505, 0.493),
        "in_the_money_probability": (0.547337257503663, 0.4658724723221915),
        "delta": (0.6044395589860037, -0.5240293090819207),
        "gamma": (0.015620889396345561, 0.016149144698391314),
        "theta": (-0.22254722153197432, 0.22755381063645636),
        "vega": (0.19665373318968424, 0.20330401888012928),
    }
