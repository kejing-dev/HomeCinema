// Home Cinema · Cinema Frame — Preview interactions (language, style, show state, align mode, panel page).
// URL query (?lang=zh&style=neon&show=showing&align=on&page=settings&zoom=.5&menu=lang) presets a state for screenshots.
window.addEventListener('DOMContentLoaded', () => {
  const $ = (id) => document.getElementById(id);
  const I18N = JSON.parse($('i18n-data').textContent);
  const q = new URLSearchParams(location.search);
  const st = { lang: 'en', langChoice: 'sys', style: 'gallery', show: 'up', align: 'off', page: 'show', zoom: '.5' };
  for (const k of Object.keys(st)) if (q.get(k)) st[k] = q.get(k);
  const t = (k) => I18N[st.lang][k] ?? I18N.en[k];
  const vol = $('frame-volume');

  function render() {
    document.documentElement.lang = st.lang === 'zh' ? 'zh-CN' : 'en';
    document.querySelectorAll('*').forEach((el) => {
      for (const a of Array.from(el.attributes)) {
        if (!a.name.startsWith('data-t-')) continue;
        el.setAttribute(a.name.slice(7), t(a.value));
      }
    });
    vol.dataset.style = st.style; vol.dataset.show = st.show; vol.dataset.align = st.align;
    document.querySelectorAll('.style-card').forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.style === st.style)));
    ['frame-art-up', 'frame-art-dim'].forEach((id) => { const im = $(id); im.src = im.getAttribute('data-src-' + st.style); });
    $('style-desc').setAttribute('data-t-text', 'sd.' + st.style); $('style-desc').setAttribute('text', t('sd.' + st.style));
    const showing = st.show === 'opening' || st.show === 'showing';
    $('show-toggle').setAttribute('text', t(showing ? 'show.end' : 'show.start'));
    $('show-toggle').setAttribute('leading-icon', showing ? 'ic_sun' : 'ic_play');
    $('ctl-status').setAttribute('text', st.align === 'on' ? t('status.align') : t('status.' + st.show));
    $('align-panel').hidden = st.align !== 'on';
    $('page-show').hidden = st.page !== 'show';
    $('page-settings').hidden = st.page !== 'settings';
    $('ctl-tabs').setAttribute('selected-index', st.page === 'show' ? '0' : '1');
    $('lang-btn').setAttribute('text', t('lang.' + st.langChoice));
    $('pv-stage').style.setProperty('--z', st.zoom);
    document.querySelectorAll('[data-pv-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.pvLang === st.lang)));
    document.querySelectorAll('[data-pv-style]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.pvStyle === st.style)));
    document.querySelectorAll('[data-pv-show]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.pvShow === st.show)));
    document.querySelectorAll('[data-pv-align]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.pvAlign === st.align)));
    document.querySelectorAll('[data-pv-page]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.pvPage === st.page)));
    document.querySelectorAll('[data-pv-zoom]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.pvZoom === st.zoom)));
  }
  const set = (patch) => { Object.assign(st, patch); render(); };

  // Preview bar
  document.querySelectorAll('[data-pv-lang]').forEach((b) => b.addEventListener('click', () => set({ lang: b.dataset.pvLang, langChoice: b.dataset.pvLang })));
  document.querySelectorAll('[data-pv-style]').forEach((b) => b.addEventListener('click', () => set({ style: b.dataset.pvStyle })));
  document.querySelectorAll('[data-pv-show]').forEach((b) => b.addEventListener('click', () => set({ show: b.dataset.pvShow })));
  document.querySelectorAll('[data-pv-align]').forEach((b) => b.addEventListener('click', () => set({ align: b.dataset.pvAlign })));
  document.querySelectorAll('[data-pv-page]').forEach((b) => b.addEventListener('click', () => set({ page: b.dataset.pvPage })));
  document.querySelectorAll('[data-pv-zoom]').forEach((b) => b.addEventListener('click', () => set({ zoom: b.dataset.pvZoom })));

  // App controls
  document.querySelectorAll('.style-card').forEach((c) => {
    if (window.spatialHoverEffect) window.spatialHoverEffect(c);
    const pick = () => set({ style: c.dataset.style });
    c.addEventListener('click', pick);
    c.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } });
  });
  let timer = null;
  $('show-toggle').addEventListener('click-action', () => {
    clearTimeout(timer);
    if (st.show === 'opening' || st.show === 'showing') { set({ show: 'closing' }); timer = setTimeout(() => set({ show: 'up' }), 6000); }
    else { set({ show: 'opening' }); timer = setTimeout(() => set({ show: 'showing' }), 4000); }
  });
  $('align-btn').addEventListener('click-action', () => set({ align: 'on' }));
  $('align-done').addEventListener('click-action', () => set({ align: 'off' }));
  $('ctl-tabs').addEventListener('select', (e) => set({ page: e.detail.index === 0 ? 'show' : 'settings' }));
  $('lang-btn').addEventListener('click-action', () => $('lang-menu').toggleAttribute('hidden'));
  ['lang-sys', 'lang-zh', 'lang-en'].forEach((id) => $(id).addEventListener('select', () => {
    const l = $(id).dataset.lang;
    $('lang-menu').setAttribute('hidden', '');
    set({ langChoice: l, lang: l === 'sys' ? 'en' : l });
  }));
  $('exit-btn').addEventListener('click-action', () => { document.body.style.opacity = '0.35'; setTimeout(() => { document.body.style.opacity = ''; }, 900); });

  if (q.get('still')) document.body.classList.add('pv-still');
  render();
  if (q.get('menu') === 'lang') $('lang-menu').removeAttribute('hidden');
  if (q.get('audit')) {
    setTimeout(async () => {
      await import('./review/audit-preview.js');
      const specUrl = new URL('design-spec.json', location.href).href;
      const spec = await (await fetch(specUrl)).json();
      const expectations = JSON.parse(q.get('expect') || '{}');
      const rep = await auditDesignPreview(spec, { specUrl, scenario: q.get('audit'), initial: q.get('audit') === 'initial', expectations });
      const pre = document.createElement('pre'); pre.id = 'audit-report'; pre.hidden = true; pre.textContent = JSON.stringify(rep); document.body.appendChild(pre);
    }, 1500);
  }
});
