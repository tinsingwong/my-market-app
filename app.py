import streamlit as st
from stock_helper import render_market_dashboard

st.set_page_config(page_title="美國股市技術分析", page_icon="🇺🇸", layout="wide")

render_market_dashboard(
    market_title="🇺🇸 美國股市 (US) 技術分析與股息儀表板",
    default_sym="NVDA",
    hint_text="例如：NVDA, AAPL, MSFT, SPY, SCHD",
    market_type="US"
)
