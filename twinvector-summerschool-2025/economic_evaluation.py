import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def economic_kpis(df: pd.DataFrame,
                  discount_rate: float,
                  cash_col: str = "total_cashflow",
                  cost_col: str = "total_costs",
                  profit_col: str = "total_profits"
                  ) -> dict:
    """
    Calculate key economic KPIs from a time-series DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain at least the columns for cashflow, total_costs, total_profits.
        Index or a column should represent year 0..N (year-end).
    discount_rate : float
        Annual discount rate as a decimal (e.g. 0.08 for 8%).
    cash_col, cost_col, profit_col : str
        Column names for cash flow, total costs, and total profits.

    Returns
    -------
    dict
        {
          'NPV': float,
          'dynamic_amortisation_time': float,
          'ROI': float
        }
    """
    # Ensure numeric and correct ordering
    df = df.copy().reset_index(drop=True)
    years = np.arange(len(df))

    # --- NPV ---
    cashflows = df[cash_col].astype(float).values
    npv = np.sum(cashflows / (1 + discount_rate) ** years)

    # --- Dynamic Amortisation Time ---
    discounted_cum = np.cumsum(cashflows / (1 + discount_rate) ** years)
    if np.any(discounted_cum >= 0):
        # Find the first year where cumulative discounted cash flow turns positive
        year_positive = np.argmax(discounted_cum >= 0)
        if year_positive == 0:
            dynamic_amort = 0.0
        else:
            # Linear interpolation between the previous year and this year
            prev_val = discounted_cum[year_positive - 1]
            this_val = discounted_cum[year_positive]
            frac = -prev_val / (this_val - prev_val)
            dynamic_amort = (year_positive - 1) + frac
    else:
        dynamic_amort = np.nan  # never amortises within horizon

    # --- ROI ---
    total_profit = df[profit_col].sum()
    total_costs = df[cost_col].abs().sum()
    roi = (total_profit - total_costs) / total_costs if total_costs != 0 else np.nan

    return {
        "NPV": npv,
        "dynamic_amortisation_time": round(dynamic_amort),
        "ROI": roi
    }


def evaluate_profitability(power: float, cap_hrs: float, path: str = 'opt/out'):
    config = f'p_{power}_h_{cap_hrs}'

    ### Read input data containing day-ahead prices
    df_inputs = pd.read_csv('opt/data/timeseries/default.csv')

    ### Read optimization result
    df_res = pd.read_csv(f'{path}/{config}/elec_buy_sell.csv')
    df_res.head()

    df_yearly_profits = df_inputs.loc[df_inputs.index[0]:df_inputs.index[8759], :].copy()

    df_yearly_profits['residual_load'] = df_yearly_profits['generation_solar'] - df_yearly_profits['demand']
    df_yearly_profits['baseline_cons'] = df_yearly_profits['residual_load'].where(
        df_yearly_profits['residual_load'] < 0., 0.).abs()
    df_yearly_profits['baseline_feedin'] = df_yearly_profits['residual_load'].where(
        df_yearly_profits['residual_load'] > 0., 0.)
    df_yearly_profits['baseline_buy'] = df_yearly_profits['baseline_cons'] * (df_yearly_profits['dayahead_price'] + 10)
    df_yearly_profits['baseline_sell'] = df_yearly_profits['baseline_feedin'] * (df_yearly_profits['dayahead_price'] - 5)

    df_yearly_profits['electricity_profits_sell'] = (df_yearly_profits['dayahead_price'] - 5) * df_res['value_sell'].values
    df_yearly_profits['electricity_costs_buy'] = (df_yearly_profits['dayahead_price'] + 10) * df_res['value_buy'].values

    df_cashflows = pd.DataFrame(index=pd.date_range(start='2024-01-01 00:00', freq='1Y', periods=13),
                                columns=['capex_bess', 'opex_bess', 'electricity_profits_sell',
                                         'electricity_costs_buy', 'avoided_costs_baseline'])

    df_cashflows.loc[df_cashflows.index[0], 'capex_bess'] = -250000 * power * cap_hrs
    df_cashflows.loc[df_cashflows.index[1]:df_cashflows.index[-1], 'capex_bess'] = 0.
    df_cashflows.loc[df_cashflows.index[0], 'opex_bess'] = 0.
    df_cashflows.loc[df_cashflows.index[1]:df_cashflows.index[-1], 'opex_bess'] = -0.015 * 250000 * power * cap_hrs
    df_cashflows['electricity_profits_sell'] = df_yearly_profits['electricity_profits_sell'].sum()
    df_cashflows['electricity_costs_buy'] = - df_yearly_profits['electricity_costs_buy'].sum()
    df_cashflows['avoided_costs_baseline'] = df_yearly_profits['baseline_buy'].sum() - \
        df_yearly_profits['baseline_sell'].sum()

    df_cashflows['total_costs'] = df_cashflows['capex_bess'] + df_cashflows['opex_bess'] + \
        df_cashflows['electricity_costs_buy']
    df_cashflows['total_profits'] = df_cashflows['electricity_profits_sell'] + df_cashflows['avoided_costs_baseline']
    df_cashflows['total_cashflow'] = df_cashflows['total_costs'] + df_cashflows['total_profits']
    df_cashflows['cumulative_cashflow'] = df_cashflows['total_cashflow'].cumsum()

    return df_cashflows


