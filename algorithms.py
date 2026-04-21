"""
algorithms.py – Web 向けアルゴリズムジェネレータ (ArrayAnimation)

オブジェクト種別:
  array1d        – 棒グラフ (後方互換)
  array1d_cells  – 正方形セル配列
  heap_tree      – ヒープ二分木
  bucket_rows    – バケツ行 / 動的キュー
  tape           – 無端テープ
  fib_tree       – フィボナッチ再帰木
  staircase      – 階段状テキスト (階乗再帰)
"""

from random import randint, random as _rand, sample as _sample
import math
import copy

# ---------------------------------------------------------------------------
# 共通ヘルパー
# ---------------------------------------------------------------------------

def _f(objects, texts=None, finished=False, found=None, text_position="top"):
    return {"objects": objects, "texts": texts or [], "finished": finished, "found": found,
            "text_position": text_position}

def _a(id, values, label="", hl=None, fills=None, ptr=None,
       watchman=None, target=None, log_scale=False):
    return {
        "id": id, "type": "array1d",
        "values": list(values), "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "fills": fills or [], "pointer": ptr,
        "watchman_index": watchman, "target": target,
        "log_scale": log_scale,
    }

def _c(id, values, label="", hl=None, fills=None, ptr=None,
       watchman=None, target=None, weight=1):
    return {
        "id": id, "type": "array1d_cells",
        "values": list(values), "label": label,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "fills": fills or [], "pointer": ptr,
        "watchman_index": watchman, "target": target,
        "weight": weight,
    }

def _heap_tree(id, values, heap_size, hl=None, label="", weight=2.5, confirmed_min=0):
    return {
        "id": id, "type": "heap_tree",
        "values": list(values), "heap_size": heap_size,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "label": label, "weight": weight,
        "confirmed_min": confirmed_min,
    }

def _bucket_rows(id, buckets, bucket_colors, label="",
                 bucket_labels=None, active_bucket=None, weight=3, direction="rows"):
    n = len(buckets)
    return {
        "id": id, "type": "bucket_rows", "num_buckets": n,
        "buckets": [list(b) for b in buckets],
        "bucket_colors": list(bucket_colors),
        "bucket_labels": bucket_labels or [str(i) for i in range(n)],
        "label": label, "active_bucket": active_bucket, "weight": weight,
        "direction": direction,
    }

def _tape(id, cells, head, label="", color="#4472C4", weight=1):
    return {
        "id": id, "type": "tape",
        "cells": list(cells), "head": int(head),
        "label": label, "color": color, "weight": weight,
    }

def _staircase(id, rows, label=""):
    return {
        "id": id, "type": "staircase",
        "rows": [dict(r) for r in rows],
        "label": label,
    }

def _ptr(index, label, color="#cc00cc"):
    return {"index": index, "label": str(label), "color": color}

def _max_val(n):
    return 999 if n >= 200 else 99

def _auto_target(data):
    if _rand() < 0.7:
        return data[randint(0, len(data) - 1)]
    return randint(1, _max_val(len(data)))

