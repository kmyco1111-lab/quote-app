import streamlit as st
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="廠商報價查詢系統", layout="wide")
st.title("📋 廠商報價查詢系統")

# 2. 定義資料讀取與處理函式
@st.cache_data
def load_data():
    try:
        # 嘗試處理不同編碼 (解決 Excel 產生的 CSV 亂碼問題)
        try:
            df = pd.read_csv("data.csv", encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv("data.csv", encoding='cp950')
        
        # 資料清理：移除金額和數量的逗號，確保為數字格式
        for col in ["金額", "數量"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # 確保所有要求的欄位都存在
        target_cols = ["廠商", "項目", "數量", "金額", "單價"]
        for col in target_cols:
            if col not in df.columns:
                df[col] = 0
        
        # 自動計算單價：金額 / 數量 (若數量為0則顯示0)
        df['單價'] = df.apply(
            lambda row: row['金額'] / row['數量'] if row['數量'] != 0 else 0, 
            axis=1
        )
        
        # 回傳指定順序的欄位
        return df[target_cols]
    except FileNotFoundError:
        return None

# 3. 載入資料
df = load_data()

if df is not None:
    # --- 側邊欄：搜尋與篩選 ---
    st.sidebar.header("🔍 搜尋條件")
    
    # 廠商下拉選單
    vendor_list = ["全部"] + sorted(list(df["廠商"].unique()))
    selected_vendor = st.sidebar.selectbox("選擇廠商", vendor_list)
    
    # 項目關鍵字搜尋
    search_query = st.sidebar.text_input("輸入項目關鍵字 (如：螺絲)", "")

    # --- 資料過濾邏輯 ---
    display_df = df.copy()
    
    if selected_vendor != "全部":
        display_df = display_df[display_df["廠商"] == selected_vendor]
        
    if search_query:
        display_df = display_df[display_df["項目"].str.contains(search_query, na=False)]

    # --- 核心功能：排序 (低價在前) ---
    # 根據單價進行由小到大排序
    display_df = display_df.sort_values(by="單價", ascending=True)

    # --- 顯示結果 ---
    st.subheader(f"📊 查詢結果 (共 {len(display_df)} 筆資料)")
    
    if not display_df.empty:
        # 顯示表格並格式化數字
        st.dataframe(
            display_df.style.highlight_min(subset=['單價'], color='#D4EDDA'), # 自動標記最低單價為淺綠色
            column_config={
                "金額": st.column_config.NumberColumn("金額", format="$ %d"),
                "單價": st.column_config.NumberColumn("單價 (低至高)", format="$ %.2f"),
                "數量": st.column_config.NumberColumn("數量", format="%d"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # 額外小資訊
        st.caption("💡 提示：系統已自動將「單價」最低的廠商排在最上方。")
    else:
        st.warning("查無符合條件的報價，請嘗試調整搜尋字眼。")

else:
    st.error("❌ 找不到 data.csv 檔案。請確認檔案與 app.py 放在同一個資料夾。")