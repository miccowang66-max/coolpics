# Cool.Pic — 技術白皮書

## 概述

Cool.Pic 是一個 AI 驅動的互動式圖像生成平台，使用者輸入文字提示詞並選擇風格後，系統透過 Hugging Face Inference API 生成高品質圖像，並在 Fabric.js 互動畫布上展示，支援拖曳、縮放、圖層管理與匯出。

## 架構設計

### 雙平台策略

| 平台 | 類型 | API 呼叫位置 | Token 來源 |
|------|------|-------------|-----------|
| Streamlit App | 伺服器端渲染 + 嵌入畫布 | Python 後端 | Streamlit Secrets |
| GitHub Pages | 純靜態前端 | 瀏覽器 JavaScript | localStorage |

### Streamlit App 架構

```
┌─────────────────────────────────────────────┐
│                 Streamlit App                │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Sidebar     │  │   Main Content        │ │
│  │              │  │                      │ │
│  │ ✍️ 提示詞輸入  │  │  <iframe>             │ │
│  │ 🎨 模型選擇   │  │  ┌──────────────────┐ │ │
│  │ ⚙️ 參數設定   │  │  │ Fabric.js Canvas │ │ │
│  │ ✨ 生成按鈕   │  │  │  - 拖曳/縮放       │ │ │
│  │              │  │  │  - 圖層管理        │ │ │
│  │              │  │  │  - PNG/JPG 匯出    │ │ │
│  └──────────────┘  │  └──────────────────┘ │ │
│                    │  ┌──────────────────┐ │ │
│                    │  │ Gallery Strip    │ │ │
│                    │  └──────────────────┘ │ │
│                    └──────────────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │ 🔧 除錯面板 (Debug Log)                  │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### 資料流

```
使用者輸入提示詞
       │
       ▼
 Streamlit Sidebar (UI 元件)
       │
       ▼
 點擊「✨ 生成圖像」
       │
       ▼
 Python call_hf_api() ────► Hugging Face Inference API
       │                           │
       │                    ┌──────┴──────┐
       │                    │  DNS 備援機制  │
       │                    │ 3 組端點自動切換 │
       │                    └──────┬──────┘
       │                           │
       ▼                           ▼
 接收 PNG bytes            api-inference.huggingface.co
       │                   router.huggingface.co
       ▼                   api.huggingface.co
 Base64 編碼
       │
       ▼
 注入 HTML Component
       │
       ▼
 Fabric.js Canvas 渲染
```

## 核心技術

### 1. 伺服器端 API 呼叫

API 呼叫在 Python 後端執行，解決瀏覽器 CORS 限制：

```python
def call_hf_api(prompt, model_id, width, height, neg_prompt, steps, guidance, seed):
    # 遍歷 3 組 API 端點，任一成功即返回
    for base_url in HF_API_URLS:
        try:
            resp = requests.post(url, headers=headers, json=payload)
            if resp.ok:
                return resp.content
        except (ConnectionError, Timeout) as e:
            continue  # DNS/網路失敗 → 自動切換下一個端點
```

### 2. 互動畫布

使用 Fabric.js 實現完整互動功能：

| 功能 | 實作 |
|------|------|
| 拖曳 | `canvas.setActiveObject()` + Fabric.js 內建拖曳 |
| 縮放 | `canvas.zoomToPoint()` + 滑鼠滾輪事件 |
| 旋轉 | Fabric.js 控制點旋轉 |
| 圖層 | `bringToFront()` / `sendToBack()` |
| 匯出 | `canvas.toDataURL()` → PNG / JPEG 下載 |
| 複製 | `object.clone()` |
| 翻轉 | `object.set('flipX' / 'flipY')` |

### 3. 動態 Widget Key

Streamlit 1.55+ 禁止直接設定 Widget Session State，使用動態 Key 解決：

```python
# 使用計數器建立新 Widget，避免 Session State 衝突
prompt = st.text_area(
    value=st.session_state["_prompt_val"],
    key=f"prompt_input_{st.session_state['_ta_key']}"
)

# 建議按鈕 → 更新值 + 遞增計數器 + 重新渲染
st.session_state["_prompt_val"] = sug
st.session_state["_ta_key"] += 1
st.rerun()
```

### 4. DNS 備援機制

Streamlit Cloud 可能無法解析特定 HuggingFace 域名，因此實作 3 組端點自動切換：

```
1. api-inference.huggingface.co  ← 標準端點
2. router.huggingface.co         ← 新版路由端點
3. api.huggingface.co            ← 備用端點
```

## 支援模型

| 模型名稱 | Model ID | 特色 |
|---------|----------|------|
| FLUX.1-schnell | black-forest-labs/FLUX.1-schnell | 快速生成 (推薦) |
| FLUX.1-dev | black-forest-labs/FLUX.1-dev | 高品質輸出 |
| Stable Diffusion XL | stabilityai/stable-diffusion-xl-base-1.0 | 經典 SDXL |
| Stable Diffusion 2.1 | stabilityai/stable-diffusion-2-1 | SD 2.1 |
| Realistic Vision V5.1 | SG161222/Realistic_Vision_V5.1_noVAE | 寫實風格 |
| Dreamshaper 8 | Lykon/dreamshaper-8 | 藝術風格 |

## 生成參數

| 參數 | 範圍 | 預設 | 說明 |
|------|------|------|------|
| width / height | 256–1024 px | 512 | 輸出解析度 |
| num_inference_steps | 1–50 | 20 | 推理步數 (越高越精細) |
| guidance_scale | 1.0–20.0 | 7.5 | 引導強度 (越高越貼近提示) |
| seed | 0–2147483647 | 42 | 隨機種子 (相同種子 = 相同結果) |
| batch | 1–4 | 1 | 單次生成數量 |

## 安全性

- **Token 管理**: HF_TOKEN 儲存於 Streamlit Secrets，不提交至 GitHub
- **GitHub Push Protection**: 自動偵測並阻擋 Token 洩漏
- **`.gitignore`**: `.env`、`.streamlit/secrets.toml` 排除於版本控制
- **伺服器端 API 呼叫**: Token 僅存在後端，不暴露給瀏覽器

## 部署

### Streamlit Cloud

```
GitHub Push → Streamlit Cloud Auto-Deploy
                          │
                    ┌─────┴─────┐
                    │ app.py    │ ← 主程式
                    │ reqs.txt  │ ← 依賴
                    │ Secrets   │ ← HF_TOKEN
                    └───────────┘
```

### GitHub Pages

```
GitHub Push → GitHub Actions → deploy.yml
                                    │
                              ┌─────┴─────┐
                              │ index.html │
                              │ css/       │
                              │ js/        │
                              └───────────┘
```

---

*最後更新: 2026-06-12*
