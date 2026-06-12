/**
 * app.js — 主程式邏輯
 * 初始化、事件綁定、狀態管理、提示詞歷史
 */

/* ── 應用程式狀態 ─────────────────────────────────────────── */
const AppState = {
  isGenerating: false,
  history:      [],        // { url, prompt, seed, timestamp }
  currentTool:  'select',
  canvasObjects: 0,
};

/* ── DOM 快取 ────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const DOM = {
  promptInput:     null,
  negPromptInput:  null,
  generateBtn:     null,
  modelSelect:     null,
  widthSlider:     null,
  heightSlider:    null,
  stepsSlider:     null,
  guidanceSlider:  null,
  widthVal:        null,
  heightVal:       null,
  stepsVal:        null,
  guidanceVal:     null,
  historyGrid:     null,
  layerList:       null,
  canvasEmpty:     null,
  progressBar:     null,
  toastContainer:  null,
  bgColorInput:    null,
  tokenInput:      null,
  tokenSaveBtn:    null,
  tokenStatus:     null,
  objectCount:     null,
  zoomLevel:       null,
};

/* ── 初始化 ──────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  _cacheDom();
  try { _initCanvas(); } catch (e) { console.error('Canvas init failed:', e); }
  _initModelSelect();
  _bindEvents();
  _loadHistory();
  _checkToken();
  _loadPromptSuggestions();
  showToast('歡迎使用 AI 畫布生成器 ✨', 'info');
});

function _cacheDom() {
  Object.keys(DOM).forEach(key => {
    DOM[key] = $(key.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, ''));
  });
  // 手動補齊
  DOM.promptInput    = $('prompt-input');
  DOM.negPromptInput = $('neg-prompt-input');
  DOM.generateBtn    = $('generate-btn');
  DOM.modelSelect    = $('model-select');
  DOM.widthSlider    = $('width-slider');
  DOM.heightSlider   = $('height-slider');
  DOM.stepsSlider    = $('steps-slider');
  DOM.guidanceSlider = $('guidance-slider');
  DOM.widthVal       = $('width-val');
  DOM.heightVal      = $('height-val');
  DOM.stepsVal       = $('steps-val');
  DOM.guidanceVal    = $('guidance-val');
  DOM.historyGrid    = $('history-grid');
  DOM.layerList      = $('layer-list');
  DOM.canvasEmpty    = $('canvas-empty');
  DOM.progressBar    = $('progress-bar');
  DOM.toastContainer = $('toast-container');
  DOM.bgColorInput   = $('bg-color-input');
  DOM.tokenInput     = $('token-input');
  DOM.tokenSaveBtn   = $('token-save-btn');
  DOM.tokenStatus    = $('token-status');
  DOM.objectCount    = $('object-count');
  DOM.zoomLevel      = $('zoom-level');
}

/* ── 畫布初始化 ──────────────────────────────────────────── */
function _initCanvas() {
  const w = Math.max(parseInt(DOM.widthSlider?.value)  || 1280, 256);
  const h = Math.max(parseInt(DOM.heightSlider?.value) || 720,  256);

  CanvasEngine.init('main-canvas', w, h, _onLayerChange);

  // 滾輪縮放
  const fabricCanvas = CanvasEngine.getCanvas();
  fabricCanvas.on('mouse:wheel', (opt) => {
    opt.e.preventDefault();
    const delta = opt.e.deltaY;
    let zoom = fabricCanvas.getZoom();
    zoom *= delta > 0 ? 0.95 : 1.05;
    zoom = Math.min(Math.max(zoom, 0.2), 4);
    fabricCanvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
    if (DOM.zoomLevel) DOM.zoomLevel.textContent = `${Math.round(zoom * 100)}%`;
  });
}

/* ── 模型下拉選單 ────────────────────────────────────────── */
function _initModelSelect() {
  if (!DOM.modelSelect) return;
  Object.entries(HF_API.MODELS).forEach(([label, val]) => {
    const opt = document.createElement('option');
    opt.value = val;
    opt.textContent = label;
    DOM.modelSelect.appendChild(opt);
  });
}

