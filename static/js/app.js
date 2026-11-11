/**
 * app.js  –  パネル管理・メインアプリケーション (ArrayAnimation)
 *
 * アルゴリズム種別 (meta.type) に応じて UI を切り替える:
 *   "search" → target 入力あり・データ条件なし
 *   "sort"   → target 入力なし・データ条件 (ランダム/昇順/降順/…) あり
 *   "misc"   → target 入力なし・データ条件なし (固定 N)
 *   "string" → テキスト T・パターン P の入力と「文字列」の種類 (ランダム/例/自由入力)
 */

"use strict";

// ===== グローバル状態 ==============================================
let algorithms = [];   // [{ id, name, meta }, ...]
let dataSizes  = [];   // [8, 16, ...]
let panelSeq   = 0;
let zoomLevel  = 1.0;

const DATA_CONDITIONS = [
  { id: 0, name: "ランダム" },
  { id: 1, name: "昇順" },
  { id: 2, name: "降順" },
  { id: 3, name: "ほぼ昇順" },
];

// ===== 文字列照合 (type: "string") ==================================
const STR_MAX_TEXT    = 64;   // algorithms.py の STR_MAX_TEXT と合わせる
const STR_MAX_PATTERN = 32;
const STR_KV_WEIGHT   = 1;    // ずらし表の枠の高さの比 (algorithms.py の STR_KV_WEIGHT と合わせる)
const STRING_KINDS = [
  { id: "acgt",   name: "ランダム (ACGT の4種)",   alpha: "ACGT" },
  { id: "ab",     name: "ランダム (A・B の2種)",   alpha: "AB" },
  { id: "alnum",  name: "ランダム (英数字62種)",   alpha: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" },
  { id: "worst",  name: "例: 最悪ケース (aaaaaaB)", text: "aaaaaaAaaaaaaCaaaaaaDaaaaaaEaaaaaaFaaaaaaaaaaaaaaB", pattern: "aaaaaaB" },
  { id: "kmp",    name: "例: KMP の定番 (ABCDABD)", text: "ABC ABCDAB ABCDABCDABDE", pattern: "ABCDABD" },
  { id: "custom", name: "自由入力" },
];

/** 種類に応じたテキストとパターンを作る。ランダムはパターンを必ず含む (長さ = データ数, 64 まで) */
function _makeString(kindId, size) {
  const kind = STRING_KINDS.find(k => k.id === kindId) || STRING_KINDS[0];
  if (kind.text) return { text: kind.text, pattern: kind.pattern };
  if (!kind.alpha) return null;
  const L  = Math.max(4, Math.min(size, STR_MAX_TEXT));
  const pl = Math.max(3, Math.min(10, Math.round(L / 4)));
  const rc = () => kind.alpha[Math.floor(Math.random() * kind.alpha.length)];
  const pat  = Array.from({ length: pl },     rc).join("");
  const body = Array.from({ length: L - pl }, rc).join("");
  const pos  = Math.floor(Math.random() * (body.length + 1));
  return { text: body.slice(0, pos) + pat + body.slice(pos), pattern: pat };
}

function _isRandomKind(kindId) {
  return !!STRING_KINDS.find(k => k.id === kindId)?.alpha;
}

// ===== スナップ設定 ================================================
const SNAP_THRESHOLD = 15;
const SNAP_GAP       = 10;

function _getTopLeftPanel(excludeEl = null) {
  let best = null, bestDist = Infinity;
  document.querySelectorAll(".panel").forEach(p => {
    if (p === excludeEl) return;
    const d = Math.sqrt(p.offsetLeft ** 2 + p.offsetTop ** 2);
    if (d < bestDist) { bestDist = d; best = p; }
  });
  return best;
}

function _snapValue(val, snapPoints, threshold) {
  let closest = val, minDiff = threshold;
  for (const sp of snapPoints) {
    const diff = Math.abs(val - sp);
    if (diff < minDiff) { minDiff = diff; closest = sp; }
  }
  return closest;
}

/** アルゴリズム ID から meta.type を返す */
function _algoType(algoId) {
  const algo = algorithms.find(a => a.id === Number(algoId));
  return algo?.meta?.type || "search";
}

// ===== ヘッダーを 2 行に収める ====================================
// ウインドウが狭いとき、ヘッダー（タイトル・ツールバー・全パネル一括）が 2 行に収まるまで、
// header に fit-1〜fit-5 を順に付けて詰める（まず文字やボタンを小さくし、次に横幅を詰める。
// 詰め方は style.css の「ヘッダーの詰め方」）。
// ウインドウの幅が変わるたびに、詰めていない状態から測り直す
const HEADER_MAX_LINES  = 2;
const HEADER_FIT_LEVELS = 5;

/** ヘッダーの中身が何行に並んでいるか（縦に重なる項目は同じ行と数える） */
function _headerLineCount(header) {
  const rects = [...header.querySelectorAll("h1, #toolbar > *, #global-controls > *")]
    .map(el => el.getBoundingClientRect())
    .filter(r => r.width > 0 && r.height > 0)
    .sort((a, b) => a.top - b.top);
  let lines = 0, bottom = -Infinity;
  for (const r of rects) {
    if (r.top >= bottom - 1) { lines++; bottom = r.bottom; }
    else bottom = Math.max(bottom, r.bottom);
  }
  return lines;
}

function _fitHeader() {
  const header = document.querySelector("header");
  if (!header) return;
  let lv = 0;
  for (;;) {
    for (let i = 1; i <= HEADER_FIT_LEVELS; i++) header.classList.toggle(`fit-${i}`, i <= lv);
    if (lv >= HEADER_FIT_LEVELS || _headerLineCount(header) <= HEADER_MAX_LINES) break;
    lv++;
  }
  header.dataset.fit = String(lv);
}

function _setupHeaderFit() {
  let pending = false;
  const request = () => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; _fitHeader(); });
  };
  window.addEventListener("resize", request);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(request);
  _fitHeader();
}

/** 「全一時停止」ボタンの表示（ヘッダーを詰めたときアイコンだけになるよう、文字は .btn-text に入れる） */
function _setPauseAllLabel(paused) {
  const btn = document.getElementById("btn-pause-all");
  if (!btn) return;
  const [icon, text] = paused ? ["▶", "全再開"] : ["⏸", "全一時停止"];
  btn.innerHTML = `${icon}<span class="btn-text">${text}</span>`;
  btn.title = text;
}

