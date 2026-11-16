import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import urllib.request
import re

# 常用港股及熱門 ETF 中文名稱對照表
HK_STOCK_NAMES = {
    "0001.HK": "長和",
    "0002.HK": "中電控股",
    "0003.HK": "香港中華煤氣",
    "0005.HK": "匯豐控股",
    "0006.HK": "電能實業",
    "0011.HK": "恒生銀行",
    "0012.HK": "恒基地產",
    "0016.HK": "新鴻基地產",
    "0017.HK": "新世界發展",
    "0027.HK": "銀河娛樂",
    "0066.HK": "港鐵公司",
    "0101.HK": "恒隆地產",
    "0175.HK": "吉利汽車",
    "0241.HK": "阿里健康",
    "0267.HK": "中信股份",
    "0288.HK": "萬洲國際",
    "0291.HK": "華潤啤酒",
    "0386.HK": "中國石油化工股份",
    "0388.HK": "香港交易所",
    "0669.HK": "創科實業",
    "0688.HK": "中國海外發展",
    "0700.HK": "騰訊控股",
    "0762.HK": "中國聯通",
    "0823.HK": "領展房產基金",
    "0857.HK": "中國石油股份",
    "0883.HK": "中國海洋石油",
    "0939.HK": "建設銀行",
    "0941.HK": "中國移動",
    "0960.HK": "龍湖集團",
    "0968.HK": "信義光能",
    "0981.HK": "中芯國際",
    "0992.HK": "聯想集團",
    "1038.HK": "長江基建集團",
    "1044.HK": "恒安國際",
    "1088.HK": "中國神華",
    "1093.HK": "石藥集團",
    "1109.HK": "華潤置地",
    "1113.HK": "長實集團",
    "1177.HK": "中國生物製藥",
    "1211.HK": "比亞迪股份",
    "1299.HK": "友邦保險",
    "1398.HK": "工商銀行",
    "1810.HK": "小米集團－Ｗ",
    "1876.HK": "百威亞太",
    "1928.HK": "金沙中國有限公司",
    "1997.HK": "九龍倉置業",
    "2007.HK": "碧桂園",
    "2015.HK": "理想汽車－Ｗ",
    "2020.HK": "安踏體育",
    "2269.HK": "藥明生物",
    "2313.HK": "申洲國際",
    "2318.HK": "中國平安",
    "2319.HK": "蒙牛乳業",
    "2331.HK": "李寧",
    "2382.HK": "舜宇光學科技",
    "2388.HK": "中銀香港",
    "2628.HK": "中國人壽",
    "2688.HK": "新奧能源",
    "2800.HK": "盈富基金",
    "2828.HK": "恒生中國企業",
    "3033.HK": "南方恒生科技",
    "3067.HK": "安碩恒生科技",
    "3110.HK": "Global X 恒生高股息率",
    "3416.HK": "Global X 國指備兌認購期權主動型ETF",
    "3419.HK": "Global X 恒指備兌認購期權主動型ETF",
    "3690.HK": "美團－Ｗ",
    "3968.HK": "招商銀行",
    "3988.HK": "中國銀行",
    "6098.HK": "碧桂園服務",
    "6618.HK": "京東健康",
    "6690.HK": "海爾智家",
    "6862.HK": "海底撈",
    "9618.HK": "京東集團－ＳＷ",
    "9633.HK": "農夫山泉",
    "9868.HK": "小鵬汽車－Ｗ",
    "9888.HK": "百度集團－ＳＷ",
    "9961.HK": "攜程集團－Ｓ",
    "9988.HK": "阿里巴巴－Ｗ",
    "9999.HK": "網易－Ｓ",
}

