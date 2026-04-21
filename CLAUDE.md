# ArrayAnimation – 開発ガイド

## アーキテクチャ概要

```
[Browser]  ←─ WebSocket ─→  [FastAPI / main.py]  ←─ import ─→  [algorithms.py]
  app.js                       /api/start                          generator関数群
  array_canvas.js              /ws/{session_id}
```

- `algorithms.py` の各関数は **Pythonジェネレータ**（`yield` でフレームを1つずつ出力）
- `main.py` がジェネレータを回しながら WebSocket でフレームをストリーミング
- ブラウザ側の `array_canvas.js` が Canvas にフレームを描画

---

## フレーム形式

```python
{
  "objects":       [...],          # 描画オブジェクトのリスト
  "texts":         [...],          # テキストオーバーレイ
  "finished":      bool,           # アニメーション完了フラグ
  "found":         int | null,     # 探索結果インデックス (search 用)
  "text_position": "top" | "bottom"  # テキスト描画位置（デフォルト "top"）
}
```

`text_position="bottom"` は、上部にオブジェクトが密集していてテキストと重なる場合に使う（例: radix_sort の Digit Queues）。

テキスト要素:
```python
{"message": "説明文", "color": "white" | "red" | "lightgreen" | "cyan" | ...}
```

---

## オブジェクト種別とヘルパー関数

### `array1d_cells` — 正方形セル配列（主力）
```python
_c(id, values, label="", hl=None, fills=None, ptr=None,
   watchman=None, target=None, weight=1)
```
- `hl`: `{インデックス: "色"}` で個別ハイライト
- `target`: 探索ターゲット値（一致セルを赤枠表示）
- `weight`: 縦方向スペース比率

### `array1d` — 棒グラフ（後方互換）
```python
_a(id, values, label="", hl=None, ..., log_scale=False)
```
- `log_scale=True`: 値の差が大きい場合に対数スケール表示

### `heap_tree` — ヒープ二分木
```python
_heap_tree(id, values, heap_size, hl=None, label="", weight=2.5, confirmed_min=0)
```
- **`confirmed_min`**: このインデックス未満のノードを「ゴースト」（極暗色）表示する
  - ヒープ構築中の「まだ処理していないノード」を視覚的に隠す仕組み
  - 葉ノード開始位置 = `N // 2`、そこから sift_down のたびに 1 減らす
  - 構築完了後は `confirmed_min=0`（全ノード通常表示）

### `bucket_rows` — バケツ行 / Digit Queues
```python
_bucket_rows(id, buckets, bucket_colors, label="",
             bucket_labels=None, active_bucket=None, weight=3)
```
- `active_bucket`: 現在アクティブなバケツインデックス（強調表示）
- 複数オブジェクトと組み合わせる場合は `weight` で縦比率を調整

### `tape` — 無端テープ（マージソート3テープ用）
```python
_tape(id, cells, head, label="", color="#4472C4", weight=1)
```

### `fib_tree` — フィボナッチ再帰木 / スライディングウィンドウ木
再帰木と反復型（スライディングウィンドウ）の両方で使用。
ノード辞書を直接構築する（専用ヘルパーなし）:
```python
{
  "n": k, "value": v, "color": "#44aa44",
  "left": {...} | None, "right": {...} | None,
  "memo": bool
}
```

### `staircase` — 階段状テキスト（階乗再帰用）
```python
_staircase(id, rows, label="")
# rows: [{"depth": int, "text": str, "color": str}, ...]
```

---

## `weight` の使い方

複数オブジェクトを同一フレームに入れるとき、縦スペースを比率で分配する:
```python
# データ(1) + ヒープ木(2.5) → 木が縦の 2.5/3.5 を占有
[
  _c("data", ..., weight=1),
  _heap_tree("tree", ..., weight=2.5),
]
```
単独オブジェクトの場合は `weight` は実質無効。

---

## アルゴリズム追加手順

1. `algorithms.py` に **ジェネレータ関数**を実装
   - シグネチャ: `def my_algo(n, **kwargs)` (sort/misc) または `def my_algo(n, target=None, data=None)` (search)
   - 最低 1 フレーム yield すること（`finished=True` のフレームで終了）

2. `AlgorithmList` に登録（ファイル末尾）:
   ```python
   ("表示名", my_algo, {"type": "search" | "sort" | "misc"}),
   ```
   - `type` によってフロントエンドの UI が変わる:
     - `search`: target 入力を表示、data_condition を非表示
     - `sort`: target を非表示、data_condition を表示
     - `misc`: 両方非表示

3. `_make_sort_data()` を使うと `data_condition`（ランダム/昇順/降順/ほぼ昇順）に対応できる

4. **1操作 = 1 `yield`** を原則とする。複数セルをまとめて1フレームにすると動きが見えなくなる。

---

## アニメーション設計パターン

### ハイライト配色の慣例
| 状況 | 色 |
|---|---|
| 比較中 / 注目中 | `"yellow"` |
| 確定済み（ソート完了） | `"#44aa44"` |
| 発見（探索成功） | `"#ff4444"` / `"red"` |
| コピー先 | `"#88ff88"` |
| バケツ対応色 | `COLORS` リスト参照 |

### 進行中テキストの構造
```python
base = [{"message": f"N = {N}", "color": "white"}]
# ... 各ステップで base + [{"message": "ステップ説明", "color": "lightgreen"}]
```

### 完了フレームの書き方
```python
yield _f([...objects...], base + [...], finished=True)
```
`found=True` / `found=False` は探索アルゴリズムのみ使用。

---

## 開発サーバー

```bash
# 起動（既存プロセスを先に終了）
lsof -ti :8005 | xargs kill -9 2>/dev/null; uvicorn main:app --port 8005
```

- ポート: **8005**
- `.claude/launch.json` に設定済み（`preview_start` ツール用）
- 静的ファイルのキャッシュ対策: `index.html` の `?v=N` クエリを更新する

---

## ファイル構成

```
ArrayAnimation/
├── main.py              FastAPI + WebSocket サーバー
├── algorithms.py        全アルゴリズム（ジェネレータ）+ AlgorithmList
├── static/
│   ├── index.html       UI シェル
│   ├── css/style.css
│   └── js/
│       ├── app.js       マルチパネル UI（パネル管理・API通信）
│       ├── array_canvas.js  Canvas 描画エンジン（ArrayCanvas クラス）
│       └── ws_client.js     WebSocket クライアント
└── .claude/
    └── launch.json      preview_start 用サーバー設定
```

---

## 現在実装済みのアルゴリズム（16本）

| カテゴリ | アルゴリズム |
|---|---|
| 探索 | 線形探索(基本), 線形探索(番兵法), 線形探索(整列済み), 二分探索(反復), 二分探索(再帰) |
| ソート | マージソート(反復), マージソート(再帰), マージソート(3テープ), ヒープソート, バケツソート, 基数ソート(LSD) |
| その他 | 階乗(反復), 階乗(再帰), フィボナッチ(反復), フィボナッチ(再帰), フィボナッチ(メモ化) |
