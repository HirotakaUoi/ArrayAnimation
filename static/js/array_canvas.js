/**
 * array_canvas.js  –  多種オブジェクト描画ユーティリティ
 *
 * 対応オブジェクト type:
 *   array1d        – 縦棒グラフ (後方互換)
 *   array1d_cells  – 正方形セル配列
 *   heap_tree      – ヒープ二分木
 *   bucket_rows    – バケツ行 / 動的キュー
 *   tape           – 無端テープ
 *   fib_tree       – フィボナッチ再帰木
 *   staircase      – 階段状テキスト (階乗再帰)
 *   string_match   – 文字列照合 (上段パターン / 下段テキスト + 比較・ずらしの注釈)
 *   kv_table       – キーと値の 2 段の表 (BMH のずらし表)
 */

"use strict";

// ---------------------------------------------------------------------------
// カラーテーマ (canvas 背景・ラベル色のみ)
// ---------------------------------------------------------------------------
const AC_THEMES = {
  dark: {
    canvasBg: "#0d1117",  valueLabelColor: "#ccc",  indexLabelColor: "#4a6080",
    foundCellBg: "#1a4a1a", foundCellText: "#44cc44",
    cellBg: "#1c2a3a",    cellEmptyBg: "#0a0e18",   nodeBg: "#0d1117",
    cellText: "#ffffff",  cellValueColor: "#dddddd",
    edgeColor: "#334455", dimEdge: "#1a2535",       ghostFill: "#0f1820",
    ghostStroke: "#1c2d3e", ghostText: "#253545",
    labelColor: "#6a8faf", badgeText: "#0d1117",
    emptyText: "#445566", textOverlay: "rgba(10,14,26,0.85)",
    connectorColor: "#2a4060",
  },
  bright: {
    canvasBg: "#f0f4ff",  valueLabelColor: "#334",  indexLabelColor: "#668",
    foundCellBg: "#b8f0b8", foundCellText: "#005500",
    cellBg: "#d8e8f8",    cellEmptyBg: "#e4eefa",   nodeBg: "#dce8f4",
    cellText: "#1a2a3a",  cellValueColor: "#223344",
    edgeColor: "#6688aa", dimEdge: "#99aabb",       ghostFill: "#dce8f4",
    ghostStroke: "#aabbcc", ghostText: "#8899aa",
    labelColor: "#6a8faf", badgeText: "#0d1117",
    emptyText: "#667788", textOverlay: "rgba(10,20,40,0.88)",
    connectorColor: "#6688aa",
  },
  hc: {
    canvasBg: "#000000",  valueLabelColor: "#fff",  indexLabelColor: "#888",
    foundCellBg: "#003300", foundCellText: "#00ff66",
    cellBg: "#182030",    cellEmptyBg: "#060810",   nodeBg: "#000000",
    cellText: "#ffffff",  cellValueColor: "#eeeeee",
    edgeColor: "#557799", dimEdge: "#223344",       ghostFill: "#080c14",
    ghostStroke: "#223344", ghostText: "#445566",
    labelColor: "#8899aa", badgeText: "#000000",
    emptyText: "#556677", textOverlay: "rgba(0,0,0,0.90)",
    connectorColor: "#446688",
  },
  hcbright: {
    canvasBg: "#ffffff",  valueLabelColor: "#111",  indexLabelColor: "#445",
    foundCellBg: "#a8eea8", foundCellText: "#003300",
    cellBg: "#d0e0f0",    cellEmptyBg: "#e4eefa",   nodeBg: "#dce8f4",
    cellText: "#1a2a3a",  cellValueColor: "#1a2a3a",
    edgeColor: "#5577aa", dimEdge: "#99aabb",       ghostFill: "#dce8f4",
    ghostStroke: "#aabbcc", ghostText: "#8899aa",
    labelColor: "#5577aa", badgeText: "#0d1117",
    emptyText: "#556677", textOverlay: "rgba(10,20,40,0.88)",
    connectorColor: "#5577aa",
  },
};
let _acThemeKey = "bright";   // 初期テーマは明るめ（index.html の <body data-theme> と ☀ ボタンの theme-active も同じにする）
function _acTheme() { return AC_THEMES[_acThemeKey] ?? AC_THEMES.dark; }
function setCanvasTheme(k) { _acThemeKey = k; }