def kpi_heatmap(df: pd.DataFrame,
                kpi: str,
                cmap: str = "YlGnBu",
                decimals: int = 2,
                figsize: tuple = (8, 5)) -> None:
    """
    Create a heatmap of a chosen KPI across power vs. capacity_hrs.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: 'power', 'capacity_hrs', and the KPI of interest.
    kpi : str
        One of 'NPV', 'ROI', or 'dynamic_amortisation_time'.
    """
    if kpi not in df.columns:
        raise ValueError(f"'{kpi}' column not found in DataFrame.")

    # Force numeric types for the KPI, power, and capacity columns
    df = df.copy()
    for col in ["power", "capacity_hrs", kpi]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop any rows with NaNs after conversion
    df = df.dropna(subset=["power", "capacity_hrs", kpi])

    # Pivot to matrix form
    pivot = df.pivot(index="capacity_hrs", columns="power", values=kpi)
    pivot = pivot.sort_index(axis=0).sort_index(axis=1)

    plt.figure(figsize=figsize)
    sns.heatmap(
        pivot,
        annot=True,
        fmt=f".{decimals}f",
        cmap=cmap,
        cbar_kws={"label": kpi}
    )
    plt.title(f"{kpi} Heatmap")
    plt.xlabel("Power (MW)")
    plt.ylabel("Capacity (h)")
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    powers = [2.5, 5.0, 7.5]
    capacities_hrs = [2.0, 4.0]

    economic_results = pd.DataFrame(index=np.arange(0, int(len(powers) * len(capacities_hrs))),
                                    columns=['power', 'capacity_hrs', 'NPV (€)', 'dynamic_amortisation_time (a)', 'ROI'])

    i = -1
    for p in powers:
        for cap_hrs in capacities_hrs:
            i += 1
            df_cashflows = evaluate_profitability(power=p, cap_hrs=cap_hrs)
            economic_kpis_res = economic_kpis(df_cashflows, discount_rate=0.06)
            economic_results.loc[i, 'power'] = p
            economic_results.loc[i, 'capacity_hrs'] = cap_hrs
            economic_results.loc[i, 'NPV (€)'] = economic_kpis_res['NPV']
            economic_results.loc[i, 'dynamic_amortisation_time (a)'] = economic_kpis_res['dynamic_amortisation_time']
            economic_results.loc[i, 'ROI'] = economic_kpis_res['ROI']

    # Plot NPV heatmap
    kpi_heatmap(economic_results, kpi="NPV (€)", cmap="coolwarm", decimals=0)

    # Plot ROI heatmap
    kpi_heatmap(economic_results, kpi="ROI", cmap="YlOrRd", decimals=2)

    # Plot dynamic amortisation time heatmap
    kpi_heatmap(economic_results, kpi="dynamic_amortisation_time (a)", cmap="viridis", decimals=1)

    economic_results.to_csv('opt/out/economic_results.csv')
