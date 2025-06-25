import iesopt


# Run the model, including some "top-level" settings.
# This example uses the day-ahead price with a markup of +10.0 EUR/MWh for buying, and allows selling at the day-ahead
# price, with a markup of +5.0 EUR/MWh.

model = iesopt.run(
    "opt/config.iesopt.yaml",
    parameters=dict(
        price_electricity_buy="10.0 + dayahead_price@data",
        price_electricity_sell="5.0 - dayahead_price@data",
    ),
)

# Other alternative parameters could, e.g., be:
#
# 1. `dict(price_electricity_buy = "dayahead_price@data", price_electricity_sell = 10.0)`
#    which models buying at the day-ahead price and selling (feed-in) at a fixed price of 10.0 EUR/MWh.
# 2. `dict(..., price_hydrogen_buy = 150.0)`
#    which models buying hydrogen at a fixed price of 150.0 EUR/MWh.
#
# and so on.

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# EXPERIMENTAL :: Plotting supply and generation (electricity).                                                        #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

from iesopttools import RDB, Figure, Trace

rdb = RDB()
entry = rdb.add_entry(model)

fig = Figure(style="seaborn", barmode="relative", labels=dict(title="electricity: supply / demand", x="time", y="MW"))

for asset in entry.query("carrier", "node = 'grid_electricity' AND direction = 'out'"):
    fig.add(Trace("bar", entry.select(asset)))

for asset in entry.query("carrier", "node = 'grid_electricity' AND direction = 'in'"):
    fig.add(Trace("bar", entry.select(asset), sign=-1.0))

fig.show(xslice=(0, 168))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# EXPERIMENTAL :: Converting the model to a draw.io (diagrams.net) sketch                                              #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

from iesopttools.diagrams import drawio

# NOTE: Open the resulting file either in the web/desktop app, or use the "Draw.io Integration" extension in VSCode!
drawio.write_entry(entry, filename="opt/out/sketch.drawio")
