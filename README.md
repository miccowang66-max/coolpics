# 🎨 Cool.Pic — AI 畫布生成器

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-7c3aed?style=flat-square&logo=github)](https://miccowang66max.github.io/cool.pic/)
[![Streamlit App](https://img.shields.io/badge/Streamlit-Live-ff4b4b?style=flat-square&logo=streamlit)](https://cool-pic.streamlit.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

> 輸入文字提示詞，透過 Hugging Face AI 在互動畫布上即時生成精彩圖像。  
> **完全免費 · 無需帳號 · 雙平台部署**

---

## 🌐 線上使用

| 平台 | URL | 說明 |
|------|-----|------|
| **靜態網頁** | [miccowang66max.github.io/cool.pic](https://miccowang66max.github.io/cool.pic/) | GitHub Pages，需輸入自己的 HF Token |
| **Streamlit App** | [cool-pic.streamlit.app](https://cool-pic.streamlit.app) | 完全開放，無需 Token，直接使用 |

---

## ✨ 功能特色

### 靜態網頁版 (GitHub Pages)
- 🖼 **互動畫布** — 基於 Fabric.js，支援拖曳、縮放、旋轉
- 📚 **圖層管理** — 前置 / 後置 / 複製 / 刪除
- 💾 **匯出** — 高解析度 PNG / JPG 下載
- 🕘 **生成歷史** — 本機 localStorage 保存
- 🎨 **多款模型** — FLUX.1、SDXL、Dreamshaper 等
- ⌨️ **快捷鍵** — Delete、Ctrl+D、[ ] 圖層等

### Python 版 (Streamlit)
- 🚀 **免帳號開放使用**
- 📦 **批次生成** — 一次最多 4 張
- 🖼 **圖庫管理** — 網格顯示所有生成圖像
- 📥 **批次下載** — ZIP 打包下載全部圖像
- 🎲 **隨機種子** — 可控制或隨機生成

---

## 🚀 部署說明

### GitHub Pages 自動部署
推送到 `main` branch 後，GitHub Actions 會自動部署至 GitHub Pages。

```bash
git push origin main
```

啟用 GitHub Pages：
1. 前往 `Settings → Pages`
2. Source 選 **GitHub Actions**
3. 等待 Action 完成，URL 即生效

### Streamlit Cloud 部署

1. 前往 [share.streamlit.io](https://share.streamlit.io)
2. 連結此 GitHub repo：`miccowang66max/cool.pic`
3. Main file: `app.py`
4. **設定 Secrets**（重要！）：
   ```
   App 設定 → Secrets → 填入：
   
   HF_TOKEN = "hf_你的真實Token"
   ```
5. 點擊 Deploy 完成！

---

## 🔧 本地開發

### 靜態網頁
```bash
# 直接用瀏覽器開啟，或用 Live Server
open index.html
```
> 注意：靜態版需在 UI 的「🔑 HF Token」區段輸入你的 Token（儲存於 localStorage）

### Streamlit 版
```bash
# 安裝依賴
pip install -r requirements.txt

# 複製 .env 範本
cp .env.example .env
# 編輯 .env，填入真實 HF_TOKEN

# 設定 Streamlit secrets（本地開發用）
# 複製 .streamlit/secrets.toml 並填入 Token

# 啟動
streamlit run app.py
```

---

## 🔑 取得 Hugging Face Token

1. 前往 [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. 點擊「New token」
3. 類型選 **Read**（免費即可）
4. 複製 Token（格式：`hf_xxxxxxxx...`）

> ⚠️ 請勿將 Token 提交至 GitHub！`.env` 和 `.streamlit/secrets.toml` 已加入 `.gitignore`

---

## 📁 專案結構

```
cool.pic/
├── index.html                  # 靜態網頁主頁
├── css/
│   └── style.css               # 設計系統（Glassmorphism 深色主題）
├── js/
│   ├── api.js                  # Hugging Face API 封裝
│   ├── canvas.js               # Fabric.js 畫布引擎
│   └── app.js                  # 主程式邏輯
├── app.py                      # Streamlit 應用程式
├── requirements.txt            # Python 依賴
├── .streamlit/
│   ├── config.toml             # Streamlit 主題設定（可提交）
│   └── secrets.toml            # 🔒 API Token（已 gitignore）
├── .env                        # 🔒 本地環境變數（已 gitignore）
├── .env.example                # .env 範本（可提交）
├── .gitignore
└── .github/
    └── workflows/
        └── deploy.yml          # GitHub Pages 自動部署
```

---

## 🛠 使用的技術

| 技術 | 用途 |
|------|------|
| [Fabric.js](http://fabricjs.com) | 互動式畫布 |
| [Hugging Face Inference API](https://huggingface.co/docs/api-inference) | AI 圖像生成 |
| [Streamlit](https://streamlit.io) | Python Web App |
| [Pillow](https://pillow.readthedocs.io) | 圖像處理 |
| [GitHub Actions](https://github.com/features/actions) | CI/CD 自動部署 |
| [GitHub Pages](https://pages.github.com) | 靜態網頁托管 |

---

## 📄 License

MIT © [miccowang66max](https://github.com/miccowang66max)
