/**
 * canvas.js — Fabric.js 畫布引擎
 * 功能：圖像管理、拖曳縮放、圖層控制、匯出
 */

const CanvasEngine = (() => {
  let canvas = null;
  let onLayerChange = null;

  /* ── 初始化 ──────────────────────────────────────────────── */
  function init(canvasId, width = 1280, height = 720, layerChangeCallback) {
    onLayerChange = layerChangeCallback;

    canvas = new fabric.Canvas(canvasId, {
      width,
      height,
      backgroundColor: '#111122',
      selection: true,
      preserveObjectStacking: true,
      renderOnAddRemove: true,
    });

    // 物件選取事件
    canvas.on('selection:created',  _onSelectionChange);
    canvas.on('selection:updated',  _onSelectionChange);
    canvas.on('selection:cleared',  _onSelectionCleared);
    canvas.on('object:modified',    () => _fireLayerUpdate());
    canvas.on('object:added',       () => _fireLayerUpdate());
    canvas.on('object:removed',     () => _fireLayerUpdate());

    // 鍵盤快捷鍵
    document.addEventListener('keydown', _handleKeyDown);

    return canvas;
  }

  /* ── 新增圖像 ────────────────────────────────────────────── */
  function addImage(url, promptText = '') {
    return new Promise((resolve, reject) => {
      fabric.Image.fromURL(url, (img) => {
        if (!img) { reject(new Error('圖像載入失敗')); return; }

        // 自動縮放至畫布的 40%
        const maxSize = Math.min(canvas.width, canvas.height) * 0.4;
        const scale = Math.min(maxSize / img.width, maxSize / img.height, 1);

        // 隨機放置，避免疊在同一位置
        const cx = canvas.width / 2  + (Math.random() - 0.5) * 200;
        const cy = canvas.height / 2 + (Math.random() - 0.5) * 150;

        img.set({
          left:          cx,
          top:           cy,
          scaleX:        scale,
          scaleY:        scale,
          originX:       'center',
          originY:       'center',
          cornerColor:   '#9d5cff',
          cornerStrokeColor: 'rgba(255,255,255,0.4)',
          cornerSize:    10,
          cornerStyle:   'circle',
          transparentCorners: false,
          borderColor:   '#9d5cff',
          borderScaleFactor: 2,
          _promptText:   promptText,
          _addedAt:      Date.now(),
        });

        // 入場動畫
        img.set({ opacity: 0, scaleX: scale * 0.7, scaleY: scale * 0.7 });
        canvas.add(img);
        canvas.setActiveObject(img);

        img.animate({ opacity: 1, scaleX: scale, scaleY: scale }, {
          duration: 380,
          easing: fabric.util.ease.easeOutCubic,
          onChange: () => canvas.renderAll(),
          onComplete: () => resolve(img),
        });
      }, { crossOrigin: 'anonymous' });
    });
  }

  /* ── 背景顏色 ────────────────────────────────────────────── */
  function setBackgroundColor(color) {
    canvas.setBackgroundColor(color, () => canvas.renderAll());
  }

  function setBackgroundImage(url) {
    fabric.Image.fromURL(url, (img) => {
      canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
        scaleX: canvas.width / img.width,
        scaleY: canvas.height / img.height,
      });
    }, { crossOrigin: 'anonymous' });
  }

  /* ── 圖層控制 ────────────────────────────────────────────── */
  function bringForward()  { const o = _active(); if (o) { canvas.bringForward(o); _fireLayerUpdate(); } }
  function sendBackward()  { const o = _active(); if (o) { canvas.sendBackwards(o); _fireLayerUpdate(); } }
  function bringToFront()  { const o = _active(); if (o) { canvas.bringToFront(o); _fireLayerUpdate(); } }
  function sendToBack()    { const o = _active(); if (o) { canvas.sendToBack(o); _fireLayerUpdate(); } }

  /* ── 變換操作 ────────────────────────────────────────────── */
  function deleteSelected() {
    const objs = canvas.getActiveObjects();
    if (objs.length === 0) return;
    canvas.discardActiveObject();
    objs.forEach(o => canvas.remove(o));
    canvas.renderAll();
  }

  function duplicateSelected() {
    const obj = _active();
    if (!obj) return;
    obj.clone((cloned) => {
      cloned.set({ left: obj.left + 20, top: obj.top + 20 });
      canvas.add(cloned);
      canvas.setActiveObject(cloned);
      canvas.renderAll();
    });
  }

  function flipH() { const o = _active(); if (o) { o.set('flipX', !o.flipX); canvas.renderAll(); } }
  function flipV() { const o = _active(); if (o) { o.set('flipY', !o.flipY); canvas.renderAll(); } }

  function setOpacity(val) {
    const o = _active();
    if (o) { o.set('opacity', val / 100); canvas.renderAll(); }
  }

  function rotate(deg) {
    const o = _active();
    if (!o) return;
    o.rotate((o.angle + deg) % 360);
    canvas.renderAll();
  }

  /* ── 選取圖層 ────────────────────────────────────────────── */
  function selectObjectByIndex(index) {
    const objs = canvas.getObjects();
    if (index >= 0 && index < objs.length) {
      canvas.setActiveObject(objs[index]);
      canvas.renderAll();
    }
  }

  /* ── 清空 ────────────────────────────────────────────────── */
  function clearCanvas() {
    canvas.clear();
    canvas.setBackgroundColor('#111122', () => canvas.renderAll());
  }

  /* ── 匯出 PNG ────────────────────────────────────────────── */
  function exportPNG(filename = 'ai-canvas.png') {
    const dataURL = canvas.toDataURL({
      format:     'png',
      multiplier: 2,
      quality:    1,
    });
    const link = document.createElement('a');
    link.href     = dataURL;
    link.download = filename;
    link.click();
    return dataURL;
  }

  function exportJPEG(filename = 'ai-canvas.jpg', quality = 0.92) {
    const dataURL = canvas.toDataURL({ format: 'jpeg', quality, multiplier: 2 });
    const link = document.createElement('a');
    link.href     = dataURL;
    link.download = filename;
    link.click();
  }

  /* ── 取得圖層列表 ────────────────────────────────────────── */
  function getLayers() {
    return canvas.getObjects().map((obj, i) => ({
      index: i,
      type:  obj.type,
      name:  obj._promptText ? `🖼 ${obj._promptText.slice(0, 20)}` : `物件 ${i + 1}`,
      thumb: _getObjectThumb(obj),
      isActive: canvas.getActiveObject() === obj,
    })).reverse(); // 最上層顯示在最前
  }

  /* ── 縮放畫布 ────────────────────────────────────────────── */
  function zoomIn()  { _setZoom(canvas.getZoom() * 1.15); }
  function zoomOut() { _setZoom(canvas.getZoom() / 1.15); }
  function resetZoom() { _setZoom(1); canvas.viewportTransform[4] = 0; canvas.viewportTransform[5] = 0; canvas.renderAll(); }

  function _setZoom(z) {
    const clamped = Math.min(Math.max(z, 0.2), 4);
    canvas.setZoom(clamped);
    canvas.renderAll();
    return clamped;
  }

  /* ── 工具模式 ────────────────────────────────────────────── */
  function setSelectMode() {
    canvas.isDrawingMode = false;
    canvas.selection     = true;
    canvas.defaultCursor = 'default';
    canvas.off('mouse:down');
    canvas.off('mouse:move');
    canvas.off('mouse:up');
  }

  function setPanMode() {
    canvas.isDrawingMode = false;
    canvas.selection     = false;
    canvas.defaultCursor = 'grab';
    let isDragging = false, lastPosX, lastPosY;
    canvas.off('mouse:down');
    canvas.off('mouse:move');
    canvas.off('mouse:up');
    canvas.on('mouse:down', (opt) => {
      isDragging = true;
      lastPosX = opt.e.clientX;
      lastPosY = opt.e.clientY;
      canvas.defaultCursor = 'grabbing';
    });
    canvas.on('mouse:move', (opt) => {
      if (!isDragging) return;
      const vpt = canvas.viewportTransform;
      vpt[4] += opt.e.clientX - lastPosX;
      vpt[5] += opt.e.clientY - lastPosY;
      lastPosX = opt.e.clientX;
      lastPosY = opt.e.clientY;
      canvas.requestRenderAll();
    });
    canvas.on('mouse:up', () => {
      isDragging = false;
      canvas.defaultCursor = 'grab';
    });
  }

  /* ── 私有函式 ────────────────────────────────────────────── */
  function _active() { return canvas.getActiveObject(); }

  function _onSelectionChange(e) {
    _fireLayerUpdate();
    const obj = e.selected?.[0];
    if (obj) {
      document.dispatchEvent(new CustomEvent('canvas:objectSelected', { detail: obj }));
    }
  }

  function _onSelectionCleared() {
    _fireLayerUpdate();
    document.dispatchEvent(new CustomEvent('canvas:selectionCleared'));
  }

  function _fireLayerUpdate() {
    if (onLayerChange) onLayerChange(getLayers());
  }

  function _getObjectThumb(obj) {
    try {
      const el = obj.getElement ? obj.getElement() : null;
      if (el && el.tagName === 'IMG') return el.src;
    } catch (_) {}
    return null;
  }

  function _handleKeyDown(e) {
    if (!canvas) return;
    // 防止在 input/textarea 觸發
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;

    const key = e.key;
    if (key === 'Delete' || key === 'Backspace')   { deleteSelected(); }
    if (key === '[')  { sendBackward(); }
    if (key === ']')  { bringForward(); }
    if (e.ctrlKey && key === 'd') { e.preventDefault(); duplicateSelected(); }
    if (e.ctrlKey && key === 'a') { e.preventDefault(); canvas.discardActiveObject(); canvas.setActiveObject(new fabric.ActiveSelection(canvas.getObjects(), { canvas })); canvas.renderAll(); }
  }

  function getCanvas() { return canvas; }
  function getObjectCount() { return canvas ? canvas.getObjects().length : 0; }

  return {
    init, addImage, setBackgroundColor, setBackgroundImage,
    bringForward, sendBackward, bringToFront, sendToBack,
    deleteSelected, duplicateSelected, flipH, flipV,
    setOpacity, rotate, selectObjectByIndex, clearCanvas,
    exportPNG, exportJPEG, getLayers,
    zoomIn, zoomOut, resetZoom,
    setSelectMode, setPanMode,
    getCanvas, getObjectCount,
  };
})();
