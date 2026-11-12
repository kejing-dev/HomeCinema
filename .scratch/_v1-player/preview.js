// Home Cinema design Preview interactions (Preview only; not app code).
window.addEventListener('DOMContentLoaded', () => {
  const $ = (id) => document.getElementById(id);
  const I18N = JSON.parse($('i18n-data').textContent);
  const TITLES = JSON.parse($('title-data').textContent);
  let lang = 'en';
  let langChoice = 'sys';
  let current = 'harbor';
  let playing = true;
  let depth = 2;
  const depthScale = [0, 0.5, 1, 1.6];
  const t = (k) => I18N[lang][k] ?? I18N.en[k];

  function applyLang() {
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.querySelectorAll('*').forEach((el) => {
      for (const a of Array.from(el.attributes)) {
        if (!a.name.startsWith('data-t-')) continue;
        const attr = a.name.slice(7);
        if (attr === 'textcontent') el.textContent = t(a.value);
        else el.setAttribute(attr, t(a.value));
      }
    });
    document.querySelectorAll('[data-title-text]').forEach((el) => el.setAttribute('text', TITLES[el.dataset.titleText][lang]));
    document.querySelectorAll('[data-left]').forEach((el) => el.setAttribute('text', t('left').replace('{m}', el.dataset.left)));
    document.querySelectorAll('.poster3d').forEach((el) => el.setAttribute('aria-label', TITLES[el.dataset.title][lang]));
    $('set-lang-btn').setAttribute('text', t('set.lang.v.' + langChoice));
    $('clear-dialog').setAttribute('confirm-text', t('clear.ok'));
    $('clear-dialog').setAttribute('dismiss-text', t('clear.cancel'));
    $('pv-en').setAttribute('aria-pressed', String(lang === 'en'));
    $('pv-zh').setAttribute('aria-pressed', String(lang === 'zh'));
    fillDetail(current);
    $('cc-play').setAttribute('semantic-label', t(playing ? 'cin.pause' : 'cin.play'));
  }
  function setLang(l) { lang = l; applyLang(); }

  // ---- Tabs
  const pages = ['page-home', 'page-library', 'page-sources', 'page-settings'];
  $('main-tabs').addEventListener('select', (e) => {
    pages.forEach((p, i) => { $(p).hidden = i !== e.detail.index; });
  });

  // ---- 3D posters: tilt toward pointer
  document.querySelectorAll('.poster3d').forEach((el) => {
    el.style.setProperty('--depth', depthScale[depth]);
    el.addEventListener('pointermove', (ev) => {
      const r = el.getBoundingClientRect();
      const dx = (ev.clientX - r.left) / r.width - 0.5;
      const dy = (ev.clientY - r.top) / r.height - 0.5;
      const k = depthScale[depth] ? 16 : 0;
      el.style.transform = `rotateY(${dx * k}deg) rotateX(${-dy * k}deg) translateZ(${depthScale[depth] * 10}px)`;
    });
    el.addEventListener('pointerleave', () => { el.style.transform = ''; });
    const open = () => openDetail(el.dataset.title);
    el.addEventListener('click', open);
    el.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(); } });
  });
  document.querySelectorAll('.cont-card').forEach((el) => {
    if (window.spatialHoverEffect) spatialHoverEffect(el);
    el.addEventListener('click', () => openDetail(el.dataset.title));
  });

  function fmt(sec) {
    const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = Math.floor(sec % 60);
    return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(s).padStart(2, '0');
  }
  function fillDetail(key) {
    const d = TITLES[key];
    $('det-art').src = 'assets/backdrop-' + key + '.svg';
    $('det-art').alt = d[lang];
    $('det-name').setAttribute('text', d[lang]);
    $('det-year').setAttribute('label', String(d.year));
    $('det-run').setAttribute('label', lang === 'zh' ? d.run.replace('Season 1 · 8 episodes', '第 1 季 · 8 集').replace('h ', ' 小时 ').replace('m', ' 分') : d.run);
    $('det-genre').setAttribute('label', d.genre[lang]);
    $('det-quality').setAttribute('label', d.q);
    $('det-overview').setAttribute('text', d.ov[lang]);
    $('det-eps').hidden = key !== 'keepers';
    const resume = $('det-resume');
    if (d.p) {
      const total = key === 'keepers' ? 51 * 60 : 6750;
      resume.setAttribute('text', t('det.resume').replace('{t}', fmt(total * d.p)));
      $('det-restart').hidden = false;
    } else {
      resume.setAttribute('text', t('det.play'));
      $('det-restart').hidden = true;
    }
  }
  function openDetail(key) { current = key; fillDetail(key); $('detail-window').removeAttribute('hidden'); }
  $('det-close').addEventListener('click-action', () => $('detail-window').setAttribute('hidden', ''));

  // ---- Cinema
  function showScene(name) {
    const cinema = name === 'cinema';
    $('scene-shared').hidden = cinema;
    $('scene-cinema-wrap').hidden = !cinema;
    $('pv-shared').setAttribute('aria-pressed', String(!cinema));
    $('pv-cinema').setAttribute('aria-pressed', String(cinema));
    if (cinema) {
      const d = TITLES[current];
      $('cinema-frame').src = 'assets/backdrop-' + current + '.svg';
      $('cc-title').setAttribute('text', d[lang]);
      $('cc-seek').setAttribute('value', String(d.p || 0));
      poke();
    }
  }
  $('det-resume').addEventListener('click-action', () => showScene('cinema'));
  $('det-restart').addEventListener('click-action', () => showScene('cinema'));
  $('cc-exit').addEventListener('click-action', () => showScene('shared'));
  $('cc-play').addEventListener('click-action', (e) => {
    playing = !playing;
    e.currentTarget.setAttribute('icon', playing ? 'ic_player_pause' : 'ic_player_play');
    e.currentTarget.setAttribute('semantic-label', t(playing ? 'cin.pause' : 'cin.play'));
    $('cinema-screen').classList.toggle('paused', !playing);
  });
  const seekBy = (d) => { const s = $('cc-seek'); s.setAttribute('value', String(Math.min(1, Math.max(0, parseFloat(s.getAttribute('value')) + d)))); };
  $('cc-back').addEventListener('click-action', () => seekBy(-15 / 6750));
  $('cc-fwd').addEventListener('click-action', () => seekBy(15 / 6750));
  $('cc-env').addEventListener('checked-change', (e) => $('scene-cinema').classList.toggle('dimmed', !e.detail.checked));
  let idle;
  function poke() { $('cinema-controls').classList.remove('idle'); clearTimeout(idle); idle = setTimeout(() => $('cinema-controls').classList.add('idle'), 5000); }
  $('scene-cinema').addEventListener('pointermove', poke);
  $('scene-cinema').addEventListener('pointerdown', poke);

  // Menus
  const wireMenu = (btn, menu) => $(btn).addEventListener('click-action', () => { $(menu).toggleAttribute('hidden'); poke(); });
  wireMenu('cc-subs', 'subs-menu'); wireMenu('cc-audio', 'audio-menu'); wireMenu('cc-size', 'size-menu');
  wireMenu('set-lang-btn', 'lang-menu');
  const check = (ids, chosen) => ids.forEach((id) => { if (id === chosen) $(id).setAttribute('trailing-icon', 'ic_check'); else $(id).removeAttribute('trailing-icon'); });
  ['subs-off', 'subs-zh', 'subs-en'].forEach((id) => $(id).addEventListener('select', () => {
    check(['subs-off', 'subs-zh', 'subs-en'], id);
    $('cinema-subline').hidden = id === 'subs-off';
    $('subs-menu').setAttribute('hidden', '');
  }));
  $('subs-load').addEventListener('select', () => $('subs-menu').setAttribute('hidden', ''));
  ['aud-1', 'aud-2'].forEach((id) => $(id).addEventListener('select', () => { check(['aud-1', 'aud-2'], id); $('audio-menu').setAttribute('hidden', ''); }));
  const sizes = { 'size-s': [640, 360, 150], 'size-m': [1024, 576, 60], 'size-l': [1320, 742, 20] };
  Object.keys(sizes).forEach((id) => $(id).addEventListener('select', () => {
    check(Object.keys(sizes), id);
    const [w, h, top] = sizes[id];
    Object.assign($('cinema-screen').style, { width: w + 'px', height: h + 'px', top: top + 'px' });
    $('size-menu').setAttribute('hidden', '');
  }));
  ['lang-sys', 'lang-zh', 'lang-en'].forEach((id) => $(id).addEventListener('select', () => {
    langChoice = $(id).dataset.lang;
    $('lang-menu').setAttribute('hidden', '');
    setLang(langChoice === 'sys' ? (navigator.language.startsWith('zh') ? 'zh' : 'en') : langChoice);
  }));

  // Settings
  $('set-depth-slider').addEventListener('step-change', (e) => {
    depth = e.detail.step;
    document.querySelectorAll('.poster3d').forEach((el) => el.style.setProperty('--depth', depthScale[depth]));
  });
  $('set-clear').addEventListener('click-action', () => $('clear-dialog').removeAttribute('hidden'));
  ['confirm', 'dismiss', 'dismiss-request'].forEach((ev) => $('clear-dialog').addEventListener(ev, () => $('clear-dialog').setAttribute('hidden', '')));
  $('set-exit').addEventListener('click-action', () => { document.body.style.opacity = '0.35'; setTimeout(() => { document.body.style.opacity = ''; }, 900); });

  // Sources / add-source sheet
  $('src-add').addEventListener('click-action', () => $('add-sheet').removeAttribute('hidden'));
  $('add-sheet').addEventListener('dismiss-request', () => $('add-sheet').setAttribute('hidden', ''));
  const opts = ['opt-emby', 'opt-jf', 'opt-dav', 'opt-local'];
  opts.forEach((id) => $(id).addEventListener('checked-change', () => {
    opts.forEach((o) => { if (o === id) $(o).setAttribute('checked', ''); else $(o).removeAttribute('checked'); });
    $('sheet-remote').hidden = id === 'opt-local';
    $('sheet-local').hidden = id !== 'opt-local';
    $('sheet-connect').setAttribute('text', t(id === 'opt-local' ? 'sheet.pick' : 'sheet.connect'));
  }));
  $('sheet-connect').addEventListener('click-action', () => {
    const which = opts.find((o) => $(o).hasAttribute('checked'));
    const row = { 'opt-emby': 'src-jf', 'opt-jf': 'src-jf', 'opt-dav': 'src-nas', 'opt-local': 'src-local' }[which];
    $(row).hidden = false;
    $('add-sheet').setAttribute('hidden', '');
  });

  // Preview bar
  $('pv-en').addEventListener('click', () => setLang('en'));
  $('pv-zh').addEventListener('click', () => setLang('zh'));
  $('pv-shared').addEventListener('click', () => showScene('shared'));
  $('pv-cinema').addEventListener('click', () => showScene('cinema'));
  const q = new URLSearchParams(location.search);
  setLang(q.get('lang') === 'zh' ? 'zh' : 'en');
  if (q.get('tab')) { const i = +q.get('tab'); $('main-tabs').setAttribute('selected-index', String(i)); pages.forEach((p, j) => { $(p).hidden = j !== i; }); }
  if (q.get('detail')) openDetail(q.get('detail'));
  if (q.get('sheet')) $('add-sheet').removeAttribute('hidden');
  if (q.get('scene') === 'cinema') showScene('cinema');
  if (q.get('audit')) {
    setTimeout(async () => {
      await import('./review/audit-preview.js');
      const specUrl = new URL('design-spec.json', location.href).href;
      const spec = await (await fetch(specUrl)).json();
      const expectations = q.get('detail') ? JSON.parse(q.get('expect') || '{}') : {};
      const rep = await auditDesignPreview(spec, { specUrl, scenario: q.get('audit'), initial: q.get('audit') === 'initial', expectations });
      const pre = document.createElement('pre'); pre.id = 'audit-report'; pre.hidden = true; pre.textContent = JSON.stringify(rep); document.body.appendChild(pre);
    }, 1500);
  }
});
