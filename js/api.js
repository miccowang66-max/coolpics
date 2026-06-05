/**
 * api.js — Hugging Face Inference API 封裝
 * 支援 FLUX.1-schnell、SDXL 等圖像生成模型
 */

const HF_API = {
  BASE_URL: 'https://api-inference.huggingface.co/models',

  MODELS: {
    'FLUX.1-schnell (快速)':        'black-forest-labs/FLUX.1-schnell',
    'FLUX.1-dev (高品質)':           'black-forest-labs/FLUX.1-dev',
    'Stable Diffusion XL':           'stabilityai/stable-diffusion-xl-base-1.0',
    'Stable Diffusion 2.1':          'stabilityai/stable-diffusion-2-1',
    'Realistic Vision':              'SG161222/Realistic_Vision_V5.1_noVAE',
    'Dreamshaper':                   'Lykon/dreamshaper-8',
  },

  /** 從 localStorage 讀取 HF Token */
  getToken() {
    return localStorage.getItem('hf_token') || '';
  },

  /** 儲存 HF Token */
  saveToken(token) {
    localStorage.setItem('hf_token', token.trim());
  },

  /**
   * 生成圖像
   * @param {string} prompt     - 文字提示詞
   * @param {object} options    - { model, width, height, negativePrompt, steps, guidance, seed }
   * @returns {Promise<string>} - Object URL (Blob)
   */
  async generateImage(prompt, options = {}) {
    const token = this.getToken();
    if (!token) throw new Error('請先在設定中輸入 Hugging Face API Token');

    const {
      model       = 'black-forest-labs/FLUX.1-schnell',
      width       = 512,
      height      = 512,
      negativePrompt = '',
      steps       = 20,
      guidance    = 7.5,
      seed        = Math.floor(Math.random() * 2147483647),
    } = options;

    const payload = {
      inputs: prompt,
      parameters: {
        width,
        height,
        num_inference_steps: steps,
        guidance_scale: guidance,
        seed,
        ...(negativePrompt && { negative_prompt: negativePrompt }),
      },
    };

    const url = `${this.BASE_URL}/${model}`;

    // 最多重試 3 次（模型可能需要預熱）
    for (let attempt = 1; attempt <= 3; attempt++) {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'image/png,image/jpeg,image/*',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const blob = await response.blob();
        return { url: URL.createObjectURL(blob), seed };
      }

      // 503 = 模型正在載入，等待後重試
      if (response.status === 503 && attempt < 3) {
        const errData = await response.json().catch(() => ({}));
        const waitSec = errData.estimated_time || 20;
        console.log(`模型載入中，等待 ${waitSec}s (第 ${attempt} 次重試)...`);
        await HF_API._sleep(Math.min(waitSec * 1000, 30000));
        continue;
      }

      // 其他錯誤
      let errMsg = `API 錯誤 ${response.status}`;
      try {
        const errData = await response.json();
        if (errData.error) errMsg = errData.error;
      } catch (_) {}

      if (response.status === 401) errMsg = 'API Token 無效，請重新設定';
      if (response.status === 429) errMsg = '請求過於頻繁，請稍後再試';
      if (response.status === 402) errMsg = 'API 額度不足，請升級 HF 方案';

      throw new Error(errMsg);
    }

    throw new Error('模型載入逾時，請稍後再試');
  },

  _sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },
};
