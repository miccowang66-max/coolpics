# 🎨 Cool.Pic — AI 畫布生成器

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-7c3aed?style=flat-square&logo=github)](https://miccowang66max.github.io/coolpics/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Live-ff4b4b?style=flat-square&logo=streamlit)](https://cool-pic.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> 輸入文字提示詞，選擇風格，透過 Hugging Face AI 在互動畫布上生成精美圖像。
> **完全免費 · 無需帳號**

---

## 🌐 線上使用

| 平台 | URL | 說明 |
|------|-----|------|
| **Streamlit App** (推薦) | [cool-pic.streamlit.app](https://cool-pic.streamlit.app) | 完全開放，伺服器端生成，無需 Token |
| **靜態網頁** | [miccowang66max.github.io/coolpics](https://miccowang66max.github.io/coolpics/) | GitHub Pages，需自行輸入 HF Token |

---

## ✨ 功能特色

### Streamlit App
- 🖼 **互動畫布** — 基於 Fabric.js，支援拖曳、縮放、旋轉、匯出 PNG/JPG
- 📚 **圖層管理** — 前置 / 後置 / 複製 / 刪除
- 🎨 **多款模型** — FLUX.1-schnell、FLUX.1-dev、SDXL、Dreamshaper 等
- 📦 **批次生成** — 一次最多 4 張
- 🖼 **圖片預覽列** — 點擊縮圖即載入畫布
- 🎲 **隨機種子** — 可控或隨機
- 🔧 **除錯面板** — 顯示 API 呼叫狀態

### 靜態網頁版 (GitHub Pages)
- 🖼 **互動畫布** — Fabric.js 拖曳、縮放、旋轉
- 📚 **圖層管理**
- 💾 **匯出** — PNG / JPG
- 🕘 **生成歷史** — localStorage 保存
- ⌨️ **快捷鍵** — Delete、Ctrl+D、[ ] 圖層等

---

## 🚀 部署說明

### Streamlit Cloud 部署

1. 前往 [share.streamlit.io](https://share.streamlit.io)
2. 連結 GitHub repo：`miccowang66-max/coolpics`
3. Main file: `app.py`
4. **設定 Secrets**（必要！）：
   ```
   Settings → Secrets → 填入：

   HF_TOKEN = "hf_你的真實Token"
   ```
5. 點擊 Deploy

### GitHub Pages 自動部署

推送至 `main` branch 後，GitHub Actions 自動部署。

---

## 🔧 本地開發

### Streamlit 版
```bash
pip install -r requirements.txt
cp .env.example .env
# 編輯 .env，填入真實 HF_TOKEN

# 設定 secrets（本地開發用）
# 建立 .streamlit/secrets.toml：
#   HF_TOKEN = "hf_你的Token"

streamlit run app.py
```

### 靜態網頁
```bash
open index.html
```
> 需在 UI 的「🔑 HF Token」區段輸入 Token（儲存於 localStorage）

---

## 🔑 取得 Hugging Face Token

1. [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. 點擊「New token」，類型選 **Read**
3. 複製 Token（格式：`hf_xxxxxxxx...`）

> ⚠️ 請勿將 Token 提交至 GitHub！`.env` 和 `.streamlit/secrets.toml` 已加入 `.gitignore`

---

## 📁 專案結構

```
coolpics/
├── app.py                      # Streamlit 應用程式（伺服器端生成 + 互動畫布）
├── index.html                  # 靜態網頁主頁
├── css/
│   └── style.css               # Glassmorphism 深色主題
├── js/
│   ├── api.js                  # HF API 封裝（靜態版用）
│   ├── canvas.js               # Fabric.js 畫布引擎
│   └── app.js                  # 主程式邏輯（靜態版用）
├── requirements.txt            # Python 依賴
├── .streamlit/
│   ├── config.toml             # Streamlit 主題設定
│   └── secrets.toml            # 🔒 API Token（已 gitignore）
├── .env                        # 🔒 本地環境變數（已 gitignore）
├── .env.example
└── .github/workflows/          # CI/CD
```

---

## 🛠 技術棧

| 技術 | 用途 |
|------|------|
| [Streamlit](https://streamlit.io) | Python Web App 框架 |
| [Fabric.js](http://fabricjs.com) | 互動式 HTML5 畫布 |
| [Hugging Face Inference API](https://huggingface.co/docs/api-inference) | AI 圖像生成 |
| [Pillow](https://pillow.readthedocs.io) | 圖像處理 |
| [Requests](https://requests.readthedocs.io) | HTTP API 呼叫 |

---

## 📄 License

MIT © [miccowang66max](https://github.com/miccowang66max)
