/* Recording-only adapter. Real deployed Worker calculations are cached BEFORE clock0.
 * No fixture values are injected. Live DOM is rendered by the deployed hmi.js.
 * worker.js posts results, sil, progress, done; recipe.mode controls result order.
 */
(() => {
  const NativeWorker = window.Worker;
  const cache = new Map();
  const key = data => JSON.stringify({recipe:data.recipe, scenario:data.scenario, params:data.params});
  const state = window.hmiRecording = {armed:false, hits:0, misses:0, cache};
  window.Worker = class extends NativeWorker {
    constructor(url, options) {
      super(url, options);
      this.isHmi = new URL(url, location.href).pathname.endsWith('/js/worker.js');
      this.pending = null;
      this.addEventListener('message', ({data}) => {
        if (!this.isHmi || !this.pending || data.id !== this.pending.id) return;
        this.pending.messages.push(data);
        if (data.type === 'done') {
          cache.set(this.pending.key, this.pending.messages);
          this.pending = null;
        }
      });
    }
    postMessage(data, ...rest) {
      if (!this.isHmi) return super.postMessage(data, ...rest);
      const k = key(data);
      if (!state.armed) {
        state.misses++;
        this.pending = {key:k, id:data.id, messages:[]};
        return super.postMessage(data, ...rest);
      }
      if (!cache.has(k)) throw Error('녹화 중 미계산 레시피: 재계산 금지');
      const messages = cache.get(k);
      if (state.resetOnly) {
        const done=messages.find(m=>m.type==='done');
        this.dispatchEvent(new MessageEvent('message',{data:{...done,id:data.id}}));
        return;
      }
      state.hits++;
      // Keep real results + SIL + final progress, skip the slow educational replay.
      const progress = messages.filter(m=>m.type==='progress').at(-1);
      for (const m of messages) {
        if (m.type==='progress' && m!==progress) continue;
        this.dispatchEvent(new MessageEvent('message', {data:{...m,id:data.id}}));
      }
    }
  };
  state.focus = selectors => {
    document.querySelectorAll('[data-v5-focus]').forEach(el=>el.removeAttribute('data-v5-focus'));
    const elements = selectors.map(s=>{
      const el=document.querySelector(s);if(!el)throw Error('HMI 대상 없음: '+s);
      el.setAttribute('data-v5-focus','');return el;
    });
    const rect=elements[0].getBoundingClientRect();
    window.scrollTo({top:Math.max(0,scrollY+rect.top-70),behavior:'instant'});
  };
})();
