import streamlit as st
import pandas as pd
import plotly.express as px
from config import PROCESSED_DIR

# Page config
st.set_page_config(page_title="FinScope Dashboard", layout="wide")
st.title("📊 FinScope: Financial Analytics Dashboard")
st.markdown("Real-time sector benchmarking and financial metrics for top US public companies.")

@st.cache_data
def load_data():
    df = pd.read_parquet(PROCESSED_DIR / "cleaned_financials.parquet")
    # Calculate margins
    df["Gross_Margin_Pct"] = (df["GrossProfit"] / df["Revenue"]) * 100
    df["Net_Margin_Pct"] = (df["NetIncome"] / df["Revenue"]) * 100
    return df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filters")
selected_sector = st.sidebar.multiselect("Sector", df["Sector"].unique(), default=df["Sector"].unique())
filtered_df = df[df["Sector"].isin(selected_sector)]

latest_date = filtered_df["Date"].max()
latest_df = filtered_df[filtered_df["Date"] == latest_date]

# --- KPI CARDS ---
st.subheader(f"Executive Summary (Latest Quarter: {latest_date.strftime('%b %Y')})")
col1, col2, col3, col4 = st.columns(4)

total_rev = latest_df["Revenue"].sum() / 1e9
avg_gross = latest_df["Gross_Margin_Pct"].mean()
avg_net = latest_df["Net_Margin_Pct"].mean()
total_profit = latest_df["NetIncome"].sum() / 1e9

col1.metric("Total Revenue", f" B")
col2.metric("Avg Gross Margin", f"{avg_gross:.1f}%")
col3.metric("Avg Net Margin", f"{avg_net:.1f}%")
col4.metric("Total Net Income", f" B")

st.divider()

# --- CHARTS ---
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Revenue by Company (Latest Quarter)")
    fig_bar = px.bar(
        latest_df.sort_values("Revenue", ascending=False).head(10), 
        x="Ticker", y="Revenue", color="Sector",
        text_auto='.2s', color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_bar.update_layout(yaxis_title="Revenue (USD)", xaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown("### Net Margin vs Gross Margin")
    fig_scatter = px.scatter(
        latest_df, x="Gross_Margin_Pct", y="Net_Margin_Pct", 
        color="Sector", hover_name="Ticker", size="Revenue",
        labels={"Gross_Margin_Pct": "Gross Margin (%)", "Net_Margin_Pct": "Net Margin (%)"}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# --- TREND LINE ---
st.markdown("### Revenue Trend Over Time (Top 5 Companies)")
top_5 = latest_df.nlargest(5, "Revenue")["Ticker"].tolist()
trend_df = filtered_df[filtered_df["Ticker"].isin(top_5)]

fig_line = px.line(
    trend_df, x="Date", y="Revenue", color="Ticker", 
    markers=True, labels={"Revenue": "Revenue (USD)", "Date": "Quarter End Date"}
)
st.plotly_chart(fig_line, use_container_width=True)
