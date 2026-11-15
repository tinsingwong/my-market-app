import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(page_title="全球股市技術分析儀表板", page_icon="📈", layout="wide")

st.title("📈 美股・加股・港股 技術分析與股息儀表板")

# --- 側邊欄設定 ---
with st.sidebar:
    st.header("🌍 市場與股票選擇")
    market = st.radio(
        "選擇股票市場：",
        ["🇺🇸 美國股市 (US)", "🇨🇦 加拿大股市 (TSX)", "🇭🇰 香港股市 (HKEX)"],
        index=0
    )

    if "美國" in market:
        default_sym = "NVDA"
        hint = "例如：AAPL, NVDA, MSFT, SPY, SCHD"
    elif "加拿大" in market:
        default_sym = "TD"
        hint = "例如：TD, RY, ENB, ZEB, VFV（無需輸入 .TO，系統會自動補上）"
    else:
        default_sym = "0700"
        hint = "例如：0700, 0005, 0941, 2800（無需輸入 .HK，系統會自動補上）"

    raw_symbol = st.text_input("輸入股票代號：", value=default_sym, help=hint).upper().strip()

    # 自動格式化三地股票代號
    symbol = raw_symbol
    currency_sign = "$"
    if raw_symbol:
        if "加拿大" in market:
            currency_sign = "CA$"
            if not raw_symbol.endswith(".TO") and not raw_symbol.endswith(".V"):
                symbol = f"{raw_symbol}.TO"
        elif "香港" in market:
            currency_sign = "HK$"
            clean_hk = raw_symbol.replace(".HK", "")
            if clean_hk.isdigit():
                clean_hk = clean_hk.zfill(4)  # 港股自動補齊 4 位數，例如 5 -> 0005
            symbol = f"{clean_hk}.HK"

    st.divider()
    st.header("⚙️ 技術指標設定")
    period = st.selectbox("選擇時間範圍：", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    show_bb = st.checkbox("顯示布林通道 (BB 20, 2)", value=True)
    show_ma = st.checkbox("顯示移動平均線 (MA20 / MA50)", value=True)
    trail_pct = st.slider("移動止損參考百分比 (%)：", min_value=3.0, max_value=20.0, value=8.0, step=0.5)

@st.cache_data(ttl=300)
def load_stock_and_info(ticker_str: str, period_str: str):
    tk = yf.Ticker(ticker_str)
    df = tk.history(period=period_str)
    info = {}
    try:
        info = tk.info or {}
    except Exception:
        info = {}
    return df, info

def format_timestamp(ts):
    if not ts:
        return "無資料"
    try:
        if isinstance(ts, (int, float)):
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
        return str(ts)[:10]
    except Exception:
        return "無資料"

if symbol:
    with st.spinner(f"正在載入 {symbol} 數據與股息資訊..."):
        df, info = load_stock_and_info(symbol, period)

    if df.empty:
        st.error(f"找不到代號 `{symbol}` 的數據，請檢查輸入是否正確。")
    else:
        stock_name = info.get("shortName") or info.get("longName") or symbol
        st.subheader(f"{stock_name} (`{symbol}`)")

        # --- 計算技術指標 ---
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

        # --- 第一排：價格與技術數據 ---
        latest_close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else latest_close
        change = latest_close - prev_close
        pct_change = (change / prev_close) * 100 if prev_close else 0
        high_in_period = float(df["High"].max())
        trailing_stop_price = high_in_period * (1 - trail_pct / 100)
        latest_rsi = float(df["RSI"].iloc[-1]) if pd.notna(df["RSI"].iloc[-1]) else 50.0
        latest_vol = int(df["Volume"].iloc[-1])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("最新收盤價", f"{currency_sign}{latest_close:,.2f}", f"{change:+.2f} ({pct_change:+.2f}%)")
        c2.metric("當日成交量", f"{latest_vol:,}")
        c3.metric("區間最高價", f"{currency_sign}{high_in_period:,.2f}")
        c4.metric(f"移動止損位 (-{trail_pct}%)", f"{currency_sign}{trailing_stop_price:,.2f}")
        c5.metric("最新 RSI (14)", f"{latest_rsi:.1f}", "超買 (>70)" if latest_rsi > 70 else ("超賣 (<30)" if latest_rsi < 30 else "中性區間"))

        # --- 第二排：每股股息、息率、除淨日、派息日 ---
        div_rate = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
        div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
        ex_div_date = format_timestamp(info.get("exDividendDate"))
        pay_div_date = format_timestamp(info.get("dividendDate"))

        # 統一處理 Yahoo Finance 股息率小數/百分比格式差異
        if div_yield is not None:
            yield_pct = div_yield * 100 if div_yield < 0.35 else div_yield
            yield_str = f"{yield_pct:.2f}%"
        else:
            yield_str = "無派息 / 無資料"

        div_rate_str = f"{currency_sign}{div_rate:,.3f}" if div_rate else "無派息 / 無資料"

        st.markdown("#### 💰 股息與除淨資訊")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("全年每股股息", div_rate_str)
        d2.metric("股息率 (息率)", yield_str)
        d3.metric("除淨日 (Ex-Dividend Date)", ex_div_date)
        d4.metric("派息日 (Dividend Date)", pay_div_date)

        # --- 繪製三層圖表：1. K線與均線/布林  2. 成交量 (Volume)  3. RSI (14) ---
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.58, 0.20, 0.22],
            subplot_titles=(f"{symbol} 價格走勢與技術指標", "成交數量 (Volume)", "RSI (14) 相對強弱指標")
        )

        # 第 1 層：K 線圖
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

        # 第 2 層：成交數量 (Volume) 紅綠柱狀圖
        vol_colors = ["green" if c >= o else "red" for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=vol_colors,
            name="成交量"
        ), row=2, col=1)

        # 第 3 層：RSI 線
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], line=dict(color="purple", width=1.5), name="RSI(14)"), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

        fig.update_layout(height=820, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