@st.cache_data(ttl=86400)
def get_hk_chinese_name(ticker_str: str) -> str:
    if ticker_str in HK_STOCK_NAMES:
        return HK_STOCK_NAMES[ticker_str]
    try:
        code_5 = ticker_str.replace(".HK", "").zfill(5)
        url = f"https://hq.sinajs.cn/list=rt_hk{code_5}"
        req = urllib.request.Request(url, headers={"Referer": "https://finance.sina.com.cn"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            raw = resp.read().decode("gbk", errors="ignore")
            match = re.search(r'="[^,]+,([^,]+),', raw)
            if match and match.group(1).strip():
                return match.group(1).strip()
    except Exception:
        pass
    return ""

# 同時抓取歷史股價、基本資訊與真實派息紀錄 (dividends)
@st.cache_data(ttl=15)
def load_stock_and_info(ticker_str: str, period_str: str):
    tk = yf.Ticker(ticker_str)
    df = tk.history(period=period_str)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # 清除收盤價為 NaN 的無效列，確保最新收盤價永遠有有效數字
    if not df.empty and "Close" in df.columns:
        df = df.dropna(subset=["Close"])

    info = {}
    try:
        info = tk.info or {}
    except Exception:
        info = {}

    divs = pd.Series(dtype=float)
    try:
        divs = tk.dividends
    except Exception:
        divs = pd.Series(dtype=float)

    return df, info, divs

def format_timestamp(ts):
    if not ts:
        return "無資料"
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        return str(ts)[:10]
    except Exception:
        return "無資料"

def render_market_dashboard(market_title: str, default_sym: str, hint_text: str, market_type: str):
    st.title(market_title)

    with st.sidebar:
        raw_symbol = st.text_input("🔍 輸入股票代號：", value=default_sym, help=hint_text, key=f"sym_{market_type}").upper().strip()
        period = st.selectbox("時間範圍：", ["3mo", "6mo", "1y", "2y", "5y"], index=2, key=f"per_{market_type}")
        col_chk1, col_chk2 = st.columns(2)
        with col_chk1:
            show_bb = st.checkbox("布林通道", value=True, key=f"bb_{market_type}")
        with col_chk2:
            show_ma = st.checkbox("MA20/50", value=True, key=f"ma_{market_type}")
        trail_pct = st.slider("移動止損 (%)：", min_value=3.0, max_value=20.0, value=8.0, step=0.5, key=f"trail_{market_type}")

        auto_refresh = st.toggle("⚡ 自動實時更新", value=False, key=f"auto_ref_{market_type}")
        refresh_sec = 30
        if auto_refresh:
            refresh_sec = st.slider("更新頻率 (秒)：", min_value=15, max_value=120, value=30, step=15, key=f"ref_sec_{market_type}")

    # 自動格式化各市場代號與幣別
    symbol = raw_symbol
    currency_sign = "$"
    if raw_symbol:
        if market_type == "CA":
            currency_sign = "CA$"
            if not raw_symbol.endswith(".TO") and not raw_symbol.endswith(".V"):
                symbol = f"{raw_symbol}.TO"
        elif market_type == "HK":
            currency_sign = "HK$"
            clean_hk = raw_symbol.replace(".HK", "")
            if clean_hk.isdigit():
                clean_hk = clean_hk.zfill(4)
            symbol = f"{clean_hk}.HK"

    if not symbol:
        st.info("請在左側輸入股票代號開始分析。")
        return

    with st.spinner(f"正在載入 {symbol} 數據與股息資訊..."):
        df, info, divs = load_stock_and_info(symbol, period)

    if df.empty:
        st.error(f"找不到代號 `{symbol}` 的數據，請檢查輸入是否正確。")
        return

    eng_name = info.get("shortName") or info.get("longName") or symbol
    if market_type == "HK":
        cn_name = get_hk_chinese_name(symbol)
        if cn_name:
            st.subheader(f"{cn_name} — {eng_name} (`{symbol}`)")
        else:
            st.subheader(f"{eng_name} (`{symbol}`)")
    else:
        st.subheader(f"{eng_name} (`{symbol}`)")

    # 計算技術指標
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["STD20"] = df["Close"].rolling(window=20).std()
    df["BB_Upper"] = df["MA20"] + (df["STD20"] * 2)
    df["BB_Lower"] = df["MA20"] - (df["STD20"] * 2)

    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # 第一排：價格與技術數據（若盤中 df 最後一筆為空，自動備援 info 的現價）
    latest_close = float(df["Close"].iloc[-1])
    if pd.isna(latest_close) or latest_close == 0:
        latest_close = float(info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0)

    prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else latest_close
    if pd.isna(prev_close) or prev_close == 0:
        prev_close = float(info.get("previousClose") or latest_close)

    change = latest_close - prev_close
    pct_change = (change / prev_close) * 100 if prev_close else 0.0
    high_in_period = float(df["High"].dropna().max()) if not df["High"].dropna().empty else latest_close
    trailing_stop_price = high_in_period * (1 - trail_pct / 100)
    latest_rsi = float(df["RSI"].dropna().iloc[-1]) if not df["RSI"].dropna().empty else 50.0
    latest_vol = int(df["Volume"].fillna(0).iloc[-1])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("最新收盤價", f"{currency_sign}{latest_close:,.2f}", f"{change:+.2f} ({pct_change:+.2f}%)")
    c2.metric("當日成交量", f"{latest_vol:,}")
    c3.metric("區間最高價", f"{currency_sign}{high_in_period:,.2f}")
    c4.metric(f"移動止損位 (-{trail_pct}%)", f"{currency_sign}{trailing_stop_price:,.2f}")
    c5.metric("最新 RSI (14)", f"{latest_rsi:.1f}", "超買 (>70)" if latest_rsi > 70 else ("超賣 (<30)" if latest_rsi < 30 else "中性區間"))

    # 第二排：精準計算全年每股股息、息率、最近除淨日與派息次數
    div_rate = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
    ex_div_date = format_timestamp(info.get("exDividendDate"))
    pay_div_date = format_timestamp(info.get("dividendDate"))
    div_freq_text = ""

    # 若 info 缺少港股股息，直接從真實歷史派息紀錄 (divs) 加總過去 12 個月派息
    if divs is not None and not divs.empty:
        divs_clean = divs[divs > 0]
        if not divs_clean.empty:
            # 取得最近一次除淨日
            last_ex_dt = divs_clean.index[-1]
            if ex_div_date == "無資料":
                ex_div_date = last_ex_dt.strftime("%Y-%m-%d")

            # 篩選過去 370 天內的實際派息紀錄並加總（例如 0002.HK 一年派 4 次息）
            cutoff_date = pd.Timestamp.now(tz=last_ex_dt.tz) - pd.Timedelta(days=370)
            recent_12m_divs = divs_clean[divs_clean.index >= cutoff_date]
            if not recent_12m_divs.empty:
                calc_annual_div = float(recent_12m_divs.sum())
                div_freq_text = f"（近1年派息 {len(recent_12m_divs)} 次）"
                if not div_rate or div_rate == 0:
                    div_rate = calc_annual_div

    # 計算真實股息率（全年每股股息 / 最新股價）
    if div_rate and div_rate > 0 and latest_close > 0:
        yield_pct = (float(div_rate) / latest_close) * 100
        yield_str = f"{yield_pct:.2f}%"
        div_rate_str = f"{currency_sign}{float(div_rate):,.3f}"
    else:
        div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
        if div_yield is not None and div_yield > 0:
            yield_pct = div_yield * 100 if div_yield < 0.35 else div_yield
            yield_str = f"{yield_pct:.2f}%"
            div_rate_str = f"{currency_sign}{float(div_rate):,.3f}" if div_rate else "依息率推算"
        else:
            yield_str = "無派息 / 無資料"
            div_rate_str = "無派息 / 無資料"

    st.markdown(f"#### 💰 股息與除淨資訊 {div_freq_text}")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("全年每股股息 (TTM)", div_rate_str)
    d2.metric("股息率 (息率)", yield_str)
    d3.metric("最近除淨日 (Ex-Div)", ex_div_date)
    d4.metric("派息日 (Dividend Date)", pay_div_date)

    # 繪製三層圖表
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.58, 0.20, 0.22],
        subplot_titles=(f"{symbol} 價格走勢與技術指標", "成交數量 (Volume)", "RSI (14) 相對強弱指標")
    )

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="K線"
    ), row=1, col=1)

    if show_ma:
        fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], line=dict(color="orange", width=1.5), name="MA20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], line=dict(color="royalblue", width=1.5), name="MA50"), row=1, col=1)

    if show_bb:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], line=dict(color="gray", width=1, dash="dot"), name="布林上軌"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], line=dict(color="gray", width=1, dash="dot"), fill="tonexty", fillcolor="rgba(128,128,128,0.1)", name="布林下軌"), row=1, col=1)

    vol_colors = ["green" if c >= o else "red" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=vol_colors,
        name="成交量"
    ), row=2, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], line=dict(color="purple", width=1.5), name="RSI(14)"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(height=820, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    if auto_refresh:
        time.sleep(refresh_sec)
        st.rerun()
