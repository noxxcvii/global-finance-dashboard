# Global Financial Dashboard 📈

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://global-finance-dashboard.streamlit.app/)

一個基於 Python (Streamlit) 與 Yahoo Finance API 開發的「全球經濟與金融指標儀表板」。
本專案主打**「配置驅動 (Configuration-driven)」**，使用者無須修改複雜的 Python 原始碼，只需透過更新 JSON 設定檔，即可動態新增指標、調整分類，並能在互動式 K 線圖上完美對比「重大歷史經濟事件」的影響。

---

## ✨ 核心特色

- **📊 即時市場快照**
  自動抓取並分門別類呈現美國三大指數、台日股、外匯、貴金屬期貨、虛擬貨幣及 VIX 恐慌指數的最新報價與漲跌幅。
- **🖥️ 專業級互動圖表**
  內建 Plotly 互動式子圖表（上層價格走勢 + 下層成交量直狀圖），支援滑鼠懸浮查詢 (Hover) 與任意縮放。
- **🗓️ 完美剔除休假斷點**
  底層寫入類別 X 軸 (Categorical Axis) 邏輯，徹底移除週末與國定假日無交易紀錄所產生的圖表視覺空白斷軌。
- **🚨 歷史事件重疊預警 (Event Shadows & Lines)**
  只要在 `config.json` 內輸入突發新聞 (例如: 以巴衝突、矽谷銀行破產)，系統即會自動將該事件以**「半透明陰影範圍」**或**「精準單日垂直標線」**映射到各項資產趨勢圖上，同時利用動態交錯演算法，讓事件標記整齊順暢地懸浮於圖表頂部，不遮蔽走勢資料！

---

## 📁 主要檔案結構

- **`app.py`** 
  儀表板的主程式（負責資料獲取、快取處理與 UI UI/Plotly 渲染引擎）。
- **`config.json`** 
  控制儀表板運作的心臟（所有的分類主題、清單參數與歷史事件都在此設定）。
- **`requirements.txt`** 
  執行此應用程式所需的 Python 相依套件清單。

---

## 🚀 如何在本地端執行

**1. 安裝依賴套件**  
請確保您的系統已安裝 Python 3.8 或以上版本，接著於終端機執行：
```bash
pip install -r requirements.txt
```

**2. 啟動 Dashboard**  
```bash
streamlit run app.py
```
啟動成功後，瀏覽器將會自動跳轉打開 `http://localhost:8501`。

---

## ⚙️ 如何自訂擴充 (config.json 教學)

本專案將複雜的邏輯全部隔離在 Python 中，所有操作都可以透過純文字修改 `config.json` 達成：

### 📌 新增或分類追蹤標的
在 `"indicators"` 字典中，依照您想要的「分類」放入名稱與對應的 Yahoo Finance Ticker 代碼：
```json
"虛擬貨幣": [
    {"name": "比特幣 (BTC-USD)", "ticker": "BTC-USD"},
    {"name": "泰達幣 (USDT-USD)", "ticker": "USDT-USD"}
]
```

### 📌 新增重大經濟/市場事件
在 `"events"` 陣列中，加入事件名稱、起訖日期與代表色（RGBA 格式）：
```json
{
    "name": "矽谷銀行破產危機",
    "start": "2023-03-08",
    "end": "2023-03-20",
    "color": "rgba(255, 0, 0, 0.2)"
}
```
*💡 備註：不管事件長達一個月，或是只有一天，儀表板都會自動判斷該畫立體陰影或單日虛線！*
