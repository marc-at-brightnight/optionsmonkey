import matplotlib.pyplot as plt
from matplotlib import rcParams
from numpy import zeros, full

from optionsmonkey.engine import StrategyEngine


def plot_pl(st: StrategyEngine):
    """
    plotPL -> displays the strategy's profit/loss profile diagram.

    Returns
    -------
    None.
    """
    if len(st.strategyprofit) == 0:
        raise RuntimeError(
            "Before plotting the profit/loss profile diagram, you must run a calculation!"
        )

    rcParams.update({"figure.autolayout": True})

    zeroline = zeros(st.s.shape[0])
    strikecallbuy = []
    strikeputbuy = []
    zerocallbuy = []
    zeroputbuy = []
    strikecallsell = []
    strikeputsell = []
    zerocallsell = []
    zeroputsell = []
    comment = "P/L profile diagram:\n--------------------\n"
    comment += "The vertical green dashed line corresponds to the position "
    comment += "of the stock's spot price. The right and left arrow "
    comment += "markers indicate the strike prices of calls and puts, "
    comment += "respectively, with blue representing long and red representing "
    comment += "short positions."

    plt.axvline(st.stock_price, ls="--", color="green")
    plt.xlabel("Stock price")
    plt.ylabel("Profit/Loss")
    plt.xlim(st.s.min(), st.s.max())

    for i in range(len(st.strike)):
        if st.strike[i] > 0.0:
            if st.type[i] == "call":
                if st.action[i] == "buy":
                    strikecallbuy.append(st.strike[i])
                    zerocallbuy.append(0.0)
                elif st.action[i] == "sell":
                    strikecallsell.append(st.strike[i])
                    zerocallsell.append(0.0)
            elif st.type[i] == "put":
                if st.action[i] == "buy":
                    strikeputbuy.append(st.strike[i])
                    zeroputbuy.append(0.0)
                elif st.action[i] == "sell":
                    strikeputsell.append(st.strike[i])
                    zeroputsell.append(0.0)

    if st.profit_target is not None:
        comment += " The blue dashed line represents the profit target level."
        targetline = full(st.s.shape[0], st.profit_target)

    if st.loss_limit is not None:
        comment += " The red dashed line represents the loss limit level."
        lossline = full(st.s.shape[0], st.loss_limit)

    print(comment)

    if st.loss_limit is not None and st.profit_target is not None:
        plt.plot(
            st.s,
            zeroline,
            "m--",
            st.s,
            lossline,
            "r--",
            st.s,
            targetline,
            "b--",
            st.s,
            st.strategyprofit,
            "k-",
            strikecallbuy,
            zerocallbuy,
            "b>",
            strikeputbuy,
            zeroputbuy,
            "b<",
            strikecallsell,
            zerocallsell,
            "r>",
            strikeputsell,
            zeroputsell,
            "r<",
            markersize=10,
        )
    elif st.loss_limit is not None:
        plt.plot(
            st.s,
            zeroline,
            "m--",
            st.s,
            lossline,
            "r--",
            st.s,
            st.strategyprofit,
            "k-",
            strikecallbuy,
            zerocallbuy,
            "b>",
            strikeputbuy,
            zeroputbuy,
            "b<",
            strikecallsell,
            zerocallsell,
            "r>",
            strikeputsell,
            zeroputsell,
            "r<",
            markersize=10,
        )
    elif st.profit_target is not None:
        plt.plot(
            st.s,
            zeroline,
            "m--",
            st.s,
            targetline,
            "b--",
            st.s,
            st.strategyprofit,
            "k-",
            strikecallbuy,
            zerocallbuy,
            "b>",
            strikeputbuy,
            zeroputbuy,
            "b<",
            strikecallsell,
            zerocallsell,
            "r>",
            strikeputsell,
            zeroputsell,
            "r<",
            markersize=10,
        )
    else:
        plt.plot(
            st.s,
            zeroline,
            "m--",
            st.s,
            st.strategyprofit,
            "k-",
            strikecallbuy,
            zerocallbuy,
            "b>",
            strikeputbuy,
            zeroputbuy,
            "b<",
            strikecallsell,
            zerocallsell,
            "r>",
            strikeputsell,
            zeroputsell,
            "r<",
            markersize=10,
        )
