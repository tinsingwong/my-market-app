import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="外匯走勢與即時換算", page_icon="💱", layout="wide")

st.title("💱 外匯走勢與即時換算")
st.caption("選擇貨幣對後，直接在右側空白欄輸入金額即可即時換算（例如輸入 90 換算加元兌美元）")

# 定義常用貨幣對
fx_pairs = {
    "🇨🇦 加元 兌 美元 (CAD → USD)": ("CADUSD=X", "CAD", "USD"),
    "🇺🇸 美元 兌 加元 (USD → CAD)": ("CAD=X", "USD", "CAD"),
    "🇨🇦 加元 兌 港幣 (CAD → HKD)": ("CADHKD=X", "CAD", "HKD"),
    "🇭🇰 港幣 兌 加元 (HKD → CAD)": ("HKDCAD=X", "HKD", "CAD"),
    "🇺🇸 美元 兌 港幣 (USD → HKD)": ("HKD=X", "USD", "HKD"),
    "🇯🇵 美元 兌 日圓 (USD → JPY)": ("JPY=X", "USD", "JPY"),
    "🇪🇺 歐元 兌 美元 (EUR → USD)": ("EURUSD=X", "EUR", "USD"),
}

# 並排放置：左邊下拉選單，右邊空白金額輸入框
col_select, col_input = st.columns([2, 1])

with col_select:
    selected_label = st.selectbox("1. 選擇貨幣對：", list(fx_pairs.keys()), index=0)

with col_input:
    amount = st.number_input(
        "2. 輸入金額（直接輸入數字）：",
        min_value=0.0,
        value=90.0,
        step=10.0,
        format="%.2f"
    )

ticker_code, from_curr, to_curr = fx_pairs[selected_label]

@st.cache_data(ttl=300)
def get_fx_history(symbol: str):
    df = yf.download(symbol, period="6mo", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df_fx = get_fx_history(ticker_code)

if df_fx.empty:
    st.error("暫時無法取得該貨幣對匯率，請稍後再試。")
else:
    latest_rate = float(df_fx["Close"].iloc[-1])
    prev_rate = float(df_fx["Close"].iloc[-2])
    rate_diff = latest_rate - prev_rate
    converted_result = amount * latest_rate

    # 醒目顯示即時換算結果
    st.success(
        f"### 💰 **{amount:,.2f} {from_curr}** ＝ **{converted_result:,.2f} {to_curr}**\n"
        f"目前即時匯率：`1 {from_curr} = {latest_rate:.4f} {to_curr}`（較前一日 `{rate_diff:+.4f}`）"
    )

    # 繪製近半年匯率走勢圖
    fig = px.line(
        df_fx, x=df_fx.index, y="Close",
        title=f"{selected_label} 近 6 個月走勢圖",
        labels={"Close": f"匯率 ({to_curr})", "Date": "日期"}
    )
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
