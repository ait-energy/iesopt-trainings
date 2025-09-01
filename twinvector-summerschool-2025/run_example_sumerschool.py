import iesopt


# Other alternative parameters could, e.g., be:
#
# 1. `dict(price_electricity_buy = "dayahead_price@data", price_electricity_sell = 10.0)`
#    which models buying at the day-ahead price and selling (feed-in) at a fixed price of 10.0 EUR/MWh.
# 2. `dict(..., price_hydrogen_buy = 150.0)`
#    which models buying hydrogen at a fixed price of 150.0 EUR/MWh,  and so on.
model = iesopt.run(
    "opt/config_summerschool2025.iesopt.yaml",
    parameters=dict(
        # price_electricity_buy = "dayahead_price@data", price_electricity_sell = 10.0 # would model buying at the day-ahead price and selling (feed-in) at a fixed price of 10.0 EUR/MWh.
    ),
)

# objective:  Zielfunktion, also sind alle Ergebnisse mit "objective", Werte, die direkt in die Zielfunktion einzahlen, bspw. objective cost
# variable sind Werte der Entscheidungsvariablen
# expressions sind Ergebnisse aus zusammengesetzten Teilen, bspw. exp = input1 + input2 - output1
# _primal gibt die tatsächliche "Menge" der Variable zu diesem Zeitpunkt an, also bspw. storage charging exp in primal gibt die Menge an Strom an die in diesem snapshot im speicher eingespeichert wird
df_results = model.results.to_pandas()

# list components
print( df_results["component"].unique() )

# electricity buy / sell
elec_buy = df_results.query("component == 'buy_electricity' and field == 'value'")
elec_sold = df_results.query("component == 'sell_electricity' and field == 'value'")
combo = elec_buy.merge(elec_sold, how="inner", on="snapshot", suffixes=("_buy", "_sell"))
combo.to_csv("opt/out/elec_buy_sold.csv")

# pv
pv = df_results.query("component == 'pv' and field == 'value'")
# load
load = df_results.query("component == 'load' and field == 'value'") 
combo=pv.merge(load, how="inner", on="snapshot", suffixes=("_pv", "_load"))
combo.to_csv("opt/out/pv_load.csv")

# battery
batt_charge = df_results.query(
    "component.str.endswith('.charging') and fieldtype == 'exp' and field =='in_electricity'",
    engine="python"
)
batt_discharge = df_results.query(
    "component.str.endswith('.discharging') and fieldtype == 'exp' and field =='in_electricity'",
    engine="python"
)
combo =batt_charge.merge(batt_discharge, how="inner", on="snapshot", suffixes=("_charge", "_discharge"))
combo.to_csv("opt/out/batt_charge_discharge.csv")



from iesopttools import RDB, Figure, Trace
import plotly.io as pio
pio.renderers.default = "browser"
rdb = RDB()
entry = rdb.add_entry(model)

fig = Figure(style="seaborn", barmode="relative", labels=dict(title="electricity: supply / demand", x="time", y="MW"))

for asset in entry.query("carrier", "node = 'grid_electricity' AND direction = 'out'"):
    fig.add(Trace("bar", entry.select(asset)))

for asset in entry.query("carrier", "node = 'grid_electricity' AND direction = 'in'"):
    fig.add(Trace("bar", entry.select(asset), sign=-1.0))

fig.show( )
fig._fig.write_html("opt/out/plot_summerschool.html")


from iesopttools.diagrams import drawio

# NOTE: Open the resulting file either in the web/desktop app, or use the "Draw.io Integration" extension in VSCode!
drawio.write_entry(entry, filename="opt/out/sketch.drawio")