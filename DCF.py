import streamlit as st
import pandas as pd

# 設定網頁標題
st.set_page_config(page_title="手動 DCF 估值工具 (5年期)", layout="wide")
st.title("📈 企業價值與股權價值估算器")

# --- 左側控制面板 ---
st.sidebar.header("🔍 公司資訊")
ticker = st.sidebar.text_input("公司名稱 / 代號", "AAPL").upper()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 手動輸入財務數據 (in Million)")

# 按照您的要求排序：FCF -> 現金 -> 總負債 -> 流通股數
f_fcf = st.sidebar.number_input("基準自由現金流 (FCF)", value=0.0, format="%.2f", step=10.0)
f_cash = st.sidebar.number_input("現金及其他投資", value=0.0, format="%.2f", step=10.0)
f_debt = st.sidebar.number_input("總負債 (Total Debt)", value=0.0, format="%.2f", step=10.0)
f_shares = st.sidebar.number_input("流通股數 (Shares)", value=0.0, format="%.2f", step=1.0)

st.sidebar.markdown("---")
st.sidebar.header("🔮 成長假設 (%)")
g_rate = st.sidebar.number_input("未來 5 年預期成長率 (%)", value=10.0, format="%.2f") / 100
wacc = st.sidebar.number_input("折現率 WACC (%)", value=8.0, format="%.2f") / 100
t_g = st.sidebar.number_input("永續成長率 (%)", value=2.5, format="%.2f") / 100

# --- DCF 計算邏輯 ---
def run_dcf_math():
    fcf_list = []
    temp_fcf = f_fcf
    # 預測未來 5 年的現金流
    for i in range(5):
        temp_fcf *= (1 + g_rate)
        fcf_list.append(temp_fcf)
        
    # 1. 計算 5 年現金流的現值 (PV of FCF)
    pv_fcf_sum = sum([fcf / ((1 + wacc) ** (i + 1)) for i, fcf in enumerate(fcf_list)])
    
    # 2. 計算終極價值現值 (PV of Terminal Value)
    pv_tv = 0
    if wacc > t_g:
        # 終極價值公式：[Year 5 FCF * (1 + t_g)] / (wacc - t_g)
        terminal_value = (fcf_list[-1] * (1 + t_g)) / (wacc - t_g)
        pv_tv = terminal_value / ((1 + wacc) ** 5)
    
    # 3. 算出企業價值 (Enterprise Value)
    enterprise_value = pv_fcf_sum + pv_tv
    
    # 4. 價值橋接：股權價值 = EV + 現金 - 負債
    equity_value = enterprise_value + f_cash - f_debt
    
    # 5. 每股合理價
    fair_price = equity_value / f_shares if f_shares > 0 else 0
    
    return enterprise_value, equity_value, fair_price, fcf_list, pv_fcf_sum, pv_tv

ev, eq_val, fair_p, fcfs, pv_fcf, pv_tv = run_dcf_math()

# --- 主畫面顯示結果 ---
st.subheader(f"📊 {ticker} 5年期估值詳情")

# 關鍵指標顯示
m_col1, m_col2 = st.columns(2)
# 由於移除了自動抓取，市價部分如果您需要比對，可以自行在側邊欄增加一個市價輸入框
m_col1.metric("模型預估合理價", f"${fair_p:.2f}")
st.markdown("---")

# 價值拆解顯示 (Value Breakdown)
st.write("### 🏗️ 5年期估值橋接過程 (Calculation Bridge)")
c_col1, c_col2, c_col3 = st.columns(3)

with c_col1:
    st.write("**1. 經營價值 (PV)**")
    st.write(f"5年現金流現值總和: `${pv_fcf:,.2f} M`")
    st.write(f"5年後終極價值現值: `${pv_tv:,.2f} M`")
    st.info(f"**企業價值 (EV): ${ev:,.2f} M**")

with c_col2:
    st.write("**2. 資產負債調整**")
    st.write(f"(+) 現金及投資: `${f_cash:,.2f} M`")
    st.write(f"(-) 總負債: `${f_debt:,.2f} M`")
    st.write(f"**淨調整項: `${(f_cash - f_debt):,.2f} M`**")

with c_col3:
    st.write("**3. 股權價值 (Equity Value)**")
    st.success(f"**股權價值: ${eq_val:,.2f} M**")
    st.write(f"除以流通股數: `{f_shares:,.2f} M` 股")
    st.write(f"**最終合理價: ${fair_p:.2f}**")

st.markdown("---")
st.subheader("📈 未來 5 年自由現金流投影 (in Million)")
if f_fcf > 0:
    chart_data = pd.DataFrame(fcfs, index=[i+1 for i in range(5)], columns=["Projected FCF"])
    st.bar_chart(chart_data)
else:
    st.warning("請在左側輸入『基準自由現金流』以產生預測圖表。")

st.caption("註：本工具僅供參考，所有數據需由使用者自行從財報中提取並填寫。")