class ArrayCanvas {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx    = canvas.getContext("2d");
  }

  get cw() { return this.canvas.width;  }
  get ch() { return this.canvas.height; }

  // ── メイン描画 ────────────────────────────────────────────────────
  draw(frame) {
    const { objects = [], texts = [], finished = false, found = null,
            text_position = "top" } = frame;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.cw, this.ch);

    // 背景
    ctx.fillStyle = _acTheme().canvasBg;
    ctx.fillRect(0, 0, this.cw, this.ch);

    // テキストボックスの高さを先に計算し、オブジェクト領域と重ならないようにする
    const TEXT_LINE_H = 18;
    const pad  = 6;
    const boxH = texts.length > 0 ? texts.length * TEXT_LINE_H + pad * 2 : 0;
    const objTop = (texts.length > 0 && text_position !== "bottom") ? boxH : 0;
    const objH   = this.ch - boxH;

    const nObjs = objects.length;
    if (nObjs > 0) {
      // weight で高さを比例配分（テキスト領域を除いた高さで分配）
      const totalW = objects.reduce((s, o) => s + (o.weight || 1), 0);
      let areaY = objTop;
      for (let oi = 0; oi < nObjs; oi++) {
        const eachH = objH * (objects[oi].weight || 1) / totalW;
        const obj   = objects[oi];
        switch (obj.type) {
          case "array1d":       this._drawArray1d(obj, areaY, eachH);      break;
          case "array1d_cells": this._drawArray1dCells(obj, areaY, eachH); break;
          case "heap_tree":     this._drawHeapTree(obj, areaY, eachH);     break;
          case "bucket_rows":   this._drawBucketRows(obj, areaY, eachH);   break;
          case "tape":          this._drawTape(obj, areaY, eachH);         break;
          case "fib_tree":      this._drawFibTree(obj, areaY, eachH);      break;
          case "staircase":     this._drawStaircase(obj, areaY, eachH);    break;
          case "string_match":  this._drawStringMatch(obj, areaY, eachH);  break;
          case "kv_table":      this._drawKvTable(obj, areaY, eachH);      break;
        }
        areaY += eachH;
      }
    }

    // テキストオーバーレイ (top または bottom)
    if (texts.length > 0) {
      ctx.save();
      ctx.fillStyle = _acTheme().textOverlay;
      if (text_position === "bottom") {
        const boxY = this.ch - boxH;
        ctx.fillRect(0, boxY, this.cw, boxH);
        ctx.font = "13px monospace";
        for (let i = 0; i < texts.length; i++) {
          ctx.fillStyle = texts[i].color || "#ddd";
          ctx.textAlign = "left";
          ctx.fillText(texts[i].message, 8, boxY + pad + (i + 1) * TEXT_LINE_H - 3);
        }
      } else {
        ctx.fillRect(0, 0, this.cw, boxH);
        ctx.font = "13px monospace";
        for (let i = 0; i < texts.length; i++) {
          ctx.fillStyle = texts[i].color || "#ddd";
          ctx.textAlign = "left";
          ctx.fillText(texts[i].message, 8, pad + (i + 1) * TEXT_LINE_H - 3);
        }
      }
      ctx.restore();
    }

    // 完了時の表示について:
    // Found/Not Found/完了 のいずれも、キャンバス上のデータ構造をdimして
    // 隠さないよう、ここでは一切描かない。全てコントロールパネル側の
    // ステータス表示 (status-done-badge) に任せる。
  }

  // ════════════════════════════════════════════════════════════════════
  // array1d – 縦棒グラフ (後方互換)
  // ════════════════════════════════════════════════════════════════════
  _drawArray1d(obj, areaY, areaH) {
    const {
      values = [], label = "",
      highlights = {}, fills = [],
      pointer = null, watchman_index = null,
      target    = null,
      log_scale = false,
    } = obj;
    const n = values.length;
    if (n === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T = 22; const PAD_B = 16; const PAD_L = 8; const PAD_R = 8;

    const HAS_TARGET = target !== null;
    const REF_W   = HAS_TARGET ? 30 : 0;
    const REF_GAP = HAS_TARGET ? 10 : 0;

    const chartL = PAD_L + REF_W + REF_GAP;
    const chartR = cw - PAD_R;
    const chartT = areaY + PAD_T;
    const chartB = areaY + areaH - PAD_B;
    const chartH = chartB - chartT;
    const barW   = (chartR - chartL) / n;

    const dataMax = Math.max(...values, HAS_TARGET ? target : 0, 1);
    let valToY, valToH;
    if (log_scale) {
      const logMax = Math.log1p(dataMax) || 1;
      valToH = (v) => chartH * Math.log1p(Math.max(0, v)) / logMax;
      valToY = (v) => chartB - valToH(v);
    } else {
      valToY = (v) => chartT + chartH * (1 - v / dataMax);
      valToH = (v) => chartH * v / dataMax;
    }

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(label, PAD_L, areaY + 12);
    }

    if (HAS_TARGET) {
      const refX = PAD_L; const refY = valToY(target);
      const refH = valToH(target); const rw = REF_W - 2;
      ctx.fillStyle = _acTheme().foundCellBg;
      ctx.fillRect(refX + 0.5, refY, rw - 1, refH);
      ctx.strokeStyle = _acTheme().foundCellText; ctx.lineWidth = 1.5;
      ctx.strokeRect(refX + 0.5, refY + 0.5, rw - 1, refH - 1);
      ctx.save(); ctx.strokeStyle = "rgba(68,204,68,0.35)";
      ctx.lineWidth = 1; ctx.setLineDash([4, 5]);
      ctx.beginPath(); ctx.moveTo(PAD_L + REF_W, refY);
      ctx.lineTo(chartR, refY); ctx.stroke(); ctx.restore();
      const rFs = Math.max(7, Math.min(10, REF_W * 0.4));
      ctx.fillStyle = _acTheme().foundCellText; ctx.font = `${rFs}px monospace`;
      ctx.textAlign = "center";
      ctx.fillText(String(target), refX + REF_W / 2 - 1, refY - 3);
    }

    const showLabel = barW >= 14;
    for (let i = 0; i < n; i++) {
      const x = chartL + i * barW;
      const y = valToY(values[i]); const h = valToH(values[i]);
      const isWatchman = (watchman_index === i);
      const hlColor    = highlights[String(i)];
      ctx.fillStyle = isWatchman ? "#cc6600" : hlColor ? hlColor : "#4472C4";
      ctx.fillRect(x + 0.5, y, barW - 1, Math.max(h, 1));
      if (showLabel) {
        const fs = Math.min(11, barW * 0.65);
        ctx.fillStyle = _acTheme().valueLabelColor; ctx.font = `${fs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(String(values[i]), x + barW / 2, y - 2);
      }
    }

    for (const fill of fills) {
      const from = Math.max(0, fill.from), to = Math.min(n - 1, fill.to);
      ctx.globalAlpha = 0.78; ctx.fillStyle = fill.color;
      ctx.fillRect(chartL + from * barW, chartT, (to - from + 1) * barW, chartH);
      ctx.globalAlpha = 1.0;
    }

    if (barW >= 14) {
      const iFs = Math.min(9, barW * 0.5);
      ctx.fillStyle = _acTheme().indexLabelColor; ctx.font = `${iFs}px sans-serif`;
      ctx.textAlign = "center";
      for (let i = 0; i < n; i++) {
        ctx.fillText(String(i), chartL + i * barW + barW / 2, chartB + 12);
      }
    }

    if (pointer) {
      const { index, label: pLabel, color: pColor = "#cc00cc" } = pointer;
      const px   = chartL + index * barW + barW / 2;
      const tipY = valToY(values[index]) - 2;
      const topY = chartT - 4;
      ctx.strokeStyle = pColor; ctx.lineWidth = 1.5;
      if (topY + (pLabel ? 12 : 0) < tipY - 7) {
        ctx.beginPath(); ctx.moveTo(px, topY + (pLabel ? 12 : 0));
        ctx.lineTo(px, tipY - 7); ctx.stroke();
      }
      ctx.fillStyle = pColor; ctx.beginPath();
      ctx.moveTo(px, tipY); ctx.lineTo(px - 5, tipY - 7);
      ctx.lineTo(px + 5, tipY - 7); ctx.closePath(); ctx.fill();
      if (pLabel) {
        const lFs = Math.max(7, Math.min(10, barW * 0.6));
        ctx.fillStyle = pColor; ctx.font = `${lFs}px monospace`;
        ctx.textAlign = "center"; ctx.fillText(pLabel, px, topY + 10);
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // array1d_cells – 正方形セル配列
  // ════════════════════════════════════════════════════════════════════
  _drawArray1dCells(obj, areaY, areaH) {
    const {
      values = [], label = "",
      highlights = {}, fills = [],
      pointer = null, watchman_index = null,
      target = null,
    } = obj;
    const n = values.length;
    if (n === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T = 22; const PAD_B = 16;
    const PAD_L = 8;  const PAD_R = 8;

    // target セルを左端に配置
    const HAS_TARGET = target !== null;
    const TGT_W   = HAS_TARGET ? 44 : 0;
    const TGT_GAP = HAS_TARGET ? 10 : 0;

    const chartL = PAD_L + TGT_W + TGT_GAP;
    const chartR = cw - PAD_R;
    const chartT = areaY + PAD_T;
    const chartB = areaY + areaH - PAD_B;
    const chartH = chartB - chartT;

    // セルサイズ: 横幅を n 等分し正方形に近づける
    const cellW  = Math.max(18, Math.min(56, (chartR - chartL) / n));
    const cellH  = Math.min(cellW, Math.max(18, chartH * 0.65));
    const totalW = cellW * n;
    const startX = chartL + Math.max(0, ((chartR - chartL) - totalW) / 2);
    const cellY  = chartT + (chartH - cellH) / 2;

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(label, PAD_L, areaY + 12);
    }

    // target セル
    if (HAS_TARGET) {
      const tx = PAD_L;
      ctx.fillStyle = _acTheme().foundCellBg;
      ctx.fillRect(tx, cellY, TGT_W - 2, cellH);
      ctx.strokeStyle = _acTheme().foundCellText; ctx.lineWidth = 1.5;
      ctx.strokeRect(tx + 0.5, cellY + 0.5, TGT_W - 3, cellH - 1);

      const fs = Math.max(8, Math.min(13, (TGT_W - 4) * 0.4));
      ctx.fillStyle = _acTheme().foundCellText; ctx.font = `bold ${fs}px monospace`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(target), tx + (TGT_W - 2) / 2, cellY + cellH / 2);
      ctx.textBaseline = "alphabetic";

      // 破線ガイド
      ctx.save(); ctx.strokeStyle = "rgba(68,204,68,0.35)";
      ctx.lineWidth = 1; ctx.setLineDash([4, 5]);
      ctx.beginPath(); ctx.moveTo(tx + TGT_W, cellY + cellH / 2);
      ctx.lineTo(chartR, cellY + cellH / 2); ctx.stroke();
      ctx.restore();
    }

    // セル描画
    for (let i = 0; i < n; i++) {
      const cx          = startX + i * cellW;
      const isWatchman  = (watchman_index === i);
      const hlColor     = highlights[String(i)];

      // 背景
      if (isWatchman) {
        ctx.fillStyle = "#3d2000";
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
      } else if (hlColor) {
        ctx.fillStyle = _acTheme().cellBg;
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
        ctx.save(); ctx.globalAlpha = 0.35;
        ctx.fillStyle = hlColor;
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
        ctx.restore();
      } else {
        ctx.fillStyle = _acTheme().cellBg;
        ctx.fillRect(cx, cellY, cellW - 1, cellH);
      }

      // ボーダー
      ctx.strokeStyle = isWatchman ? "#cc6600" : hlColor ? hlColor : "#336699";
      ctx.lineWidth   = isWatchman ? 2 : hlColor ? 1.5 : 1;
      ctx.strokeRect(cx + 0.5, cellY + 0.5, cellW - 2, cellH - 1);

      // 値ラベル
      const fs = Math.max(8, Math.min(14, cellW * 0.48, cellH * 0.48));
      ctx.fillStyle    = _acTheme().cellText;
      ctx.font         = `${fs}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(values[i]), cx + cellW / 2, cellY + cellH / 2);
      ctx.textBaseline = "alphabetic";

      // インデックスラベル (下)
      if (cellW >= 14) {
        const iFs = Math.max(7, Math.min(9, cellW * 0.38));
        ctx.fillStyle = _acTheme().indexLabelColor; ctx.font = `${iFs}px sans-serif`;
        ctx.textAlign = "center";
        ctx.fillText(String(i), cx + cellW / 2, cellY + cellH + 12);
      }
    }

    // フィル (除外領域)
    for (const fill of fills) {
      const from = Math.max(0, fill.from), to = Math.min(n - 1, fill.to);
      ctx.save(); ctx.globalAlpha = 0.55;
      ctx.fillStyle = fill.color;
      ctx.fillRect(startX + from * cellW, cellY,
                   (to - from + 1) * cellW, cellH);
      ctx.restore();
    }

    // ポインタ矢印
    if (pointer) {
      const { index, label: pLabel, color: pColor = "#cc00cc" } = pointer;
      const px   = startX + index * cellW + cellW / 2;
      const tipY = cellY - 2;
      const topY = chartT - 4;
      ctx.strokeStyle = pColor; ctx.lineWidth = 1.5;
      if (topY + (pLabel ? 12 : 0) < tipY - 7) {
        ctx.beginPath(); ctx.moveTo(px, topY + (pLabel ? 12 : 0));
        ctx.lineTo(px, tipY - 7); ctx.stroke();
      }
      ctx.fillStyle = pColor; ctx.beginPath();
      ctx.moveTo(px, tipY); ctx.lineTo(px - 5, tipY - 7);
      ctx.lineTo(px + 5, tipY - 7); ctx.closePath(); ctx.fill();
      if (pLabel) {
        const lFs = Math.max(7, Math.min(10, cellW * 0.5));
        ctx.fillStyle = pColor; ctx.font = `${lFs}px monospace`;
        ctx.textAlign = "center"; ctx.fillText(pLabel, px, topY + 10);
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // heap_tree – ヒープ二分木
  // ════════════════════════════════════════════════════════════════════
  _drawHeapTree(obj, areaY, areaH) {
    const { values = [], heap_size = 0, highlights = {}, label = "",
            confirmed_min = 0 } = obj;
    const N = values.length;
    if (N === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD    = 16;
    const chartL = PAD;
    const chartR = cw - PAD;
    const chartT = areaY + PAD + (label ? 14 : 4);
    const chartB = areaY + areaH - PAD;
    const chartW = chartR - chartL;
    const chartH = chartB - chartT;

    // 木の深さ：heap_size ベースで計算することで、
    // フェーズ1 では実際に挿入されたノード数だけツリーが広がり、
    // フェーズ2 では heap_size の縮小とともにツリーが小さくなる
    const displaySize = heap_size > 0 ? heap_size : N;
    const levels = Math.floor(Math.log2(displaySize)) + 1;
    const levelH = chartH / levels;
    const nodeR  = Math.max(8, Math.min(20, levelH * 0.32,
                             chartW / Math.pow(2, Math.ceil(levels / 2)) * 0.45));

    // ノード座標
    function nodePos(i) {
      const level       = Math.floor(Math.log2(i + 1));
      const posInLevel  = i - (Math.pow(2, level) - 1);
      const nodesInLvl  = Math.pow(2, level);
      return {
        x: chartL + chartW * (posInLevel + 0.5) / nodesInLvl,
        y: chartT + levelH * (level + 0.5),
      };
    }

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD, areaY + 14);
    }

    // 辺 (heap_size 以内。ghost 辺は暗く描画)
    for (let i = 1; i < heap_size; i++) {
      const isGhostEdge = i < confirmed_min;
      ctx.strokeStyle = isGhostEdge ? _acTheme().dimEdge : _acTheme().edgeColor;
      ctx.lineWidth   = isGhostEdge ? 0.5 : 1;
      const parent = Math.floor((i - 1) / 2);
      const p1 = nodePos(parent), p2 = nodePos(i);
      ctx.beginPath(); ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y); ctx.stroke();
    }

    // ノード描画 (heap_size 以内)
    const fs = Math.max(6, Math.min(12, nodeR * 0.72));
    for (let i = 0; i < heap_size; i++) {
      const isGhost = i < confirmed_min;
      const pos     = nodePos(i);
      const hlColor = highlights[String(i)];

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, nodeR, 0, Math.PI * 2);

      if (isGhost) {
        // 未処理ノード: 非常に暗い色で描画 (存在はほのめかす)
        ctx.fillStyle   = _acTheme().ghostFill;
        ctx.fill();
        ctx.strokeStyle = _acTheme().ghostStroke;
        ctx.lineWidth   = 0.8;
        ctx.stroke();
        ctx.fillStyle    = _acTheme().ghostText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), pos.x, pos.y);
        ctx.textBaseline = "alphabetic";
      } else {
        // 確定済みノード: 通常描画
        if (hlColor) {
          ctx.fillStyle = _acTheme().nodeBg; ctx.fill();
          ctx.save(); ctx.globalAlpha = 0.4;
          ctx.fillStyle = hlColor; ctx.fill(); ctx.restore();
          ctx.strokeStyle = hlColor; ctx.lineWidth = 2;
        } else {
          ctx.fillStyle = _acTheme().cellBg; ctx.fill();
          ctx.strokeStyle = "#4472C4"; ctx.lineWidth = 1.5;
        }
        ctx.stroke();

        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(values[i]), pos.x, pos.y);
        ctx.textBaseline = "alphabetic";

        // インデックス (右下小)
        if (nodeR >= 12) {
          const iFs = Math.max(6, Math.min(8, nodeR * 0.42));
          ctx.fillStyle = _acTheme().indexLabelColor;
          ctx.font      = `${iFs}px sans-serif`;
          ctx.textAlign = "center";
          ctx.fillText(String(i), pos.x + nodeR * 0.7, pos.y + nodeR + iFs);
        }
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // bucket_rows – バケツ行 / 動的キュー
  // ════════════════════════════════════════════════════════════════════
  _drawBucketRows(obj, areaY, areaH) {
    const {
      num_buckets = 0, buckets = [], bucket_colors = [],
      bucket_labels = [], label = "", active_bucket = null,
      direction = "rows",   // "rows" | "columns"
    } = obj;
    if (num_buckets === 0) return;

    if (direction === "columns") {
      this._drawBucketColumns(obj, areaY, areaH);
      return;
    }

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T   = label ? 18 : 6;
    const PAD_B   = 4;
    const PAD_L   = 6;
    const LBL_W   = 24;
    const SEP_W   = 4;

    const totalH  = areaH - PAD_T - PAD_B;
    const rowH    = Math.max(14, Math.min(36, totalH / num_buckets));
    const cellW   = Math.min(rowH * 1.1, 42);
    const cellPad = 2;

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD_L, areaY + 14);
    }

    for (let b = 0; b < num_buckets; b++) {
      const rowY    = areaY + PAD_T + b * rowH;
      const cells   = buckets[b] || [];
      const color   = bucket_colors[b % bucket_colors.length] || "#4472C4";
      const isActive = active_bucket === b;
      const lblText = bucket_labels[b] !== undefined ? String(bucket_labels[b]) : String(b);

      ctx.fillStyle = isActive ? "#ffffff" : color;
      ctx.font      = `${Math.max(8, Math.min(11, rowH * 0.5))}px monospace`;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(lblText, PAD_L + LBL_W, rowY + rowH / 2);
      ctx.textBaseline = "alphabetic";

      ctx.strokeStyle = isActive ? "#ffffff" : color;
      ctx.lineWidth   = isActive ? 1.5 : 1;
      ctx.beginPath();
      ctx.moveTo(PAD_L + LBL_W + SEP_W, rowY + 3);
      ctx.lineTo(PAD_L + LBL_W + SEP_W, rowY + rowH - 3);
      ctx.stroke();

      for (let c = 0; c < cells.length; c++) {
        const cx     = PAD_L + LBL_W + SEP_W + cellPad + c * (cellW + cellPad);
        const isLast = isActive && c === cells.length - 1;

        ctx.fillStyle = _acTheme().nodeBg;
        ctx.fillRect(cx, rowY + 2, cellW, rowH - 4);
        ctx.save(); ctx.globalAlpha = isLast ? 0.5 : 0.22;
        ctx.fillStyle = color;
        ctx.fillRect(cx, rowY + 2, cellW, rowH - 4);
        ctx.restore();

        ctx.strokeStyle = isLast ? _acTheme().cellText : color;
        ctx.lineWidth   = isLast ? 1.5 : 1;
        ctx.strokeRect(cx + 0.5, rowY + 2.5, cellW - 1, rowH - 5);

        const fs = Math.max(7, Math.min(12, cellW * 0.44, (rowH - 4) * 0.55));
        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(cells[c]), cx + cellW / 2, rowY + rowH / 2);
        ctx.textBaseline = "alphabetic";
      }

      if (cells.length === 0) {
        ctx.strokeStyle = color; ctx.globalAlpha = 0.2; ctx.lineWidth = 0.5;
        const cx = PAD_L + LBL_W + SEP_W + cellPad;
        ctx.strokeRect(cx + 0.5, rowY + 2.5, cellW - 1, rowH - 5);
        ctx.globalAlpha = 1;
      }
    }

    ctx.restore();
  }

  // ── bucket_rows カラムレイアウト (1バケツ = 1列, ラベルが上・セルは下へ伸びる) ──
  _drawBucketColumns(obj, areaY, areaH) {
    const {
      num_buckets = 0, buckets = [], bucket_colors = [],
      bucket_labels = [], label = "", active_bucket = null,
    } = obj;

    const ctx    = this.ctx;
    const cw     = this.cw;
    // テキストオーバーレイ（最大3行 × 18 + 12 ≈ 66px）の下からコンテンツを開始する
    const TEXT_OVERLAY_H = 66;
    const PAD_T  = TEXT_OVERLAY_H;   // オーバーレイ分を避けるパディング
    const LBL_H  = 16;               // 各列ラベル行の高さ
    const PAD_B  = 4;
    const PAD_LR = 4;

    const usableW  = cw - PAD_LR * 2;
    const colW     = usableW / num_buckets;
    const cellPad  = 2;
    const cellW    = Math.max(8, colW - cellPad * 2);
    const usableH  = areaH - PAD_T - LBL_H - PAD_B;
    const maxItems = Math.max(1, ...buckets.map(b => b.length));
    const cellH    = Math.max(10, Math.min(colW * 0.9, usableH / Math.max(4, maxItems)));
    const fs       = Math.max(7, Math.min(11, cellH * 0.55, cellW * 0.5));

    // セル開始 Y（ラベル行のすぐ下）
    const cellStartY = areaY + PAD_T + LBL_H;

    ctx.save();

    // セクションラベル（オーバーレイ直下に配置）
    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD_LR, areaY + PAD_T - 4);
    }

    for (let b = 0; b < num_buckets; b++) {
      const colX     = PAD_LR + b * colW + cellPad;
      const cells    = buckets[b] || [];
      const color    = bucket_colors[b % bucket_colors.length] || "#4472C4";
      const isActive = active_bucket === b;
      const lblText  = bucket_labels[b] !== undefined ? String(bucket_labels[b]) : String(b);

      // 列ラベル（上端）
      const lblY = areaY + PAD_T + LBL_H - 4;
      ctx.fillStyle    = isActive ? "#ffffff" : color;
      ctx.font         = `${Math.max(8, Math.min(11, colW * 0.38))}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "alphabetic";
      ctx.fillText(lblText, colX + cellW / 2, lblY);

      // 区切り線（ラベルの下）
      ctx.strokeStyle = isActive ? "#ffffff" : color;
      ctx.lineWidth   = isActive ? 1.2 : 0.5;
      ctx.globalAlpha = isActive ? 1.0 : 0.4;
      ctx.beginPath();
      ctx.moveTo(colX,          cellStartY);
      ctx.lineTo(colX + cellW,  cellStartY);
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      // セル（上から下へ積む: index 0 が一番上）
      for (let c = 0; c < cells.length; c++) {
        const cellY  = cellStartY + c * cellH + cellPad;
        const isLast = isActive && c === cells.length - 1;

        ctx.fillStyle = "#0d1117";
        ctx.fillRect(colX, cellY, cellW, cellH - cellPad);
        ctx.save();
        ctx.globalAlpha = isLast ? 0.55 : 0.25;
        ctx.fillStyle   = color;
        ctx.fillRect(colX, cellY, cellW, cellH - cellPad);
        ctx.restore();

        ctx.strokeStyle = isLast ? "#ffffff" : color;
        ctx.lineWidth   = isLast ? 1.2 : 0.6;
        ctx.strokeRect(colX + 0.5, cellY + 0.5, cellW - 1, cellH - cellPad - 1);

        ctx.fillStyle    = "#ffffff";
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(cells[c]), colX + cellW / 2, cellY + (cellH - cellPad) / 2);
        ctx.textBaseline = "alphabetic";
      }

      // 空列（細い輪郭のみ）
      if (cells.length === 0) {
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.15;
        ctx.lineWidth   = 0.5;
        ctx.strokeRect(colX + 0.5, cellStartY + cellPad + 0.5, cellW - 1, cellH - cellPad - 1);
        ctx.globalAlpha = 1.0;
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // tape – 無端テープ
  // ════════════════════════════════════════════════════════════════════
  _drawTape(obj, areaY, areaH) {
    const { cells = [], head = 0, label = "", color = "#4472C4",
            highlights = {}, sorted_upto = null, swap = null,
            reserve_arc = false, head_label = null } = obj;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD    = 6;
    const LBL_W  = 64;
    // reserve_arc: セル上に注釈 (交換アーク)、セル下に添字ラベルの余白を確保
    const ARC_H  = reserve_arc ? 24 : 0;
    const BOT_H  = reserve_arc ? 34 : 14;               // 添字 + ヘッド矢印 + 名前
    // セルサイズを array1d_cells と揃える (小さめに抑える)
    // reserve_arc の単体テープは、全セル + 前後の余白が収まる範囲で大きく描く
    const availW0 = cw - PAD * 2 - LBL_W;
    const cellH  = reserve_arc
      ? Math.max(18, Math.min(48,
          areaH - PAD * 2 - ARC_H - BOT_H,
          availW0 / Math.max(6, cells.length + 3)))
      : Math.max(18, Math.min(28, areaH - PAD * 2 - 16));
    const cellW  = cellH;
    const tapeY  = areaY + ARC_H + (areaH - ARC_H - cellH - BOT_H) / 2;
    const availW = cw - PAD * 2 - LBL_W;
    const nVis   = Math.max(3, Math.floor(availW / cellW));
    const half   = Math.floor(nVis / 2);
    const startX = PAD + LBL_W + half * cellW;

    ctx.save();

    // ラベル
    ctx.fillStyle    = color;
    ctx.font         = "11px monospace";
    ctx.textAlign    = "left";
    ctx.textBaseline = "middle";
    ctx.fillText(label, PAD, tapeY + cellH / 2);
    ctx.textBaseline = "alphabetic";

    // 左端ハッシュ記号
    this._drawTapeHashmark(ctx, PAD + LBL_W, tapeY, cellW * 0.6, cellH);
    // 右端ハッシュ記号
    this._drawTapeHashmark(ctx, PAD + LBL_W + nVis * cellW, tapeY, cellW * 0.6, cellH);

    // セル
    for (let vi = 0; vi < nVis; vi++) {
      const idx    = head - half + vi;
      const cx     = PAD + LBL_W + vi * cellW;
      const inData = idx >= 0 && idx < cells.length;
      const isHead = (idx === head);

      if (!inData) {
        // 空白セル (ハッチング)
        ctx.fillStyle = _acTheme().cellEmptyBg;
        ctx.fillRect(cx, tapeY, cellW - 1, cellH);
        ctx.strokeStyle = _acTheme().dimEdge; ctx.lineWidth = 0.5;
        ctx.strokeRect(cx + 0.5, tapeY + 0.5, cellW - 2, cellH - 1);
        ctx.save(); ctx.strokeStyle = _acTheme().dimEdge; ctx.lineWidth = 0.5;
        ctx.setLineDash([3, 4]);
        for (let hx = cx + 4; hx < cx + cellW - 2; hx += 5) {
          ctx.beginPath(); ctx.moveTo(hx, tapeY + 2);
          ctx.lineTo(hx - (cellH - 4) * 0.5, tapeY + cellH - 2); ctx.stroke();
        }
        ctx.restore();
      } else {
        // データセル
        const hlColor  = highlights[String(idx)];
        const isSorted = (sorted_upto !== null && idx < sorted_upto);

        ctx.fillStyle = _acTheme().cellBg;
        ctx.fillRect(cx, tapeY, cellW - 1, cellH);
        // 整列確定済み領域 (薄い緑)
        if (isSorted) {
          ctx.save(); ctx.globalAlpha = 0.26;
          ctx.fillStyle = "#44aa44";
          ctx.fillRect(cx, tapeY, cellW - 1, cellH);
          ctx.restore();
        }
        if (hlColor) {
          ctx.save(); ctx.globalAlpha = 0.5;
          ctx.fillStyle = hlColor;
          ctx.fillRect(cx, tapeY, cellW - 1, cellH);
          ctx.restore();
        } else if (isHead) {
          ctx.save(); ctx.globalAlpha = 0.45;
          ctx.fillStyle = color;
          ctx.fillRect(cx, tapeY, cellW - 1, cellH);
          ctx.restore();
        }
        ctx.strokeStyle = hlColor ? hlColor
                        : isHead  ? color
                        : isSorted ? "#44aa44"
                        : _acTheme().edgeColor;
        ctx.lineWidth   = isHead ? 2.5 : hlColor ? 2 : 1;
        ctx.strokeRect(cx + 0.5, tapeY + 0.5, cellW - 2, cellH - 1);

        const fs = Math.max(8, Math.min(13, cellW * 0.42, cellH * 0.46));
        ctx.fillStyle    = _acTheme().cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(String(cells[idx]), cx + cellW / 2, tapeY + cellH / 2);
        ctx.textBaseline = "alphabetic";

        // 添字ラベル (下)
        if (reserve_arc && cellW >= 14) {
          const iFs = Math.max(7, Math.min(9, cellW * 0.38));
          ctx.fillStyle = _acTheme().indexLabelColor;
          ctx.font      = `${iFs}px sans-serif`;
          ctx.textAlign = "center";
          ctx.fillText(String(idx), cx + cellW / 2, tapeY + cellH + 11);
        }
      }
    }

    // 交換アーク注釈 (セルより上のレイヤ・上の余白に描く)
    if (swap && ARC_H > 0) {
      const phase = swap.phase || "before";
      const aCol  = (phase === "after") ? "#66ddff" : "#ff6600";
      const xa = PAD + LBL_W + (swap.a - head + half) * cellW + cellW / 2;
      const xb = PAD + LBL_W + (swap.b - head + half) * cellW + cellW / 2;
      const topY  = tapeY - 5;
      const ctrlY = tapeY - ARC_H - 6;

      ctx.save();
      ctx.strokeStyle = aCol; ctx.lineWidth = 2.5; ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(xa, topY);
      ctx.quadraticCurveTo((xa + xb) / 2, ctrlY, xb, topY);
      ctx.stroke();
      // 両端の矢尻 (セルを指す)
      ctx.fillStyle = aCol;
      for (const ax of [xa, xb]) {
        ctx.beginPath();
        ctx.moveTo(ax, topY + 4);
        ctx.lineTo(ax - 4.5, topY - 3);
        ctx.lineTo(ax + 4.5, topY - 3);
        ctx.closePath(); ctx.fill();
      }
      // アーク頂点に交換記号
      ctx.font = "bold 12px sans-serif";
      ctx.textAlign = "center"; ctx.textBaseline = "bottom";
      ctx.fillText("⇄", (xa + xb) / 2, (topY + ctrlY) / 2 + 3);
      ctx.textBaseline = "alphabetic";
      ctx.restore();
    }

    // ヘッド矢印
    const hx = PAD + LBL_W + half * cellW + cellW / 2;
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    if (reserve_arc) {
      ctx.font = "13px sans-serif";
      ctx.fillText("▲", hx, tapeY + cellH + 24);
      if (head_label) {
        ctx.font = "10px monospace";
        ctx.fillText(`${head_label} = ${head}`, hx, tapeY + cellH + 34);
      }
    } else {
      ctx.font = "12px sans-serif";
      ctx.fillText("▲", hx, tapeY + cellH + 13);
    }

    ctx.restore();
  }

  _drawTapeHashmark(ctx, x, tapeY, w, cellH) {
    ctx.save();
    ctx.fillStyle = _acTheme().cellEmptyBg;
    ctx.fillRect(x, tapeY, w - 1, cellH);
    ctx.strokeStyle = _acTheme().dimEdge; ctx.lineWidth = 0.5;
    ctx.strokeRect(x + 0.5, tapeY + 0.5, w - 2, cellH - 1);
    ctx.setLineDash([3, 4]);
    for (let hx = x + 3; hx < x + w - 2; hx += 5) {
      ctx.beginPath(); ctx.moveTo(hx, tapeY + 2);
      ctx.lineTo(hx - (cellH - 4) * 0.5, tapeY + cellH - 2); ctx.stroke();
    }
    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // fib_tree – フィボナッチ再帰木
  // ════════════════════════════════════════════════════════════════════
  _drawFibTree(obj, areaY, areaH) {
    const { root } = obj;
    if (!root) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD    = 20;
    const chartL = PAD;
    const chartR = cw - PAD;
    const chartT = areaY + PAD;
    const chartB = areaY + areaH - PAD;
    const chartW = chartR - chartL;
    const chartH = chartB - chartT;

    // 深さ・最大幅を計算
    function depth(node) {
      if (!node) return 0;
      return 1 + Math.max(depth(node.left), depth(node.right));
    }
    function leafCount(node) {
      if (!node) return 0;
      if (!node.left && !node.right) return 1;
      return (node.left ? leafCount(node.left) : 0) +
             (node.right ? leafCount(node.right) : 0);
    }

    const d   = depth(root);
    const lc  = Math.max(1, leafCount(root));
    if (d === 0) return;

    const levelH = chartH / d;
    const nodeR  = Math.max(8, Math.min(18, levelH * 0.3,
                             chartW / (lc * 2.2)));

    // ノード位置を計算 (葉の位置から再帰的に決定)
    let leafIdx = 0;
    function assignPos(node, depth_) {
      if (!node) return;
      const y = chartT + levelH * (depth_ + 0.5);
      if (!node.left && !node.right) {
        // 葉ノード: 左から順に等間隔
        node._x = chartL + chartW * (leafIdx + 0.5) / lc;
        node._y = y;
        leafIdx++;
      } else {
        assignPos(node.left,  depth_ + 1);
        assignPos(node.right, depth_ + 1);
        const lx = node.left  ? node.left._x  : null;
        const rx = node.right ? node.right._x : null;
        node._x = lx !== null && rx !== null ? (lx + rx) / 2
                : lx !== null ? lx : rx;
        node._y = y;
      }
    }
    leafIdx = 0;
    assignPos(root, 0);

    ctx.save();

    // 辺
    function drawEdges(node) {
      if (!node) return;
      if (node.left) {
        ctx.beginPath(); ctx.moveTo(node._x, node._y);
        ctx.lineTo(node.left._x, node.left._y);
        ctx.strokeStyle = _acTheme().edgeColor; ctx.lineWidth = 1; ctx.stroke();
        drawEdges(node.left);
      }
      if (node.right) {
        ctx.beginPath(); ctx.moveTo(node._x, node._y);
        ctx.lineTo(node.right._x, node.right._y);
        ctx.strokeStyle = _acTheme().edgeColor; ctx.lineWidth = 1; ctx.stroke();
        drawEdges(node.right);
      }
    }
    drawEdges(root);

    // ノード
    function drawNodes(node) {
      if (!node) return;
      const color = node.color || "#4472C4";

      ctx.beginPath();
      ctx.arc(node._x, node._y, nodeR, 0, Math.PI * 2);
      ctx.fillStyle = _acTheme().nodeBg; ctx.fill();
      ctx.save(); ctx.globalAlpha = 0.4;
      ctx.fillStyle = color; ctx.fill(); ctx.restore();
      ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.stroke();

      // ラベル: f(n) / =v
      const fs = Math.max(6, Math.min(11, nodeR * 0.68));
      ctx.fillStyle    = "#ccddee";
      ctx.font         = `${fs}px monospace`;
      ctx.textAlign    = "center";
      ctx.textBaseline = "middle";

      const hasVal = node.value !== null && node.value !== undefined;
      if (hasVal) {
        ctx.fillText(`f(${node.n})`, node._x, node._y - fs * 0.55);
        ctx.fillStyle = color;
        ctx.fillText(`=${node.value}`, node._x, node._y + fs * 0.55);
      } else {
        ctx.fillText(`f(${node.n})`, node._x, node._y);
      }
      ctx.textBaseline = "alphabetic";

      // メモ化ノード: 右上にバッジ
      if (node.memo) {
        const bR = Math.max(4, nodeR * 0.35);
        ctx.beginPath();
        ctx.arc(node._x + nodeR * 0.72, node._y - nodeR * 0.72, bR, 0, Math.PI * 2);
        ctx.fillStyle = "#44aacc"; ctx.fill();
        ctx.strokeStyle = "#fff"; ctx.lineWidth = 1; ctx.stroke();
        ctx.fillStyle = "#fff"; ctx.font = `bold ${Math.max(5, bR * 0.9)}px sans-serif`;
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText("M", node._x + nodeR * 0.72, node._y - nodeR * 0.72);
        ctx.textBaseline = "alphabetic";
      }

      drawNodes(node.left);
      drawNodes(node.right);
    }
    drawNodes(root);

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // staircase – 階段状テキスト (階乗再帰)
  // ════════════════════════════════════════════════════════════════════
  _drawStaircase(obj, areaY, areaH) {
    const { rows = [], label = "" } = obj;
    if (rows.length === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;

    const PAD_T   = label ? 20 : 6;
    const PAD_L   = 10;
    const PAD_R   = 8;
    const maxDepth = rows.reduce((m, r) => Math.max(m, r.depth || 0), 0);
    const INDENT   = Math.min(18, maxDepth > 0 ? (cw * 0.3) / maxDepth : 18);
    const rowH     = Math.max(12, Math.min(22, (areaH - PAD_T - 4) / Math.max(rows.length, 1)));
    const fs       = Math.max(9, Math.min(13, rowH * 0.68));

    ctx.save();

    if (label) {
      ctx.fillStyle = "#6a8faf"; ctx.font = "10px sans-serif";
      ctx.textAlign = "left"; ctx.fillText(label, PAD_L, areaY + 14);
    }

    for (let i = 0; i < rows.length; i++) {
      const { text, depth = 0, color = "#aaa" } = rows[i];
      const rowY = areaY + PAD_T + i * rowH;
      const rowX = PAD_L + depth * INDENT;
      const isActive = (color === "yellow" || color === "#ffff00");

      // アクティブ行の背景ハイライト
      if (isActive) {
        ctx.save(); ctx.globalAlpha = 0.12;
        ctx.fillStyle = "#ffff00";
        ctx.fillRect(rowX - 3, rowY, cw - rowX - PAD_R, rowH);
        ctx.restore();
      }

      // 接続線 (前の行から indent が増えた場合)
      if (i > 0 && rows[i].depth > rows[i - 1].depth) {
        const prevX = PAD_L + rows[i - 1].depth * INDENT + 3;
        const prevY = areaY + PAD_T + (i - 1) * rowH + rowH * 0.75;
        ctx.strokeStyle = _acTheme().connectorColor; ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(prevX, prevY);
        ctx.lineTo(prevX, rowY + rowH * 0.5);
        ctx.lineTo(rowX - 1, rowY + rowH * 0.5);
        ctx.stroke();
        // 矢印
        ctx.fillStyle = _acTheme().connectorColor;
        ctx.beginPath();
        ctx.moveTo(rowX - 1, rowY + rowH * 0.5);
        ctx.lineTo(rowX - 5, rowY + rowH * 0.5 - 3);
        ctx.lineTo(rowX - 5, rowY + rowH * 0.5 + 3);
        ctx.closePath(); ctx.fill();
      }

      // テキスト
      ctx.fillStyle = color;
      ctx.font      = `${fs}px monospace`;
      ctx.textAlign = "left";
      ctx.fillText(text, rowX + 4, rowY + rowH * 0.78);
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // string_match – 文字列照合
  //   上から: ずらし矢印の帯 / 表 (KMP の PMT) / パターンの添字 / パターン /
  //           比較の注釈 / テキスト / テキストの添字 / ポインタ
  //   列 c の x 座標は全段共通 (パターンは shift 列目から並ぶ)
  // ════════════════════════════════════════════════════════════════════
  _drawStringMatch(obj, areaY, areaH) {
    const {
      text = [], pattern = null, shift = 0, cols = 0,
      text_label = "T", pattern_label = "P",
      text_hl = {}, pattern_hl = {}, compare = null,
      ghost = null, arrow = null, table = null, pointers = [],
      pattern_dim_from = null,
    } = obj;
    const ctx = this.ctx;
    const cw  = this.cw;
    const th  = _acTheme();
    const n = text.length;
    const m = pattern ? pattern.length : 0;
    const nCols = Math.max(cols, n, shift + m, 1);

    const C_DATA  = "#4a7ab8";   // データのセル枠
    const C_TABLE = "#8a6ac8";   // 表のセル枠
    const C_ARROW = "#ff9900";   // ずらしの注釈
    const STATE = {
      cmp: { color: "#ffd700", mark: "?" },
      eq:  { color: "#44cc44", mark: "=" },
      ne:  { color: "#ff4444", mark: "≠" },
    };

    ctx.save();

    // ── 左のラベル列 (幅は 3 つのアルゴリズムで共通にする: 並べたときに列の位置がそろうように) ──
    ctx.font = "bold 12px sans-serif";
    const labels = ["T", "P", "PMT", "接頭辞", text_label, pattern_label, table ? table.label : ""];
    const LBL_W  = Math.ceil(Math.max(...labels.map(s => ctx.measureText(s).width))) + 14;
    const PAD_L = 8, PAD_R = 10;
    const availW = cw - PAD_L - LBL_W - PAD_R;

    // ── 縦方向の配分 (パネル既定の高さでもセルが小さくなりすぎないよう余白は最小限) ──
    //    表 (KMP の PMT) の行は、表が無いアルゴリズムやプレビューでも常に確保する
    //    (アルゴリズムや開始前後で T・P の大きさと位置が変わらないように)
    let ARROW_H = 28, IDX_H = 12, PTR_H = 16, GAP_MIN = 16;
    const TBL_GAP  = 3;
    const unitRows = 1 + 2 + 0.9;                        // 表 + パターン + テキスト + 比較の隙間
    // パネルが低いときは、セルを 16px 確保できるところまで余白の帯を縮める (全段が収まるように)
    const want = ARROW_H + IDX_H * 2 + PTR_H + TBL_GAP + 4 + unitRows * 16;
    if (areaH < want) {
      const k = Math.max(0.45, areaH / want);
      ARROW_H *= k; IDX_H *= k; PTR_H *= k; GAP_MIN *= k;
    }
    const fixedH = ARROW_H + IDX_H * 2 + PTR_H + TBL_GAP + 4;
    // 横は必ず収める (64 文字をせまいパネルに出すときはセルが小さくなる → パネルを広げて見る)
    const cell = Math.min(44, availW / nCols, Math.max(6, (areaH - fixedH) / unitRows));
    const gapH = Math.max(GAP_MIN, cell * 0.9);
    const contentH = ARROW_H + cell + TBL_GAP + IDX_H + cell + gapH + cell + IDX_H + PTR_H;
    const gridX = PAD_L + LBL_W + Math.max(0, (availW - nCols * cell) / 2);
    const colX  = (c) => gridX + c * cell;

    const topY    = areaY + Math.max(2, (areaH - contentH) / 2);
    const baseY   = topY + ARROW_H;                         // ずらし矢印の端点
    const tblY    = baseY;
    const pIdxY   = baseY + cell + TBL_GAP;
    const patY    = pIdxY + IDX_H;
    const txtY    = patY + cell + gapH;
    const tIdxY   = txtY + cell;
    const ptrY    = tIdxY + IDX_H;

    const fs  = Math.max(6, Math.min(20, cell * 0.6));
    const iFs = Math.max(7, Math.min(10, cell * 0.45));
    const idxEvery = cell >= 14 ? 1 : cell >= 9 ? 5 : 10;

    const drawCell = (x, y, ch, hl, border, dim = false) => {
      ctx.save();
      if (dim) ctx.globalAlpha = 0.3;
      ctx.fillStyle = th.cellBg;
      ctx.fillRect(x, y, cell - 1, cell);
      if (hl) {
        ctx.save(); ctx.globalAlpha *= 0.5;
        ctx.fillStyle = hl; ctx.fillRect(x, y, cell - 1, cell);
        ctx.restore();
      }
      ctx.strokeStyle = hl || border;
      ctx.lineWidth   = hl ? 2.5 : 1.5;
      ctx.strokeRect(x + 0.75, y + 0.75, cell - 2.5, cell - 1.5);
      if (cell >= 7) {                     // これより小さいと文字は読めないので枠だけ
        const isSpace = (ch === " ");
        ctx.fillStyle    = isSpace ? th.indexLabelColor : th.cellText;
        ctx.font         = `${fs}px monospace`;
        ctx.textAlign    = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(isSpace ? "␣" : String(ch), x + cell / 2, y + cell / 2 + 1);
      }
      ctx.restore();
    };
    const drawIdx = (c, label, y, dim = false) => {
      if (IDX_H < 8 || label % idxEvery !== 0) return;   // 帯が縮んで入らないときは省く
      ctx.save();
      if (dim) ctx.globalAlpha = 0.35;
      ctx.fillStyle = th.indexLabelColor;
      ctx.font = `${iFs}px sans-serif`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(label), colX(c) + cell / 2, y + IDX_H / 2);
      ctx.restore();
    };
    const drawLabel = (s, y) => {
      ctx.fillStyle = th.valueLabelColor;
      ctx.font = "bold 12px sans-serif";
      ctx.textAlign = "right"; ctx.textBaseline = "middle";
      ctx.fillText(s, gridX - 8, y + cell / 2);
    };

    // ── テキスト (下段) ──
    drawLabel(text_label, txtY);
    for (let c = 0; c < n; c++) {
      drawCell(colX(c), txtY, text[c], text_hl[String(c)], C_DATA);
      drawIdx(c, c, tIdxY);
    }
    // テキストの外 (このフレームでパターンが末尾からはみ出している分だけ): 破線の空セル
    const overEnd = pattern
      ? Math.max(shift + m, (ghost !== null && ghost !== undefined) ? ghost + m : 0)
      : 0;
    for (let c = n; c < Math.min(overEnd, nCols); c++) {
      ctx.save();
      ctx.fillStyle = th.cellEmptyBg;
      ctx.fillRect(colX(c), txtY, cell - 1, cell);
      ctx.setLineDash([3, 3]);
      ctx.strokeStyle = th.edgeColor; ctx.lineWidth = 1.5;
      ctx.strokeRect(colX(c) + 1, txtY + 1, cell - 3, cell - 2);
      ctx.restore();
    }
    if (overEnd > n) {                     // テキストの終わりを示す縦線
      ctx.save();
      ctx.strokeStyle = th.valueLabelColor; ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(colX(n) - 0.5, txtY - 3); ctx.lineTo(colX(n) - 0.5, txtY + cell + 3);
      ctx.stroke();
      ctx.restore();
    }

    // ── 表 (KMP の PMT など。パターンと同じ列に並ぶ) ──
    if (table) {
      const { values = [], offset = 0, highlights: thl = {} } = table;
      drawLabel(table.label || "", tblY);
      for (let k = 0; k < values.length; k++) {
        const v = values[k];
        drawCell(colX(offset + k), tblY, (v === null || v === undefined) ? "" : String(v),
                 thl[String(k)], C_TABLE);
      }
    }

    if (pattern) {
      drawLabel(pattern_label, patY);
      // ── 移動前 / 移動先の位置 (破線。実体のパターンより下に描く) ──
      if (ghost !== null && ghost !== undefined && ghost !== shift) {
        for (let k = 0; k < m; k++) {
          const x = colX(ghost + k);
          ctx.save();
          ctx.setLineDash([4, 3]);
          ctx.strokeStyle = C_ARROW; ctx.lineWidth = 1.5; ctx.globalAlpha = 0.9;
          ctx.strokeRect(x + 1, patY + 1, cell - 3, cell - 2);
          ctx.setLineDash([]);
          ctx.globalAlpha = 0.35;
          ctx.fillStyle = th.cellText;
          ctx.font = `${fs}px monospace`;
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(pattern[k] === " " ? "␣" : String(pattern[k]), x + cell / 2, patY + cell / 2 + 1);
          ctx.restore();
        }
      }
      // ── パターン (上段) ──
      for (let k = 0; k < m; k++) {
        const dim = (pattern_dim_from !== null && k >= pattern_dim_from);
        drawCell(colX(shift + k), patY, pattern[k], pattern_hl[String(k)], C_DATA, dim);
        drawIdx(shift + k, k, pIdxY, dim);
      }
    }

    // ── 比較の注釈 (上下のセルを結ぶ。データより上のレイヤ) ──
    if (compare && pattern) {
      const st = STATE[compare.state] || STATE.cmp;
      const x  = colX(compare.col) + cell / 2;
      const y1 = patY + cell + 2, y2 = txtY - 2;
      ctx.strokeStyle = st.color; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(x, y1); ctx.lineTo(x, y2); ctx.stroke();
      const r  = Math.max(5, Math.min(11, gapH * 0.4));
      const my = (y1 + y2) / 2;
      ctx.beginPath(); ctx.arc(x, my, r, 0, Math.PI * 2);
      ctx.fillStyle = st.color; ctx.fill();
      ctx.strokeStyle = th.canvasBg; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.fillStyle = "#111111";
      ctx.font = `bold ${Math.round(r * 1.45)}px sans-serif`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(st.mark, x, my + 1);
    }

    // ── ポインタ (テキストの添字の下。名前と値は矢印の右に) ──
    for (const p of pointers) {
      const x   = colX(p.col) + cell / 2;
      const col = p.color || "#dd55dd";
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.moveTo(x, ptrY + 1); ctx.lineTo(x - 6, ptrY + 11); ctx.lineTo(x + 6, ptrY + 11);
      ctx.closePath(); ctx.fill();
      ctx.font = "bold 11px monospace";
      ctx.textAlign = "left"; ctx.textBaseline = "middle";
      ctx.fillText(`${p.label}=${p.col}`, x + 8, ptrY + 7);
    }

    // ── ずらし矢印 (最上段の帯。いちばん上のレイヤ) ──
    if (arrow && arrow.from !== arrow.to) {
      const x0 = colX(arrow.from) + cell / 2;
      const x1 = colX(arrow.to)   + cell / 2;
      const yB = baseY - 2;
      const yC = topY + ARROW_H * 0.43;          // 帯の高さに合わせて曲線の頂点を決める
      ctx.strokeStyle = C_ARROW; ctx.fillStyle = C_ARROW;
      ctx.lineWidth = 3; ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(x0, yB);
      ctx.bezierCurveTo(x0, yC, x1, yC, x1, yB - 8);
      ctx.stroke();
      ctx.beginPath();                                   // 矢尻 (移動先を指す)
      ctx.moveTo(x1, yB + 1); ctx.lineTo(x1 - 6, yB - 9); ctx.lineTo(x1 + 6, yB - 9);
      ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.arc(x0, yB, 3.5, 0, Math.PI * 2); ctx.fill();   // 起点
      if (arrow.label) {
        // ラベルは曲線の頂点に重ねる (背景を塗って線より手前に出す)
        const apexY = 0.25 * yB + 0.75 * yC;
        ctx.font = "bold 12px sans-serif";
        ctx.textAlign = "center"; ctx.textBaseline = "middle";
        const lx = (x0 + x1) / 2;
        const tw = ctx.measureText(arrow.label).width;
        ctx.fillStyle = th.canvasBg;
        ctx.fillRect(lx - tw / 2 - 4, apexY - 8, tw + 8, 16);
        ctx.strokeStyle = C_ARROW; ctx.lineWidth = 1.5;
        ctx.strokeRect(lx - tw / 2 - 4, apexY - 8, tw + 8, 16);
        ctx.fillStyle = C_ARROW;
        ctx.fillText(arrow.label, lx, apexY + 1);
      }
    }

    ctx.restore();
  }

  // ════════════════════════════════════════════════════════════════════
  // kv_table – キーと値の 2 段の表 (BMH のずらし表)
  // ════════════════════════════════════════════════════════════════════
  _drawKvTable(obj, areaY, areaH) {
    const { label = "", keys = [], values = [], highlights = {},
            row_labels = ["key", "value"] } = obj;
    const k = keys.length;
    if (k === 0) return;

    const ctx = this.ctx;
    const cw  = this.cw;
    const th  = _acTheme();
    const C_TABLE = "#8a6ac8";

    ctx.save();
    // 見出し (label) は表の右に置き、縦の余白を使わない
    ctx.font = "bold 11px sans-serif";
    const LBL_W  = Math.ceil(Math.max(...row_labels.map(s => ctx.measureText(s).width))) + 14;
    ctx.font = "bold 12px sans-serif";
    const TTL_W  = label ? Math.ceil(ctx.measureText(label).width) + 12 : 0;
    const PAD_L = 8, PAD_R = 10, PAD_V = 4;
    const availW = cw - PAD_L - LBL_W - PAD_R - TTL_W;
    const cellW  = Math.min(48, availW / k);                 // 横は必ず収める
    const cellH  = Math.max(14, Math.min(32, (areaH - PAD_V * 2) / 2));
    const gridX  = PAD_L + LBL_W;
    const gridY  = areaY + PAD_V + Math.max(0, (areaH - PAD_V * 2 - cellH * 2) / 2);

    if (label) {
      ctx.fillStyle = th.valueLabelColor;
      ctx.textAlign = "left"; ctx.textBaseline = "middle";
      ctx.fillText(label, gridX + k * cellW + 10, gridY + cellH);
    }

    const fitText = (s, x, y, w, h, bold) => {
      let size = Math.max(8, Math.min(16, h * 0.55));
      ctx.font = `${bold ? "bold " : ""}${size}px monospace`;
      while (size > 8 && ctx.measureText(s).width > w - 4) {
        size -= 1;
        ctx.font = `${bold ? "bold " : ""}${size}px monospace`;
      }
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(s, x + w / 2, y + h / 2 + 1);
    };

    for (let r = 0; r < 2; r++) {
      const y = gridY + r * cellH;
      ctx.fillStyle = th.valueLabelColor;
      ctx.font = "bold 11px sans-serif";
      ctx.textAlign = "right"; ctx.textBaseline = "middle";
      ctx.fillText(row_labels[r] ?? "", gridX - 8, y + cellH / 2);
      for (let c = 0; c < k; c++) {
        const x  = gridX + c * cellW;
        const hl = highlights[String(c)];
        ctx.fillStyle = r === 0 ? th.cellEmptyBg : th.cellBg;
        ctx.fillRect(x, y, cellW - 1, cellH);
        if (hl) {
          ctx.save(); ctx.globalAlpha = 0.5;
          ctx.fillStyle = hl; ctx.fillRect(x, y, cellW - 1, cellH);
          ctx.restore();
        }
        ctx.strokeStyle = hl || C_TABLE;
        ctx.lineWidth   = hl ? 2.5 : 1.5;
        ctx.strokeRect(x + 0.75, y + 0.75, cellW - 2.5, cellH - 1.5);
        const v = r === 0 ? keys[c] : values[c];
        ctx.fillStyle = th.cellText;
        fitText((v === null || v === undefined) ? "" : String(v), x, y, cellW, cellH, r === 0);
      }
    }

    ctx.restore();
  }

  // ── プレビュー描画 ────────────────────────────────────────────────
  /**
   * @param {number}   numItems
   * @param {boolean}  sorted
   * @param {number|null} forcedTarget
   * @param {Array|null}  sharedValues
   * @param {boolean}  showTarget
   * @param {string}   mode  "bars" | "cells"
   */
  drawPreview(numItems, sorted = false, forcedTarget = null,
              sharedValues = null, showTarget = true, mode = "bars") {
    const maxVal = numItems >= 200 ? 999 : 99;
    let values = sharedValues
      ? [...sharedValues]
      : Array.from({ length: numItems }, () => Math.floor(Math.random() * maxVal) + 1);
    if (sorted) values.sort((a, b) => a - b);

    const target = showTarget
      ? (forcedTarget !== null ? forcedTarget : values[Math.floor(Math.random() * numItems)])
      : null;

    const type = (mode === "cells") ? "array1d_cells" : "array1d";
    this.draw({
      objects: [{
        id:             "preview",
        type,
        values,
        label:          "Data",
        highlights:     {},
        fills:          [],
        pointer:        null,
        watchman_index: null,
        target,
        log_scale:      false,
        weight:         1,
      }],
      texts:    [],
      finished: false,
    });
    return { values, target };
  }
}
