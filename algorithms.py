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
  string_match   – 文字列照合 (上段パターン / 下段テキスト)
  kv_table       – キーと値の 2 段の表 (BMH のずらし表)
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

def _tape(id, cells, head, label="", color="#4472C4", weight=1,
          hl=None, sorted_upto=None, swap=None, reserve_arc=False,
          head_label=None):
    """無端テープ

    hl          – {インデックス: "色"} で個別セルをハイライト
    sorted_upto – このインデックス未満を「整列確定」(薄緑)で表示
    swap        – {"a": idx, "b": idx, "phase": "before"|"after"} 交換アーク注釈
    reserve_arc – True でセル上に注釈用スペース・セル下に添字ラベルを確保
    head_label  – ヘッド矢印の下に表示する名前 (例 "pos")
    """
    return {
        "id": id, "type": "tape",
        "cells": list(cells), "head": int(head),
        "label": label, "color": color, "weight": weight,
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "sorted_upto": sorted_upto, "swap": swap,
        "reserve_arc": bool(reserve_arc), "head_label": head_label,
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
# 文字列照合 (type: "string")
#   ルートの PatternMatchingAnimation.py (Matplotlib 版) の Web 移植。
#   - 力まかせ法 / KMP 法 / BMH 法 の 3 本
#   - 元の版の不具合はこちらで修正済み:
#       KMP: 表の作成で「不一致かつ j > 0」のとき同じ i で比較し直していなかった
#            (例: P = "ABAABX" の表が [-1,0,0,1,0,0] になり、照合で一致を見落とす)
#       BMH: ずらし量を不一致になったテキストの文字 T[i] ではなく P[p] で引いていた
#            (ずらし量が常に 1 になり、力まかせ法と同じ動きになっていた)
# ===========================================================================

STR_MAX_TEXT    = 64     # テキストの最大長 (これ以上はセルが小さくなりすぎる)
STR_MAX_PATTERN = 32
_STR_HOLD       = 2      # 結果・変化のフレームを保持する枚数 (速度 ×0.5 でも見えるように)

_SC_CMP   = "yellow"     # 比較中
_SC_EQ    = "#44cc44"    # 一致
_SC_NE    = "#ff4444"    # 不一致
_SC_FOUND = "#ff4444"    # 発見 (探索成功の慣例色)
_SC_SET   = "#66ddff"    # 表に書き込んだ値 / 比較せずに一致とわかっている部分
_SC_LOOK  = "#ff9900"    # 表を参照 / ずらし


def _sm(text, pattern, shift, label_t="T", label_p="P", t_hl=None, p_hl=None,
        compare=None, ghost=None, arrow=None, table=None, ptrs=None,
        p_dim_from=None, weight=3):
    """文字列照合の描画オブジェクト (type: string_match)

    text / pattern – 下段 (テキスト) / 上段 (パターン) の文字列。pattern=None で上段なし
    shift          – パターンの先頭を置く列 (テキストの添字)
    compare        – {"col": 列, "state": "cmp"|"eq"|"ne"} 上下のセルを結ぶ比較の注釈
    ghost          – パターンの「移動前 / 移動先」を破線で示す列
    arrow          – {"from": 列, "to": 列, "label": str} パターンのずらしを示す矢印
    table          – {"label", "values", "offset", "highlights"} パターンの上に並べる表 (KMP の PMT)
    ptrs           – [{"col", "label", "color"}] テキストの下に出すポインタ
    p_dim_from     – この添字以降のパターンのセルを薄く表示
    cols           – 全フレーム共通の列数 (_string_run が後から設定する)
    """
    return {
        "id": "sm", "type": "string_match",
        "text": list(text), "pattern": list(pattern) if pattern is not None else None,
        "shift": int(shift), "cols": 0,
        "text_label": label_t, "pattern_label": label_p,
        "text_hl": {str(k): v for k, v in (t_hl or {}).items()},
        "pattern_hl": {str(k): v for k, v in (p_hl or {}).items()},
        "compare": compare, "ghost": ghost, "arrow": arrow, "table": table,
        "pointers": list(ptrs or []), "pattern_dim_from": p_dim_from,
        "weight": weight,
    }


def _sm_table(label, values, offset, hl=None):
    return {"label": label, "values": list(values), "offset": int(offset),
            "highlights": {str(k): v for k, v in (hl or {}).items()}}


def _kv_table(id, label, keys, values, hl=None, row_labels=("文字 c", "表[c]"), weight=1):
    """キーと値の 2 段の表 (type: kv_table) – BMH のずらし表用"""
    return {
        "id": id, "type": "kv_table", "label": label,
        "keys": [str(k) for k in keys], "values": list(values),
        "highlights": {str(k): v for k, v in (hl or {}).items()},
        "row_labels": list(row_labels), "weight": weight,
    }


def _sptr(col, label, color="#dd55dd"):
    return {"col": int(col), "label": str(label), "color": color}


def _ch(c):
    """メッセージ用の 1 文字表示 (空白は ␣)"""
    return "␣" if c == " " else c


def _hold(frame, k=_STR_HOLD):
    for _ in range(k):
        yield frame


def _str_inputs(n, text, pattern):
    """テキストとパターンを決める。未指定・不正ならランダム (ACGT) に置き換える"""
    if not text:
        L  = max(4, min(int(n), STR_MAX_TEXT))
        pl = max(3, min(10, round(L / 4)))
        pat  = "".join("ACGT"[randint(0, 3)] for _ in range(pl))
        body = [("ACGT"[randint(0, 3)]) for _ in range(L - pl)]
        pos  = randint(0, len(body))
        text = "".join(body[:pos]) + pat + "".join(body[pos:])
        if not pattern:
            pattern = pat
    text = str(text)[:STR_MAX_TEXT]
    if not pattern or len(pattern) > len(text) or len(pattern) > STR_MAX_PATTERN:
        pl = max(1, min(len(text), STR_MAX_PATTERN, max(3, round(len(text) / 4))))
        s  = randint(0, len(text) - pl)
        pattern = text[s:s + pl]
    return text, str(pattern)


def _string_run(frames):
    """全フレームを作ってから、列数 cols を全フレーム共通の値にそろえて流す。
    (パターンが末尾からはみ出す位置まで進むことがあるため、表示がずれないよう最大値に合わせる)"""
    frames = list(frames)
    need = 1
    for fr in frames:
        for o in fr["objects"]:
            if o["type"] != "string_match":
                continue
            pm = len(o["pattern"]) if o["pattern"] else 0
            need = max(need, len(o["text"]), o["shift"] + pm)
            if o["ghost"] is not None:
                need = max(need, o["ghost"] + pm)
            for p in o["pointers"]:
                need = max(need, p["col"] + 1)
            if o["table"]:
                need = max(need, o["table"]["offset"] + len(o["table"]["values"]))
    for fr in frames:
        for o in fr["objects"]:
            if o["type"] == "string_match":
                o["cols"] = need
    yield from frames


def _found_frames(make, i, m):
    """発見時: 一致した範囲を点滅させてから完了フレーム"""
    t_hl = {i + k: _SC_FOUND for k in range(m)}
    p_hl = {k: _SC_FOUND for k in range(m)}
    for _ in range(2):
        yield make(t_hl={i + k: _SC_EQ for k in range(m)}, p_hl={k: _SC_EQ for k in range(m)})
        yield make(t_hl=t_hl, p_hl=p_hl)
    fr = make(t_hl=t_hl, p_hl=p_hl)
    fr["finished"] = True
    fr["found"] = True
    yield fr


# ---------------------------------------------------------------------------
# 力まかせ法 (素朴法)
# ---------------------------------------------------------------------------

def string_match_brute_force(n, text=None, pattern=None, **kwargs):
    T, P = _str_inputs(n, text, pattern)
    yield from _string_run(_bf_frames(T, P))


def _bf_frames(T, P):
    n, m = len(T), len(P)
    st = {"cmp": 0, "shift": 0}

    def F(i, msg, color="lightgreen", **kw):
        info = {"message": f"比較 {st['cmp']} 回 ・ ずらし {st['shift']} 回", "color": "cyan"}
        return _f([_sm(T, P, i, ptrs=[_sptr(i, "i")], **kw)],
                  [{"message": msg, "color": color}, info])

    yield F(0, "パターンをテキストの先頭 (i = 0) に合わせ、左から 1 文字ずつ比べる", color="white")
    for i in range(n - m + 1):
        for j in range(m):
            ok_t = {i + k: _SC_EQ for k in range(j)}
            ok_p = {k: _SC_EQ for k in range(j)}
            st["cmp"] += 1
            c, d = T[i + j], P[j]
            yield F(i, f"T[{i + j}] = '{_ch(c)}' と P[{j}] = '{_ch(d)}' を比較  (i = {i}, j = {j})",
                    t_hl={**ok_t, i + j: _SC_CMP}, p_hl={**ok_p, j: _SC_CMP},
                    compare={"col": i + j, "state": "cmp"})
            if c == d:
                yield from _hold(F(i, f"'{_ch(c)}' = '{_ch(d)}' 一致 → 次の文字へ (j = {j + 1})",
                                   t_hl={**ok_t, i + j: _SC_EQ}, p_hl={**ok_p, j: _SC_EQ},
                                   compare={"col": i + j, "state": "eq"}))
                continue
            yield from _hold(F(i, f"'{_ch(c)}' ≠ '{_ch(d)}' 不一致", color="orange",
                               t_hl={**ok_t, i + j: _SC_NE}, p_hl={**ok_p, j: _SC_NE},
                               compare={"col": i + j, "state": "ne"}))
            break
        else:
            # 全文字一致
            yield from _found_frames(
                lambda t_hl, p_hl: F(i, f"一致!  T[{i}..{i + m - 1}] = P   (i = {i} で発見)", color="red",
                                     t_hl=t_hl, p_hl=p_hl),
                i, m)
            return
        if i < n - m:
            st["shift"] += 1
            arw = {"from": i, "to": i + 1, "label": "+1"}
            yield from _hold(F(i, "パターンを 1 文字右へずらす (一致していた分もやり直し)", color="orange",
                               ghost=i + 1, arrow=arw))
            yield from _hold(F(i + 1, f"i = {i + 1}: P の先頭から比べ直す", color="orange",
                               ghost=i, arrow=arw))
    last = F(n - m, "テキストの末尾まで調べたが、パターンは見つからない", color="red")
    last["finished"] = True
    last["found"] = False
    yield last


# ---------------------------------------------------------------------------
# KMP 法 (Knuth-Morris-Pratt)
#   PMT[j] = P[0..j-1] の「接頭辞 = 接尾辞」となる最長の長さ (PMT[0] = -1)
#   不一致のときは j - PMT[j] 文字ずらし、j = PMT[j] から比較を続ける
# ---------------------------------------------------------------------------

def string_match_kmp(n, text=None, pattern=None, **kwargs):
    T, P = _str_inputs(n, text, pattern)
    yield from _string_run(_kmp_frames(T, P))


def _kmp_frames(T, P):
    n, m = len(T), len(P)
    st = {"build": 0, "cmp": 0, "shift": 0}
    pmt = [None] * m

    # ── 1. PMT の作成: P 自身を右にずらしながら、接頭辞と比べる ─────────
    def B(msg, color="lightgreen", shift=0, pat=True, t_hl=None, p_hl=None, tbl_hl=None,
          compare=None, ghost=None, arrow=None, dim=None):
        info = {"message": f"PMT の作成: 比較 {st['build']} 回", "color": "cyan"}
        obj = _sm(P, P if pat else None, shift, label_t="P", label_p="接頭辞",
                  t_hl=t_hl, p_hl=p_hl, compare=compare, ghost=ghost, arrow=arrow,
                  table=_sm_table("PMT", pmt, 0, tbl_hl), p_dim_from=dim)
        return _f([obj], [{"message": msg, "color": color}, info])

    yield B("まず PMT (部分一致表) を作る: PMT[j] = P[0..j-1] の接頭辞と接尾辞が一致する最長の長さ",
            color="white", pat=False)
    pmt[0] = -1
    yield from _hold(B("PMT[0] = -1 (定義: 先頭で不一致なら 1 文字ずらす)", pat=False, tbl_hl={0: _SC_SET}))
    if m > 1:
        pmt[1] = 0
        yield from _hold(B("PMT[1] = 0 (1 文字では、接頭辞 = 接尾辞 となる部分はない)",
                           pat=False, tbl_hl={1: _SC_SET}))
    i, j = 2, 0
    prev_shift = None
    while i < m:
        sh = i - 1 - j                       # P[j] が P[i-1] の真上に来るように置く
        ok_t = {sh + k: _SC_EQ for k in range(j)}
        ok_p = {k: _SC_EQ for k in range(j)}
        moved = prev_shift is not None and prev_shift != sh
        st["build"] += 1
        a, b = P[i - 1], P[j]
        yield B(f"PMT[{i}] を求める: P[{i - 1}] = '{_ch(a)}' と P[{j}] = '{_ch(b)}' を比較  (i = {i}, j = {j})",
                shift=sh, t_hl={**ok_t, i - 1: _SC_CMP}, p_hl={**ok_p, j: _SC_CMP},
                tbl_hl={i: _SC_CMP}, compare={"col": i - 1, "state": "cmp"}, dim=j + 1,
                ghost=prev_shift if moved else None,
                arrow={"from": prev_shift, "to": sh, "label": f"+{sh - prev_shift}"} if moved else None)
        prev_shift = sh
        if a == b:
            yield from _hold(B(f"'{_ch(a)}' = '{_ch(b)}' 一致 → 接頭辞が 1 文字のびる", shift=sh,
                               t_hl={**ok_t, i - 1: _SC_EQ}, p_hl={**ok_p, j: _SC_EQ},
                               tbl_hl={i: _SC_CMP}, compare={"col": i - 1, "state": "eq"}, dim=j + 1))
            j += 1
            pmt[i] = j
            yield from _hold(B(f"PMT[{i}] = j = {j}", shift=sh,
                               t_hl={sh + k: _SC_EQ for k in range(j)}, p_hl={k: _SC_EQ for k in range(j)},
                               tbl_hl={i: _SC_SET}, dim=j))
            i += 1
        elif j > 0:
            yield from _hold(B(f"'{_ch(a)}' ≠ '{_ch(b)}' 不一致 → j = PMT[{j}] で短い接頭辞に切り替える",
                               color="orange", shift=sh,
                               t_hl={**ok_t, i - 1: _SC_NE}, p_hl={**ok_p, j: _SC_NE},
                               tbl_hl={j: _SC_LOOK}, compare={"col": i - 1, "state": "ne"}, dim=j + 1))
            nj  = pmt[j]
            nsh = i - 1 - nj
            arw = {"from": sh, "to": nsh, "label": f"j: {j} → {nj}"}
            yield from _hold(B(f"j = PMT[{j}] = {nj}: 接頭辞を右へずらし、同じ P[{i - 1}] と比べ直す",
                               color="orange", shift=sh, t_hl=ok_t, p_hl=ok_p,
                               tbl_hl={j: _SC_LOOK}, dim=j + 1, ghost=nsh, arrow=arw))
            yield from _hold(B(f"j = {nj}", color="orange", shift=nsh,
                               t_hl={nsh + k: _SC_EQ for k in range(nj)}, p_hl={k: _SC_EQ for k in range(nj)},
                               tbl_hl={j: _SC_LOOK}, dim=nj + 1, ghost=sh, arrow=arw))
            prev_shift = nsh
            j = nj
        else:
            yield from _hold(B(f"'{_ch(a)}' ≠ '{_ch(b)}' 不一致 (j = 0)", color="orange", shift=sh,
                               t_hl={i - 1: _SC_NE}, p_hl={0: _SC_NE},
                               tbl_hl={i: _SC_CMP}, compare={"col": i - 1, "state": "ne"}, dim=1))
            pmt[i] = 0
            yield from _hold(B(f"PMT[{i}] = 0 (一致する接頭辞なし)", shift=sh, tbl_hl={i: _SC_SET}, dim=0))
            i += 1
    yield from _hold(B("PMT が完成: " + "  ".join(f"[{k}]={v}" for k, v in enumerate(pmt)),
                       color="white", pat=False))

    # ── 2. 照合: PMT はパターンと一緒に動く ──────────────────────────
    def F(i, j, msg, color="lightgreen", tbl_hl=None, **kw):
        info = {"message": f"照合: 比較 {st['cmp']} 回 ・ ずらし {st['shift']} 回"
                           f"   (PMT の作成: 比較 {st['build']} 回)", "color": "cyan"}
        obj = _sm(T, P, i, table=_sm_table("PMT", pmt, i, tbl_hl), ptrs=[_sptr(i, "i")], **kw)
        return _f([obj], [{"message": msg, "color": color}, info])

    i = j = 0
    yield from _hold(F(0, 0, "照合開始: パターンをテキストの先頭 (i = 0) に合わせる", color="white"))
    while i + j < n:
        ok_t = {i + k: _SC_EQ for k in range(j)}
        ok_p = {k: _SC_EQ for k in range(j)}
        st["cmp"] += 1
        c, d = T[i + j], P[j]
        yield F(i, j, f"T[{i + j}] = '{_ch(c)}' と P[{j}] = '{_ch(d)}' を比較  (i = {i}, j = {j})",
                t_hl={**ok_t, i + j: _SC_CMP}, p_hl={**ok_p, j: _SC_CMP},
                compare={"col": i + j, "state": "cmp"})
        if c == d:
            yield from _hold(F(i, j, f"'{_ch(c)}' = '{_ch(d)}' 一致 → 次の文字へ (j = {j + 1})",
                               t_hl={**ok_t, i + j: _SC_EQ}, p_hl={**ok_p, j: _SC_EQ},
                               compare={"col": i + j, "state": "eq"}))
            j += 1
            if j == m:
                yield from _found_frames(
                    lambda t_hl, p_hl: F(i, j, f"一致!  T[{i}..{i + m - 1}] = P   (i = {i} で発見)", color="red",
                                         t_hl=t_hl, p_hl=p_hl),
                    i, m)
                return
            continue
        yield from _hold(F(i, j, f"'{_ch(c)}' ≠ '{_ch(d)}' 不一致 → PMT[{j}] = {pmt[j]} を見る", color="orange",
                           t_hl={**ok_t, i + j: _SC_NE}, p_hl={**ok_p, j: _SC_NE},
                           tbl_hl={j: _SC_LOOK}, compare={"col": i + j, "state": "ne"}))
        s  = j - pmt[j]
        nj = pmt[j] if j > 0 else 0
        ni = i + s
        st["shift"] += 1
        arw = {"from": i, "to": ni, "label": f"+{s}"}
        yield from _hold(F(i, j, f"j - PMT[j] = {j} - ({pmt[j]}) = {s} 文字右へずらす", color="orange",
                           t_hl=ok_t, p_hl=ok_p, tbl_hl={j: _SC_LOOK}, ghost=ni, arrow=arw))
        if nj > 0:
            msg = f"先頭 {nj} 文字は一致しているとわかっている → 比べずに P[{nj}] から続ける (j = {nj})"
        else:
            msg = f"i = {ni}: P の先頭から比べる (j = 0)"
        yield from _hold(F(ni, nj, msg, color="orange",
                           t_hl={ni + k: _SC_SET for k in range(nj)}, p_hl={k: _SC_SET for k in range(nj)},
                           tbl_hl={j: _SC_LOOK}, ghost=i, arrow=arw))
        i, j = ni, nj
    last = F(i, j, f"テキストの末尾に達した (i + j = {i + j} = n) → パターンは見つからない", color="red")
    last["finished"] = True
    last["found"] = False
    yield last


# ---------------------------------------------------------------------------
# BMH 法 (Boyer-Moore-Horspool)
#   パターンの末尾から左へ比べ、不一致ならずらし表で大きくずらす。
#   ずらし表[c] = m - 1 - (P の中で c が最後に現れる位置)、P にない文字は m
#   不一致の位置 i (テキスト) / p (パターン) から  i += max(表[T[i]], m - p)
# ---------------------------------------------------------------------------

def string_match_bmh(n, text=None, pattern=None, **kwargs):
    T, P = _str_inputs(n, text, pattern)
    yield from _string_run(_bmh_frames(T, P))


def _bmh_frames(T, P):
    n, m = len(T), len(P)
    st = {"cmp": 0, "shift": 0}
    keys = []
    for c in P:
        if c not in keys:
            keys.append(c)
    vals = {c: None for c in keys}
    OTHER = len(keys)                      # 表の「その他」列の添字

    def kidx(c):
        return keys.index(c) if c in keys else OTHER

    def tbl(key=None, color=_SC_SET):
        ks = [_ch(c) for c in keys] + ["その他"]
        vs = [vals[c] for c in keys] + [m]
        return _kv_table("bmh_table", "ずらし表", ks, vs,
                         hl={key: color} if key is not None else None)

    def F(start, msg, color="lightgreen", key=None, key_color=_SC_SET, ptr=None, **kw):
        info = {"message": f"比較 {st['cmp']} 回 ・ ずらし {st['shift']} 回", "color": "cyan"}
        ptrs = [_sptr(ptr, "i")] if ptr is not None else []
        return _f([_sm(T, P, start, ptrs=ptrs, **kw), tbl(key, key_color)],
                  [{"message": msg, "color": color}, info])

    # ── 1. ずらし表の作成 ──────────────────────────────────────────
    yield F(0, "まずずらし表を作る: 表[c] = パターン末尾から、c が最後に現れる位置までの距離",
            color="white")
    yield from _hold(F(0, f"P にない文字はすべて m = {m} (表では「その他」)", key=OTHER))
    for k in range(m):
        c = P[k]
        before = vals[c]
        vals[c] = m - 1 - k
        note = f"  ({before} を上書き: 後ろに現れた位置が優先)" if before is not None else ""
        yield from _hold(F(0, f"P[{k}] = '{_ch(c)}' → 表['{_ch(c)}'] = m - 1 - {k} = {vals[c]}{note}",
                           key=kidx(c), p_hl={k: _SC_CMP}))

    # ── 2. 照合: 末尾から左へ ────────────────────────────────────────
    i = m - 1
    yield from _hold(F(0, f"照合開始: パターン末尾 P[{m - 1}] とテキスト T[{i}] から右→左へ比べる",
                       color="white", ptr=i))
    while i < n:
        p = m - 1
        start = i - p
        while p >= 0:
            ok_t = {start + k: _SC_EQ for k in range(p + 1, m)}
            ok_p = {k: _SC_EQ for k in range(p + 1, m)}
            st["cmp"] += 1
            c, d = T[i], P[p]
            yield F(start, f"T[{i}] = '{_ch(c)}' と P[{p}] = '{_ch(d)}' を比較  (i = {i}, p = {p})",
                    ptr=i, t_hl={**ok_t, i: _SC_CMP}, p_hl={**ok_p, p: _SC_CMP},
                    compare={"col": i, "state": "cmp"})
            if c != d:
                yield from _hold(F(start, f"'{_ch(c)}' ≠ '{_ch(d)}' 不一致", color="orange", ptr=i,
                                   t_hl={**ok_t, i: _SC_NE}, p_hl={**ok_p, p: _SC_NE},
                                   compare={"col": i, "state": "ne"}))
                break
            yield from _hold(F(start, f"'{_ch(c)}' = '{_ch(d)}' 一致 → 1 つ左へ (i--, p--)", ptr=i,
                               t_hl={**ok_t, i: _SC_EQ}, p_hl={**ok_p, p: _SC_EQ},
                               compare={"col": i, "state": "eq"}))
            i -= 1
            p -= 1
        if p < 0:
            s0 = i + 1
            yield from _found_frames(
                lambda t_hl, p_hl: F(s0, f"一致!  T[{s0}..{s0 + m - 1}] = P   (位置 {s0} で発見)", color="red",
                                     t_hl=t_hl, p_hl=p_hl),
                s0, m)
            return
        c = T[i]
        s1 = vals.get(c, m)
        s2 = m - p
        adv = max(s1, s2)
        key = kidx(c)
        src = f"表['{_ch(c)}']" if c in vals else f"表['{_ch(c)}'] (P にない文字)"
        ok_t = {start + k: _SC_EQ for k in range(p + 1, m)}
        ok_p = {k: _SC_EQ for k in range(p + 1, m)}
        yield from _hold(F(start, f"{src} = {s1},  m - p = {m} - {p} = {s2}  → i を max = {adv} 進める",
                           color="orange", key=key, key_color=_SC_LOOK, ptr=i,
                           t_hl={**ok_t, i: _SC_NE}, p_hl={**ok_p, p: _SC_NE}))
        ni     = i + adv
        nstart = ni - (m - 1)
        st["shift"] += 1
        arw = {"from": start, "to": nstart, "label": f"+{nstart - start}"}
        yield from _hold(F(start, f"パターンを {nstart - start} 文字右へずらす (i = {i} → {ni})",
                           color="orange", key=key, key_color=_SC_LOOK, ptr=i, ghost=nstart, arrow=arw))
        if ni < n:
            msg = f"i = {ni}: 新しい位置で、パターン末尾から比べる"
        else:
            msg = f"i = {ni} ≥ n = {n}: パターンがテキストの外に出たので終了"
        yield from _hold(F(nstart, msg, color="orange", key=key, key_color=_SC_LOOK, ptr=ni,
                           ghost=start, arrow=arw))
        i = ni
    last = F(i - (m - 1), "テキストの末尾まで調べたが、パターンは見つからない", color="red", ptr=i)
    last["finished"] = True
    last["found"] = False
    yield last


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
# ノームソート (1テープ) – ヘッドが ±1 しか動けない 1 本のテープで整列
# ---------------------------------------------------------------------------

def gnome_sort_tape(n, data_condition=0, data=None):
    """ノームソート (1テープ)

    ノームソートは「左隣と比べ、順序が正しければ 1 コマ右へ、
    逆順なら交換して 1 コマ左へ戻る」だけのアルゴリズム。
    ヘッドの移動が常に ±1 コマなので、巻き戻しのできない
    3 テープ方式と違い **1 本のテープだけ** で実行できる。
    """
    MAX_N = 32                                   # テープ表示・O(N^2) の都合で上限
    data  = _make_sort_data(n, data_condition, data)
    N     = min(len(data), MAX_N)
    tape  = data[:N]

    CMP_C  = "yellow"        # 比較中
    OK_C   = "#44aa44"       # 順序OK / 確定
    BAD_C  = "#ff6600"       # 逆順 (交換前)
    NEW_C  = "#66ddff"       # 交換直後

    title = f"ノームソート (1テープ)  N = {N}"
    if len(data) > MAX_N:
        title += f"   ※ {len(data)} 個中 先頭 {N} 個"

    cnt = {"cmp": 0, "swp": 0}

    def frame(head, sorted_upto, msg, color="lightgreen",
              hl=None, swap=None, finished=False):
        texts = [
            {"message": title, "color": "white"},
            {"message": f"ヘッド位置 pos = {head}    比較 {cnt['cmp']} 回 / "
                        f"交換 {cnt['swp']} 回", "color": "cyan"},
            {"message": msg, "color": color},
        ]
        return _f([_tape("tape", tape, head, "テープ", "#4472C4",
                         hl=hl, sorted_upto=sorted_upto, swap=swap,
                         reserve_arc=True, head_label="pos")],
                  texts, finished=finished)

    # ── 初期データ → テープへ ──
    yield _f([_c("init", tape, "初期データ")],
             [{"message": title, "color": "white"},
              {"message": "1 本のテープに書き込みます", "color": "cyan"},
              {"message": "ヘッドは 1 コマずつ左右にしか動けません",
               "color": "lightgreen"}])

    pos = 0
    yield frame(0, 0, "テープの先頭にヘッドを置きます  (pos = 0)", "cyan")

    while pos < N:
        # 先頭では左隣が無いので比較せず前進
        if pos == 0:
            yield frame(0, 0, "pos = 0: 左隣が無いので比較せずに前進", "lightgreen",
                        hl={0: OK_C})
            pos = 1
            if pos < N:
                yield frame(pos, pos, f"ヘッドを 1 コマ右へ  →  pos = {pos}",
                            "lightgreen")
            continue

        a, b = tape[pos - 1], tape[pos]
        cnt["cmp"] += 1
        yield frame(pos, pos,
                    f"比較: A[{pos - 1}] = {a}   と   A[{pos}] = {b}", "yellow",
                    hl={pos - 1: CMP_C, pos: CMP_C})

        if a <= b:
            yield frame(pos, pos, f"{a} ≦ {b}  順序OK  →  ヘッドを右へ",
                        "lightgreen", hl={pos - 1: OK_C, pos: OK_C})
            pos += 1
            if pos < N:
                yield frame(pos, pos, f"ヘッドを 1 コマ右へ  →  pos = {pos}",
                            "lightgreen")
        else:
            # 交換前 (逆順): 交換アークを付けて「これから入れ替える」ことを示す
            yield frame(pos, pos, f"{a} > {b}  逆順  →  2 つを交換する", "#ff8844",
                        hl={pos - 1: BAD_C, pos: BAD_C},
                        swap={"a": pos - 1, "b": pos, "phase": "before"})
            tape[pos - 1], tape[pos] = tape[pos], tape[pos - 1]
            cnt["swp"] += 1
            # 交換後: 値が入れ替わったことを別色で示す
            yield frame(pos, pos - 1,
                        f"交換完了: A[{pos - 1}] = {b}   A[{pos}] = {a}", "#66ddff",
                        hl={pos - 1: NEW_C, pos: NEW_C},
                        swap={"a": pos - 1, "b": pos, "phase": "after"})
            pos -= 1
            yield frame(pos, pos, f"ヘッドを 1 コマ左へ戻る  →  pos = {pos}",
                        "#ff8844")

    yield frame(N, N, "ヘッドがテープの右端を越えました  →  整列完了", "#FFD700",
                hl={i: OK_C for i in range(N)})
    yield _f([_c("done", tape, "ソート結果",
                 hl={i: OK_C for i in range(N)})],
             [{"message": title, "color": "white"},
              {"message": f"比較 {cnt['cmp']} 回 / 交換 {cnt['swp']} 回",
               "color": "cyan"},
              {"message": "ソート完了!", "color": "#FFD700"}],
             finished=True)


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
    # ── 文字列照合 ──
    ("文字列照合: 力まかせ法",        string_match_brute_force, {"type": "string"}),
    ("文字列照合: KMP 法",           string_match_kmp,         {"type": "string"}),
    ("文字列照合: BMH 法",           string_match_bmh,         {"type": "string"}),
    # ── ソート ──
    ("マージソート (反復)",           merge_sort_iter,         {"type": "sort"}),
    ("マージソート (再帰)",           merge_sort_rec,          {"type": "sort"}),
    ("マージソート (3テープ)",        merge_sort_tape,         {"type": "sort"}),
    ("ヒープソート",                 heap_sort,               {"type": "sort"}),
    ("バケツソート",                 bucket_sort,             {"type": "sort"}),
    ("基数ソート (LSD)",            radix_sort,              {"type": "sort"}),
    ("ノームソート (1テープ)",        gnome_sort_tape,         {"type": "sort"}),
    # ── その他 ──
    ("階乗 (反復)",                 factorial_iter,          {"type": "misc"}),
    ("階乗 (再帰)",                 factorial_rec,           {"type": "misc"}),
    ("フィボナッチ (反復)",           fibonacci_iter,          {"type": "misc"}),
    ("フィボナッチ (再帰)",           fibonacci_rec,           {"type": "misc"}),
    ("フィボナッチ (メモ化)",         fibonacci_memo,          {"type": "misc"}),
]

DataSizeList = [8, 16, 32, 64, 100, 128, 200, 256, 512]
