import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
currdir = os.path.dirname(os.path.abspath(__file__))
loadprofile_file = os.path.join(currdir, 'synthload2025.xlsx')

# *Faktoren die auf das Jährliche Demand zu multipliezeren 
# sind aber wie gesagt ich weiß nicht ob sie aufs Jahr oder jeweiliger Tag etc normiert sind

df = pd.read_excel(loadprofile_file, sheet_name='Profile', skiprows=1)
df["ts [UTC]"] = pd.to_datetime(df["ts [UTC]"])
#  In Austria, the average household electricity usage is around 4,415 kWh kWh per year,
yearly_demand_household = 4500.0
yearly_demand_industry = 4500.0 * 1000.
yearly_demand = 4500.
print(df.head())

time = df['ts [UTC]']
need_household = df["Haushalt"] 
need_industry = df["Gewerbe allgemein"] 
need_bakery = df["Bäckerei mit Backstube"] 

plt.plot(time[1000:1200], need_household[1000:1200], label="Household")
plt.plot(time[1000:1200], need_industry[1000:1200], label="Industry")
plt.plot(time[1000:1200], need_bakery[1000:1200], label="Bakery")
# Set x ticks (every Nth point or by date format if datetime)
plt.xticks(rotation=45)  # rotate labels for readability

# If your time column is datetime, use locators for better control:
plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
plt.ylabel("Normalized demand")
plt.legend(); plt.tight_layout()
plt.show()