/* ── 事件綁定 ────────────────────────────────────────────── */
function _bindEvents() {
  // 生成按鈕
  DOM.generateBtn?.addEventListener('click', handleGenerate);

  // Enter 快捷鍵（Ctrl+Enter 或 Cmd+Enter）
  DOM.promptInput?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleGenerate();
  });

  // 滑桿即時更新
  _bindSlider('width-slider',    'width-val',    v => `${v}px`);
  _bindSlider('height-slider',   'height-val',   v => `${v}px`);
  _bindSlider('steps-slider',    'steps-val',    v => v);
  _bindSlider('guidance-slider', 'guidance-val', v => v);

  // 背景顏色
  DOM.bgColorInput?.addEventListener('input', (e) => {
    CanvasEngine.setBackgroundColor(e.target.value);
  });

  // 工具列按鈕
  document.querySelectorAll('[data-tool]').forEach(btn => {
    btn.addEventListener('click', () => {
      const tool = btn.dataset.tool;
      AppState.currentTool = tool;
      document.querySelectorAll('[data-tool]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (tool === 'pan') CanvasEngine.setPanMode();
      else               CanvasEngine.setSelectMode();
    });
  });

  // 工具列操作
  _bindToolBtn('tb-delete',    () => CanvasEngine.deleteSelected());
  _bindToolBtn('tb-duplicate', () => CanvasEngine.duplicateSelected());
  _bindToolBtn('tb-flip-h',    () => CanvasEngine.flipH());
  _bindToolBtn('tb-flip-v',    () => CanvasEngine.flipV());
  _bindToolBtn('tb-rot-l',     () => CanvasEngine.rotate(-90));
  _bindToolBtn('tb-rot-r',     () => CanvasEngine.rotate(90));
  _bindToolBtn('tb-front',     () => CanvasEngine.bringToFront());
  _bindToolBtn('tb-back',      () => CanvasEngine.sendToBack());
  _bindToolBtn('tb-clear',     () => { if (confirm('確定要清除畫布上的所有物件嗎？')) { CanvasEngine.clearCanvas(); _onLayerChange([]); showToast('畫布已清除', 'info'); } });
  _bindToolBtn('tb-zoom-in',   () => { CanvasEngine.zoomIn();   _updateZoomLabel(); });
  _bindToolBtn('tb-zoom-out',  () => { CanvasEngine.zoomOut();  _updateZoomLabel(); });
  _bindToolBtn('tb-zoom-reset',() => { CanvasEngine.resetZoom(); _updateZoomLabel(); });
  _bindToolBtn('tb-export-png',() => { CanvasEngine.exportPNG(`cool-pic-${Date.now()}.png`); showToast('PNG 已下載！', 'success'); });
  _bindToolBtn('tb-export-jpg',() => { CanvasEngine.exportJPEG(`cool-pic-${Date.now()}.jpg`); showToast('JPG 已下載！', 'success'); });

  // Token 儲存
  DOM.tokenSaveBtn?.addEventListener('click', _saveToken);
  DOM.tokenInput?.addEventListener('keydown', (e) => { if (e.key === 'Enter') _saveToken(); });
}

function _bindSlider(sliderId, valId, fmt) {
  const slider = $(sliderId);
  const val    = $(valId);
  if (!slider || !val) return;
  val.textContent = fmt(slider.value);
  slider.addEventListener('input', () => { val.textContent = fmt(slider.value); });
}

function _bindToolBtn(id, fn) {
  $(id)?.addEventListener('click', fn);
}