// ===== 起動 ========================================================
window.addEventListener("DOMContentLoaded", async () => {
  await loadMeta();
  _setupGlobalControls();
  _setupZoomControls();
  _setupThemeControls();
  document.getElementById("btn-add-panel")   .addEventListener("click", addPanel);
  document.getElementById("btn-start-all")   .addEventListener("click", startAll);
  document.getElementById("btn-pause-all")   .addEventListener("click", pauseAll);
  document.getElementById("btn-stop-all")    .addEventListener("click", stopAll);
  document.getElementById("btn-reset-all")   .addEventListener("click", resetAll);
  document.getElementById("btn-sync-size")   .addEventListener("click", syncSize);
  document.getElementById("btn-apply-global").addEventListener("click", applyGlobalToAll);
  addPanel();
  _setupHeaderFit();
});

async function loadMeta() {
  const [alRes, dsRes] = await Promise.all([
    fetch("/api/algorithms"),
    fetch("/api/datasizes"),
  ]);
  algorithms = await alRes.json();
  dataSizes  = await dsRes.json();
}

// ===== 速度スライダーの目盛り（パネルとヘッダーの速度スライダーで共通） =====
// スライダー値は 1〜200（index.html と パネルのテンプレートの range の min・max と同じ）。
//   左端 1 = ステップ実行（Space / Enter で 1 コマ進む）
//   20 = ×0.1、40 = ×0.5、80 = ×1、120 = ×2、160 = ×5、右端 200 = ×10。その間は等比で結ぶ
//   （×1 = 0.1 秒/フレーム、×0.5 = 0.2 秒、×0.1 = 1 秒、×10 = 0.01 秒。2〜19 は ×0.1 のまま）
// マウス・タッチでドラッグしている間は、これらの位置の近くでつまみが止まる（吸着する）。目盛りは <datalist> で表示。
// 表示の倍率は実際の 1 フレームの時間から求める（倍率 = 0.1 秒 ÷ 1 フレームの秒数）。
// 開始時・スライダー操作時・倍率表示はすべてここを通す（開始直後とスライダー操作後の速度をずらさない）
const SPEED_SLIDER_MAX  = 200;   // 右端
const SPEED_MS_X1       = 100;   // ×1 の ms/フレーム
const SPEED_STOPS       = [[20, 0.1], [40, 0.5], [80, 1], [120, 2], [160, 5], [200, 10]];   // [スライダー値, 倍率]
const SPEED_STEP_POS    = 1;     // 左端 = ステップ実行
const SPEED_STEP_MS     = 50;    // ステップ実行中、サーバーが 1 コマ送ったあとに待つ時間（この間に一時停止が届く）
const SPEED_STEP_STATUS = "ステップ実行（Space / Enter で 1 コマ）";
const SPEED_SNAP_PX     = 10;    // 止まる位置までこの距離（px）以内なら吸着する

function _speedIsStep(sliderVal) {
  return Number(sliderVal) <= SPEED_STEP_POS;
}

function _speedMult(sliderVal) {
  const v = Math.min(Math.max(Number(sliderVal), SPEED_STOPS[0][0]), SPEED_SLIDER_MAX);
  for (let i = 1; i < SPEED_STOPS.length; i++) {          // 隣り合う止まる位置の間を等比で結ぶ
    const [a, ma] = SPEED_STOPS[i - 1], [b, mb] = SPEED_STOPS[i];
    if (v <= b) return ma * (mb / ma) ** ((v - a) / (b - a));
  }
  return SPEED_STOPS[SPEED_STOPS.length - 1][1];
}

/** ms/フレーム（整数） */
function _speedMs(sliderVal) {
  if (_speedIsStep(sliderVal)) return SPEED_STEP_MS;
  return Math.round(SPEED_MS_X1 / _speedMult(sliderVal));
}

/** 秒/フレーム（サーバーへ送る値） */
function _speedSec(sliderVal) {
  return _speedMs(sliderVal) / 1000;
}

/** 表示の倍率（実際の 1 フレームの時間から求める）。×0.5・×1・×2・×5・×10 のように末尾の 0 は省く */
function _speedLabel(sliderVal) {
  if (_speedIsStep(sliderVal)) return "ステップ";
  const m = SPEED_MS_X1 / _speedMs(sliderVal);
  const s = m.toFixed(m < 1 ? 2 : 1).replace(/\.?0+$/, "");   // 1 未満は小数 2 桁まで（×0.25 など）
  return `×${s}`;
}

// 目盛りの <datalist> を 1 つだけ作り、すべての速度スライダーで共有する
function _speedTicksId() {
  const id = "speed-ticks";
  if (!document.getElementById(id)) {
    const dl = document.createElement("datalist");
    dl.id = id;
    dl.appendChild(new Option("ステップ", SPEED_STEP_POS));
    SPEED_STOPS.forEach(([v, m]) => dl.appendChild(new Option(`×${m}`, v)));
    document.body.appendChild(dl);
  }
  return id;
}

// 吸着はドラッグ中（マウス・タッチ）だけ。キーボードの矢印では 1 目盛りずつ動かせる
let _speedDragEl = null;
window.addEventListener("pointerup",     () => { _speedDragEl = null; });
window.addEventListener("pointercancel", () => { _speedDragEl = null; });

/** 速度スライダーに目盛りと吸着を付ける（input の処理では _snapSpeed を通す） */
function _setupSpeedSlider(rng) {
  rng.setAttribute("list", _speedTicksId());
  rng.addEventListener("pointerdown", () => { _speedDragEl = rng; });
}

/** ドラッグ中に止まる位置の近くなら、つまみをそこへ寄せる。寄せた後の値を返す */
function _snapSpeed(rng) {
  const v = Number(rng.value);
  if (_speedDragEl !== rng) return v;
  const set = (d) => { rng.value = d; return d; };
  const x01 = SPEED_STOPS[0][0];
  if (v < x01) return set(v - SPEED_STEP_POS < x01 - v ? SPEED_STEP_POS : x01);   // ステップと ×0.1 の間は近い方へ
  const min = Number(rng.min) || 1;
  const max = Number(rng.max) || SPEED_SLIDER_MAX;
  const pxPerUnit = rng.getBoundingClientRect().width / (max - min);
  const tol = Math.max(2, SPEED_SNAP_PX / (pxPerUnit || 1));
  let best = null;
  for (const [d] of SPEED_STOPS) {
    if (Math.abs(v - d) <= tol && (best === null || Math.abs(v - d) < Math.abs(v - best))) best = d;
  }
  return best === null ? v : set(best);
}

