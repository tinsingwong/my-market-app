import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="外匯走勢與即時換算", page_icon="💱", layout="wide")

st.title("💱 外匯匯率與即時換算")
st.caption("自選基準貨幣與目標貨幣，即時查詢匯率換算與歷史走勢")

# 支援的獨立貨幣清單
currencies = {
    "加幣 (CAD)": "CAD",
    "美元 (USD)": "USD",
    "港幣 (HKD)": "HKD",
    "日圓 (JPY)": "JPY",
    "歐元 (EUR)": "EUR",
    "英鎊 (GBP)": "GBP",
    "澳幣 (AUD)": "AUD",
    "台幣 (TWD)": "TWD",
    "人民幣 (CNY)": "CNY",
    "挪威克朗 (NOK)": "NOK",
}

@st.cache_data(ttl=300)
def fetch_fx_data(from_code: str, to_code: str, period_str: str = "1mo"):
    if from_code == to_code:
        dates = pd.date_range(end=pd.Timestamp.today(), periods=10)
        return pd.DataFrame({"Close": [1.0] * 10}, index=dates)
    ticker = f"{from_code}{to_code}=X"
    df = yf.download(ticker, period=period_str, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# --- 頂部 4 個常用匯率看板 ---
top_pairs = [
    ("加幣/港幣", "CAD", "HKD"),
    ("美元/加幣", "USD", "CAD"),
    ("美元/港幣", "HKD", "HKD") if False else ("美元/港幣", "USD", "HKD"),
    ("日圓/港幣", "JPY", "HKD"),
]

top_cols = st.columns(4)
for idx, (label, c1, c2) in enumerate(top_pairs):
    df_top = fetch_fx_data(c1, c2, "5d")
    with top_cols[idx]:
        if not df_top.empty and len(df_top) >= 2:
            cur = float(df_top["Close"].iloc[-1])
            prv = float(df_top["Close"].iloc[-2])
            diff = cur - prv
            pct = (diff / prv) * 100
            st.metric(label, f"{cur:.4f}", f"{diff:+.4f} ({pct:+.2f}%)")
        else:
            st.metric(label, "載入中", "-")

st.divider()

# --- 🔄 自選貨幣對換（兩欄獨立貨幣 + 互換按鈕 + 旁邊兩個空白計算欄）---
st.subheader("🔄 自選貨幣對換")

currency_labels = list(currencies.keys())

if "fx_from" not in st.session_state:
    st.session_state.fx_from = "加幣 (CAD)"
if "fx_to" not in st.session_state:
    st.session_state.fx_to = "港幣 (HKD)"

def swap_currencies():
    st.session_state.fx_from, st.session_state.fx_to = (
        st.session_state.fx_to,
        st.session_state.fx_from,
    )

# 並排 5 欄：[1. 基準貨幣] | [⇄ 互換] | [2. 目標貨幣] | [基準金額輸入] | [目標金額結果]
col_from, col_swap, col_to, col_amt_from, col_amt_to = st.columns([1.4, 0.5, 1.4, 1.2, 1.2])

with col_from:
    from_label = st.selectbox("1. 基準貨幣 (From)：", currency_labels, key="fx_from")

with col_swap:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    st.button("⇄ 互換", on_click=swap_currencies, use_container_width=True)

with col_to:
    to_label = st.selectbox("2. 目標貨幣 (To)：", currency_labels, key="fx_to")

from_code = currencies[from_label]
to_code = currencies[to_label]

# 時間週期選擇
period_map = {"1個月": "1mo", "6個月": "6mo", "1年": "1y", "5年": "5y"}
selected_period_label = st.radio("時間週期：", list(period_map.keys()), horizontal=True, index=0)
period_val = period_map[selected_period_label]

# 抓取匯率數據
df_fx = fetch_fx_data(from_code, to_code, period_val)

if df_fx.empty:
    st.error(f"暫時無法取得 {from_code}/{to_code} 的匯率數據，請稍後再試。")
else:
    latest_rate = float(df_fx["Close"].iloc[-1])
    prev_rate = float(df_fx["Close"].iloc[-2]) if len(df_fx) >= 2 else latest_rate
    rate_diff = latest_rate - prev_rate
    rate_pct = (rate_diff / prev_rate) * 100 if prev_rate else 0.0

    # 在兩欄貨幣旁邊的 2 個空白計算位置填入數字並即時換算
    with col_amt_from:
        from_amount = st.number_input(
            f"輸入 {from_code} 金額：",
            min_value=0.0,
            value=100.0,
            step=10.0,
            format="%.2f",
            key="fx_from_amount"
        )

    calculated_to_amount = from_amount * latest_rate

    with col_amt_to:
        st.text_input(
            f"兌換 {to_code} 總數：",
            value=f"{calculated_to_amount:,.2f}",
            disabled=False,
            key=f"fx_to_display_{from_code}_{to_code}_{from_amount}"
        )

    # 最新報價大字指標
    st.metric(
        label=f"{from_label} 兌 {to_label} ({from_code}/{to_code}) 最新報價",
        value=f"{latest_rate:.4f}",
        delta=f"{rate_diff:+.4f} ({rate_pct:+.2f}%)"
    )

    # 歷史走勢折線圖
    fig = px.line(
        df_fx,
        x=df_fx.index,
        y="Close",
        labels={"Close": f"匯率 ({to_code})", "Date": "日期"},
    )
    fig.update_traces(line_color="#00CC66", line_width=2.5)
    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="",
        yaxis_title=""
    )
    st.plotly_chart(fig, use_container_width=True)
