import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="美股技術分析儀表板", page_icon="📈", layout="wide")

st.title("📈 美股技術分析儀表板")
st.caption("支援 K 線圖、布林通道 (Bollinger Bands)、均線 (MA) 與 RSI 動能指標")

# 側邊欄參數設定
with st.sidebar:
    st.header("⚙️ 技術指標設定")
    symbol = st.text_input("輸入股票代號 (例如 AAPL, NVDA, TSLA, SPY)：", value="NVDA").upper().strip()
    period = st.selectbox("選擇時間範圍：", ["3mo", "6mo", "1y", "2y", "5y"], index=2)
    show_bb = st.checkbox("顯示布林通道 (BB 20, 2)", value=True)
    show_ma = st.checkbox("顯示移動平均線 (MA20 / MA50)", value=True)
    trail_pct = st.slider("移動止損參考百分比 (%)：", min_value=3.0, max_value=20.0, value=8.0, step=0.5)

@st.cache_data(ttl=300)
def load_stock_data(ticker: str, period_str: str):
    df = yf.download(ticker, period=period_str, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

if symbol:
    df = load_stock_data(symbol, period)

    if df.empty:
        st.error(f"找不到代號 `{symbol}` 的數據，請確認輸入是否正確。")
    else:
        # 計算技術指標
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA50"] = df["Close"].rolling(window=50).mean()
        df["STD20"] = df["Close"].rolling(window=20).std()
        df["BB_Upper"] = df["MA20"] + (df["STD20"] * 2)
        df["BB_Lower"] = df["MA20"] - (df["STD20"] * 2)

        # 計算 RSI (14)
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # 頂部關鍵數據卡片
        latest_close = float(df["Close"].iloc[-1])
        prev_close = float(df["Close"].iloc[-2])
        change = latest_close - prev_close
        pct_change = (change / prev_close) * 100
        high_in_period = float(df["High"].max())
        trailing_stop_price = high_in_period * (1 - trail_pct / 100)
        latest_rsi = float(df["RSI"].iloc[-1])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"{symbol} 最新收盤價", f"${latest_close:,.2f}", f"{change:+.2f} ({pct_change:+.2f}%)")
        c2.metric("區間最高價", f"${high_in_period:,.2f}")
        c3.metric(f"移動止損位 (-{trail_pct}%)", f"${trailing_stop_price:,.2f}")
        c4.metric("最新 RSI (14)", f"{latest_rsi:.1f}", "超買 (>70)" if latest_rsi > 70 else ("超賣 (<30)" if latest_rsi < 30 else "中性區間"))

        # 繪製 K 線與 RSI 雙層圖表
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            vertical_spacing=0.06, row_heights=[0.72, 0.28],
            subplot_titles=(f"{symbol} 價格走勢與技術指標", "RSI (14) 相對強弱指標")
        )

        # K 線圖
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

        # RSI 線
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], line=dict(color="purple", width=1.5), name="RSI(14)"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        fig.update_layout(height=680, xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
