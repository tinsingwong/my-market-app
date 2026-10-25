import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="全球市場行情儀表板", layout="centered", page_icon="📈")

# 自訂 CSS：縮小 st.metric 數值字體大小，保持畫面整齊
st.markdown("""
<style>
div[data-testid="stMetricValue"] > div {
    font-size: 1.35rem !important;
    font-weight: 600;
}
div[data-testid="stMetricLabel"] > div {
    font-size: 0.9rem !important;
}
div[data-testid="stMetricDelta"] > div {
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 全球市場行情與技術分析")

# 頂部更新控制列
col_btn, col_interval, col_status = st.columns([1, 1.3, 2])

with col_btn:
    if st.button("🔄 手動刷新"):
        st.rerun()

with col_interval:
    refresh_option = st.selectbox(
        "自動刷新頻率：",
        ["關閉", "30 秒", "1 分鐘", "5 分鐘"],
        index=1,
        label_visibility="collapsed"
    )

if refresh_option == "30 秒":
    st_autorefresh(interval=30 * 1000, key="auto_refresh_timer")
elif refresh_option == "1 分鐘":
    st_autorefresh(interval=60 * 1000, key="auto_refresh_timer")
elif refresh_option == "5 分鐘":
    st_autorefresh(interval=300 * 1000, key="auto_refresh_timer")

with col_status:
    st.caption(f"最後更新：`{datetime.now().strftime('%H:%M:%S')}`")

# 建立 5 個獨立分頁
tab_fx, tab_hk, tab_ca, tab_us, tab_tech = st.tabs([
    "💱 外匯匯率", 
    "🇭🇰 香港股市", 
    "🇨🇦 加拿大股市", 
    "🇺🇸 美國股市",
    "🔍 技術分析 (RSI/通道)"
])

PERIOD_MAP = {"1個月": "1mo", "6個月": "6mo", "1年": "1y", "5年": "5y"}

# 常見港股與熱門股票中文對照表 (可隨時擴充)
CHINESE_NAME_MAP = {
    # 港股指數與藍籌
    "^HSI": "恒生指數",
    "0001.HK": "長和",
    "0002.HK": "中電控股",
    "0003.HK": "香港中華煤氣",
    "0005.HK": "滙豐控股",
    "0006.HK": "電能實業",
    "0011.HK": "恒生銀行",
    "0012.HK": "恒基地產",
    "0016.HK": "新鴻基地產",
    "0017.HK": "新世界發展",
    "0027.HK": "銀河娛樂",
    "0066.HK": "港鐵公司",
    "0175.HK": "吉利汽車",
    "0267.HK": "中信股份",
    "0288.HK": "萬洲國際",
    "0386.HK": "中國石油化工",
    "0388.HK": "香港交易所",
    "0700.HK": "騰訊控股",
    "0823.HK": "領展房產基金",
    "0857.HK": "中國石油股份",
    "0883.HK": "中國海洋石油",
    "0939.HK": "建設銀行",
    "0941.HK": "中國移動",
    "0968.HK": "信義光能",
    "0981.HK": "中芯國際",
    "0992.HK": "聯想集團",
    "1024.HK": "快手",
    "1088.HK": "中國神華",
    "1093.HK": "石藥集團",
    "1109.HK": "華潤置地",
    "1113.HK": "長實集團",
    "1177.HK": "中生製藥",
    "1211.HK": "比亞迪股份",
    "1299.HK": "友邦保險",
    "1398.HK": "工商銀行",
    "1810.HK": "小米集團",
    "1928.HK": "金沙中國",
    "2015.HK": "理想汽車",
    "2020.HK": "安踏體育",
    "2269.HK": "藥明生物",
    "2318.HK": "中國平安",
    "2319.HK": "蒙牛乳業",
    "2328.HK": "中國財險",
    "2382.HK": "舜宇光學科技",
    "2388.HK": "中銀香港",
    "2800.HK": "盈富基金",
    "3690.HK": "美團",
    "3968.HK": "招商銀行",
    "3988.HK": "中國銀行",
    "9618.HK": "京東集團",
    "9866.HK": "蔚來",
    "9868.HK": "小鵬汽車",
    "9888.HK": "百度集團",
    "9961.HK": "攜程集團",
    "9988.HK": "阿里巴巴",
    "9999.HK": "網易",
    # 常用美股 / 加股
    "AAPL": "蘋果公司",
    "MSFT": "微軟公司",
    "NVDA": "輝達 / 英偉達",
    "GOOGL": "谷歌 Alphabet",
    "AMZN": "亞馬遜",
    "TSLA": "特斯拉",
    "RY.TO": "加拿大皇家銀行",
    "TD.TO": "道明銀行",
    "BNS.TO": "豐業銀行",
    "ENB.TO": "安橋能源",
}

def render_simple_chart(ticker_symbol: str, label_name: str, period_key: str, line_color: str = "#29b5e8"):
    try:
        t = yf.Ticker(ticker_symbol)
        price = t.fast_info.last_price
        prev = t.fast_info.previous_close
        curr = t.fast_info.currency or ""
        delta_val = price - prev
        delta_pct = (delta_val / prev) * 100

        if "=X" in ticker_symbol:
            delta_str = f"{delta_val:+.4f} ({delta_pct:+.2f}%)"
            val_str = f"{price:.4f} {curr}"
        else:
            delta_str = f"{delta_val:+.2f} ({delta_pct:+.2f}%)"
            val_str = f"{price:.2f} {curr}"

        st.metric(
            label=f"{label_name} 最新報價",
            value=val_str,
            delta=delta_str
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
                height=300,
                xaxis_title="日期",
                yaxis_title=f"價格 ({curr})"
            )
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"取得報價失敗：{e}")

# ==========================================
# 分頁 1：外匯
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
            d_val = p - prev_p
            d_pct = (d_val / prev_p) * 100
            col.metric(label=name, value=f"{p:.4f}", delta=f"{d_val:+.4f} ({d_pct:+.2f}%)")
        except Exception:
            col.metric(label=name, value="--")

    st.markdown("---")
    selected_fx = st.selectbox("選擇匯率：", list(FX_WATCHLIST.keys()), key="fx_select")
    fx_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="fx_range")
    render_simple_chart(FX_WATCHLIST[selected_fx], selected_fx, fx_range, line_color="#00BA38")

# ==========================================
# 分頁 2：港股
# ==========================================
with tab_hk:
    st.caption("香港恆生指數及藍籌股（代號後綴為 .HK）")
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
    selected_hk = st.selectbox("選擇港股：", list(HK_WATCHLIST.keys()), key="hk_select")
    hk_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="hk_range")
    render_simple_chart(HK_WATCHLIST[selected_hk], selected_hk, hk_range, line_color="#FF6161")

# ==========================================
# 分頁 3：加股
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
    selected_ca = st.selectbox("選擇加股：", list(CA_WATCHLIST.keys()), key="ca_select")
    ca_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="ca_range")
    render_simple_chart(CA_WATCHLIST[selected_ca], selected_ca, ca_range, line_color="#F8766D")

# ==========================================
# 分頁 4：美股
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
    selected_us = st.selectbox("選擇美股：", list(US_WATCHLIST.keys()), key="us_select")
    us_range = st.radio("時間週期：", list(PERIOD_MAP.keys()), horizontal=True, key="us_range")
    render_simple_chart(US_WATCHLIST[selected_us], selected_us, us_range, line_color="#619CFF")

# ==========================================
# 分頁 5：獨立技術分析 (支援港股中文名 + 英文全名)
# ==========================================
with tab_tech:
    st.caption("輸入任意股票代號，自動繪製 14 天 RSI 與保力加通道 (Bollinger Bands)")

    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        raw_input = st.text_input(
            "輸入股票代號：",
            value="0700.HK",
            placeholder="美股直接輸入(如 NVDA, AAPL)；港股直接輸號碼(如 700 或 0700.HK)；加股加 .TO",
            key="tech_search_input"
        ).strip().upper()

    with search_col2:
        search_range = st.selectbox(
            "查看週期：",
            ["6個月", "1年", "2年"],
            index=0,
            key="tech_range_select"
        )

    PERIOD_SEARCH_MAP = {"6個月": "6mo", "1年": "1y", "2年": "2y"}

    # 自動智能格式化港股代號 (若使用者只輸入 700 或 0700，自動轉換為 0700.HK)
    search_symbol = raw_input
    if raw_input.isdigit():
        search_symbol = f"{int(raw_input):04d}.HK"

    if search_symbol:
        try:
            stock = yf.Ticker(search_symbol)
            hist = stock.history(period=PERIOD_SEARCH_MAP[search_range])

            if hist.empty:
                st.warning(f"查無標的 `{search_symbol}`，請確認代號格式是否正確。")
            else:
                # 取得英文全名
                eng_name = search_symbol
                try:
                    info_dict = stock.info
                    eng_name = info_dict.get("longName") or info_dict.get("shortName") or search_symbol
                except Exception:
                    eng_name = search_symbol

                # 匹配中文名
                chinese_name = CHINESE_NAME_MAP.get(search_symbol, "")

                # 組合顯示標題
                if chinese_name:
                    display_title = f"{chinese_name} {eng_name} ({search_symbol})"
                else:
                    display_title = f"{eng_name} ({search_symbol})"

                st.subheader(f"🏢 {display_title}")

                # 1. 保力加通道 (20MA, 2倍標準差)
                hist["MA20"] = hist["Close"].rolling(window=20).mean()
                hist["STD20"] = hist["Close"].rolling(window=20).std()
                hist["BB_Upper"] = hist["MA20"] + (hist["STD20"] * 2)
                hist["BB_Lower"] = hist["MA20"] - (hist["STD20"] * 2)

                # 2. 14天 RSI (Wilder 平滑)
                delta = hist["Close"].diff()
                gain = delta.clip(lower=0)
                loss = -1 * delta.clip(upper=0)
                avg_gain = gain.ewm(com=13, adjust=False).mean()
                avg_loss = loss.ewm(com=13, adjust=False).mean()
                rs = avg_gain / avg_loss
                hist["RSI14"] = 100 - (100 / (1 + rs))

                last_row = hist.iloc[-1]
                prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else last_row["Close"]
                
                price = last_row["Close"]
                volume = int(last_row["Volume"])
                rsi = last_row["RSI14"]
                bb_mid = last_row["MA20"]
                curr = stock.fast_info.currency or ""
                
                delta_val = price - prev_close
                delta_pct = (delta_val / prev_close) * 100
                delta_display = f"{delta_val:+.2f} ({delta_pct:+.2f}%)"

                # 頂部四格指標卡片
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("當前最新價", f"{price:.2f} {curr}", delta_display)
                c2.metric("最新成交量", f"{volume:,.0f}")
                rsi_status = " (超買)" if rsi >= 70 else (" (超賣)" if rsi <= 30 else " (中性)")
                c3.metric("14天 RSI", f"{rsi:.1f}{rsi_status}")
                c4.metric("保力加中軌(20MA)", f"{bb_mid:.2f} {curr}")

                # 繪製雙層技術圖表
                fig = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.08,
                    row_heights=[0.7, 0.3],
                    subplot_titles=(f"{display_title} 價格走勢與保力加通道 (Bollinger Bands)", "14 天相對強弱指標 (RSI)")
                )

                # 保力加通道
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["BB_Upper"],
                    line=dict(color="rgba(150, 150, 150, 0.4)", width=1, dash="dash"),
                    name="BB 上軌 (+2σ)"
                ), row=1, col=1)

                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["BB_Lower"],
                    line=dict(color="rgba(150, 150, 150, 0.4)", width=1, dash="dash"),
                    fill='tonexty',
                    fillcolor='rgba(200, 200, 200, 0.1)',
                    name="BB 通道範圍"
                ), row=1, col=1)

                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["MA20"],
                    line=dict(color="orange", width=1.5),
                    name="20日均線 (中軌)"
                ), row=1, col=1)

                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["Close"],
                    line=dict(color="#29b5e8", width=2),
                    name="收盤價"
                ), row=1, col=1)

                # RSI
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["RSI14"],
                    line=dict(color="#ab63fa", width=2),
                    name="RSI 14"
                ), row=2, col=1)

                fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)

                fig.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    height=520,
                    xaxis2_title="日期",
                    yaxis_title=f"價格 ({curr})",
                    yaxis2_title="RSI (0-100)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                fig.update_yaxes(range=[0, 100], row=2, col=1)

                st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"分析 `{search_symbol}` 時發生錯誤：{e}")
