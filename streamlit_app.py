import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import snowflake.connector
from datetime import datetime

st.set_page_config(page_title="Yahoo Finance ELT Dashboard", page_icon="📈", layout="wide")

@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account="sh90880.us-east-2.aws",
        user="dbt_prod_user",
        password=st.secrets["SNOWFLAKE_PASSWORD"],
        role="TRANSFORMER",
        warehouse="DBT_WH",
        database="STAGING",
        schema="dbt_dev_marts"
    )

@st.cache_data(ttl=3600)
def load_data():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT PRICE_DATE, TICKER, OPEN_PRICE, HIGH_PRICE, LOW_PRICE,
               CLOSE_PRICE, VOLUME, DAILY_RETURN_PCT, CUMULATIVE_RETURN_PCT,
               MA_7, MA_30, MA_90, MOMENTUM_SIGNAL, DAILY_RETURN_CATEGORY
        FROM STAGING.dbt_dev_marts.FCT_STOCK_PRICES
        ORDER BY PRICE_DATE
    """, conn)
    df.columns = [c.lower() for c in df.columns]
    df["price_date"] = pd.to_datetime(df["price_date"])
    return df

@st.cache_data(ttl=3600)
def load_tickers():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM STAGING.dbt_dev_marts.DIM_TICKERS", conn)
    df.columns = [c.lower() for c in df.columns]
    return df

try:
    df = load_data()
    dim = load_tickers()
    data_loaded = True
except Exception as e:
    st.error(f"Could not connect to Snowflake: {e}")
    data_loaded = False

st.title("📈 Yahoo Finance ELT Dashboard")
st.caption("Data pipeline: Yahoo Finance → Snowflake → dbt → Streamlit")

if not data_loaded:
    st.stop()

st.divider()

st.sidebar.header("Filters")
tickers = sorted(df["ticker"].unique().tolist())
selected_tickers = st.sidebar.multiselect("Tickers", options=tickers, default=tickers)
date_range = st.sidebar.date_input(
    "Date range",
    value=[df["price_date"].min(), df["price_date"].max()],
    min_value=df["price_date"].min(),
    max_value=df["price_date"].max()
)
show_ma = st.sidebar.multiselect("Moving averages", options=["MA 7", "MA 30", "MA 90"], default=["MA 30"])

filtered = df[
    (df["ticker"].isin(selected_tickers)) &
    (df["price_date"] >= pd.to_datetime(date_range[0])) &
    (df["price_date"] <= pd.to_datetime(date_range[1]))
]

st.subheader("Current Snapshot")
if selected_tickers:
    cols = st.columns(len(selected_tickers))
    for i, ticker in enumerate(selected_tickers):
        ticker_data = filtered[filtered["ticker"] == ticker]
        if ticker_data.empty:
            continue
        latest = ticker_data.iloc[-1]
        with cols[i]:
            st.metric(
                label=ticker,
                value=f"${latest['close_price']:.2f}",
                delta=f"{latest['daily_return_pct']:.2f}%"
            )
            st.caption(f"Total return: {latest['cumulative_return_pct']:.1f}%")

st.divider()

colors = {"AAPL": "#007AFF", "GOOGL": "#34C759", "MSFT": "#5856D6", "AMZN": "#FF9500", "META": "#FF2D55"}

st.subheader("Stock Prices")
fig = go.Figure()
for ticker in selected_tickers:
    t = filtered[filtered["ticker"] == ticker]
    color = colors.get(ticker, "#888")
    fig.add_trace(go.Scatter(x=t["price_date"], y=t["close_price"], name=ticker, line=dict(color=color, width=2)))
    if "MA 7" in show_ma:
        fig.add_trace(go.Scatter(x=t["price_date"], y=t["ma_7"], name=f"{ticker} MA7", line=dict(color=color, width=1, dash="dot"), showlegend=False))
    if "MA 30" in show_ma:
        fig.add_trace(go.Scatter(x=t["price_date"], y=t["ma_30"], name=f"{ticker} MA30", line=dict(color=color, width=1, dash="dash"), showlegend=False))
    if "MA 90" in show_ma:
        fig.add_trace(go.Scatter(x=t["price_date"], y=t["ma_90"], name=f"{ticker} MA90", line=dict(color=color, width=1, dash="longdash"), showlegend=False))
fig.update_layout(height=450, xaxis_title="Date", yaxis_title="Price (USD)", hovermode="x unified", legend=dict(orientation="h", y=1.02))
st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Cumulative Returns Since 2020")
fig2 = go.Figure()
for ticker in selected_tickers:
    t = filtered[filtered["ticker"] == ticker]
    fig2.add_trace(go.Scatter(x=t["price_date"], y=t["cumulative_return_pct"], name=ticker, line=dict(color=colors.get(ticker, "#888"), width=2)))
fig2.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
fig2.update_layout(height=350, xaxis_title="Date", yaxis_title="Cumulative Return (%)", hovermode="x unified", legend=dict(orientation="h", y=1.02))
st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("Daily Volume")
fig3 = px.bar(filtered, x="price_date", y="volume", color="ticker", color_discrete_map=colors, barmode="group", height=300)
fig3.update_layout(xaxis_title="Date", yaxis_title="Volume", legend=dict(orientation="h", y=1.02))
st.plotly_chart(fig3, use_container_width=True)

st.divider()

st.subheader("Ticker Summary")
display_dim = dim[dim["ticker"].isin(selected_tickers)][[
    "ticker", "company_name", "sector", "latest_close_price",
    "total_return_pct", "all_time_high", "all_time_low",
    "avg_daily_volume", "best_day_return_pct", "worst_day_return_pct"
]].rename(columns={
    "ticker": "Ticker", "company_name": "Company", "sector": "Sector",
    "latest_close_price": "Latest Close", "total_return_pct": "Total Return %",
    "all_time_high": "All Time High", "all_time_low": "All Time Low",
    "avg_daily_volume": "Avg Volume", "best_day_return_pct": "Best Day %",
    "worst_day_return_pct": "Worst Day %"
})
st.dataframe(display_dim, use_container_width=True, hide_index=True)

st.divider()
st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC | Data via Yahoo Finance | Pipeline: Snowflake + dbt + Airflow")
