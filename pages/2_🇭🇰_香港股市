import streamlit as st
from stock_helper import render_market_dashboard

st.set_page_config(page_title="香港股市技術分析", page_icon="🇭🇰", layout="wide")

render_market_dashboard(
    market_title="🇭🇰 香港股市 (HKEX) 技術分析與股息儀表板",
    default_sym="0700",
    hint_text="例如：0700, 0005, 0941, 2800（無需輸入 .HK，自動補齊 4 位數）",
    market_type="HK"
)