def _make_sort_data(n, data_condition=0, data=None):
    if data is not None:
        return list(data)
    max_val = _max_val(n)
    if data_condition == 1:
        return sorted([randint(1, max_val) for _ in range(n)])
    elif data_condition == 2:
        return sorted([randint(1, max_val) for _ in range(n)], reverse=True)
    elif data_condition == 3:
        lst = sorted([randint(1, max_val) for _ in range(n)])
        for _ in range(max(1, n // 10)):
            i, j = _sample(range(n), 2)
            lst[i], lst[j] = lst[j], lst[i]
        return lst
    else:
        return [randint(1, max_val) for _ in range(n)]


# ===========================================================================
# 探索アルゴリズム (type: "search")
# ===========================================================================

def linear_search(n, target=None, data=None):
    data = list(data) if data is not None else [randint(1, _max_val(n)) for _ in range(n)]
    if target is None: target = _auto_target(data)
    N = len(data)
    base = [{"message": f"N = {N},   target = {target}", "color": "white"}]
    yield _f([_c("data", data, "Data", target=target)], base)
    for i in range(N):
        found = (data[i] == target)
        cmp   = "==" if found else "!="
        t     = base + [{"message": f"data[{i}] = {data[i]}   {cmp}   {target}",
                          "color": "red" if found else "lightgreen"}]
        if found:
            t2 = base + [{"message": f"Found!   index = {i}", "color": "red"}]
            for _ in range(3):
                yield _f([_c("data", data, "Data", hl={i: "yellow"}, ptr=_ptr(i, f"<=> {target}"), target=target)], t2)
                yield _f([_c("data", data, "Data", hl={i: "#ff4444"}, ptr=_ptr(i, f"== {target}", "red"), target=target)], t2)
            yield _f([_c("data", data, "Data", hl={i: "#ff4444"}, target=target)], t2, finished=True, found=True)
            return
        yield _f([_c("data", data, "Data", hl={i: "yellow"}, ptr=_ptr(i, f"<=> {target}"), target=target)], t)
    yield _f([_c("data", data, "Data", target=target)],
             base + [{"message": "Target Not Found!", "color": "red"}], finished=True, found=False)


def linear_search_watchman(n, target=None, data=None):
    data = list(data) if data is not None else [randint(1, _max_val(n)) for _ in range(n)]
    if target is None: target = _auto_target(data)
    N = len(data)
    base = [{"message": f"N = {N},   target = {target}", "color": "white"}]
    yield _f([_c("data", data, "Data", target=target)], base)
    s = data + [target]
    yield _f([_c("data", s, "Data", hl={N: "yellow"}, watchman=N, target=target)],
             base + [{"message": f"番兵 {target} を末尾 (index {N}) に追加", "color": "orange"}])
    i = 0
    while s[i] != target:
        yield _f([_c("data", s, "Data", hl={i: "yellow"}, ptr=_ptr(i, f"<=> {target}"), watchman=N, target=target)],
                 base + [{"message": f"data[{i}] = {s[i]}   !=   {target}", "color": "lightgreen"}])
        i += 1
    if i >= N:
        yield _f([_c("data", s, "Data", hl={i: "yellow"}, ptr=_ptr(i, "sentinel", "orange"), watchman=N, target=target)],
                 base + [{"message": "番兵に到達 → Target Not Found!", "color": "red"}], finished=True, found=False)
    else:
        t3 = base + [{"message": f"Found!   index = {i}", "color": "red"}]
        for _ in range(3):
            yield _f([_c("data", s, "Data", hl={i: "yellow"}, ptr=_ptr(i, f"<=> {target}"), watchman=N, target=target)], t3)
            yield _f([_c("data", s, "Data", hl={i: "#ff4444"}, ptr=_ptr(i, f"== {target}", "red"), watchman=N, target=target)], t3)
        yield _f([_c("data", s, "Data", hl={i: "#ff4444"}, watchman=N, target=target)], t3, finished=True, found=True)


def linear_search_sorted(n, target=None, data=None):
    data = sorted(data) if data is not None else sorted([randint(1, _max_val(n)) for _ in range(n)])
    if target is None: target = _auto_target(data)
    N = len(data)
    base = [{"message": f"Sorted,   N = {N},   target = {target}", "color": "white"}]
    yield _f([_c("data", data, "Data (Sorted)", target=target)], base)
    for i in range(N):
        found = (data[i] == target); over = (data[i] > target)
        cmp   = "==" if found else (">=" if over else "<")
        color = "red" if found else ("orange" if over else "lightgreen")
        t     = base + [{"message": f"data[{i}] = {data[i]}   {cmp}   {target}", "color": color}]
        if found:
            t2 = base + [{"message": f"Found!   index = {i}", "color": "red"}]
            for _ in range(3):
                yield _f([_c("data", data, "Data (Sorted)", hl={i: "yellow"}, ptr=_ptr(i, f">= {target}"), target=target)], t2)
                yield _f([_c("data", data, "Data (Sorted)", hl={i: "#ff4444"}, ptr=_ptr(i, f"== {target}", "red"), target=target)], t2)
            yield _f([_c("data", data, "Data (Sorted)", hl={i: "#ff4444"}, target=target)], t2, finished=True, found=True)
            return
        elif over:
            yield _f([_c("data", data, "Data (Sorted)", hl={i: "yellow"}, ptr=_ptr(i, f">= {target}"), target=target)], t)
            yield _f([_c("data", data, "Data (Sorted)", hl={i: "yellow"}, target=target)],
                     base + [{"message": f"data[{i}] > {target} → Not Found!", "color": "red"}], finished=True, found=False)
            return
        yield _f([_c("data", data, "Data (Sorted)", hl={i: "yellow"}, ptr=_ptr(i, f">= {target}"), target=target)], t)
    yield _f([_c("data", data, "Data (Sorted)", target=target)],
             base + [{"message": "Target Not Found! (end of array)", "color": "red"}], finished=True, found=False)


def binary_search(n, target=None, data=None):
    data = sorted(data) if data is not None else sorted([randint(1, _max_val(n)) for _ in range(n)])
    if target is None: target = _auto_target(data)
    N = len(data)
    base = [{"message": f"Sorted,   N = {N},   target = {target}", "color": "white"}]
    yield _f([_c("data", data, "Data (Sorted)", target=target)], base)
    first, last, fills = 0, N - 1, []
    while first <= last:
        center = (first + last) // 2
        t = base + [{"message": f"first={first}  center={center}  last={last}", "color": "lightgreen"},
                    {"message": f"data[{center}] = {data[center]}", "color": "cyan"}]
        yield _f([_c("data", data, "Data (Sorted)", hl={center: "yellow", first: "#aaffaa", last: "#aaffaa"},
                      fills=fills, ptr=_ptr(center, f"? {target}"), target=target)], t)
        if data[center] == target:
            t2 = base + [{"message": f"Found!   index = {center}", "color": "red"}]
            for _ in range(3):
                yield _f([_c("data", data, "Data (Sorted)", hl={center: "yellow"}, fills=fills, ptr=_ptr(center, f"== {target}"), target=target)], t2)
                yield _f([_c("data", data, "Data (Sorted)", hl={center: "#ff4444"}, fills=fills, ptr=_ptr(center, f"== {target}", "red"), target=target)], t2)
            yield _f([_c("data", data, "Data (Sorted)", hl={center: "#ff4444"}, fills=fills, target=target)], t2, finished=True, found=True)
            return
        elif target < data[center]:
            fills = fills + [{"from": center, "to": last, "color": "#555555"}]; last = center - 1
        else:
            fills = fills + [{"from": first, "to": center, "color": "#555555"}]; first = center + 1
        yield _f([_c("data", data, "Data (Sorted)", fills=fills, target=target)],
                 base + [{"message": f"→ {'左' if target < data[center] else '右'}半分を探索", "color": "orange"}])
    yield _f([_c("data", data, "Data (Sorted)", fills=fills, target=target)],
             base + [{"message": "Target Not Found!", "color": "red"}], finished=True, found=False)


def binary_search_recursive(n, target=None, data=None):
    data = sorted(data) if data is not None else sorted([randint(1, _max_val(n)) for _ in range(n)])
    if target is None: target = _auto_target(data)
    N = len(data)
    base = [{"message": f"Sorted,   N = {N},   target = {target}   (再帰)", "color": "white"}]
    yield _f([_c("data", data, "Data (Sorted)", target=target)], base)

    def rec(first, last, fills, depth):
        if first > last:
            yield _f([_c("data", data, "Data (Sorted)", fills=fills, target=target)],
                     base + [{"message": f"depth={depth}: first > last → Not Found!", "color": "red"}],
                     finished=True, found=False)
            return
        center = (first + last) // 2
        t = base + [{"message": f"depth={depth}: first={first}  center={center}  last={last}", "color": "lightgreen"},
                    {"message": f"data[{center}] = {data[center]}", "color": "cyan"}]
        yield _f([_c("data", data, "Data (Sorted)", hl={center: "yellow", first: "#aaffaa", last: "#aaffaa"},
                      fills=fills, ptr=_ptr(center, f"? {target}"), target=target)], t)
        if data[center] == target:
            t2 = base + [{"message": f"Found!   depth={depth},   index = {center}", "color": "red"}]
            for _ in range(3):
                yield _f([_c("data", data, "Data (Sorted)", hl={center: "yellow"}, fills=fills, ptr=_ptr(center, f"== {target}"), target=target)], t2)
                yield _f([_c("data", data, "Data (Sorted)", hl={center: "#ff4444"}, fills=fills, ptr=_ptr(center, f"== {target}", "red"), target=target)], t2)
            yield _f([_c("data", data, "Data (Sorted)", hl={center: "#ff4444"}, fills=fills, target=target)], t2, finished=True, found=True)
        elif target < data[center]:
            new_fills = fills + [{"from": center, "to": last, "color": "#555555"}]
            yield _f([_c("data", data, "Data (Sorted)", fills=new_fills, target=target)],
                     base + [{"message": f"depth={depth}: {target} < data[{center}] → 左へ再帰", "color": "orange"}])
            yield from rec(first, center - 1, new_fills, depth + 1)
        else:
            new_fills = fills + [{"from": first, "to": center, "color": "#555555"}]
            yield _f([_c("data", data, "Data (Sorted)", fills=new_fills, target=target)],
                     base + [{"message": f"depth={depth}: {target} > data[{center}] → 右へ再帰", "color": "orange"}])
            yield from rec(center + 1, last, new_fills, depth + 1)

    yield from rec(0, N - 1, [], 0)


# ===========================================================================
# ソートアルゴリズム (type: "sort")
# ===========================================================================

# ---------------------------------------------------------------------------
# マージソート (反復) – バッファ↔データ両方のコピーを可視化
# ---------------------------------------------------------------------------

def merge_sort_iter(n, data_condition=0, data=None):
    data   = _make_sort_data(n, data_condition, data)
    N      = len(data)
    buffer = [0] * N
    base   = [{"message": f"マージソート (反復)  N = {N}", "color": "white"}]

    # 最初からバッファを表示
    yield _f([_c("data", data, "Data"), _c("buf", buffer, "Buffer [0]*N")], base)

    msize = 1
    while msize < N:
        k = 0; base1 = 0
        while base1 < N:
            base2 = base1 + msize
            i = j = 0
            while True:
                ai = base1 + i; bj = base2 + j
                if i < msize and ai < N and j < msize and bj < N:
                    t = base + [{"message": f"msize={msize}  比較 data[{ai}]={data[ai]} vs data[{bj}]={data[bj]}",
                                  "color": "lightgreen"}]
                    yield _f([_c("data", data, "Data",   hl={ai: "yellow", bj: "orange"}),
                               _c("buf",  buffer, "Buffer", hl={k: "#334466"})], t)
                    if data[ai] <= data[bj]:
                        buffer[k] = data[ai]
                        yield _f([_c("data", data, "Data",   hl={ai: "#88ff88"}),
                                   _c("buf",  buffer, "Buffer", hl={k: "yellow"})], t)
                        i += 1
                    else:
                        buffer[k] = data[bj]
                        yield _f([_c("data", data, "Data",   hl={bj: "#ff8888"}),
                                   _c("buf",  buffer, "Buffer", hl={k: "yellow"})], t)
                        j += 1
                    k += 1
                elif i < msize and ai < N:
                    buffer[k] = data[ai]; i += 1; k += 1
                elif j < msize and bj < N:
                    buffer[k] = data[bj]; j += 1; k += 1
                else:
                    break
            base1 += 2 * msize

        # Buffer → Data へのコピー (セルごとに可視化)
        t_copy = base + [{"message": f"msize={msize}: Buffer → Data へコピー", "color": "cyan"}]
        for ci in range(N):
            data[ci] = buffer[ci]
            hl_d = {j: "#44aa44" for j in range(ci)}
            hl_d[ci] = "yellow"
            yield _f([_c("data", list(data), "Data",   hl=hl_d),
                      _c("buf",  list(buffer), "Buffer", hl={ci: "#88ff88"})], t_copy)
        yield _f([_c("data", list(data), "Data",   hl={j: "#44aa44" for j in range(N)}),
                  _c("buf",  list(buffer), "Buffer")],
                 base + [{"message": f"msize={msize} 完了", "color": "cyan"}])
        msize *= 2

    yield _f([_c("data", data, "Data"), _c("buf", buffer, "Buffer")],
             base + [{"message": "ソート完了!", "color": "#FFD700"}], finished=True)


# ---------------------------------------------------------------------------
# マージソート (再帰) – ソート範囲 + コピーバックを可視化
# ---------------------------------------------------------------------------

def merge_sort_rec(n, data_condition=0, data=None):
    data = _make_sort_data(n, data_condition, data)
    N    = len(data)
    aux  = [0] * N
    base = [{"message": f"マージソート (再帰)  N = {N}", "color": "white"}]

    # 最初からバッファを表示
    yield _f([_c("data", data, "Data"), _c("aux", aux, "Auxiliary [0]*N")], base)

    RANGE_COLOR = "rgba(40,100,200,0.18)"

    def _merge(lo, mid, hi, depth):
        for idx in range(lo, hi + 1):
            aux[idx] = data[idx]
        range_fill = {"from": lo, "to": hi, "color": RANGE_COLOR}
        i, j, k = lo, mid + 1, lo
        while i <= mid or j <= hi:
            if   i > mid:          v = aux[j]; src = j; j += 1
            elif j > hi:           v = aux[i]; src = i; i += 1
            elif aux[i] <= aux[j]: v = aux[i]; src = i; i += 1
            else:                  v = aux[j]; src = j; j += 1
            t = base + [{"message": f"depth={depth}: merge [{lo}..{mid}]+[{mid+1}..{hi}]",
                          "color": "lightgreen"}]
            yield _f([_c("data", list(data), "Data",
                          hl={k: "yellow"}, fills=[range_fill]),
                       _c("aux", list(aux), "Auxiliary",
                          hl={src: "#88ff88"}, fills=[range_fill])], t)
            data[k] = v; k += 1

        # コピーバック完了フレーム
        hl_done = {j: "#44aa44" for j in range(lo, hi + 1)}
        yield _f([_c("data", list(data), "Data", hl=hl_done, fills=[range_fill]),
                  _c("aux", list(aux), "Auxiliary", fills=[range_fill])],
                 base + [{"message": f"depth={depth}: [{lo}..{hi}] マージ完了", "color": "cyan"}])

    def _msort(lo, hi, depth):
        if lo >= hi:
            return
        mid = (lo + hi) // 2
        range_fill = {"from": lo, "to": hi, "color": RANGE_COLOR}
        t = base + [{"message": f"depth={depth}: ソート範囲 [{lo}..{hi}] → 分割",
                      "color": "cyan"}]
        yield _f([_c("data", list(data), "Data",
                      fills=[{"from": lo, "to": mid, "color": "rgba(80,180,80,0.18)"},
                              {"from": mid+1, "to": hi, "color": "rgba(180,80,80,0.18)"}]),
                   _c("aux", list(aux), "Auxiliary", fills=[range_fill])], t)
        yield from _msort(lo, mid, depth + 1)
        yield from _msort(mid + 1, hi, depth + 1)
        yield from _merge(lo, mid, hi, depth)

    yield from _msort(0, N - 1, 0)
    yield _f([_c("data", data, "Data"), _c("aux", aux, "Auxiliary")],
             base + [{"message": "ソート完了!", "color": "#FFD700"}], finished=True)


# ---------------------------------------------------------------------------
# マージソート (テープ) – 初期配列 → 3テープ
# ---------------------------------------------------------------------------

def merge_sort_tape(n, data_condition=0, data=None):
    data = _make_sort_data(n, data_condition, data)
    N    = min(len(data), 32)
    data = data[:N]

    base = [{"message": f"マージソート (3テープ)  N = {N}", "color": "white"}]

    tape_a = list(data)
    tape_b = []
    tape_c = []

    def frame(ha, hb, hc, msg=None, color="lightgreen", finished=False):
        texts = base[:]
        if msg:
            texts = texts + [{"message": msg, "color": color}]
        return _f([
            _tape("tapeA", tape_a, ha, "テープ A", "#4472C4"),
            _tape("tapeB", tape_b, hb, "テープ B", "#44aa44"),
            _tape("tapeC", tape_c, hc, "テープ C", "#cc6600"),
        ], texts, finished=finished)

    # 初期状態を array1d_cells で表示してから テープ表示へ
    yield _f([_c("init", data, "初期データ")],
             base + [{"message": "テープAへ転送します", "color": "cyan"}])
    yield frame(0, 0, 0, "テープAに全データ。テープB・Cは空白。")

    msize = 1
    while msize < N:
        # 分配
        old_a = list(tape_a)
        tape_b, tape_c = [], []
        i = 0; chunk = 0
        while i < N:
            end  = min(i + msize, N)
            to_b = (chunk % 2 == 0)
            for j in range(i, end):
                v = old_a[j]
                if to_b:
                    tape_b.append(v)
                    yield frame(j, len(tape_b)-1, max(0, len(tape_c)-1),
                                 f"msize={msize}: A[{j}]={v} → テープ B")
                else:
                    tape_c.append(v)
                    yield frame(j, max(0, len(tape_b)-1), len(tape_c)-1,
                                 f"msize={msize}: A[{j}]={v} → テープ C")
            i += msize; chunk += 1
        yield frame(0, 0, 0, f"msize={msize}: 分配完了", "cyan")

        # マージ
        tape_a = []
        ib = ic = 0
        while ib < len(tape_b) or ic < len(tape_c):
            b_end = min(ib + msize, len(tape_b))
            c_end = min(ic + msize, len(tape_c))
            bi, ci = ib, ic
            while bi < b_end or ci < c_end:
                use_b = (ci >= c_end) or (bi < b_end and tape_b[bi] <= tape_c[ci])
                if use_b:
                    v = tape_b[bi]; bi += 1
                    tape_a.append(v)
                    yield frame(len(tape_a)-1, bi-1, ci,
                                 f"msize={msize}: B[{bi-1}]={v} → A[{len(tape_a)-1}]")
                else:
                    v = tape_c[ci]; ci += 1
                    tape_a.append(v)
                    yield frame(len(tape_a)-1, bi, ci-1,
                                 f"msize={msize}: C[{ci-1}]={v} → A[{len(tape_a)-1}]")
            ib = b_end; ic = c_end
        yield frame(0, 0, 0, f"msize={msize}: マージ完了", "cyan")
        msize *= 2

    yield frame(0, 0, 0, "ソート完了!", "#FFD700", finished=True)


# ---------------------------------------------------------------------------
# ヒープソート – 正方形セル + ヒープ木 (insertHeap 方式: 根1つから成長)
# ---------------------------------------------------------------------------

def heap_sort(n, data_condition=0, data=None):
    data = _make_sort_data(n, data_condition, data)
    N    = len(data)
    base = [{"message": f"ヒープソート  N = {N}", "color": "white"}]

    done_hl = {}

    def objs(hl=None, heap_size=None):
        sz = heap_size if heap_size is not None else N
        combined = dict(done_hl)
        if hl:
            combined.update(hl)
        return [
            _c("data", list(data), "Data", hl=combined, weight=1),
            _heap_tree("tree", data, sz, hl=combined, weight=2.5),
        ]

    def _sift_up(pos, heap_size):
        """挿入後に上へ浮かせる"""
        while pos > 0:
            parent = (pos - 1) // 2
            hl = {pos: "yellow", parent: "#aaaaff"}
            t  = base + [{"message": f"sift_up: data[{pos}]={data[pos]}  vs  parent[{parent}]={data[parent]}", "color": "lightgreen"}]
            yield _f(objs(hl=hl, heap_size=heap_size), t)
            if data[pos] > data[parent]:
                data[pos], data[parent] = data[parent], data[pos]
                hl2 = {pos: "orange", parent: "orange"}
                yield _f(objs(hl=hl2, heap_size=heap_size),
                         base + [{"message": f"swap [{pos}] ↔ [{parent}]", "color": "orange"}])
                pos = parent
            else:
                break

    def _sift_down(i, size):
        """取り出し後に下へ沈める"""
        while True:
            largest = i
            l, r    = 2*i+1, 2*i+2
            if l < size and data[l] > data[largest]: largest = l
            if r < size and data[r] > data[largest]: largest = r
            hl = {i: "yellow"}
            if l < size: hl[l] = "#aaaaff"
            if r < size: hl[r] = "#44aaff"
            t = base + [{"message": f"sift_down i={i}  最大={largest}", "color": "lightgreen"}]
            yield _f(objs(hl=hl, heap_size=size), t)
            if largest == i:
                break
            data[i], data[largest] = data[largest], data[i]
            hl2 = {i: "orange", largest: "orange"}
            yield _f(objs(hl=hl2, heap_size=size),
                     base + [{"message": f"swap [{i}] ↔ [{largest}]", "color": "orange"}])
            i = largest

    # Phase 1: 1 要素ずつ末尾に挿入 → sift_up で整列 (木が根から成長)
    t1 = base + [{"message": "フェーズ1: ヒープ構築 (1要素ずつ挿入・sift up)", "color": "cyan"}]
    yield _f(objs(heap_size=1), t1)          # 根ノードだけの木
    for i in range(1, N):
        yield _f(objs(hl={i: "yellow"}, heap_size=i + 1),
                 t1 + [{"message": f"data[{i}]={data[i]} を末尾に挿入 (heap_size={i+1})", "color": "lightgreen"}])
        yield from _sift_up(i, i + 1)

    t2 = base + [{"message": "ヒープ構築完了 → フェーズ2: 最大値を順次取り出す", "color": "cyan"}]
    yield _f(objs(heap_size=N), t2)

    # Phase 2: 最大値 (根) を末尾と swap → sift_down
    for end in range(N - 1, 0, -1):
        data[0], data[end] = data[end], data[0]
        done_hl[end] = "#44aa44"
        hl = {0: "orange", end: "orange"}
        yield _f(objs(hl=hl, heap_size=end),
                 base + [{"message": f"data[0]={data[end]} → 位置 {end} (確定)", "color": "orange"}])
        yield from _sift_down(0, end)

    done_hl[0] = "#44aa44"
    yield _f(objs(heap_size=0),
             base + [{"message": "ソート完了!", "color": "#FFD700"}], finished=True)


# ---------------------------------------------------------------------------
# バケツソート (カウント方式) – 値域 1..K のカウント配列で可視化
# ---------------------------------------------------------------------------

def bucket_sort(n, data_condition=0, data=None):
    K  = 20   # バケツ数 = 値域 (1..K)
    N  = max(8, min(int(n), 256))

    # 値域 1..K のデータを新規生成 (外部 data は値域が異なるため無視)
    if data_condition == 1:
        orig = sorted([randint(1, K) for _ in range(N)])
    elif data_condition == 2:
        orig = sorted([randint(1, K) for _ in range(N)], reverse=True)
    elif data_condition == 3:
        lst = sorted([randint(1, K) for _ in range(N)])
        for _ in range(max(1, N // 10)):
            i, j = _sample(range(N), 2)
            lst[i], lst[j] = lst[j], lst[i]
        orig = lst
    else:
        orig = [randint(1, K) for _ in range(N)]

    data = list(orig)
    base = [{"message": f"バケツソート  N={N},  値域=1~{K},  バケツ数={K}", "color": "white"}]

    # counts[i] = 値 (i+1) の出現回数  (i: 0..K-1)
    counts = [0] * K

    def disp(data_hl=None, cnt_hl=None):
        return [
            _c("data",   list(data),   "Data",                     hl=data_hl or {}, weight=1),
            _c("counts", list(counts), f"Counts  [index = value-1]", hl=cnt_hl  or {}, weight=1),
        ]

    yield _f(disp(), base + [{"message": "入力データとカウント配列 (初期すべて 0)", "color": "cyan"}])

    # フェーズ1: 各要素をカウントアップ
    t1 = base + [{"message": "フェーズ1: 各要素に対応するバケツをカウントアップ", "color": "cyan"}]
    for i in range(N):
        v  = data[i]
        bi = v - 1          # バケツインデックス (0-based)
        counts[bi] += 1
        yield _f(disp(data_hl={i: "#4472C4"}, cnt_hl={bi: "yellow"}),
                 t1 + [{"message": f"data[{i}]={v}  →  counts[{bi}] = {counts[bi]}", "color": "lightgreen"}])

    yield _f(disp(), base + [{"message": "カウント完了 → フェーズ2: バケツから順に回収", "color": "cyan"}])

    # フェーズ2: カウントに従い result を構築
    result = list(data)   # 上書き
    ri = 0
    t2 = base + [{"message": "フェーズ2: counts 配列からソート済み列を生成", "color": "cyan"}]
    for bi in range(K):
        v = bi + 1
        while counts[bi] > 0:
            counts[bi] -= 1
            result[ri]  = v
            hl_r        = {j: "#44aa44" for j in range(ri)}
            hl_r[ri]    = "#4472C4"
            yield _f([
                _c("result", list(result), "Result",                     hl=hl_r,         weight=1),
                _c("counts", list(counts), f"Counts  [index = value-1]", hl={bi: "yellow"}, weight=1),
            ], t2 + [{"message": f"counts[{bi}] → {counts[bi]}: 値 {v}  →  result[{ri}]", "color": "lightgreen"}])
            ri += 1

    yield _f([_c("data", result, "Data (Sorted)", hl={j: "#44aa44" for j in range(N)})],
             base + [{"message": "ソート完了!", "color": "#FFD700"}], finished=True)


# ---------------------------------------------------------------------------
# 基数ソート (LSD) – キューを上・データを下に配置
# ---------------------------------------------------------------------------

def radix_sort(n, data_condition=0, data=None):
    data     = _make_sort_data(n, data_condition, data)
    N        = len(data)
    max_val  = max(data)
    n_digits = max(1, math.floor(math.log10(max_val)) + 1) if max_val > 0 else 1

    DIGIT_COLORS = [
        "#4444cc", "#44aacc", "#44ccaa", "#44cc44", "#aacc44",
        "#cccc44", "#ccaa44", "#cc4444", "#cc44aa", "#aa44cc",
    ]
    DIGIT_NAMES = ["1の位", "10の位", "100の位", "1000の位"]

    base = [{"message": f"基数ソート (LSD)  N={N},  max={max_val},  桁数={n_digits}", "color": "white"}]

    queues = [[] for _ in range(10)]
    labels = [str(i) for i in range(10)]

    def objs(data_hl=None, active_q=None):
        # Data (weight=2) を上, Digit Queues (weight=3.5) を下
        # テキストは上部描画 → Data エリア上部に重なるが、下半分は見える
        # weight=2 で Data が十分な高さを確保し、テキストボックス分を吸収する
        return [
            _bucket_rows("dq", queues, DIGIT_COLORS, "Digit Queues",
                         bucket_labels=labels, active_bucket=active_q,
                         weight=3.5, direction="columns"),
            _c("data", data, "Data", hl=data_hl, weight=2.5),
        ]

    def rf(objects, texts, finished=False):
        """radix sort 用フレーム: テキストを上部に配置"""
        return _f(objects, texts, finished=finished, text_position="top")

    yield rf(objs(), base)

    exp = 1
    for pass_num in range(n_digits):
        dname = DIGIT_NAMES[min(pass_num, 3)]
        t_col = base + [{"message": f"パス {pass_num+1}/{n_digits}: {dname}でソート", "color": "cyan"}]

        # 分配
        queues = [[] for _ in range(10)]
        hl = {}
        for i in range(N):
            d = (data[i] // exp) % 10
            queues[d].append(data[i])
            hl[i] = DIGIT_COLORS[d]
            t = t_col + [{"message": f"data[{i}]={data[i]}  {dname}={d} → キュー {d}",
                           "color": "lightgreen"}]
            yield rf(objs(data_hl={**hl, i: "white"}, active_q=d), t)

        yield rf(objs(data_hl=hl),
                 base + [{"message": f"パス {pass_num+1}: 分配完了 → 回収", "color": "cyan"}])

        # 回収
        k = 0
        for d in range(10):
            for v in queues[d]:
                data[k] = v; k += 1

        hl2 = {i: DIGIT_COLORS[(data[i] // exp) % 10] for i in range(N)}
        yield rf(objs(data_hl=hl2),
                 base + [{"message": f"パス {pass_num+1}: {dname}でソート完了", "color": "lightgreen"}])
        exp *= 10

    yield rf(objs(),
             base + [{"message": "ソート完了!", "color": "#FFD700"}], finished=True)


# ===========================================================================
# その他アルゴリズム (type: "misc")
# ===========================================================================

# ---------------------------------------------------------------------------
# 階乗 (反復) – 正方形セル
# ---------------------------------------------------------------------------

def factorial_iter(n, **kwargs):
    N    = max(3, min(int(n), 20))
    base = [{"message": f"階乗 (反復): {N}! を計算", "color": "white"}]
    rows = []

    def _frame(msg=None, color="lightgreen", finished=False):
        texts = base[:]
        if msg:
            texts = texts + [{"message": msg, "color": color}]
        return _f([_staircase("stair", rows)], texts, finished=finished)

    yield _frame("反復的に計算します")
    fact = 1
    for i in range(1, N + 1):
        prev = fact
        fact *= i
        rows.append({"text": f"{prev} × {i} = {fact}", "depth": 0, "color": "yellow"})
        yield _frame(f"ステップ {i}: {prev} × {i} = {fact}", "lightgreen")
        rows[-1]["color"] = "#44aa44"

    rows[-1]["color"] = "#FFD700"
    yield _frame(f"{N}! = {fact}", "#FFD700", finished=True)


# ---------------------------------------------------------------------------
# 階乗 (再帰) – 階段状 staircase 可視化
# ---------------------------------------------------------------------------

def factorial_rec(n, **kwargs):
    N = max(3, min(int(n), 15))
    base = [{"message": f"階乗 (再帰): {N}! を計算", "color": "white"}]

    rows = []

    def _frame(msg=None, color="lightgreen", finished=False):
        texts = base[:]
        if msg:
            texts = texts + [{"message": msg, "color": color}]
        return _f([_staircase("stair", rows)], texts, finished=finished)

    def _calc(k):
        depth = N - k
        if k <= 1:
            rows.append({"text": "fact(1) = 1  ← 基底ケース", "depth": depth, "color": "#ff8888"})
            yield _frame("基底ケース: fact(1) = 1", "cyan")
            return 1

        # 呼び出しフレーム (下降)
        row_idx = len(rows)
        rows.append({"text": f"fact({k}) = {k} × fact({k-1}) = ?", "depth": depth, "color": "yellow"})
        yield _frame(f"fact({k}) を呼び出し中...")
        rows[row_idx]["color"] = "#6688aa"  # 再帰中はグレー

        sub = yield from _calc(k - 1)

        result = k * sub
        # 戻り値フレーム (上昇)
        rows.append({"text": f"fact({k}) = {k} × {sub} = {result}", "depth": depth, "color": "#44aa44"})
        yield _frame(f"fact({k}) = {k} × {sub} = {result}", "#FFD700")
        return result

    yield _frame("再帰的に計算します")
    result = yield from _calc(N)
    yield _frame(f"{N}! = {result}", "#FFD700", finished=True)


# ---------------------------------------------------------------------------
# フィボナッチ (反復) – 累積成長ツリー (添付図の左鎖ツリー形式)
# fib(k) = {左: fib(k-1) の完全ツリー,  右: fib(k-2) の葉ノード}
# 根を1つ追加するたびにツリーが深く成長していく
# ---------------------------------------------------------------------------

def fibonacci_iter(n, **kwargs):
    N = max(4, min(int(n), 12))   # 深さが N になるため 12 程度が上限
    base = [{"message": f"フィボナッチ (反復): fib(0)~fib({N}) を計算", "color": "white"}]

    def leaf_node(k, v, color="#44aa44"):
        return {"n": k, "value": v, "color": color, "left": None, "right": None, "memo": False}

    def frame(root, msg=None, color="lightgreen", finished=False):
        texts = base[:] + ([{"message": msg, "color": color}] if msg else [])
        return _f([{"id": "fib", "type": "fib_tree", "root": copy.deepcopy(root)}],
                  texts, finished=finished)

    # --- 初期値 ---
    root0 = leaf_node(0, 0)
    yield frame(root0, "fib(0) = 0  (初期値)", "cyan")

    root1 = leaf_node(1, 1)
    yield frame(root1, "fib(1) = 1  (初期値)", "cyan")

    prev2_val  = 0;  prev2_root = root0   # fib(0)
    prev1_val  = 1;  prev1_root = root1   # fib(1)

    # --- fib(2)..fib(N): 毎ステップ新しい根を追加 ---
    for k in range(2, N + 1):
        curr_val = prev1_val + prev2_val

        # 新根: 左=fib(k-1)の完全ツリー, 右=fib(k-2)の葉 (値だけ保持)
        new_root = {
            "n": k, "value": curr_val, "color": "#ffff00",
            "left":  copy.deepcopy(prev1_root),
            "right": leaf_node(k - 2, prev2_val),
            "memo":  False,
        }
        yield frame(new_root,
                    f"fib({k}) = fib({k-1}) + fib({k-2}) = {prev1_val} + {prev2_val} = {curr_val}",
                    "lightgreen")
        new_root["color"] = "#44aa44"
        yield frame(new_root, f"fib({k}) = {curr_val}", "#FFD700")

        prev2_val, prev1_val   = prev1_val, curr_val
        prev2_root, prev1_root = prev1_root, new_root

    yield frame(prev1_root, f"fib({N}) = {prev1_val}", "#FFD700", finished=True)


# ---------------------------------------------------------------------------
# フィボナッチ (再帰) – 再帰木
# ---------------------------------------------------------------------------

def fibonacci_rec(n, **kwargs):
    N = max(3, min(int(n), 8))
    base = [{"message": f"フィボナッチ (再帰木)  fib({N}) を計算", "color": "white"}]
    root = {"n": N, "value": None, "color": "#888888", "left": None, "right": None, "memo": False}

    def _frame(msg=None, color="lightgreen", finished=False):
        texts = base[:]
        if msg: texts = texts + [{"message": msg, "color": color}]
        return _f([{"id": "fib", "type": "fib_tree", "root": copy.deepcopy(root)}], texts, finished=finished)

    def _calc(node):
        node["color"] = "#ffff00"
        yield _frame(f"fib({node['n']}) を計算中...")
        if node["n"] <= 1:
            node["value"] = max(0, node["n"]); node["color"] = "#44aa44"
            yield _frame(f"fib({node['n']}) = {node['value']} (基底)", "cyan")
            return
        node["left"] = {"n": node["n"]-1, "value": None, "color": "#888888", "left": None, "right": None, "memo": False}
        yield _frame(f"fib({node['n']}) → 左: fib({node['n']-1})")
        yield from _calc(node["left"])
        node["color"] = "#ffff00"
        node["right"] = {"n": node["n"]-2, "value": None, "color": "#888888", "left": None, "right": None, "memo": False}
        yield _frame(f"fib({node['n']}) → 右: fib({node['n']-2})")
        yield from _calc(node["right"])
        node["value"] = node["left"]["value"] + node["right"]["value"]
        node["color"] = "#44aa44"
        yield _frame(f"fib({node['n']}) = {node['left']['value']} + {node['right']['value']} = {node['value']}", "#FFD700")

    yield _frame("再帰木を展開します")
    yield from _calc(root)
    yield _f([{"id": "fib", "type": "fib_tree", "root": copy.deepcopy(root)}],
             base + [{"message": f"fib({N}) = {root['value']}", "color": "#FFD700"}], finished=True)


# ---------------------------------------------------------------------------
# フィボナッチ (メモ化再帰) – メモから再利用するノードをシアンで表示
# ---------------------------------------------------------------------------

def fibonacci_memo(n, **kwargs):
    N = max(3, min(int(n), 12))   # メモ化により大きい N も可
    base = [{"message": f"フィボナッチ (メモ化再帰)  fib({N}) を計算", "color": "white"}]
    root = {"n": N, "value": None, "color": "#888888", "left": None, "right": None, "memo": False}
    memo = {}

    def _frame(msg=None, color="lightgreen", finished=False):
        texts = base[:]
        if msg: texts = texts + [{"message": msg, "color": color}]
        return _f([{"id": "fib", "type": "fib_tree", "root": copy.deepcopy(root)}], texts, finished=finished)

    def _calc(node):
        node["color"] = "#ffff00"
        if node["n"] in memo:
            node["value"] = memo[node["n"]]; node["color"] = "#44aacc"; node["memo"] = True
            yield _frame(f"fib({node['n']}) = {node['value']}  ← メモから取得", "#44aacc")
            return
        yield _frame(f"fib({node['n']}) を計算中...")
        if node["n"] <= 1:
            node["value"] = max(0, node["n"]); node["color"] = "#44aa44"
            memo[node["n"]] = node["value"]
            yield _frame(f"fib({node['n']}) = {node['value']} (基底)", "cyan")
            return
        node["left"] = {"n": node["n"]-1, "value": None, "color": "#888888", "left": None, "right": None, "memo": False}
        yield _frame(f"fib({node['n']}) → 左: fib({node['n']-1})")
        yield from _calc(node["left"])
        node["color"] = "#ffff00"
        node["right"] = {"n": node["n"]-2, "value": None, "color": "#888888", "left": None, "right": None, "memo": False}
        yield _frame(f"fib({node['n']}) → 右: fib({node['n']-2})")
        yield from _calc(node["right"])
        node["value"] = node["left"]["value"] + node["right"]["value"]
        node["color"] = "#44aa44"; memo[node["n"]] = node["value"]
        yield _frame(f"fib({node['n']}) = {node['left']['value']} + {node['right']['value']} = {node['value']}", "#FFD700")

    yield _frame("メモ化再帰で計算します (シアン = メモから取得)")
    yield from _calc(root)
    yield _f([{"id": "fib", "type": "fib_tree", "root": copy.deepcopy(root)}],
             base + [{"message": f"fib({N}) = {root['value']}", "color": "#FFD700"}], finished=True)




# ===========================================================================
# アルゴリズム一覧 / データサイズ一覧
# ===========================================================================

AlgorithmList = [
    # ── 探索 ──
    ("線形探索 (基本)",             linear_search,           {"type": "search"}),
    ("線形探索 (番兵法)",            linear_search_watchman,  {"type": "search"}),
    ("線形探索 (整列済み配列)",       linear_search_sorted,    {"type": "search", "sorted": True}),
    ("二分探索 (反復)",             binary_search,           {"type": "search", "sorted": True}),
    ("二分探索 (再帰)",             binary_search_recursive, {"type": "search", "sorted": True}),
    # ── ソート ──
    ("マージソート (反復)",           merge_sort_iter,         {"type": "sort"}),
    ("マージソート (再帰)",           merge_sort_rec,          {"type": "sort"}),
    ("マージソート (3テープ)",        merge_sort_tape,         {"type": "sort"}),
    ("ヒープソート",                 heap_sort,               {"type": "sort"}),
    ("バケツソート",                 bucket_sort,             {"type": "sort"}),
    ("基数ソート (LSD)",            radix_sort,              {"type": "sort"}),
    # ── その他 ──
    ("階乗 (反復)",                 factorial_iter,          {"type": "misc"}),
    ("階乗 (再帰)",                 factorial_rec,           {"type": "misc"}),
    ("フィボナッチ (反復)",           fibonacci_iter,          {"type": "misc"}),
    ("フィボナッチ (再帰)",           fibonacci_rec,           {"type": "misc"}),
    ("フィボナッチ (メモ化)",         fibonacci_memo,          {"type": "misc"}),
]

DataSizeList = [8, 16, 32, 64, 100, 128, 200, 256, 512]
