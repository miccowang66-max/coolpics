"""
app.py — Cool.Pic AI 畫布生成器 (Streamlit 版)
公開部署，任何人皆可使用。
HF Token 由 Streamlit Secrets 管理，使用者無需設定。
"""

import io
import time
import zipfile
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# ── 頁面設定（必須第一個 st 呼叫）─────────────────────────
st.set_page_config(
    page_title="Cool.Pic — AI 畫布生成器",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help":      "https://github.com/miccowang66-max/coolpic",
        "Report a bug":  "https://github.com/miccowang66-max/coolpic/issues",
        "About":         "## Cool.Pic\nAI 驅動的互動式圖像生成器",
    },
)

# ── 自訂 CSS（深色玻璃態主題）───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@600;700;800&display=swap');

/* 全域 */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #07070f;
    color: #f0f0ff;
}

/* 隱藏預設 Streamlit 元素 */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 1rem; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1a 0%, #0a0a15 100%);
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stSidebar"] .stMarkdown p {
    color: #a0a0c0;
    font-size: 0.85rem;
}

/* 按鈕 */
.stButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #9d5cff 100%);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.55rem 1.2rem;
    width: 100%;
    transition: all 0.2s;
    box-shadow: 0 0 20px rgba(124,58,237,0.3);
}
.stButton > button:hover {
    box-shadow: 0 0 36px rgba(124,58,237,0.55);
    transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

/* 下載按鈕 */
.stDownloadButton > button {
    background: rgba(124,58,237,0.15);
    border: 1px solid rgba(124,58,237,0.4);
    color: #b08aff;
    border-radius: 8px;
    font-size: 0.82rem;
    font-weight: 500;
    width: 100%;
    transition: all 0.2s;
}
.stDownloadButton > button:hover {
    background: rgba(124,58,237,0.28);
    border-color: rgba(124,58,237,0.7);
    color: #fff;
}

/* Select / Slider */
.stSelectbox label, .stSlider label, .stTextArea label, .stTextInput label {
    color: #a0a0c0 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}
.stTextArea textarea, .stTextInput input {
    background: rgba(0,0,0,0.35) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 10px !important;
    color: #f0f0ff !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: rgba(124,58,237,0.5) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.15) !important;
}
.stSelectbox div[data-baseweb="select"] > div {
    background: rgba(0,0,0,0.35) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 10px !important;
    color: #f0f0ff !important;
}

/* 圖像卡片 */
.img-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 10px;
    transition: border-color 0.2s, box-shadow 0.2s;
    margin-bottom: 12px;
}
.img-card:hover {
    border-color: rgba(124,58,237,0.35);
    box-shadow: 0 0 24px rgba(124,58,237,0.1);
}

/* 提示詞標籤 */
.prompt-tag {
    display: inline-block;
    background: rgba(124,58,237,0.18);
    border: 1px solid rgba(124,58,237,0.35);
    color: #b08aff;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.72rem;
    margin: 2px;
    cursor: pointer;
}

/* 標題 */
.hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #f0f0ff 0%, #b08aff 60%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 0.3rem;
}
.hero-sub {
    color: #60607a;
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}

/* Info boxes */
.info-box {
    background: rgba(6,182,212,0.08);
    border: 1px solid rgba(6,182,212,0.25);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #67e8f9;
}
.warn-box {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #fbbf24;
}
.success-box {
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #34d399;
}

/* 分隔線 */
hr { border-color: rgba(255,255,255,0.06); }

