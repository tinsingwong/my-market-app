import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="全球市場行情儀表板", layout="centered", page_icon="📈")

st.title("📈 全球市場行情儀表板")

# 頂部更新狀態列
col_btn, col_time = st.columns([1, 2])
with col_btn:
    if st.button("🔄 刷新最新報價"):
        st.rerun()
with col_time:
    st.caption(f"最後更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 關鍵：建立四個獨立分頁標籤
tab_fx, tab_hk, tab_ca, tab_us = st.tabs([
    "💱 外匯匯率", 
    "🇭🇰 香港股市", 
    "🇨🇦 加拿大股市", 
    "🇺🇸 美國股市"
])

PERIOD_MAP = {"1個月": "1mo", "6個月": "6mo", "1年": "1y", "5年": "5y"}

def render_chart(ticker_symbol: str, label_name: str, period_key: str, line_color: str = "#29b5e8"):
    try:
        t = yf.Ticker(ticker_symbol)
        price = t.fast_info.last_price
        prev = t.fast_info.previous_close
        curr = t.fast_info.currency or ""
        delta_pct = ((price - prev) / prev) * 100

        st.metric(
            label=f"{label_name} 最新報價",
            value=f"{price:.4f} {curr}" if "=X" in ticker_symbol else f"{price:.2f} {curr}",
            delta=f"{delta_pct:+.2f}%"
        )

        hist = t.history(period=PERIOD_MAP[period_key])
        if not hist.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, 
                y=hist["Close"], 
                mode="lines",
                name="收盤價",
                line=dict(color=line_color, width=2)
            ))
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                height=320,
                xaxis_title="日期",
                yaxis_title=f"價格 ({curr})"
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"取得報價失敗：{e}")

# ==========================================
# 分頁 1：外匯匯率（已擴充更多幣別）
# ==========================================
with tab_fx:
    st.caption("全球即時匯率換算與歷史走勢")

    FX_WATCHLIST = {
        "加幣 / 港幣 (CAD/HKD)": "CADHKD=X",
        "美元 / 加幣 (USD/CAD)": "USDCAD=X",
        "美元 / 港幣 (USD/HKD)": "USDHKD=X",
        "英鎊 / 加幣 (GBP/CAD)": "GBPCAD=X",
        "英鎊 / 美元 (GBP/USD)": "GBPUSD=X",
        "歐元 / 加幣 (EUR/CAD)": "EURCAD=X",
        "歐元 / 美元 (EUR/USD)": "EURUSD=X",
        "日圓 / 港幣 (JPY/HKD)": "JPYHKD=X",
        "澳幣 / 加幣 (AUD/CAD)": "AUDCAD=X",
        "美元 / 人民幣 (USD/CNH)": "USDCNH=X",
    }

    col1, col2, col3, col4 = st.columns(4)
    quick_fx = [
        ("加幣/港幣", "CADHKD=X", col1),
        ("美元/加幣", "USDCAD=X", col2),
        ("美元/港幣", "USDHKD=X", col3),
        ("日圓/港幣", "JPYHKD=X", col4),
    ]
    for name, sym, col in quick_fx:
        try:
            p = yf.Ticker(sym).fast_info.last_price
            prev_p = yf.Ticker(sym).fast_info.previous_close
            d_pct = ((p - prev_p) / prev_p) * 100
            col.metric(label=name, value=f"{p:.4f}", delta=f"{d_pct:+.2f}%")
        except Exception:
            col.metric(label=name, value="--")

    st.markdown("---")
    selected_fx = st.selectbox("選擇要查看走勢的匯率：", list(FX_WATCHLIST.keys()), key="fx_select")
    fx_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="fx_range")
    render_chart(FX_WATCHLIST[selected_fx], selected_fx, fx_range, line_color="#00BA38")

# ==========================================
# 分頁 2：香港股市 (HKEX)
# ==========================================
with tab_hk:
    st.caption("香港恆生指數及港股藍籌（代號後綴為 .HK）")

    HK_WATCHLIST = {
        "恆生指數 (^HSI)": "^HSI",
        "騰訊控股 (0700.HK)": "0700.HK",
        "匯豐控股 (0005.HK)": "0005.HK",
        "阿里巴巴 (9988.HK)": "9988.HK",
        "美團 (3690.HK)": "3690.HK",
        "比亞迪股份 (1211.HK)": "1211.HK",
        "港交所 (0388.HK)": "0388.HK",
        "領展房產基金 (0823.HK)": "0823.HK",
    }

    selected_hk = st.selectbox("選擇港股標的：", list(HK_WATCHLIST.keys()), key="hk_select")
    hk_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="hk_range")
    render_chart(HK_WATCHLIST[selected_hk], selected_hk, hk_range, line_color="#FF6161")

# ==========================================
# 分頁 3：加拿大股市 (TSX)
# ==========================================
with tab_ca:
    st.caption("加拿大多倫多證券交易所股票及 ETF（代號後綴為 .TO）")

    CA_WATCHLIST = {
        "標普/多倫多綜合指數 (^GSPTSE)": "^GSPTSE",
        "加拿大皇家銀行 (RY.TO)": "RY.TO",
        "道明銀行 (TD.TO)": "TD.TO",
        "加拿大豐業銀行 (BNS.TO)": "BNS.TO",
        "安橋能源 (ENB.TO)": "ENB.TO",
        "加拿大鵝 (GOOS.TO)": "GOOS.TO",
        "加拿大國家鐵路 (CNR.TO)": "CNR.TO",
        "iShares 標普多倫多60 ETF (XIU.TO)": "XIU.TO",
    }

    selected_ca = st.selectbox("選擇加股標的：", list(CA_WATCHLIST.keys()), key="ca_select")
    ca_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="ca_range")
    render_chart(CA_WATCHLIST[selected_ca], selected_ca, ca_range, line_color="#F8766D")

# ==========================================
# 分頁 4：美國股市 (NYSE / NASDAQ)
# ==========================================
with tab_us:
    st.caption("美國大盤指數 ETF 與熱門個股")

    US_WATCHLIST = {
        "標普 500 ETF (SPY)": "SPY",
        "納斯達克 100 ETF (QQQ)": "QQQ",
        "道瓊斯工業 ETF (DIA)": "DIA",
        "蘋果 (AAPL)": "AAPL",
        "微軟 (MSFT)": "MSFT",
        "英偉達 (NVDA)": "NVDA",
        "谷歌 (GOOGL)": "GOOGL",
        "亞馬遜 (AMZN)": "AMZN",
        "波克夏海瑟威 B (BRK-B)": "BRK-B",
    }

    selected_us = st.selectbox("選擇美股標的：", list(US_WATCHLIST.keys()), key="us_select")
    us_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="us_range")
    render_chart(US_WATCHLIST[selected_us], selected_us, us_range, line_color="#619CFF")
