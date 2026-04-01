import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# ==========================================
# 頁面佈局與設計 (必須是第一個 Streamlit 指令)
# ==========================================
st.set_page_config(
    page_title="全球經濟與金融指標儀表板",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. 讀取設定檔 (配置驅動)
# ==========================================
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

config = load_config()
indicators_dict = config['indicators']
timeframes = config['timeframes']
events = config.get('events', []) # 讀取設定的重大經濟事件

# 展開成單一層級清單以供快速查找與抓取API (不影響原本邏輯)
ticker_to_name = {}
ticker_list = []
for category, items in indicators_dict.items():
    for item in items:
        ticker_to_name[item['ticker']] = item['name']
        ticker_list.append(item['ticker'])

# ==========================================
# 2. 獲取數據的工具函式
# ==========================================
@st.cache_data(ttl=300) # 快取 5 分鐘
def fetch_latest_data(tickers):
    data = {}
    for ticker in tickers:
        try:
            tkr = yf.Ticker(ticker)
            # 獲取過去 5 天的資料以計算漲跌
            hist = tkr.history(period="5d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                pct_change = (current_price - prev_price) / prev_price * 100
                data[ticker] = {
                    'price': float(current_price),
                    'pct_change': float(pct_change)
                }
            elif len(hist) == 1:
                current_price = hist['Close'].iloc[-1]
                data[ticker] = {
                    'price': float(current_price),
                    'pct_change': 0.0
                }
            else:
                data[ticker] = {'price': None, 'pct_change': None}
        except Exception:
            data[ticker] = {'price': None, 'pct_change': None}
    return data

@st.cache_data(ttl=300)
def fetch_historical_data(ticker, period):
    try:
        data = yf.Ticker(ticker).history(period=period)
        return data
    except:
        return pd.DataFrame()

# ==========================================
# 3. 側邊欄與標題佈局
# ==========================================

# 側邊欄：設定區塊
with st.sidebar:
    st.title("⚙️ 儀表板設定")
    st.markdown("---")
    
    color_convention = st.radio(
        "📈 漲跌顏色標示習慣",
        options=["美股習慣 (綠漲紅跌)", "台股習慣 (紅漲綠跌)"],
        index=0,
        help="選擇您習慣的漲跌幅顏色視覺"
    )
    
    st.markdown("---")
    st.markdown("""
    **💡 資料來源:** [Yahoo Finance](https://finance.yahoo.com/)  
    **⏱️ 更新頻率:** 即時 (API 延遲或由快取控制約5分鐘)
    """)

# 設定 delta 顏色行為 (Streamlit metric)
if "美股" in color_convention:
    delta_color = "normal"  # normal: positive is green, negative is red
else:
    delta_color = "inverse" # inverse: positive is red, negative is green

# 標題區
st.title("🌎 全球經濟與金融指標儀表板")
st.markdown("即時追蹤全球重要指數、恐慌情緒與原物料價格")
st.markdown("---")

# ==========================================
# 4. 頂部：指標卡片區 (按主題分類視覺化)
# ==========================================
st.subheader("📊 今日市場快照")

# 獲取最新報價
latest_data = fetch_latest_data(ticker_list)

# 依照 config 中的主題分類依序渲染卡片
cols_per_row = 4
for category, items in indicators_dict.items():
    st.markdown(f"**▍ {category}**")
    category_tickers = [item['ticker'] for item in items]
    
    for i in range(0, len(category_tickers), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(category_tickers):
                ticker = category_tickers[i + j]
                col = cols[j]
                item_data = latest_data.get(ticker)
                name = ticker_to_name.get(ticker, ticker)
                
                if item_data is not None and item_data['price'] is not None:
                    # 依據數值範圍優化報價顯示 (例如虛擬貨幣拿掉小數點，匯率保留到四位)
                    price = item_data['price']
                    if 'JPY=X' in ticker:
                        price_str = f"{price:,.4f}"
                    elif price > 10000:
                        price_str = f"{price:,.0f}"
                    else:
                        price_str = f"{price:,.2f}"
                        
                    # 顯示格式
                    col.metric(
                        label=name,
                        value=price_str,
                        delta=f"{item_data['pct_change']:+.2f}%",
                        delta_color=delta_color
                    )
                else:
                    col.metric(label=name, value="N/A", delta="N/A")
    st.markdown("<br>", unsafe_allow_html=True) # 分類之間留空隙

st.markdown("---")

# ==========================================
# 5. 主體：互動式折線圖區
# ==========================================
st.subheader("📈 歷史走勢與技術線圖")

# 控制區：二層下拉選單切換主題與指標
ctrl_col1, ctrl_col2, ctrl_col3, _ = st.columns([1.5, 2, 1.5, 3])

with ctrl_col1:
    # 第一層：選擇主題
    default_cat = config.get('default_category', list(indicators_dict.keys())[0])
    selected_category = st.selectbox(
        "一、選擇主題：",
        options=list(indicators_dict.keys()),
        index=list(indicators_dict.keys()).index(default_cat)
    )

with ctrl_col2:
    # 第二層：選擇指標
    cat_items = indicators_dict[selected_category]
    cat_names = [item['name'] for item in cat_items]
    
    # 若該分類中有 config 的預設指標，則選中，否則選第一個
    default_idx = 0
    for idx, item in enumerate(cat_items):
        if item['ticker'] == config.get('default_indicator'):
            default_idx = idx
            
    selected_name = st.selectbox(
        "二、選擇標的：",
        options=cat_names,
        index=default_idx
    )
    selected_ticker = next(item['ticker'] for item in cat_items if item['name'] == selected_name)

with ctrl_col3:
    # 第三層：選擇時間範圍
    selected_timeframe_name = st.selectbox(
        "三、時間區間：",
        options=list(timeframes.keys()),
        index=1 # 預設改為1年(因為短維度已被刪除)
    )
    selected_period = timeframes[selected_timeframe_name]

# 繪製選擇的圖表
hist_data = fetch_historical_data(selected_ticker, selected_period)

if not hist_data.empty:
    hist_data.reset_index(inplace=True)
    
    # 判斷日期欄位名稱 (yfinance 針對不同 period 可能回傳 Date 或 Datetime)
    date_col = 'Datetime' if 'Datetime' in hist_data.columns else 'Date'
    
    # 決定走勢線與 K 線的顏色 (根據習慣)
    # 美股: 綠漲紅跌; 台股: 紅漲綠跌
    inc_color = '#00CC96' if "美股" in color_convention else '#EF553B' # 上漲顏色
    dec_color = '#EF553B' if "美股" in color_convention else '#00CC96' # 下跌顏色
    line_color = inc_color # 預設折線圖走勢使用上漲色
    
    # 讓使用者切換圖表模式 (新增 st.radio 在圖表上方)
    chart_type = st.radio(
        "圖表類型：", 
        ["📉 預設折線圖 (加附成交量)", "🕯️ 專業 K 線圖 (加附成交量)"], 
        horizontal=True
    )
    
    # 將時間轉為字串，強制 Plotly 視為類別變數 (Categorical Axis)，
    # 這樣可以 100% 完美剔除所有週末、國定假日與非交易時段產生的圖表空白斷點！
    # （由於已無短時分(5d, 1mo)需求，統一格式化至日期即可）
    x_labels = hist_data[date_col].dt.strftime('%Y-%m-%d')
        
    # 建立子圖表 (2列1行：上方價格 70%, 下方成交量 30%)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.7, 0.3]
    )
    
    # 根據選擇渲染上方主要圖表
    if "折線圖" in chart_type:
        fig.add_trace(go.Scatter(
            x=x_labels, y=hist_data['Close'],
            mode='lines',
            line=dict(color=line_color, width=2),
            name='收盤價'
        ), row=1, col=1)
    else:
        fig.add_trace(go.Candlestick(
            x=x_labels,
            open=hist_data['Open'], high=hist_data['High'],
            low=hist_data['Low'], close=hist_data['Close'],
            increasing_line_color=inc_color, decreasing_line_color=dec_color,
            name='K線'
        ), row=1, col=1)
        
    # 渲染下方成交量直狀圖
    # 成交量顏色：如果收盤 >= 開盤視為上漲 (使用 inc_color)，否則下殺 (dec_color)
    volume_colors = [inc_color if row['Close'] >= row['Open'] else dec_color for _, row in hist_data.iterrows()]
    
    fig.add_trace(go.Bar(
        x=x_labels, y=hist_data['Volume'],
        marker_color=volume_colors,
        opacity=0.8,
        name='成交量'
    ), row=2, col=1)

    # 統一排版與深色模式優化支援響應式 (RWD)
    fig.update_layout(
        title=f"{selected_name} - {selected_timeframe_name} 行情圖",
        template="plotly_dark",
        hovermode="x unified",
        # 將上方間距 (t) 推大到 100，預留給事件文字標籤浮空顯示的空間
        margin=dict(l=20, r=20, t=100, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        # 隱藏自帶的 K 線下方時間軸滑塊，避免與成交量圖重疊
        xaxis_rangeslider_visible=False 
    )
    
    # 設定 X 軸為分類型態並限制標籤數量 (避免文字擠成一團)
    fig.update_xaxes(type='category', nticks=12, row=1, col=1)
    fig.update_xaxes(type='category', nticks=12, row=2, col=1)
    
    # 更新 Y 軸兩圖的標題
    fig.update_yaxes(title_text="價格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    
    # 加入重大歷史事件陰影 (配置驅動)
    if 'events' in globals():
        for event_idx, event in enumerate(events):
            try:
                # 統一移除時區資訊，單純比較日期大小以防報錯
                event_start = pd.to_datetime(event['start']).tz_localize(None)
                event_end = pd.to_datetime(event['end']).tz_localize(None)
                naive_dates = hist_data[date_col].dt.tz_localize(None)
                
                # 尋找存在於圖表範圍內的事件區間
                mask = (naive_dates >= event_start) & (naive_dates <= event_end)
                if mask.any():
                    # 抓取有實體交易資料的真實第一天與最後一天
                    valid_indices = mask[mask].index
                    start_idx = valid_indices[0]
                    end_idx = valid_indices[-1]
                    
                    x0_str = x_labels.loc[start_idx]
                    
                    # 無論單日或多天，皆使用數值位移 (index - 0.5 到 index + 0.5) 
                    # 這樣可以讓單一天數也能夠撐開成包含完整一天柱子寬度的「塊狀陰影」，
                    # 且不觸發 Plotly 類別軸對於字串繪製的底層 Bug。
                    shadow_color = event.get('color', 'rgba(255,0,0,0.2)')
                    
                    fig.add_vrect(
                        x0=start_idx - 0.5, x1=end_idx + 0.5,
                        fillcolor=shadow_color,
                        opacity=1, layer="below", line_width=0,
                        row="all", col=1 # 貫穿上下兩圖
                    )
                    
                    # 計算 Y 軸標籤的垂直高度 (超過 1.0 代表懸浮在圖表外的上緣空白處)。
                    # 利用取餘數交錯排列 (高低輪替: 1.02 -> 1.09 -> 1.16) 防止三年線圖下多個事件文字重疊。
                    y_offset = 1.02 + (event_idx % 3) * 0.07
                    
                    # 擷取該事件對應的搶眼實心顏色 (字體與陰影同色系)
                    text_color = shadow_color.replace('0.2)', '1)').replace('rgba', 'rgb')
                    
                    # 單獨把事件名稱掛在整張主圖的「上方」 (使用精準出現的第一天 x0_str)
                    fig.add_annotation(
                        x=x0_str,
                        y=y_offset,
                        xref="x1",
                        yref="paper", # 以整張圖表的高度為百分比基準，1.0以上即突出圖表
                        text=event.get('name', ''),
                        showarrow=False,
                        xanchor="left",
                        xshift=0,
                        font=dict(color=text_color, size=13)
                        # 注意：使用 xref/yref="paper" 時，不需額外給定 row/col以免衝突
                    )
            except Exception:
                pass
    
    # 顯示合併後的新圖表
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("無法獲取此指標的歷史資料，或該市場今日未開盤。")