/* ── 圖像生成流程 ────────────────────────────────────────── */
async function handleGenerate() {
  if (AppState.isGenerating) return;

  const prompt = DOM.promptInput?.value.trim();
  if (!prompt) {
    showToast('請輸入提示詞', 'error');
    DOM.promptInput?.focus();
    return;
  }

  const token = HF_API.getToken();
  if (!token || token === 'hf_your_token_here') {
    showToast('請先設定 Hugging Face API Token', 'error');
    $('token-input')?.focus();
    $('token-section')?.scrollIntoView({ behavior: 'smooth' });
    return;
  }

  _setGenerating(true);

  try {
    const options = {
      model:          DOM.modelSelect?.value,
      width:          parseInt($('width-slider')?.value  || 512),
      height:         parseInt($('height-slider')?.value || 512),
      negativePrompt: DOM.negPromptInput?.value.trim() || '',
      steps:          parseInt($('steps-slider')?.value  || 20),
      guidance:       parseFloat($('guidance-slider')?.value || 7.5),
    };

    _setProgress(20);
    showToast('🎨 正在生成圖像...', 'info');

    const result = await HF_API.generateImage(prompt, options);

    _setProgress(80);
    try {
      await CanvasEngine.addImage(result.url, prompt);
    } catch (canvasErr) {
      console.error('Canvas addImage failed:', canvasErr);
    }
    _setProgress(100);

    // 更新 UI
    _addToHistory({ url: result.url, prompt, seed: result.seed, timestamp: Date.now() });
    _updateEmptyState();
    DOM.promptInput.value = '';
    showToast(`✅ 圖像生成完成！(seed: ${result.seed})`, 'success');

  } catch (err) {
    showToast(`❌ ${err.message}`, 'error');
    console.error(err);
  } finally {
    _setGenerating(false);
    setTimeout(() => _setProgress(0), 600);
  }
}

/* ── 生成狀態管理 ────────────────────────────────────────── */
function _setGenerating(state) {
  AppState.isGenerating = state;
  document.body.classList.toggle('generating', state);
  if (DOM.generateBtn) {
    DOM.generateBtn.disabled = state;
    DOM.generateBtn.innerHTML = state
      ? `<div class="spinner"></div> 生成中...`
      : `✨ 生成圖像`;
  }
}

function _setProgress(pct) {
  if (!DOM.progressBar) return;
  if (pct === 0) {
    DOM.progressBar.style.width = '0%';
    DOM.progressBar.style.opacity = '0';
  } else {
    DOM.progressBar.style.opacity = '1';
    DOM.progressBar.style.width = `${pct}%`;
  }
}

/* ── 圖層面板更新 ────────────────────────────────────────── */
function _onLayerChange(layers) {
  if (!DOM.layerList) return;
  DOM.layerList.innerHTML = '';

  if (DOM.objectCount) {
    DOM.objectCount.textContent = `${layers.length} 個物件`;
  }

  if (layers.length === 0) {
    DOM.layerList.innerHTML = '<p style="color:var(--text-muted);font-size:0.78rem;text-align:center;padding:8px">畫布空白</p>';
    return;
  }

  layers.forEach(layer => {
    const item = document.createElement('div');
    item.className = `layer-item${layer.isActive ? ' selected' : ''}`;
    item.innerHTML = `
      ${layer.thumb
        ? `<img class="layer-thumb" src="${layer.thumb}" alt="" crossorigin="anonymous">`
        : `<div class="layer-thumb" style="background:var(--bg-elevated);display:flex;align-items:center;justify-content:center;font-size:1rem">🖼</div>`}
      <span class="layer-name" title="${layer.name}">${layer.name}</span>
      <div class="layer-actions">
        <button class="layer-action-btn" title="上移" data-action="forward" data-idx="${layer.index}">↑</button>
        <button class="layer-action-btn" title="下移" data-action="backward" data-idx="${layer.index}">↓</button>
        <button class="layer-action-btn" title="刪除" data-action="delete" data-idx="${layer.index}" style="color:var(--rose)">✕</button>
      </div>`;

    item.addEventListener('click', (e) => {
      if (e.target.dataset.action) {
        e.stopPropagation();
        const idx = parseInt(e.target.dataset.idx);
        const action = e.target.dataset.action;
        CanvasEngine.selectObjectByIndex(idx);
        if (action === 'forward')  CanvasEngine.bringForward();
        if (action === 'backward') CanvasEngine.sendBackward();
        if (action === 'delete')   CanvasEngine.deleteSelected();
        _updateEmptyState();
      } else {
        CanvasEngine.selectObjectByIndex(layer.index);
      }
    });

    DOM.layerList.appendChild(item);
  });

  _updateEmptyState();
}