// ステップ実行: Space / Enter で、ステップ実行中のすべてのパネルを 1 コマ進める
// （文字の入力欄にいるときは使わない。ボタンにフォーカスがあっても、そのボタンは押さない）
function _stepPanels() {
  return [...document.querySelectorAll(".panel")].map(el => el._panel)
    .filter(p => p && p.isRunning && p._stepMode);
}
function _isTextEntry(el) {
  return !!el?.closest?.('textarea, select, [contenteditable=""], [contenteditable="true"], ' +
    'input:not([type=range]):not([type=checkbox]):not([type=radio]):not([type=button]):not([type=submit])');
}
let _stepKeyUsed = false;
document.addEventListener("keydown", (ev) => {
  if ((ev.key !== " " && ev.key !== "Enter") || ev.isComposing || ev.altKey || ev.ctrlKey || ev.metaKey) return;
  if (_isTextEntry(ev.target)) return;
  const panels = _stepPanels();
  if (!panels.length) return;
  ev.preventDefault();             // ボタンのクリックやページのスクロールにしない
  _stepKeyUsed = true;
  panels.forEach(p => p.stepOnce());
});
document.addEventListener("keyup", (ev) => {   // Space はキーを離したときにボタンが押されるので、それも止める
  if (ev.key === " " && _stepKeyUsed) ev.preventDefault();
  if (ev.key === " " || ev.key === "Enter") _stepKeyUsed = false;
});

// ===== 全パネル一括設定 ============================================

function _setupGlobalControls() {
  const gSize = document.getElementById("global-size");
  dataSizes.forEach(s => gSize.appendChild(new Option(String(s), s)));
  gSize.value = 16;

  const gCond = document.getElementById("global-condition");
  DATA_CONDITIONS.forEach(c => gCond.appendChild(new Option(c.name, c.id)));

  const gSpeed    = document.getElementById("global-speed");
  const gSpeedVal = document.getElementById("global-speed-val");
  _setupSpeedSlider(gSpeed);
  gSpeed.addEventListener("input", () => {
    gSpeedVal.textContent = _speedLabel(_snapSpeed(gSpeed));
  });
}

/** 全パネルへグローバル設定を適用 */
function applyGlobalToAll() {
  const size        = Number(document.getElementById("global-size").value);
  const speedSlider = Number(document.getElementById("global-speed").value);
  const condition   = Number(document.getElementById("global-condition").value);
  let   targetRaw   = document.getElementById("global-target").value.trim();
  const maxVal      = size >= 200 ? 999 : 99;

  // search 向け: target が空なら共通値を生成
  if (targetRaw === "") {
    targetRaw = String(Math.floor(Math.random() * maxVal) + 1);
    document.getElementById("global-target").value = targetRaw;
  }

  // search 向け: 共通データを 1 回生成して全パネルで共有
  const sharedValues = Array.from({ length: size },
                                   () => Math.floor(Math.random() * maxVal) + 1);

  // string 向け: 最初の文字列照合パネルの種類で 1 回だけ作り、全パネルで共有する
  // (同じテキスト・パターンでアルゴリズムどうしを比べられるように)
  let sharedStr = null;

  document.querySelectorAll(".panel").forEach(el => {
    const panel = el._panel;
    if (!panel) return;
    el.querySelector(".rng-speed").value = speedSlider;
    panel._applySpeed(speedSlider);
    if (!panel.isRunning) {
      const type = _algoType(el.querySelector(".sel-algo").value);
      el.querySelector(".sel-size").value = size;
      if (type === "search") {
        el.querySelector(".inp-target").value = targetRaw;
        panel._applySharedPreview(sharedValues, targetRaw);
      } else if (type === "sort") {
        el.querySelector(".sel-condition").value = condition;
        panel._drawPreview();
      } else if (type === "string") {
        if (!sharedStr) sharedStr = panel._stringForShare();
        panel._setString(sharedStr.kind, sharedStr.text, sharedStr.pattern);
        panel._drawPreview();
      } else {
        panel._drawPreview();
      }
    }
  });
}

// ===== ズーム ======================================================

function _applyZoom(level) {
  const ZOOM_MIN = 0.25, ZOOM_MAX = 2.0;
  zoomLevel = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round(level * 10) / 10));
  document.getElementById("panels-container").style.transform = `scale(${zoomLevel})`;
  document.getElementById("zoom-label").textContent = Math.round(zoomLevel * 100) + "%";
}

function _setupZoomControls() {
  document.getElementById("btn-zoom-in")   .addEventListener("click", () => _applyZoom(zoomLevel + 0.1));
  document.getElementById("btn-zoom-out")  .addEventListener("click", () => _applyZoom(zoomLevel - 0.1));
  document.getElementById("btn-zoom-reset").addEventListener("click", () => _applyZoom(1.0));
  document.getElementById("panels-container").addEventListener("wheel", (e) => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    _applyZoom(zoomLevel + (e.deltaY < 0 ? 0.1 : -0.1));
  }, { passive: false });
}

// ===== テーマ切替 ==================================================

function _applyTheme(key) {
  document.body.dataset.theme = key;
  setCanvasTheme(key);
  document.querySelectorAll(".theme-btn").forEach(b => {
    b.classList.toggle("theme-active", b.dataset.th === key);
  });
  document.querySelectorAll(".panel").forEach(el => {
    const panel = el._panel;
    if (!panel) return;
    if (panel.arrayCanvas && panel._lastFrame) {
      // 完了後の最終状態もテーマ切替で消えないよう、最新フレームを保持したまま再描画
      panel.arrayCanvas.draw(panel._lastFrame);
    } else {
      panel._drawPreview();
    }
  });
}

function _setupThemeControls() {
  document.querySelectorAll(".theme-btn").forEach(btn => {
    btn.addEventListener("click", () => _applyTheme(btn.dataset.th));
  });
}

// ===== コンテナサイズ更新 ==========================================

function _updateContainerSize() {
  const container = document.getElementById("panels-container");
  let maxRight = 0, maxBottom = 0;
  container.querySelectorAll(".panel").forEach(p => {
    maxRight  = Math.max(maxRight,  p.offsetLeft + p.offsetWidth  + 20);
    maxBottom = Math.max(maxBottom, p.offsetTop  + p.offsetHeight + 20);
  });
  container.style.minWidth  = maxRight  + "px";
  container.style.minHeight = maxBottom + "px";
}

// ===== サイズ統一 ==================================================

