import streamlit as st
from stock_helper import render_market_dashboard

st.set_page_config(page_title="加拿大股市技術分析", page_icon="🇨🇦", layout="wide")

render_market_dashboard(
    market_title="🇨🇦 加拿大股市 (TSX) 技術分析與股息儀表板",
    default_sym="TD",
    hint_text="例如：TD, RY, ENB, ZEB, VFV（無需輸入 .TO，系統自動補上）",
    market_type="CA"
)
