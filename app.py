"""
app.py — Cool.Pic AI 畫布生成器 (Streamlit 版)
嵌入完整互動畫布（Fabric.js），支援拖曳、縮放、圖層、匯出。
HF Token 由 Streamlit Secrets 管理，使用者無需設定。
"""

import json
import streamlit as st
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ── 頁面設定 ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Cool.Pic — AI 畫布生成器",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help":      "https://github.com/miccowang66-max/coolpic",
        "Report a bug":  "https://github.com/miccowang66-max/coolpic/issues",
        "About":         "## Cool.Pic\nAI 驅動的互動式圖像生成器",
    },
)

# ── 隱藏 Streamlit 預設 UI，讓畫布全屏 ──────────────────────
st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    .stApp { padding: 0 !important; }
    iframe { border: none; }
</style>
""", unsafe_allow_html=True)

# ── 讀取 HF Token ───────────────────────────────────────────
hf_token = st.secrets.get("HF_TOKEN", "")

# ── 讀取靜態資源 ───────────────────────────────────────────
try:
    css_content = (HERE / "css" / "style.css").read_text(encoding="utf-8")
except FileNotFoundError:
    css_content = ""

try:
    index_html = (HERE / "index.html").read_text(encoding="utf-8")
except FileNotFoundError:
    index_html = ""

try:
    api_js = (HERE / "js" / "api.js").read_text(encoding="utf-8")
except FileNotFoundError:
    api_js = ""

try:
    canvas_js = (HERE / "js" / "canvas.js").read_text(encoding="utf-8")
except FileNotFoundError:
    canvas_js = ""

try:
    app_js = (HERE / "js" / "app.js").read_text(encoding="utf-8")
except FileNotFoundError:
    app_js = ""

# ── 修改 api.js：支援 Streamlit Secrets 自動注入 Token ──────
# 使用者手動輸入的 Token (localStorage) 優先，伺服器 Token 為備用
api_js = api_js.replace(
    "return localStorage.getItem('hf_token') || '';",
    "var t = localStorage.getItem('hf_token'); if (t) return t; return window.STREAMLIT_HF_TOKEN || '';"
)

# ── 組裝完整 HTML ──────────────────────────────────────────
html = index_html

# 行內 CSS
if '<link rel="stylesheet" href="css/style.css">' in html:
    html = html.replace(
        '<link rel="stylesheet" href="css/style.css">',
        f'<style>\n{css_content}\n</style>'
    )
else:
    html = html.replace('</head>', f'<style>\n{css_content}\n</style>\n</head>')

# Token 注入 + JS
token_script = f'<script>window.STREAMLIT_HF_TOKEN = {json.dumps(hf_token)};</script>'

html = html.replace(
    '<script src="js/api.js"></script>',
    f'{token_script}\n<script>\n{api_js}\n</script>'
)
html = html.replace(
    '<script src="js/canvas.js"></script>',
    f'<script>\n{canvas_js}\n</script>'
)
html = html.replace(
    '<script src="js/app.js"></script>',
    f'<script>\n{app_js}\n</script>'
)

# ── 渲染完整互動 App ───────────────────────────────────────
st.components.v1.html(html, height=880, scrolling=True)
