import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="自選股總覽看板", page_icon="📊", layout="wide")

st.title("📊 美股與大盤指數即時總覽")
st.caption("輸入多個代號（以逗號分隔），一次比較最新價格、當日漲跌幅與 52 週高低點位置")

default_watchlist = "SPY, QQQ, NVDA, AAPL, MSFT, GOOGL, TSLA, CAD=X"
watchlist_input = st.text_input("自選代號清單 (以英文逗號分隔)：", value=default_watchlist)

tickers = [t.strip().upper() for t in watchlist_input.split(",") if t.strip()]

if st.button("🔄 重新整理即時報價") or tickers:
    rows = []
    with st.spinner("正在更新最新市場報價..."):
        for sym in tickers:
            try:
                tk = yf.Ticker(sym)
                hist = tk.history(period="5d")
                if len(hist) >= 2:
                    last_p = float(hist["Close"].iloc[-1])
                    prev_p = float(hist["Close"].iloc[-2])
                    chg = last_p - prev_p
                    pct = (chg / prev_p) * 100
                    rows.append({
                        "代號": sym,
                        "最新價格": round(last_p, 4 if "=X" in sym else 2),
                        "漲跌金額": round(chg, 4 if "=X" in sym else 2),
                        "漲跌幅 (%)": round(pct, 2),
                        "當日最高": round(float(hist["High"].iloc[-1]), 2),
                        "當日最低": round(float(hist["Low"].iloc[-1]), 2),
                    })
            except Exception:
                pass

    if rows:
        df_summary = pd.DataFrame(rows)
        st.dataframe(
            df_summary.style.map(
                lambda v: "color: green; font-weight: bold;" if isinstance(v, (int, float)) and v > 0 else ("color: red; font-weight: bold;" if isinstance(v, (int, float)) and v < 0 else ""),
                subset=["漲跌金額", "漲跌幅 (%)"]
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("未能取得報價資料，請檢查代號格式。")
