import streamlit as st
import pandas as pd

# 1. 網頁基本設定
st.set_page_config(page_title="雲端廠商報價查詢系統", layout="wide")
st.title("🌐 雲端廠商報價查詢系統")

# 2. 定義資料讀取函式 (連結 Google Sheets)
@st.cache_data(ttl=300)  # 每 5 分鐘自動失效，強制抓取雲端最新資料
def load_data():
    # 這是你提供的 Google Sheets 連結
    sheet_url = "https://docs.google.com/spreadsheets/d/1ualXNJ8WFEvtNAkm8uP3FtRgIlNVgz138gLQQ8JRDe0/edit?usp=sharing"
    
    # 將 Google Sheets 連結轉換為 CSV 下載連結
    csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')
    
    try:
        # 直接從雲端讀取資料
        df = pd.read_csv(csv_url)
        
        # 【修正 1】自動移除欄位名稱前後的空白 (避免 '項目 ' 導致讀取錯誤)
        df.columns = df.columns.str.strip()
        
        # 資料清理：確保金額與數量是數字，並處理掉可能存在的逗號
        for col in ["金額", "數量"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # 檢查並補齊必要欄位
        target_cols = ["廠商", "項目", "數量", "金額", "單價"]
        for col in target_cols:
            if col not in df.columns:
                df[col] = 0
        
        # 自動計算單價：金額 / 數量
        df['單價'] = df.apply(
            lambda row: row['金額'] / row['數量'] if row['數量'] != 0 else 0, 
            axis=1
        )
        
        # 只回傳需要的欄位與正確順序
        return df[target_cols]
    except Exception as e:
        st.error(f"連線 Google Sheets 失敗，請確認表格權限已開啟。錯誤訊息: {e}")
        return None

# 3. 執行資料讀取
df = load_data()

if df is not None:
    # --- 側邊欄：搜尋與篩選 ---
    st.sidebar.header("🔍 搜尋條件")
    
    # 廠商下拉選單 (自動去重並排序)
    # 確保廠商欄位沒有空白值，避免報錯
    vendor_list = ["全部"] + sorted(list(df["廠商"].dropna().astype(str).unique()))
    selected_vendor = st.sidebar.selectbox("篩選廠商", vendor_list)
    
    # 項目搜尋
    search_query = st.sidebar.text_input("搜尋項目 (關鍵字)", "")

    # --- 過濾邏輯 ---
    display_df = df.copy()
    
    # 1. 廠商篩選
    if selected_vendor != "全部":
        display_df = display_df[display_df["廠商"] == selected_vendor]
    
    # 2. 關鍵字搜尋 【主要修正處】
    if search_query:
        # case=False 代表忽略大小寫 (搜尋 'aws' 也能找到 'AWS')
        display_df = display_df[display_df["項目"].astype(str).str.contains(search_query, case=False, na=False)]

    # --- 核心功能：自動排序 (低價在前) ---
    display_df = display_df.sort_values(by="單價", ascending=True)

    # --- 顯示介面 ---
    st.subheader(f"📊 報價清單 (已依單價由低至高排序)")
    
    if not display_df.empty:
        # 顯示表格並將最低單價標註為綠色
        st.dataframe(
            display_df.style.highlight_min(subset=['單價'], color='#D4EDDA'),
            column_config={
                "金額": st.column_config.NumberColumn("總金額", format="$ %d"),
                "單價": st.column_config.NumberColumn("單價 (低價優先)", format="$ %.2f"),
                "數量": st.column_config.NumberColumn("數量", format="%d"),
            },
            use_container_width=True,
            hide_index=True
        )
        st.info("💡 資料來源：Google Sheets。若在 Excel 修改後，請等待幾分鐘或點擊左側「立即同步」按鈕。")
    else:
        st.warning("查無符合條件的報價資料。請嘗試其他關鍵字或清除篩選條件。")

    # 手動重新整理按鈕
    if st.sidebar.button("立即同步雲端資料"):
        st.cache_data.clear()
        st.rerun()