/* ── 空白狀態 ────────────────────────────────────────────── */
function _updateEmptyState() {
  if (!DOM.canvasEmpty) return;
  const isEmpty = CanvasEngine.getObjectCount() === 0;
  DOM.canvasEmpty.classList.toggle('hidden', !isEmpty);
}

/* ── 歷史紀錄 ────────────────────────────────────────────── */
function _addToHistory(item) {
  AppState.history.unshift(item);
  if (AppState.history.length > 20) AppState.history.pop();
  _saveHistory();
  _renderHistory();
}

function _renderHistory() {
  if (!DOM.historyGrid) return;
  DOM.historyGrid.innerHTML = '';

  if (AppState.history.length === 0) {
    DOM.historyGrid.innerHTML = '<p style="color:var(--text-muted);font-size:0.75rem;grid-column:1/-1;text-align:center;padding:8px">尚無紀錄</p>';
    return;
  }

  AppState.history.forEach((item, i) => {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.title = item.prompt;
    div.innerHTML = `
      <img src="${item.url}" alt="${item.prompt}" crossorigin="anonymous">
      <div class="hi-overlay">
        <button class="hi-add-btn" data-idx="${i}">＋ 加入畫布</button>
      </div>`;
    div.querySelector('.hi-add-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      CanvasEngine.addImage(AppState.history[i].url, AppState.history[i].prompt)
        .then(() => { showToast('已加入畫布', 'success'); _updateEmptyState(); });
    });
    DOM.historyGrid.appendChild(div);
  });
}

function _saveHistory() {
  try {
    const toSave = AppState.history.map(({ prompt, seed, timestamp }) => ({ prompt, seed, timestamp }));
    localStorage.setItem('canvas_history_meta', JSON.stringify(toSave));
  } catch (_) {}
}

function _loadHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem('canvas_history_meta') || '[]');
    AppState.history = saved;
  } catch (_) {}
  _renderHistory();
}

/* ── Token 管理 ──────────────────────────────────────────── */
function _checkToken() {
  const token = HF_API.getToken();
  if (DOM.tokenInput) DOM.tokenInput.value = token;
  _updateTokenStatus(token && token !== 'hf_your_token_here');
}

function _saveToken() {
  const val = DOM.tokenInput?.value.trim();
  if (!val || val.length < 10) {
    showToast('Token 格式不正確', 'error');
    return;
  }
  HF_API.saveToken(val);
  _updateTokenStatus(true);
  showToast('✅ Token 已儲存', 'success');
}

function _updateTokenStatus(valid) {
  if (!DOM.tokenStatus) return;
  DOM.tokenStatus.textContent = valid ? '✅ 已設定' : '⚠️ 未設定';
  DOM.tokenStatus.style.color = valid ? 'var(--green)' : 'var(--amber)';
}

/* ── 提示詞建議 Chips ────────────────────────────────────── */
function _loadPromptSuggestions() {
  const suggestions = [
    '宇宙星雲中的太空城市',
    '水墨風格的山水畫',
    '賽博龐克街道霓虹燈',
    '可愛的貓咪宇航員',
    '夢幻森林中的精靈',
    '未來主義建築概念圖',
    '日落海邊水彩插圖',
    '機械風格的機器人',
  ];

  const container = $('prompt-chips');
  if (!container) return;

  suggestions.forEach(s => {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = s;
    chip.addEventListener('click', () => {
      if (DOM.promptInput) {
        DOM.promptInput.value = s;
        DOM.promptInput.focus();
      }
    });
    container.appendChild(chip);
  });
}

/* ── Zoom 標籤 ───────────────────────────────────────────── */
function _updateZoomLabel() {
  if (!DOM.zoomLevel) return;
  const z = CanvasEngine.getCanvas()?.getZoom() || 1;
  DOM.zoomLevel.textContent = `${Math.round(z * 100)}%`;
}

/* ── Toast 通知 ──────────────────────────────────────────── */
function showToast(msg, type = 'info', duration = 3500) {
  if (!DOM.toastContainer) return;
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || ''}</span><span>${msg}</span>`;
  DOM.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('fade-out');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}