function syncSize() {
  const panels = [...document.querySelectorAll(".panel")];
  if (panels.length < 2) return;
  const front =
    document.querySelector(".panel.front") ||
    panels.reduce((a, b) =>
      (parseInt(b.style.zIndex) || 1) > (parseInt(a.style.zIndex) || 1) ? b : a
    );
  const w = front.offsetWidth, h = front.offsetHeight;
  panels.forEach(el => {
    if (el !== front) { el.style.width = w + "px"; el.style.height = h + "px"; }
  });
}

// ===== パネル追加 ==================================================
function addPanel() {
  const panel = new ArrayPanel(++panelSeq);
  panel.mount(document.getElementById("panels-container"));
}

// ===== 全開始 / 全一時停止 / 全停止 / 全リセット ====================
function startAll() {
  document.querySelectorAll(".panel").forEach(el => {
    const p = el._panel;
    if (p && !p.isRunning) p.start();
  });
}
function pauseAll() {
  const panels = [...document.querySelectorAll(".panel")]
    .map(el => el._panel).filter(p => p && p.isRunning);
  const anyRunning = panels.some(p => !p.isPaused);
  panels.forEach(p => {
    if (anyRunning && !p.isPaused) p.togglePause();
    else if (!anyRunning && p.isPaused) p.togglePause();
  });
  _setPauseAllLabel(anyRunning);
}
function stopAll() {
  document.querySelectorAll(".panel").forEach(el => {
    const p = el._panel;
    if (p && p.isRunning) p.stop();
  });
  _setPauseAllLabel(false);
}
function resetAll() {
  document.querySelectorAll(".panel").forEach(el => {
    const p = el._panel;
    if (p) p.reset();
  });
  _setPauseAllLabel(false);
}

// ===================================================================
// ArrayPanel クラス
// ===================================================================
class ArrayPanel {
  constructor(id) {
    this.id          = id;
    this.sessionId   = null;
    this.client      = null;
    this.arrayCanvas = null;
    this.el          = null;
    this.isRunning   = false;
    this.isPaused    = false;
    this.numItems    = 0;
    this._lastFrame  = null;
    this._frameCount = 0;
    this._speed      = 0.1;
    // 文字列照合: リセット・リサイズ・テーマ切替では作り直さない (種類・データ数の変更と 🎲 でのみ作り直す)
    this._strKind    = "acgt";
    this._strText    = null;
    this._strPattern = null;
  }

  // ── DOM 構築 ────────────────────────────────────────────────────
  mount(container) {
    const el = document.createElement("div");
    el.className = "panel";
    el._panel    = this;
    el.id        = `panel-${this.id}`;
    el.innerHTML = this._template();

    let initLeft = 0, initTop = 0;
    const existing = container.querySelectorAll(".panel");
    if (existing.length > 0) {
      let maxRight = 0, maxBottom = 0;
      existing.forEach(p => {
        maxRight  = Math.max(maxRight,  p.offsetLeft + p.offsetWidth  + 12);
        maxBottom = Math.max(maxBottom, p.offsetTop  + p.offsetHeight + 12);
      });
      const panelW = 520;
      if (maxRight + panelW <= window.innerWidth) {
        initLeft = maxRight; initTop = 0;
      } else {
        initLeft = 0; initTop = maxBottom;
      }
    }
    el.style.left = initLeft + "px";
    el.style.top  = initTop  + "px";
    container.appendChild(el);
    this.el = el;

    this._bind();
    this._populateSelects();
    this._updateParamVisibility();
    { let mz = 0;
      document.querySelectorAll(".panel").forEach(p =>
        { mz = Math.max(mz, parseInt(p.style.zIndex) || 1); });
      el.style.zIndex = mz + 1; }
    requestAnimationFrame(() => this._drawPreview());
    return el;
  }

  _template() {
    return `
      <div class="panel-header">
        <span class="drag-handle" title="ドラッグして移動">⠿</span>
        <span class="panel-title">パネル ${this.id}</span>
        <button class="panel-close" title="削除">✕</button>
      </div>

      <div class="params-row">
        <label>アルゴリズム
          <select class="sel-algo"></select>
        </label>
      </div>
      <div class="params-row">
        <label class="lbl-size">データ数
          <select class="sel-size"></select>
        </label>
        <label class="lbl-target">target
          <input type="number" class="inp-target" min="0" max="999" placeholder="自動"
                 style="width:60px" title="探索する値 (空欄=自動)">
        </label>
        <label class="lbl-condition" style="display:none">データ条件
          <select class="sel-condition"></select>
        </label>
        <label class="lbl-strkind" style="display:none">文字列
          <select class="sel-strkind"></select>
        </label>
        <button class="btn btn-secondary btn-str-regen" style="display:none"
                title="同じ種類で文字列を作り直す">🎲</button>
        <div class="speed-group speed-main">
          <label>速度</label>
          <input type="range" class="rng-speed" min="1" max="200" value="80"
                 title="大きいほど速い。左端はステップ実行（Space / Enter で 1 コマ）。ステップ・×0.1・×0.5・×1・×2・×5・×10 で止まる">
          <span class="speed-value">×1</span>
        </div>
      </div>
      <div class="params-row str-row" style="display:none">
        <label class="lbl-str lbl-str-text">T
          <input type="text" class="inp-text" maxlength="${STR_MAX_TEXT}" spellcheck="false"
                 autocomplete="off" title="テキスト (${STR_MAX_TEXT} 文字まで)">
        </label>
        <label class="lbl-str lbl-str-pat">P
          <input type="text" class="inp-pattern" maxlength="${STR_MAX_PATTERN}" spellcheck="false"
                 autocomplete="off" title="パターン (${STR_MAX_PATTERN} 文字まで)">
        </label>
        <span class="str-error"></span>
      </div>

      <div class="controls-row">
        <button class="btn btn-primary   btn-start">▶ 開始</button>
        <button class="btn btn-warning   btn-pause" disabled>⏸ 一時停止</button>
        <button class="btn btn-danger    btn-stop"  disabled>⏹ 停止</button>
        <button class="btn btn-secondary btn-reset" disabled>↺ リセット</button>
      </div>

      <div class="canvas-wrapper">
        <canvas class="array-canvas"></canvas>
        <div class="text-overlay">（開始ボタンを押してください）</div>
      </div>

      <div class="status-bar">
        <span class="status-algo">-</span>
        <span class="status-state">待機中</span>
        <span class="status-frames">フレーム: 0</span>
        <span class="status-done-badge"></span>
      </div>
      <div class="resize-handle" title="リサイズ"></div>
    `;
  }

