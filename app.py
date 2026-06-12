"""
app.py — Cool.Pic AI 畫布生成器 (Streamlit 版)
伺服器端呼叫 HF API 生成圖像，嵌入互動畫布顯示。
HF Token 由 Streamlit Secrets 管理，使用者無需設定。
"""

import io
import json
import time
import base64
import requests
import streamlit as st
from pathlib import Path
from PIL import Image
from datetime import datetime

HERE = Path(__file__).resolve().parent

# ── 頁面設定 ─────────────────────────────────────────────────
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

# ── 隱藏 Streamlit 預設 UI 按鈕，讓畫布全屏 ──────────────────
st.markdown("""
<style>
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }
    .block-container { padding: 1rem 1rem 0 1rem !important; max-width: 100% !important; }
    iframe { border: none; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ── HF Token / 模型設定 ──────────────────────────────────────
hf_token = st.secrets.get("HF_TOKEN", "")

MODELS = {
    "FLUX.1-schnell (快速)":          "black-forest-labs/FLUX.1-schnell",
    "FLUX.1-dev (高品質)":             "black-forest-labs/FLUX.1-dev",
    "Stable Diffusion XL":             "stabilityai/stable-diffusion-xl-base-1.0",
    "Stable Diffusion 2.1":            "stabilityai/stable-diffusion-2-1",
    "Realistic Vision V5.1":           "SG161222/Realistic_Vision_V5.1_noVAE",
    "Dreamshaper 8":                   "Lykon/dreamshaper-8",
}

HF_API_URL = "https://api-inference.huggingface.co/models"

# ── Session ──────────────────────────────────────────────────
for k, v in {"gallery": [], "total": 0, "_ta_key": 0, "_prompt_val": "", "_seed_key": 0, "_seed_val": 42}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def call_hf_api(prompt, model_id, width, height, neg_prompt, steps, guidance, seed):
    """伺服器端呼叫 HF Inference API，回傳 raw PNG bytes"""
    if not hf_token:
        raise ValueError("未設定 HF_TOKEN，請至 Streamlit Cloud Settings → Secrets 設定")

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type":  "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": width, "height": height,
            "num_inference_steps": steps,
            "guidance_scale": guidance,
            "seed": seed,
            **({"negative_prompt": neg_prompt} if neg_prompt else {}),
        },
    }
    url = f"{HF_API_URL}/{model_id}"

    for attempt in range(1, 4):
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.ok:
            return resp.content
        if resp.status_code == 503:
            wait = min(float(resp.json().get("estimated_time", 25)), 35)
            st.toast(f"模型預熱中，等待 {wait:.0f}s…", icon="⏳")
            time.sleep(wait)
            continue
        err = f"API 錯誤 {resp.status_code}"
        try:
            err = resp.json().get("error", err)
        except Exception:
            pass
        if resp.status_code == 401:
            err = "API Token 無效"
        elif resp.status_code == 429:
            err = "請求過於頻繁，請稍後再試"
        raise RuntimeError(err)
    raise TimeoutError("模型載入逾時")


# ═══════════════ SIDEBAR ═══════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:12px 0 20px">
      <div style="font-size:2.5rem;filter:drop-shadow(0 0 12px rgba(124,58,237,0.5))">🎨</div>
      <div style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:800;
                  background:linear-gradient(135deg,#f0f0ff,#b08aff);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  background-clip:text;">Cool.Pic</div>
      <div style="color:#60607a;font-size:0.7rem;letter-spacing:0.06em">AI 畫布生成器</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**✍️ 提示詞**")
    prompt = st.text_area(
        "描述你想生成的圖像",
        value=st.session_state["_prompt_val"],
        key=f"prompt_input_{st.session_state['_ta_key']}",
        placeholder="例如：夢幻星空下的古老城堡，水彩風格，高細節，4K...",
        height=100,
        label_visibility="collapsed",
    )

    # 快速建議
    SUGGESTIONS = ["宇宙星雲城市", "水墨山水畫", "賽博龐克街道", "貓咪宇航員", "夢幻精靈森林",
                   "機械風機器人", "日落海邊水彩", "古代日本城堡", "魔法圖書館", "未來太空站"]
    cols = st.columns(2)
    for i, sug in enumerate(SUGGESTIONS):
        if cols[i % 2].button(sug, key=f"sug_{i}", use_container_width=True):
            st.session_state["_prompt_val"] = sug
            st.session_state["_ta_key"] += 1
            st.rerun()

    st.markdown("**🚫 負面提示詞（可選）**")
    neg_prompt = st.text_area("排除", key="neg_input", placeholder="模糊、低品質、變形...",
                              height=65, label_visibility="collapsed")

    st.divider()
    st.markdown("**⚙️ 生成設定**")
    selected_model_label = st.selectbox("AI 模型", list(MODELS.keys()), index=0)
    selected_model = MODELS[selected_model_label]

    cw, ch = st.columns(2)
    with cw:
        width  = st.select_slider("寬度",  options=[256, 384, 512, 640, 768, 1024], value=512)
    with ch:
        height = st.select_slider("高度", options=[256, 384, 512, 640, 768, 1024], value=512)

    steps    = st.slider("推理步數", 1, 50, 20)
    guidance = st.slider("引導強度", 1.0, 20.0, 7.5, 0.5)

    cseed, cbtn = st.columns([3, 1])
    with cseed:
        seed = st.number_input("隨機種子", 0, 2147483647,
                               value=st.session_state["_seed_val"],
                               key=f"seed_input_{st.session_state['_seed_key']}")
    with cbtn:
        if st.button("🎲", help="隨機種子"):
            import random
            st.session_state["_seed_val"] = random.randint(0, 2147483647)
            st.session_state["_seed_key"] += 1
            st.rerun()

    batch = st.select_slider("批次生成", options=[1, 2, 4], value=1)
    generate_clicked = st.button("✨ 生成圖像", use_container_width=True, type="primary")

    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("本次生成", st.session_state.total)
    c2.metric("圖庫數量", len(st.session_state.gallery))

    if st.button("🗑 清除圖庫", use_container_width=True):
        st.session_state.gallery = []
        st.session_state.total = 0
        st.rerun()


# ═══════════════ MAIN ═══════════════

# ── 伺服器端生成 ─────────────────────────────────────────
if generate_clicked:
    if not prompt.strip():
        st.warning("請在左側輸入提示詞！")
    else:
        new_images = []
        for b in range(batch):
            current_seed = (seed + b) if batch > 1 else seed
            label = f"🎨 AI 創作中{' (' + str(b+1) + '/' + str(batch) + ')' if batch > 1 else ''}..."
            with st.spinner(label):
                try:
                    img_bytes = call_hf_api(
                        prompt=prompt.strip(), model_id=selected_model,
                        width=width, height=height, neg_prompt=neg_prompt.strip(),
                        steps=steps, guidance=guidance, seed=current_seed,
                    )
                    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    ts = datetime.now().strftime("%H%M%S")
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    entry = {
                        "b64": base64.b64encode(buf.getvalue()).decode(),
                        "prompt": prompt.strip(),
                        "size": f"{width}×{height}",
                        "seed": current_seed,
                        "ts": ts,
                    }
                    new_images.append(entry)
                    st.session_state.gallery.insert(0, entry)
                    st.session_state.total += 1
                except Exception as e:
                    st.error(f"生成失敗：{e}")
                    break

        if new_images:
            st.success(f"✅ 生成完成！{len(new_images)} 張新圖像已加入下方畫布")

# ── 建構嵌入 HTML (互動畫布 + 已生成圖像) ──────────────────
try:
    css_content = (HERE / "css" / "style.css").read_text(encoding="utf-8")
except FileNotFoundError:
    css_content = ""

try:
    canvas_js = (HERE / "js" / "canvas.js").read_text(encoding="utf-8")
except FileNotFoundError:
    canvas_js = ""

gallery_json = json.dumps(st.session_state.gallery, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
<style>
/* ── Design Tokens ──────────────────────────────── */
:root {{
    --bg-base: #07070f; --bg-surface: #0d0d1a; --bg-elevated: #12122a;
    --glass-bg: rgba(255,255,255,0.04); --glass-border: rgba(255,255,255,0.08);
    --accent-primary: #7c3aed; --accent-glow: #9d5cff;
    --text-primary: #f0f0ff; --text-secondary: #a0a0c0; --text-muted: #60607a; --text-accent: #b08aff;
    --green: #10b981; --rose: #f43f5e; --amber: #f59e0b;
    --sp-xs: 4px; --sp-sm: 8px; --sp-md: 16px; --sp-lg: 24px;
    --r-sm: 6px; --r-md: 12px; --r-lg: 18px; --r-full: 9999px;
    --shadow-lg: 0 16px 64px rgba(0,0,0,0.6); --shadow-accent: 0 0 32px rgba(124,58,237,0.35);
    --font-body: 'Inter', system-ui, sans-serif; --font-display: 'Outfit', system-ui, sans-serif;
    --toolbar-h: 56px;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 14px; }}
body {{
    font-family: var(--font-body); background: var(--bg-base); color: var(--text-primary);
    min-height: 100vh; overflow: hidden; line-height: 1.5;
}}
body::before {{
    content: ''; position: fixed; inset: 0;
    background-image: linear-gradient(rgba(124,58,237,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(124,58,237,0.03) 1px, transparent 1px);
    background-size: 40px 40px; z-index: 0; pointer-events: none;
}}
#app {{ position: relative; z-index: 1; display: flex; flex-direction: column; height: 100vh; width: 100%; }}
/* ── Toolbar ───────────────────────────────────── */
#toolbar {{
    height: var(--toolbar-h); background: var(--bg-surface);
    border-bottom: 1px solid var(--glass-border); display: flex; align-items: center;
    padding: 0 var(--sp-md); gap: var(--sp-sm); flex-shrink: 0; z-index: 5;
}}
.toolbar-group {{ display: flex; align-items: center; gap: 4px; }}
.toolbar-sep {{ width: 1px; height: 24px; background: var(--glass-border); margin: 0 var(--sp-xs); flex-shrink: 0; }}
.tool-btn {{
    width: 36px; height: 36px; display: flex; align-items: center; justify-content: center;
    background: transparent; border: 1px solid transparent; border-radius: var(--r-sm);
    color: var(--text-secondary); cursor: pointer; font-size: 1rem; transition: all 150ms;
}}
.tool-btn:hover {{ background: rgba(255,255,255,0.07); border-color: var(--glass-border); color: var(--text-primary); }}
.tool-btn.active {{ background: rgba(124,58,237,0.18); border-color: rgba(124,58,237,0.4); color: var(--accent-glow); }}
.toolbar-spacer {{ flex: 1; }}
#canvas-info {{ font-size: 0.75rem; color: var(--text-muted); display: flex; align-items: center; gap: var(--sp-sm); }}
.status-dot {{ width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); }}
.btn-danger {{ background: rgba(244,63,94,0.15) !important; border-color: rgba(244,63,94,0.3) !important; color: var(--rose) !important; }}
.btn-danger:hover {{ background: rgba(244,63,94,0.25) !important; }}
/* ── Canvas Stage ──────────────────────────────── */
#canvas-stage {{
    flex: 1; overflow: auto; display: flex; align-items: center; justify-content: center;
    background: radial-gradient(ellipse at 70% 30%, rgba(124,58,237,0.07) 0%, transparent 55%),
                radial-gradient(ellipse at 30% 80%, rgba(6,182,212,0.05) 0%, transparent 50%), var(--bg-base);
    position: relative;
}}
#canvas-wrapper {{ position: relative; box-shadow: var(--shadow-lg), 0 0 60px rgba(124,58,237,0.15); border-radius: var(--r-md); overflow: hidden; border: 1px solid var(--glass-border); }}
#canvas-wrapper canvas {{ display: block; }}
/* ── Empty State ───────────────────────────────── */
#canvas-empty {{
    position: absolute; inset: 0; display: flex; flex-direction: column;
    align-items: center; justify-content: center; pointer-events: none;
    transition: opacity 280ms; z-index: 2;
}}
#canvas-empty.hidden {{ opacity: 0; }}
.empty-icon {{ font-size: 4rem; margin-bottom: var(--sp-md); filter: drop-shadow(0 0 24px rgba(124,58,237,0.4)); }}
.empty-title {{ font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; color: var(--text-secondary); margin-bottom: var(--sp-xs); }}
.empty-sub {{ font-size: 0.88rem; color: var(--text-muted); text-align: center; }}
/* ── Gallery Strip ─────────────────────────────── */
#gallery-strip {{
    height: 120px; flex-shrink: 0; background: var(--bg-surface);
    border-top: 1px solid var(--glass-border); display: none; align-items: center;
    padding: 0 var(--sp-md); gap: var(--sp-sm); overflow-x: auto; z-index: 5;
}}
#gallery-strip.has-images {{ display: flex; }}
.gallery-thumb {{
    width: 90px; height: 90px; border-radius: var(--r-sm); cursor: pointer;
    border: 2px solid transparent; object-fit: cover; flex-shrink: 0;
    transition: border-color 150ms, transform 150ms;
}}
.gallery-thumb:hover {{ border-color: var(--accent-glow); transform: scale(1.05); }}
.gallery-thumb.active {{ border-color: var(--accent-glow); }}
/* ── Layer Panel ────────────────────────────────── */
#layer-bar {{
    max-height: 200px; overflow-y: auto; background: var(--bg-surface);
    border-top: 1px solid var(--glass-border); padding: var(--sp-sm) var(--sp-md);
    display: none; z-index: 5;
}}
#layer-bar.show {{ display: flex; flex-wrap: wrap; gap: var(--sp-sm); }}
.layer-item {{
    display: flex; align-items: center; gap: 6px; padding: 4px 8px;
    border-radius: var(--r-sm); cursor: pointer; font-size: 0.75rem;
    border: 1px solid transparent; color: var(--text-secondary);
}}
.layer-item:hover {{ background: rgba(255,255,255,0.05); }}
.layer-item.selected {{ background: rgba(124,58,237,0.18); border-color: rgba(124,58,237,0.4); }}
.layer-thumb {{ width: 28px; height: 28px; border-radius: 4px; object-fit: cover; }}
</style>
</head>
<body>
<div id="app">
  <!-- TOOLBAR -->
  <div id="toolbar" role="toolbar">
    <div class="toolbar-group">
      <button class="tool-btn active" data-tool="select" id="tool-select">⬚</button>
      <button class="tool-btn" data-tool="pan" id="tool-pan">✋</button>
    </div>
    <div class="toolbar-sep"></div>
    <div class="toolbar-group">
      <button class="tool-btn" id="tb-duplicate">⧉</button>
      <button class="tool-btn" id="tb-delete">🗑</button>
      <button class="tool-btn" id="tb-flip-h">↔</button>
      <button class="tool-btn" id="tb-flip-v">↕</button>
      <button class="tool-btn" id="tb-rot-l">↺</button>
      <button class="tool-btn" id="tb-rot-r">↻</button>
    </div>
    <div class="toolbar-sep"></div>
    <div class="toolbar-group">
      <button class="tool-btn" id="tb-front">⬆</button>
      <button class="tool-btn" id="tb-back">⬇</button>
    </div>
    <div class="toolbar-sep"></div>
    <div class="toolbar-group">
      <button class="tool-btn" id="tb-zoom-out">－</button>
      <span id="zoom-level" style="font-size:0.78rem;color:var(--text-muted);min-width:44px;text-align:center">100%</span>
      <button class="tool-btn" id="tb-zoom-in">＋</button>
      <button class="tool-btn" id="tb-zoom-reset" style="font-size:0.7rem">1:1</button>
    </div>
    <div class="toolbar-spacer"></div>
    <div class="toolbar-group">
      <button class="tool-btn btn-danger" id="tb-clear" style="width:auto;padding:0 10px;font-size:0.8rem">清除</button>
      <button class="tool-btn" id="tb-export-png" style="width:auto;padding:0 10px;font-size:0.8rem">PNG ↓</button>
      <button class="tool-btn" id="tb-export-jpg" style="width:auto;padding:0 10px;font-size:0.8rem">JPG ↓</button>
    </div>
    <div class="toolbar-sep"></div>
    <div id="canvas-info"><div class="status-dot"></div><span>Cool.Pic</span></div>
  </div>

  <!-- CANVAS STAGE -->
  <div id="canvas-stage">
    <div id="canvas-empty">
      <div class="empty-icon">🎨</div>
      <div class="empty-title">畫布空白</div>
      <div class="empty-sub">在左側 Streamlit 面板輸入提示詞<br>點擊「✨ 生成圖像」開始創作</div>
    </div>
    <div id="canvas-wrapper">
      <canvas id="main-canvas"></canvas>
    </div>
  </div>

  <!-- GALLERY STRIP -->
  <div id="gallery-strip"></div>

  <!-- LAYER BAR -->
  <div id="layer-bar"></div>
</div>

<script>
// ── Pre-loaded gallery images from server ──────────────────
var PRELOADED_GALLERY = {gallery_json};

{canvas_js}

// ── App init ──────────────────────────────────────────────
(function() {{
    var engine = CanvasEngine;
    var canvas = null;

    function init() {{
        try {{
            canvas = engine.init('main-canvas', 1024, 720, renderLayers);
        }} catch(e) {{
            console.error('Canvas init error:', e);
            document.getElementById('canvas-empty').innerHTML = '<div class=\"empty-icon\">⚠️</div><div class=\"empty-title\">畫布載入失敗</div><div class=\"empty-sub\">請重新整理頁面</div>';
            return;
        }}
        setupToolbar();
        setupGallery();
        loadPreloadedImages();
    }}

    function setupToolbar() {{
        var btns = document.querySelectorAll('[data-tool]');
        btns.forEach(function(b) {{
            b.addEventListener('click', function() {{
                btns.forEach(function(x) {{ x.classList.remove('active'); }});
                b.classList.add('active');
                if (b.dataset.tool === 'pan') engine.setPanMode();
                else engine.setSelectMode();
            }});
        }});
        bind('tb-delete', function() {{ engine.deleteSelected(); }});
        bind('tb-duplicate', function() {{ engine.duplicateSelected(); }});
        bind('tb-flip-h', function() {{ engine.flipH(); }});
        bind('tb-flip-v', function() {{ engine.flipV(); }});
        bind('tb-rot-l', function() {{ engine.rotate(-90); }});
        bind('tb-rot-r', function() {{ engine.rotate(90); }});
        bind('tb-front', function() {{ engine.bringToFront(); }});
        bind('tb-back', function() {{ engine.sendToBack(); }});
        bind('tb-zoom-in', function() {{ engine.zoomIn(); updateZoom(); }});
        bind('tb-zoom-out', function() {{ engine.zoomOut(); updateZoom(); }});
        bind('tb-zoom-reset', function() {{ engine.resetZoom(); updateZoom(); }});
        bind('tb-clear', function() {{ engine.clearCanvas(); renderLayers(); updateEmpty(); }});
        bind('tb-export-png', function() {{ engine.exportPNG('cool-pic-' + Date.now() + '.png'); }});
        bind('tb-export-jpg', function() {{ engine.exportJPEG('cool-pic-' + Date.now() + '.jpg'); }});

        canvas.on('mouse:wheel', function(opt) {{
            opt.e.preventDefault();
            var z = canvas.getZoom();
            z *= opt.e.deltaY > 0 ? 0.95 : 1.05;
            z = Math.min(Math.max(z, 0.2), 4);
            canvas.zoomToPoint({{ x: opt.e.offsetX, y: opt.e.offsetY }}, z);
            updateZoom();
        }});
    }}

    function setupGallery() {{
        var strip = document.getElementById('gallery-strip');
        if (PRELOADED_GALLERY.length === 0) return;
        strip.classList.add('has-images');
        PRELOADED_GALLERY.forEach(function(item, i) {{
            var img = document.createElement('img');
            img.src = 'data:image/png;base64,' + item.b64;
            img.className = 'gallery-thumb';
            img.title = item.prompt;
            img.addEventListener('click', function() {{
                addToCanvas(item.b64, item.prompt);
                document.querySelectorAll('.gallery-thumb.active').forEach(function(el) {{ el.classList.remove('active'); }});
                img.classList.add('active');
            }});
            strip.appendChild(img);
        }});
    }}

    function loadPreloadedImages() {{
        if (PRELOADED_GALLERY.length === 0) return;
        var last = PRELOADED_GALLERY[0];
        addToCanvas(last.b64, last.prompt);
        document.querySelector('.gallery-thumb')?.classList.add('active');
    }}

    function addToCanvas(b64, prompt) {{
        var url = 'data:image/png;base64,' + b64;
        engine.addImage(url, prompt).then(function() {{
            updateEmpty();
            renderLayers();
        }}).catch(function(e) {{
            console.error('addImage error:', e);
        }});
    }}

    function renderLayers(layers) {{
        if (!layers) layers = engine.getLayers();
        var bar = document.getElementById('layer-bar');
        bar.innerHTML = '';
        if (layers.length > 0) {{
            bar.classList.add('show');
            layers.forEach(function(layer) {{
                var item = document.createElement('div');
                item.className = 'layer-item' + (layer.isActive ? ' selected' : '');
                item.innerHTML = (layer.thumb ? '<img class="layer-thumb" src="' + layer.thumb + '">' : '<div class="layer-thumb" style="background:var(--bg-elevated)">🖼</div>') + '<span>' + layer.name + '</span>';
                item.addEventListener('click', function() {{ engine.selectObjectByIndex(layer.index); }});
                bar.appendChild(item);
            }});
        }} else {{
            bar.classList.remove('show');
        }}
        updateEmpty();
    }}

    function updateEmpty() {{
        var el = document.getElementById('canvas-empty');
        var count = engine.getObjectCount();
        if (el) el.classList.toggle('hidden', count > 0);
    }}

    function updateZoom() {{
        var el = document.getElementById('zoom-level');
        var z = canvas?.getZoom() || 1;
        if (el) el.textContent = Math.round(z * 100) + '%';
    }}

    function bind(id, fn) {{
        var el = document.getElementById(id);
        if (el) el.addEventListener('click', fn);
    }}

    document.addEventListener('DOMContentLoaded', init);
}})();
</script>
</body>
</html>"""

# ── 渲染互動畫布 ──────────────────────────────────────────
st.components.v1.html(html, height=750, scrolling=True)
