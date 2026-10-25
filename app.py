import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="全球匯率與股市即時行情", layout="centered", page_icon="📈")

st.title("📈 全球匯率與股市即時行情")

# 頂部更新列
col_btn, col_time = st.columns([1, 2])
with col_btn:
    if st.button("🔄 刷新報價"):
        st.rerun()
with col_time:
    st.caption(f"最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 1. 重點匯率面板 ---
st.subheader("💱 重點匯率")
CURRENCY_LIST = {
    "加幣/港幣 (CAD/HKD)": "CADHKD=X",
    "美元/加幣 (USD/CAD)": "USDCAD=X",
    "美元/港幣 (USD/HKD)": "USDHKD=X",
    "英鎊/美元 (GBP/USD)": "GBPUSD=X",
}

cols = st.columns(len(CURRENCY_LIST))
for idx, (label, sym) in enumerate(CURRENCY_LIST.items()):
    try:
        t = yf.Ticker(sym)
        p = t.fast_info.last_price
        prev = t.fast_info.previous_close
        delta_pct = ((p - prev) / prev) * 100
        with cols[idx]:
            st.metric(label=label.split(" ")[0], value=f"{p:.4f}", delta=f"{delta_pct:+.2f}%")
    except Exception:
        with cols[idx]:
            st.metric(label=label.split(" ")[0], value="--")

st.markdown("---")

# --- 2. 股票與指數行情 ---
st.subheader("📊 自選股票與 ETF 走勢")

WATCHLIST = {
    "標普500 ETF (SPY)": "SPY",
    "納斯達克100 ETF (QQQ)": "QQQ",
    "蘋果 (AAPL)": "AAPL",
    "微軟 (MSFT)": "MSFT",
    "加拿大皇家銀行 (RY.TO)": "RY.TO",
    "道明銀行 (TD.TO)": "TD.TO",
    "騰訊控股 (0700.HK)": "0700.HK",
    "匯豐控股 (0005.HK)": "0005.HK",
}

selected_label = st.selectbox("請選擇查看標的：", list(WATCHLIST.keys()))
selected_sym = WATCHLIST[selected_label]

time_range = st.radio("時間週期：", ["1個月", "6個月", "1年", "5年"], horizontal=True)
range_map = {"1個月": "1mo", "6個月": "6mo", "1年": "1y", "5年": "5y"}

try:
    stock = yf.Ticker(selected_sym)
    info_price = stock.fast_info.last_price
    info_prev = stock.fast_info.previous_close
    curr = stock.fast_info.currency
    delta_pct = ((info_price - info_prev) / info_prev) * 100

    st.metric(
        label=f"{selected_label} 最新價",
        value=f"{info_price:.2f} {curr}",
        delta=f"{delta_pct:+.2f}%"
    )

    hist = stock.history(period=range_map[time_range])
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist.index, 
            y=hist['Close'], 
            mode='lines',
            name='收盤價',
            line=dict(color='#ff4b4b', width=2)
        ))
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            xaxis_title="日期",
            yaxis_title=f"價格 ({curr})"
        )
        st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"行情載入失敗：{e}")