  // ── セレクトを動的に生成 ─────────────────────────────────────
  _populateSelects() {
    const selAlgo = this.el.querySelector(".sel-algo");
    algorithms.forEach(a => selAlgo.appendChild(new Option(a.name, a.id)));
    selAlgo.value = (this.id - 1) % algorithms.length;

    const selSize = this.el.querySelector(".sel-size");
    dataSizes.forEach(s => selSize.appendChild(new Option(String(s), s)));
    selSize.value = document.getElementById("global-size")?.value || 16;

    const selCond = this.el.querySelector(".sel-condition");
    DATA_CONDITIONS.forEach(c => selCond.appendChild(new Option(c.name, c.id)));

    const selKind = this.el.querySelector(".sel-strkind");
    STRING_KINDS.forEach(k => selKind.appendChild(new Option(k.name, k.id)));
    selKind.value = this._strKind;

    const gSpeed = document.getElementById("global-speed")?.value;
    if (gSpeed) {
      this.el.querySelector(".rng-speed").value = gSpeed;
      this._applySpeed(Number(gSpeed));
    }
  }

  // ── アルゴリズム種別に応じて UI を表示/非表示 ─────────────────
  _updateParamVisibility() {
    const algoId = Number(this.el.querySelector(".sel-algo").value);
    const type   = _algoType(algoId);

    this.el.querySelector(".lbl-target")   .style.display = type === "search" ? "" : "none";
    this.el.querySelector(".lbl-condition").style.display = type === "sort"   ? "" : "none";
    // lbl-size は常に表示 (misc でも num_items は参照される。string ではランダムな文字列の長さ)
    const isStr = (type === "string");
    this.el.querySelector(".lbl-strkind")  .style.display = isStr ? "" : "none";
    this.el.querySelector(".btn-str-regen").style.display = isStr ? "" : "none";
    this.el.querySelector(".str-row")      .style.display = isStr ? "" : "none";
    this.el.querySelector(".lbl-size").title =
      isStr ? `ランダムな文字列の長さ (${STR_MAX_TEXT} 文字まで)` : "";
    if (isStr && this._strText === null) this._regenString();
  }

  // ── 文字列照合: テキスト・パターン ─────────────────────────────
  /** 入力の誤りを返す (問題なければ null)。文字数は Python と同じくコードポイント単位 */
  _strError() {
    const t = [...(this._strText ?? "")].length;
    const p = [...(this._strPattern ?? "")].length;
    if (t === 0)               return "テキスト T を入力してください";
    if (p === 0)               return "パターン P を入力してください";
    if (t > STR_MAX_TEXT)      return `T は ${STR_MAX_TEXT} 文字までです`;
    if (p > STR_MAX_PATTERN)   return `P は ${STR_MAX_PATTERN} 文字までです`;
    if (p > t)                 return "P が T より長くなっています";
    return null;
  }

  _showStrStatus() {
    const err = this._strError();
    const sp  = this.el.querySelector(".str-error");
    sp.textContent = err
      ? `⚠ ${err}`
      : `n = ${[...this._strText].length}, m = ${[...this._strPattern].length}`;
    sp.classList.toggle("is-error", !!err);
    // 🎲 はランダムの種類のときだけ意味がある
    this.el.querySelector(".btn-str-regen").disabled = !_isRandomKind(this._strKind);
  }

  _setString(kind, text, pattern) {
    this._strKind    = kind;
    this._strText    = text;
    this._strPattern = pattern;
    this.el.querySelector(".sel-strkind").value = kind;
    this.el.querySelector(".inp-text")   .value = text;
    this.el.querySelector(".inp-pattern").value = pattern;
    this._showStrStatus();
  }

  /** 選んでいる種類で作り直す (自由入力のときは今の文字列のまま) */
  _regenString() {
    const kind = this.el.querySelector(".sel-strkind").value;
    if (kind === "custom") {
      this._strKind = kind;
      if (this._strText === null) this._setString(kind, "", "");
      else this._showStrStatus();
      return;
    }
    const size = Number(this.el.querySelector(".sel-size").value) || 16;
    const s = _makeString(kind, size);
    this._setString(kind, s.text, s.pattern);
  }

  /** 全パネル一括適用で共有する文字列 (ランダムならデータ数を反映して作り直す) */
  _stringForShare() {
    if (this.el.querySelector(".sel-strkind").value !== "custom" || this._strText === null) {
      this._regenString();
    }
    return { kind: this._strKind, text: this._strText, pattern: this._strPattern };
  }

