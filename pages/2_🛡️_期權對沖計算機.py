import streamlit as st
import yfinance as yf
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="期權對沖計算機", page_icon="🛡️", layout="wide")

st.title("🛡️ Zero-Cost Collar 零成本領口期權對沖試算")
st.caption("評估買入保護性看跌期權 (Long Put) 並賣出備兌看漲期權 (Short Call) 的風險與收益區間")

col_top1, col_top2 = st.columns([1.5, 1])
with col_top1:
    ticker = st.text_input("輸入持股代號：", value="AAPL").upper().strip()
with col_top2:
    shares = st.number_input("持有股數 (1張期權 = 100股)：", min_value=100, value=100, step=100)

# 抓取現價作為預設參考
current_price = 200.0
if ticker:
    try:
        info_price = yf.Ticker(ticker).fast_info["lastPrice"]
        if info_price:
            current_price = float(info_price)
    except Exception:
        pass

st.info(f"📌 **{ticker}** 目前參考市價：**${current_price:,.2f}**（總持倉市值：**${current_price * shares:,.2f}**）")

c1, c2, c3 = st.columns(3)
with c1:
    entry_price = st.number_input("持股成本價 ($)：", min_value=0.1, value=round(current_price, 2), step=1.0)
with c2:
    put_strike = st.number_input("買入 Put 行使價 (下檔保護線 $)：", min_value=0.1, value=round(current_price * 0.92, 1), step=1.0)
    put_premium = st.number_input("買入 Put 支付權利金 ($/股)：", min_value=0.0, value=round(current_price * 0.025, 2), step=0.1)
with c3:
    call_strike = st.number_input("賣出 Call 行使價 (上檔封頂線 $)：", min_value=0.1, value=round(current_price * 1.10, 1), step=1.0)
    call_premium = st.number_input("賣出 Call 收取權利金 ($/股)：", min_value=0.0, value=round(current_price * 0.025, 2), step=0.1)

net_premium = (call_premium - put_premium) * shares
max_loss = ((put_strike - entry_price) * shares) + net_premium
max_profit = ((call_strike - entry_price) * shares) + net_premium

m1, m2, m3 = st.columns(3)
m1.metric("淨權利金收支", f"${net_premium:+,.2f}", "零成本/淨收入" if net_premium >= 0 else "淨支出")
m2.metric("最大可能虧損 (下檔封底)", f"${max_loss:+,.2f}")
m3.metric("最大可能獲利 (上檔封頂)", f"${max_profit:+,.2f}")

# 繪製到期損益曲線圖
price_range = np.linspace(entry_price * 0.7, entry_price * 1.3, 100)
unhedged_pnl = (price_range - entry_price) * shares
collar_pnl = []
for p in price_range:
    effective_p = min(max(p, put_strike), call_strike)
    collar_pnl.append((effective_p - entry_price) * shares + net_premium)

fig = go.Figure()
fig.add_trace(go.Scatter(x=price_range, y=unhedged_pnl, mode="lines", name="無對沖純持股損益", line=dict(dash="dash", color="gray")))
fig.add_trace(go.Scatter(x=price_range, y=collar_pnl, mode="lines", name="Collar 領口對沖後損益", line=dict(color="royalblue", width=3)))
fig.add_hline(y=0, line_color="black", line_width=1)
fig.update_layout(title=f"{ticker} 期權到期損益結構對比圖", xaxis_title="到期股價 ($)", yaxis_title="總損益 ($)", height=430)
st.plotly_chart(fig, use_container_width=True)
