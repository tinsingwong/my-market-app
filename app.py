import streamlit as st
from stock_helper import render_market_dashboard

st.set_page_config(page_title="美國股市技術分析", page_icon="🇺🇸", layout="wide")

def us_market_page():
    render_market_dashboard(
        market_title="🇺🇸 美國股市 (US) 技術分析與股息儀表板",
        default_sym="NVDA",
        hint_text="例如：NVDA, AAPL, MSFT, SPY, SCHD",
        market_type="US"
    )

# 自訂左側導覽選單，將原本的 "app" 改名為 "美國股市 (US)"
pages = [
    st.Page(us_market_page, title="美國股市 (US)", icon="🇺🇸", default=True),
    st.Page("pages/1_🇨🇦_加拿大股市.py", title="加拿大股市 (CA)", icon="🇨🇦"),
    st.Page("pages/2_🇭🇰_香港股市.py", title="香港股市 (HK)", icon="🇭🇰"),
    st.Page("pages/3_💱_外匯與即時換算.py", title="外匯與即時換算", icon="💱"),
    st.Page("pages/4_🛡️_期權對沖計算機.py", title="期權對沖計算機", icon="🛡️"),
    st.Page("pages/5_📊_自選股總覽看板.py", title="自選股總覽看板", icon="📊"),
]

pg = st.navigation(pages)
pg.run()