  // ── イベントバインド ─────────────────────────────────────────
  _bind() {
    const q = (sel) => this.el.querySelector(sel);

    q(".panel-close").addEventListener("click", () => this.destroy());
    q(".btn-start")  .addEventListener("click", () => this.start());
    q(".btn-pause")  .addEventListener("click", () => this.togglePause());
    q(".btn-stop")   .addEventListener("click", () => this.stop());
    q(".btn-reset")  .addEventListener("click", () => this.reset());

    _setupSpeedSlider(q(".rng-speed"));
    q(".rng-speed").addEventListener("input", (ev) => {
      this._applySpeed(_snapSpeed(ev.target));
    });

    q(".sel-algo").addEventListener("change", () => {
      if (!this.isRunning) { this._updateParamVisibility(); this._drawPreview(); }
    });
    q(".sel-size")     .addEventListener("change", () => {
      if (this.isRunning) return;
      // 文字列照合: ランダムの種類なら新しい長さで作り直す
      if (_algoType(q(".sel-algo").value) === "string" && _isRandomKind(this._strKind)) {
        this._regenString();
      }
      this._drawPreview();
    });
    q(".sel-strkind")  .addEventListener("change", () => {
      this._regenString();
      if (!this.isRunning) this._drawPreview();
    });
    q(".btn-str-regen").addEventListener("click", () => {
      this._regenString();
      if (!this.isRunning) this._drawPreview();
    });
    const onStrInput = () => {
      // 手で書き換えたら「自由入力」に切り替える
      this._strText    = q(".inp-text").value;
      this._strPattern = q(".inp-pattern").value;
      this._strKind    = "custom";
      q(".sel-strkind").value = "custom";
      this._showStrStatus();
      if (!this.isRunning) this._drawPreview();
    };
    q(".inp-text")   .addEventListener("input", onStrInput);
    q(".inp-pattern").addEventListener("input", onStrInput);
    q(".inp-target")   .addEventListener("change", () => { if (!this.isRunning) this._drawPreview(); });
    q(".sel-condition").addEventListener("change", () => { if (!this.isRunning) this._drawPreview(); });

    this.el.addEventListener("mousedown", () => this._bringToFront());

    const ro = new ResizeObserver(() => this._onResize());
    ro.observe(this.el);
    ro.observe(q(".canvas-wrapper"));

    // ── ドラッグ (Pointer Events) ────────────────────────────────
    const handle = q(".drag-handle");
    handle.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      handle.setPointerCapture(e.pointerId);
      this._bringToFront();
      handle.style.cursor = "grabbing";
      let prevX = e.clientX, prevY = e.clientY;

      const onMove = (mv) => {
        const dx = (mv.clientX - prevX) / zoomLevel;
        const dy = (mv.clientY - prevY) / zoomLevel;
        prevX = mv.clientX; prevY = mv.clientY;
        this.el.style.left = ((parseFloat(this.el.style.left) || 0) + dx) + "px";
        this.el.style.top  = ((parseFloat(this.el.style.top)  || 0) + dy) + "px";
        _updateContainerSize();
      };
      const onUp = () => {
        handle.style.cursor = "";
        handle.removeEventListener("pointermove",   onMove);
        handle.removeEventListener("pointerup",     onUp);
        handle.removeEventListener("pointercancel", onUp);
        // リリース時にスナップ適用（ドラッグ中は吸着させない）
        const ref = _getTopLeftPanel(this.el);
        if (ref) {
          const rL = ref.offsetLeft, rT = ref.offsetTop;
          const rR = rL + ref.offsetWidth, rB = rT + ref.offsetHeight;
          const cW = this.el.offsetWidth,   cH = this.el.offsetHeight;
          this.el.style.left = _snapValue(parseFloat(this.el.style.left) || 0,
            [rL, rR - cW, rR + SNAP_GAP, rL - cW - SNAP_GAP], SNAP_THRESHOLD) + "px";
          this.el.style.top  = _snapValue(parseFloat(this.el.style.top)  || 0,
            [rT, rB - cH, rB + SNAP_GAP, rT - cH - SNAP_GAP], SNAP_THRESHOLD) + "px";
          _updateContainerSize();
        }
      };
      handle.addEventListener("pointermove",   onMove);
      handle.addEventListener("pointerup",     onUp);
      handle.addEventListener("pointercancel", onUp);
    });

    // ── リサイズ (Pointer Events) ────────────────────────────────
    const resizeEl = q(".resize-handle");
    resizeEl.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      e.stopPropagation();
      resizeEl.setPointerCapture(e.pointerId);
      let prevX = e.clientX, prevY = e.clientY;

      const onMove = (mv) => {
        const dx = (mv.clientX - prevX) / zoomLevel;
        const dy = (mv.clientY - prevY) / zoomLevel;
        prevX = mv.clientX; prevY = mv.clientY;
        this.el.style.width  = Math.max(280, this.el.offsetWidth  + dx) + "px";
        this.el.style.height = Math.max(340, this.el.offsetHeight + dy) + "px";
      };
      const onUp = () => {
        resizeEl.removeEventListener("pointermove",   onMove);
        resizeEl.removeEventListener("pointerup",     onUp);
        resizeEl.removeEventListener("pointercancel", onUp);
      };
      resizeEl.addEventListener("pointermove",   onMove);
      resizeEl.addEventListener("pointerup",     onUp);
      resizeEl.addEventListener("pointercancel", onUp);
    });
  }

  // ── 最前面へ ──────────────────────────────────────────────────
  _bringToFront() {
    let maxZ = 0;
    document.querySelectorAll(".panel").forEach(p => {
      maxZ = Math.max(maxZ, parseInt(p.style.zIndex) || 1);
    });
    this.el.style.zIndex = maxZ + 1;
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("front"));
    this.el.classList.add("front");
  }

  // ── リサイズハンドラ ─────────────────────────────────────────
  _onResize() {
    const ref = _getTopLeftPanel(this.el);
    if (ref) {
      const snapW = _snapValue(this.el.offsetWidth,  [ref.offsetWidth],  SNAP_THRESHOLD);
      const snapH = _snapValue(this.el.offsetHeight, [ref.offsetHeight], SNAP_THRESHOLD);
      if (snapW !== this.el.offsetWidth)  this.el.style.width  = snapW + "px";
      if (snapH !== this.el.offsetHeight) this.el.style.height = snapH + "px";
    }

    const wrapper = this.el.querySelector(".canvas-wrapper");
    const canvas  = this.el.querySelector(".array-canvas");
    const w = wrapper.clientWidth, h = wrapper.clientHeight;
    if (w <= 0 || h <= 0) return;

    const sizeChanged = (canvas.width !== w || canvas.height !== h);
    if (!sizeChanged) return;
    canvas.width = w; canvas.height = h;

    if (this._lastFrame) {
      const ac = new ArrayCanvas(canvas);
      if (this.isRunning && this.arrayCanvas) {
        this.arrayCanvas.canvas = canvas;
        this.arrayCanvas.ctx    = canvas.getContext("2d");
      }
      ac.draw(this._lastFrame);
    } else {
      this._drawPreviewOnCanvas(canvas);
    }
  }

  // ── プレビュー描画 ──────────────────────────────────────────
  _drawPreview() {
    const wrapper = this.el.querySelector(".canvas-wrapper");
    const canvas  = this.el.querySelector(".array-canvas");
    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight || Math.round(w * 0.55);
    if (w <= 0) return;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
    }
    this._drawPreviewOnCanvas(canvas);
  }

  /** 全パネル一括適用: 外部から共有データを渡して search プレビューを描画 */
  _applySharedPreview(sharedValues, targetRaw) {
    const wrapper = this.el.querySelector(".canvas-wrapper");
    const canvas  = this.el.querySelector(".array-canvas");
    const w = wrapper.clientWidth;
    const h = wrapper.clientHeight || Math.round(w * 0.55);
    if (w <= 0) return;
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
    }
    const algoId = Number(this.el.querySelector(".sel-algo").value);
    const algo   = algorithms.find(a => a.id === algoId);
    const sorted = !!(algo?.meta?.sorted);
    const forced = targetRaw !== "" ? Number(targetRaw) : null;
    this._lastFrame = null;   // 前回の終了フレームを破棄（_drawPreviewOnCanvas と同じ理由）
    this._previewCache = new ArrayCanvas(canvas).drawPreview(
      sharedValues.length, sorted, forced, sharedValues, true, "cells"
    );
  }

  _drawPreviewOnCanvas(canvas) {
    // 表示をプレビューに置き換えるので、前回の終了フレームを破棄する
    // （残すと、完了後にデータ数変更などでプレビューを差し替えたあと、
    //   リサイズ・テーマ切替で前回の終了状態が描き直される）
    this._lastFrame = null;
    const numItems = Number(this.el.querySelector(".sel-size").value) || 16;
    const algoId   = Number(this.el.querySelector(".sel-algo").value);
    const algo     = algorithms.find(a => a.id === algoId);
    const type     = algo?.meta?.type || "search";

    // misc 型 (階乗・フィボナッチ等) は配列を使わないため空白キャンバスを表示
    if (type === "misc") {
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = _acTheme().canvasBg;   // 今のテーマの背景色（固定の暗い色だと明るいテーマで黒く見えた）
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      return;
    }

    // string 型: パターンをテキストの先頭に合わせた状態を表示
    if (type === "string") {
      if (this._strText === null) this._regenString();
      // 実行中のフレーム (algorithms.py の _string_run) と同じ枠で描く:
      //   説明 2 行・列数 = テキスト長 + パターン長・ずらし表の枠 (空)
      //   → 開始しても、またアルゴリズムが違っても T・P の大きさと位置が変わらない
      // (1 行目は「開始ボタンを押してください」の表示と重なるので空けておく)
      const T   = [...this._strText];
      const P   = [...this._strPattern];
      const err = this._strError();
      this._previewCache = null;
      new ArrayCanvas(canvas).draw({
        objects: [
          {
            id: "sm", type: "string_match",
            text: T, pattern: P.length ? P : null, shift: 0,
            cols: Math.max(T.length + P.length, 1),
            text_label: "T", pattern_label: "P", weight: 3,
          },
          { id: "kv", type: "kv_table", label: "", keys: [], values: [], weight: STR_KV_WEIGHT },
        ],
        texts: [
          { message: "", color: "white" },
          err ? { message: `⚠ ${err}`, color: "#ff6666" }
              : { message: `テキスト T: n = ${T.length}   パターン P: m = ${P.length}`, color: "white" },
        ],
        finished: false,
      });
      return;
    }

    const sorted     = !!(algo?.meta?.sorted);
    const showTarget = (type === "search");
    const tRaw       = this.el.querySelector(".inp-target").value.trim();
    const forced     = (showTarget && tRaw !== "") ? Number(tRaw) : null;
    this._previewCache = new ArrayCanvas(canvas).drawPreview(
      numItems, sorted, forced, null, showTarget, "cells"
    );
  }

  // ── スピード変換（目盛りはファイル先頭の _speedMult / _speedSec） ──
  _applySpeed(sliderVal) {
    const speed = _speedSec(sliderVal);
    this.el.querySelector(".speed-value").textContent = _speedLabel(sliderVal);
    if (this.client) this.client.setSpeed(speed);
    this._speed = speed;
    this._setStepMode(_speedIsStep(sliderVal));
  }

  _currentSpeed() {
    return _speedSec(this.el.querySelector(".rng-speed").value);
  }

  // ── ステップ実行（速度スライダーが左端。Space / Enter で 1 コマ進む） ──
  // サーバーへは「1 コマ届いたら一時停止・キーで再開」を送る（サーバー側は変更不要）。
  // 一時停止が届く前にサーバーが次のコマを送っても、捨てずにためて次のキーで表示する。
  _stepReset() {
    this._stepWanted     = this._stepMode ? 1 : 0;   // 開始直後の 1 コマ目は表示する
    this._stepHold       = false;                    // ステップ実行のためにサーバーを止めているか
    this._stepQueue      = [];
    this._stepCloseLater = false;
  }

  _onWsFrame(frame) {
    if (!this._stepMode) { this._onFrame(frame); return; }
    if (!this._stepHold) { this.client?.pause(); this._stepHold = true; }   // 1 コマ届いたら止める
    if (this._stepWanted > 0 && !this._stepQueue.length) { this._stepWanted--; this._onFrame(frame); }
    else this._stepQueue.push(frame);
  }

  stepOnce() {
    if (!this.isRunning || !this._stepMode) return;
    if (this._stepQueue?.length) {
      this._onFrame(this._stepQueue.shift());
      if (!this._stepQueue.length && this._stepCloseLater) { this._stepCloseLater = false; this._onClose(); }
      return;
    }
    this._stepWanted = 1;
    if (this._stepHold) { this.client?.resume(); this._stepHold = false; }
  }

  _setStepMode(on) {
    if (on === !!this._stepMode) return;
    this._stepMode = on;
    if (!this.isRunning) return;
    if (on) {
      if (this.isPaused) {            // 一時停止中にステップ実行へ: サーバーは止めたまま、ボタンの表示だけ戻す
        this.isPaused  = false;
        this._stepHold = true;
        this.el.querySelector(".btn-pause").textContent = "⏸ 一時停止";
      }
      this._stepWanted = 0;
      if (!this._stepHold) { this.client?.pause(); this._stepHold = true; }
      this._showStepUi();
    } else {
      this._setBtns({ start: false, pause: true, stop: true, reset: false });
      this._setStatus("実行中", "#90caf9");
      this._stepDrain();
    }
  }

  _showStepUi() {
    this._setBtns({ start: false, pause: false, stop: true, reset: false });
    this._setStatus(SPEED_STEP_STATUS, "#FFD700");
  }

  // ステップ実行をやめたとき: ためたコマを今の速さで表示してから、サーバーを再開する
  _stepDrain() {
    if (!this.isRunning || this._stepMode) return;
    if (this._stepQueue?.length) {
      this._onFrame(this._stepQueue.shift());
      setTimeout(() => this._stepDrain(), this._speed * 1000);
      return;
    }
    if (this._stepCloseLater) { this._stepCloseLater = false; this._onClose(); return; }
    if (this._stepHold) { this.client?.resume(); this._stepHold = false; }
  }

  // ── 開始 ────────────────────────────────────────────────────────
  async start() {
    if (this.isRunning) return;

    const algoId   = Number(this.el.querySelector(".sel-algo").value);
    const numItems = Number(this.el.querySelector(".sel-size").value);
    const speed    = this._currentSpeed();
    const type     = _algoType(algoId);

    if (type === "string") {
      if (this._strText === null) this._regenString();
      const err = this._strError();
      if (err) {
        this._setStatus(`入力エラー: ${err}`, "red");
        return;
      }
    }

    let info;
    try {
      const body = { algorithm_id: algoId, num_items: numItems, speed };

      if (type === "search") {
        const tRaw = this.el.querySelector(".inp-target").value.trim();
        if (tRaw !== "") {
          body.target = Number(tRaw);
        } else if (this._previewCache?.target !== undefined && this._previewCache.target !== null) {
          body.target = this._previewCache.target;
        }
        if (this._previewCache?.values) {
          body.data = this._previewCache.values;
        }
      } else if (type === "sort") {
        body.data_condition = Number(this.el.querySelector(".sel-condition").value);
        if (this._previewCache?.values) {
          body.data = this._previewCache.values;
        }
      } else if (type === "string") {
        body.text    = this._strText;
        body.pattern = this._strPattern;
      }
      // misc: num_items だけ送れば OK

      const res = await fetch("/api/start", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(await res.text());
      info = await res.json();
    } catch (e) {
      this._setStatus(`エラー: ${e.message}`, "red");
      return;
    }

    this.sessionId   = info.session_id;
    this.numItems    = info.num_items;
    this.isRunning   = true;
    this.isPaused    = false;
    this._lastFrame  = null;
    this._frameCount = 0;

    const canvas = this.el.querySelector(".array-canvas");
    this.arrayCanvas = new ArrayCanvas(canvas);

    this.el.querySelector(".panel-title").textContent = info.algo_name;
    this.el.classList.add("running");
    this.el.classList.remove("finished");
    this._setStatus("実行中", "#90caf9");
    this._setBtns({ start: false, pause: true, stop: true, reset: false });
    this.el.querySelector(".status-algo").textContent   = info.algo_name;
    this.el.querySelector(".text-overlay").textContent  = "";
    this._clearDoneBadge();

    // ステップ実行（速度スライダーが左端）なら、1 コマ目を表示したあと Space / Enter を待つ
    this._stepMode = _speedIsStep(this.el.querySelector(".rng-speed").value);
    this._stepReset();
    if (this._stepMode) this._showStepUi();

    this.client = new AnimationClient(
      this.sessionId,
      (frame) => this._onWsFrame(frame),
      ()      => this._onClose(),
      ()      => this._setStatus("接続エラー", "red"),
    );
    this.client.connect();
  }

  // ── フレーム受信 ─────────────────────────────────────────────
  _onFrame(frame) {
    this._lastFrame  = frame;
    this._frameCount = (this._frameCount ?? 0) + 1;

    this.arrayCanvas.draw(frame);
    this.el.querySelector(".status-frames").textContent = `フレーム: ${this._frameCount}`;

    if (frame.finished) {
      this.isRunning = false;
      this.el.classList.remove("running");
      this.el.classList.add("finished");
      this._setStatus("完了", "#44aa44");
      this._setBtns({ start: false, pause: false, stop: false, reset: true });
      // Found/Not Found/完了は、キャンバス上のデータをdimして隠さないよう
      // ステータスバーの固定背景色バッジにのみ表示する
      this._showDoneBadge(frame);
    }
  }

  _showDoneBadge(frame) {
    const badge = this.el.querySelector(".status-done-badge");
    badge.classList.remove("badge-found", "badge-notfound", "flash");
    if (frame.found === true) {
      badge.textContent = "✅ Found !";
      badge.classList.add("badge-found");
    } else if (frame.found === false) {
      badge.textContent = "❌ Not Found";
      badge.classList.add("badge-notfound");
    } else {
      badge.textContent = "🎉 完了!";
    }
    badge.classList.add("visible");
    void badge.offsetWidth;
    badge.classList.add("flash");
  }

  _clearDoneBadge() {
    const badge = this.el.querySelector(".status-done-badge");
    badge.textContent = "";
    badge.classList.remove("visible", "badge-found", "badge-notfound", "flash");
  }

  // ── WebSocket クローズ ────────────────────────────────────────
  _onClose() {
    if (this._stepQueue?.length) { this._stepCloseLater = true; return; }   // ためたコマを表示し終えてから閉じる
    if (this.isRunning) {
      this.isRunning = false;
      this.el.classList.remove("running");
      this._setStatus("切断", "#888");
      this._setBtns({ start: true, pause: false, stop: false, reset: false });
    }
  }

  // ── 一時停止 / 再開 ────────────────────────────────────────────
  togglePause() {
    if (!this.isRunning) return;
    if (this._stepMode) return;   // ステップ実行中は Space / Enter で進める（一時停止ボタンは使わない）
    this.isPaused = !this.isPaused;
    const btn = this.el.querySelector(".btn-pause");
    if (this.isPaused) {
      this.client.pause();
      btn.textContent = "▶ 再開";
      this._setStatus("一時停止", "#FFD700");
    } else {
      this.client.resume();
      btn.textContent = "⏸ 一時停止";
      this._setStatus("実行中", "#90caf9");
    }
  }

  // ── 停止 ─────────────────────────────────────────────────────
  stop() {
    if (!this.isRunning) return;
    this._stepReset();
    this.client?.stop();
    this.client?.disconnect();
    this.client    = null;
    this.isRunning = false;
    this.el.classList.remove("running");
    this._setStatus("停止", "#888");
    this._setBtns({ start: true, pause: false, stop: false, reset: true });
  }

  // ── リセット ─────────────────────────────────────────────────
  reset() {
    if (this.isRunning) this.stop();
    this.el.querySelector(".text-overlay").textContent  = "（開始ボタンを押してください）";
    this.el.querySelector(".status-frames").textContent = "フレーム: 0";
    this._clearDoneBadge();
    this.el.classList.remove("finished");
    this._setStatus("待機中", "#888");
    this._setBtns({ start: true, pause: false, stop: false, reset: false });
    this.arrayCanvas = null;
    this._lastFrame  = null;
    this._frameCount = 0;
    this._drawPreview();
  }

  // ── パネル削除 ───────────────────────────────────────────────
  destroy() {
    this.stop();
    this.el?.remove();
  }

  // ── ヘルパー ─────────────────────────────────────────────────
  _setBtns({ start, pause, stop, reset }) {
    const q = (s) => this.el.querySelector(s);
    q(".btn-start").disabled = !start;
    q(".btn-pause").disabled = !pause;
    q(".btn-stop") .disabled = !stop;
    q(".btn-reset").disabled = !reset;
    if (!pause) q(".btn-pause").textContent = "⏸ 一時停止";
  }

  _setStatus(text, color = "#aaa") {
    const el = this.el.querySelector(".status-state");
    el.textContent = text;
    el.style.color = color;
  }
}