/* Spinner */
.stSpinner > div { border-top-color: #9d5cff !important; }

/* Metric */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] { color: #b08aff !important; }
[data-testid="stMetricLabel"] { color: #60607a !important; font-size: 0.78rem !important; }

/* Gallery grid */
.gallery-header {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #f0f0ff;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* 快速提示詞按鈕 */
[data-testid="column"] .stButton > button {
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.3);
    color: #b08aff;
    font-size: 0.78rem;
    padding: 0.35rem 0.6rem;
    box-shadow: none;
    font-weight: 500;
}
[data-testid="column"] .stButton > button:hover {
    background: rgba(124,58,237,0.25);
    box-shadow: none;
    transform: none;
}
</style>
""", unsafe_allow_html=True)


# ── HF API 設定 ───────────────────────────────────────────
MODELS = {
    "⚡ FLUX.1-schnell (快速推薦)":   "black-forest-labs/FLUX.1-schnell",
    "🎨 FLUX.1-dev (高品質)":          "black-forest-labs/FLUX.1-dev",
    "🖼 Stable Diffusion XL":          "stabilityai/stable-diffusion-xl-base-1.0",
    "🌙 Stable Diffusion 2.1":         "stabilityai/stable-diffusion-2-1",
    "📸 Realistic Vision V5.1":        "SG161222/Realistic_Vision_V5.1_noVAE",
    "✨ Dreamshaper 8":                "Lykon/dreamshaper-8",
}

PROMPT_SUGGESTIONS = [
    "🌌 宇宙星雲城市",
    "🎋 水墨山水畫",
    "🌃 賽博龐克街道",
    "🐱 貓咪宇航員",
    "🧚 夢幻精靈森林",
    "🤖 機械風機器人",
    "🌅 日落海邊水彩",
    "🏯 古代日本城堡",
    "🔮 魔法圖書館",
    "🚀 未來太空站",
]

HF_API_URL = "https://api-inference.huggingface.co/models"


# ── Session State 初始化 ──────────────────────────────────
def init_state():
    defaults = {
        "gallery":        [],   # list of { image, prompt, model, size, timestamp }
        "generating":     False,
        "total_generated": 0,
        "prompt_input":   "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── HF API 呼叫 ──────────────────────────────────────────
def generate_image_hf(prompt: str, model: str, width: int, height: int,
                       neg_prompt: str, steps: int, guidance: float, seed: int) -> bytes:
    """
    呼叫 Hugging Face Inference API 生成圖像。
    Token 從 Streamlit Secrets 取得，使用者無需輸入。
    """
    token = st.secrets.get("HF_TOKEN", "")
    if not token:
        raise ValueError("❌ 伺服器端尚未設定 HF_TOKEN，請聯絡管理員。")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "Accept":        "image/png,image/jpeg,image/*",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "width":              width,
            "height":             height,
            "num_inference_steps": steps,
            "guidance_scale":     guidance,
            "seed":               seed,
            **({"negative_prompt": neg_prompt} if neg_prompt else {}),
        },
    }

    url = f"{HF_API_URL}/{model}"

    for attempt in range(1, 4):
        resp = requests.post(url, headers=headers, json=payload, timeout=120)

        if resp.ok:
            return resp.content   # raw image bytes

        if resp.status_code == 503:
            try:
                wait = resp.json().get("estimated_time", 25)
            except Exception:
                wait = 25
            wait = min(float(wait), 35)
            st.toast(f"模型預熱中，等待 {wait:.0f}s（第 {attempt} 次）...", icon="⏳")
            time.sleep(wait)
            continue

        # 其他錯誤
        err = f"API 錯誤 {resp.status_code}"
        try:
            err = resp.json().get("error", err)
        except Exception:
            pass
        if resp.status_code == 401:
            err = "API Token 無效，請聯絡管理員。"
        elif resp.status_code == 429:
            err = "請求過於頻繁，請稍後再試。"
        raise RuntimeError(err)

    raise TimeoutError("模型載入逾時，請稍後再試。")


# ════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align:center;padding:12px 0 20px">
      <div style="font-size:3rem;filter:drop-shadow(0 0 16px rgba(124,58,237,0.5))">🎨</div>
      <div style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:800;
                  background:linear-gradient(135deg,#f0f0ff,#b08aff);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text;">Cool.Pic</div>
      <div style="color:#60607a;font-size:0.75rem;letter-spacing:0.06em;text-transform:uppercase">
        AI 畫布生成器
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 提示詞 ──────────────────────────────────────────
    st.markdown("**✍️ 提示詞**")
    prompt = st.text_area(
        "描述你想生成的圖像",
        placeholder="例如：夢幻星空下的古老城堡，水彩風格，高細節，4K...",
        height=110,
        key="prompt_area",
        label_visibility="collapsed",
    )

    # 快速建議按鈕
    st.markdown("<div style='font-size:0.75rem;color:#60607a;margin-bottom:4px'>💡 快速建議</div>",
                unsafe_allow_html=True)
    cols_chips = st.columns(2)
    for i, sug in enumerate(PROMPT_SUGGESTIONS):
        if cols_chips[i % 2].button(sug, key=f"chip_{i}", use_container_width=True):
            st.session_state["prompt_area"] = sug
            st.rerun()

    st.markdown("**🚫 負面提示詞（可選）**")
    neg_prompt = st.text_area(
        "排除的內容",
        placeholder="模糊、低品質、變形、浮水印...",
        height=65,
        label_visibility="collapsed",
    )

    st.divider()

    # ── 模型設定 ─────────────────────────────────────────
    st.markdown("**⚙️ 生成設定**")

    selected_model_label = st.selectbox(
        "AI 模型",
        list(MODELS.keys()),
        index=0,
    )
    selected_model = MODELS[selected_model_label]

    col_w, col_h = st.columns(2)
    with col_w:
        width  = st.select_slider("寬度",  options=[256, 384, 512, 640, 768, 1024], value=512)
    with col_h:
        height = st.select_slider("高度", options=[256, 384, 512, 640, 768, 1024], value=512)

    steps    = st.slider("推理步數",   min_value=1,   max_value=50,  value=20, step=1)
    guidance = st.slider("引導強度",   min_value=1.0, max_value=20.0, value=7.5, step=0.5)

    col_seed, col_rand = st.columns([3, 1])
    with col_seed:
        seed = st.number_input("隨機種子", min_value=0, max_value=2147483647,
                               value=st.session_state.get("seed_val", 42), step=1)
    with col_rand:
        if st.button("🎲", help="隨機種子"):
            import random
            st.session_state["seed_val"] = random.randint(0, 2147483647)
            st.rerun()

    st.divider()

    # ── 生成數量 ─────────────────────────────────────────
    batch = st.select_slider("批次生成數量", options=[1, 2, 4], value=1)

    # ── 生成按鈕 ─────────────────────────────────────────
    generate_clicked = st.button("✨ 生成圖像", use_container_width=True, type="primary")

    st.divider()

    # ── 統計 ─────────────────────────────────────────────
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("本次生成", st.session_state.total_generated)
    col_m2.metric("圖庫數量", len(st.session_state.gallery))

    # ── 清除圖庫 ─────────────────────────────────────────
    if st.button("🗑 清除圖庫", use_container_width=True):
        st.session_state.gallery = []
        st.session_state.total_generated = 0
        st.rerun()

    st.divider()

    # ── 批次下載 ─────────────────────────────────────────
    if st.session_state.gallery:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, item in enumerate(st.session_state.gallery):
                png_bytes = io.BytesIO()
                item["image"].save(png_bytes, format="PNG")
                zf.writestr(
                    f"cool_pic_{i+1:03d}_{item['timestamp']}.png",
                    png_bytes.getvalue()
                )
        st.download_button(
            "📦 下載全部圖像 (ZIP)",
            data=zip_buf.getvalue(),
            file_name=f"cool_pic_gallery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            use_container_width=True,
        )

    # ── 關於 ─────────────────────────────────────────────
    st.markdown("""
    <div style="margin-top:16px;padding:10px 12px;background:rgba(255,255,255,0.03);
                border:1px solid rgba(255,255,255,0.07);border-radius:10px;
                font-size:0.75rem;color:#60607a;line-height:1.7">
        🚀 Powered by <b style="color:#b08aff">Hugging Face</b><br>
        🖼 <a href="https://github.com/miccowang66-max/coolpic"
              style="color:#b08aff;text-decoration:none"
              target="_blank">GitHub: coolpic</a><br>
        ⚡ 免費開放使用，無需帳號
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
#  MAIN CONTENT
# ════════════════════════════════════════════════════════

# 頁面標題
st.markdown("""
<div class="hero-title">🎨 Cool.Pic AI 畫布生成器</div>
<div class="hero-sub">輸入提示詞，AI 即刻為你創作獨一無二的圖像 · 完全免費 · 無需帳號</div>
""", unsafe_allow_html=True)

# ── 生成流程 ─────────────────────────────────────────────
if generate_clicked:
    if not prompt.strip():
        st.markdown('<div class="warn-box">⚠️ 請在左側輸入提示詞！</div>', unsafe_allow_html=True)
    else:
        progress_container = st.empty()
        results_container  = st.empty()

        new_images = []
        has_error  = False

        for b in range(batch):
            current_seed = (seed + b) if batch > 1 else seed
            with st.spinner(f"🎨 AI 創作中{'（批次 ' + str(b+1) + '/' + str(batch) + '）' if batch > 1 else ''}..."):
                try:
                    img_bytes = generate_image_hf(
                        prompt      = prompt.strip(),
                        model       = selected_model,
                        width       = width,
                        height      = height,
                        neg_prompt  = neg_prompt.strip(),
                        steps       = steps,
                        guidance    = guidance,
                        seed        = current_seed,
                    )
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    ts  = datetime.now().strftime("%H%M%S")
                    entry = {
                        "image":     img,
                        "prompt":    prompt.strip(),
                        "neg_prompt": neg_prompt.strip(),
                        "model":     selected_model_label,
                        "size":      f"{width}×{height}",
                        "seed":      current_seed,
                        "timestamp": ts,
                    }
                    new_images.append(entry)
                    st.session_state.gallery.insert(0, entry)
                    st.session_state.total_generated += 1

                except Exception as e:
                    st.markdown(f'<div class="warn-box">❌ 生成失敗：{e}</div>',
                                unsafe_allow_html=True)
                    has_error = True
                    break

        if new_images:
            st.markdown('<div class="success-box">✅ 圖像生成完成！向下滾動查看圖庫。</div>',
                        unsafe_allow_html=True)

            # 立即顯示新圖像
            st.markdown("---")
            st.markdown('<div class="gallery-header">🆕 剛剛生成</div>', unsafe_allow_html=True)
            cols_new = st.columns(min(len(new_images), 4))
            for i, item in enumerate(new_images):
                with cols_new[i % len(cols_new)]:
                    st.image(item["image"], use_container_width=True, caption=item["prompt"][:50])
                    png_buf = io.BytesIO()
                    item["image"].save(png_buf, format="PNG")
                    st.download_button(
                        "⬇️ 下載 PNG",
                        data=png_buf.getvalue(),
                        file_name=f"cool_pic_{item['timestamp']}_seed{item['seed']}.png",
                        mime="image/png",
                        use_container_width=True,
                        key=f"dl_new_{i}",
                    )


# ── 使用說明（當圖庫為空時顯示）────────────────────────────
if not st.session_state.gallery:
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="img-card" style="text-align:center;padding:20px">
          <div style="font-size:2.5rem;margin-bottom:12px">✍️</div>
          <div style="font-weight:600;margin-bottom:6px;color:#f0f0ff">1. 輸入提示詞</div>
          <div style="font-size:0.82rem;color:#60607a">在左側欄輸入你想生成的圖像描述，或點擊快速建議標籤</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="img-card" style="text-align:center;padding:20px">
          <div style="font-size:2.5rem;margin-bottom:12px">⚙️</div>
          <div style="font-weight:600;margin-bottom:6px;color:#f0f0ff">2. 調整設定</div>
          <div style="font-size:0.82rem;color:#60607a">選擇 AI 模型、圖像尺寸、推理步數等參數</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="img-card" style="text-align:center;padding:20px">
          <div style="font-size:2.5rem;margin-bottom:12px">✨</div>
          <div style="font-weight:600;margin-bottom:6px;color:#f0f0ff">3. 生成 & 下載</div>
          <div style="font-size:0.82rem;color:#60607a">點擊生成按鈕，圖像出現後可立即下載 PNG</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box" style="margin-top:12px;text-align:center">
        ⚡ 完全免費 · 無需帳號 · AI 驅動 · Powered by Hugging Face
    </div>
    """, unsafe_allow_html=True)


# ── 圖庫展示 ─────────────────────────────────────────────
if st.session_state.gallery:
    st.markdown("---")
    col_gal_h, col_gal_s = st.columns([3, 1])
    with col_gal_h:
        st.markdown(f'<div class="gallery-header">📚 圖庫（{len(st.session_state.gallery)} 張）</div>',
                    unsafe_allow_html=True)
    with col_gal_s:
        grid_cols = st.select_slider("每行顯示", options=[2, 3, 4], value=3, label_visibility="collapsed")

    cols = st.columns(grid_cols)
    for idx, item in enumerate(st.session_state.gallery):
        with cols[idx % grid_cols]:
            st.markdown('<div class="img-card">', unsafe_allow_html=True)
            st.image(item["image"], use_container_width=True)

            # 提示詞（截斷）
            st.markdown(
                f'<div style="font-size:0.75rem;color:#a0a0c0;margin:4px 0 2px;'
                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
                f'max-width:100%" title="{item["prompt"]}">'
                f'🖊 {item["prompt"][:40]}{"…" if len(item["prompt"])>40 else ""}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:0.68rem;color:#60607a">📐 {item["size"]} · 🎲 {item["seed"]}</div>',
                unsafe_allow_html=True,
            )

            png_buf = io.BytesIO()
            item["image"].save(png_buf, format="PNG")
            st.download_button(
                "⬇️ 下載",
                data=png_buf.getvalue(),
                file_name=f"cool_pic_{item['timestamp']}_seed{item['seed']}.png",
                mime="image/png",
                use_container_width=True,
                key=f"dl_gallery_{idx}_{item['timestamp']}",
            )
            st.markdown('</div>', unsafe_allow_html=True)
