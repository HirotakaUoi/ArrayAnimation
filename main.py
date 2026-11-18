"""
main.py – FastAPI + WebSocket バックエンド (ArrayAnimation)
起動: uvicorn main:app --reload --port 8004
"""

import asyncio
import uuid
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

from algorithms import AlgorithmList, DataSizeList

app = FastAPI(title="ArrayAnimation API")

# セッション管理: { session_id: { generator, speed, paused, stopped, ... } }
sessions: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@app.get("/api/algorithms")
def get_algorithms():
    return [
        {"id": i, "name": name, "meta": meta}
        for i, (name, fn, meta) in enumerate(AlgorithmList)
    ]


@app.get("/api/datasizes")
def get_datasizes():
    return DataSizeList


class StartParams(BaseModel):
    algorithm_id:   int
    num_items:      int   = 16
    speed:          float = 0.10      # 秒/フレーム
    target:         Optional[int] = None        # 探索対象 (search 用)
    data:           Optional[list[int]] = None  # 初期データ (search / sort 共用)
    data_condition: int   = 0         # 0=ランダム 1=昇順 2=降順 3=ほぼ昇順 (sort 用)
    text:           Optional[str] = None        # テキスト (string 用)
    pattern:        Optional[str] = None        # パターン (string 用)


def _make_generator(params: "StartParams"):
    """algorithm_id と各パラメータから、アルゴリズムのジェネレータを作る。

    /api/start と /api/preview で同じロジックを使う。
    同じ data を渡せば最初のフレームは同一になるため、プレビュー（最初の
    フレーム）と実行開始後の最初のフレームでデータ構造の位置がそろう。
    """
    algo_name, algo_fn, algo_meta = AlgorithmList[params.algorithm_id]
    algo_type = algo_meta.get("type", "search")

    if algo_type == "misc":
        # misc: num_items だけ渡す (factorial/fibonacci は内部で cap)
        generator = algo_fn(params.num_items)
    elif algo_type == "string":
        # string: テキストとパターンを渡す (未指定・不正ならアルゴリズム側でランダム生成)
        generator = algo_fn(params.num_items, text=params.text, pattern=params.pattern)
    elif algo_type == "sort":
        # sort: data_condition と data を渡す (target は不要)
        generator = algo_fn(
            params.num_items,
            data_condition=params.data_condition,
            data=params.data,
        )
    else:
        # search: target と data を渡す
        generator = algo_fn(params.num_items, params.target, params.data)

    return algo_name, generator


# アルゴリズムごとの「テキストの最大行数」のキャッシュ。
# アニメーション中はフレームによってテキストの行数が変わる（例: マージソートは
# 1 行 ↔ 2 行、ヒープソートは 2 行 ↔ 3 行）。そのたびに上部のテキスト帯の高さが
# 変わると、下のデータ構造が上下に動いてしまう（開始直後に「微妙にずれて戻る」）。
# そこで全フレームで最大行数ぶんの帯を確保し、行数が少ないフレームでも帯の高さを
# 一定に保つ。行数は N やデータにほぼ依存しない構造的な値なので、小さい N で一度
# だけ数えてキャッシュする。
_max_lines_cache: dict[int, int] = {}


def _calc_max_text_lines(algorithm_id: int) -> int:
    algo_name, algo_fn, algo_meta = AlgorithmList[algorithm_id]
    algo_type = algo_meta.get("type", "search")

    # 分岐で行数が変わる場合に備え、代表的な入力をいくつか試して最大を取る
    if algo_type == "sort":
        trials = [{"data_condition": c} for c in (0, 1, 2, 3)]
    elif algo_type == "search":
        # 見つかる場合と見つからない場合の両方（not found 分岐の行も数える）
        trials = [{}, {"target": 10 ** 9}]
    else:
        trials = [{}]

    mx = 1
    for extra in trials:
        try:
            p = StartParams(algorithm_id=algorithm_id, num_items=16, **extra)
            _, gen = _make_generator(p)
            for k, fr in enumerate(gen):
                mx = max(mx, len(fr.get("texts", [])))
                if k > 8000:   # 念のための打ち切り（O(N^2) のノームソート対策）
                    break
            gen.close()
        except Exception:
            pass
    return mx


def _reserve_lines(algorithm_id: int) -> int:
    if algorithm_id not in _max_lines_cache:
        _max_lines_cache[algorithm_id] = _calc_max_text_lines(algorithm_id)
    return _max_lines_cache[algorithm_id]


@app.post("/api/preview")
def preview_frame(params: StartParams):
    """実行を始めずに、アルゴリズムの最初のフレームだけを返す。

    クライアントはこのフレームをそのままプレビューに描画する。/api/start に
    同じ data を渡せば、開始後の最初のフレームと完全に同じ枠（テキスト帯の
    高さ・オブジェクトの数と weight）になるので、開始してもデータ構造の位置が
    ずれない。misc 型（階乗・フィボナッチ）はプレビューしない（空白表示）。
    """
    if params.algorithm_id not in range(len(AlgorithmList)):
        return JSONResponse({"error": "invalid algorithm_id"}, status_code=400)

    _, generator = _make_generator(params)
    try:
        frame = next(generator)
    except StopIteration:
        frame = {"objects": [], "texts": [], "finished": False, "found": None,
                 "text_position": "top"}
    finally:
        generator.close()
    # テキスト帯の高さを全フレームで一定にするための予約行数（下記 send_frames と同じ）
    frame["reserve_lines"] = _reserve_lines(params.algorithm_id)
    return {"frame": frame}


@app.post("/api/start")
def start_session(params: StartParams):
    if params.algorithm_id not in range(len(AlgorithmList)):
        return JSONResponse({"error": "invalid algorithm_id"}, status_code=400)

    algo_name, generator = _make_generator(params)

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "generator": generator,
        "speed":     params.speed,
        "paused":    False,
        "stopped":   False,
        "algo_name": algo_name,
        "num_items": params.num_items,
        "reserve_lines": _reserve_lines(params.algorithm_id),
    }
    return {
        "session_id": session_id,
        "algo_name":  algo_name,
        "num_items":  params.num_items,
    }


# ---------------------------------------------------------------------------
# WebSocket  /ws/{session_id}
# クライアントからの制御メッセージ:
#   {"action": "set_speed", "speed": 0.05}
#   {"action": "pause"}
#   {"action": "resume"}
#   {"action": "stop"}
# ---------------------------------------------------------------------------

@app.websocket("/ws/{session_id}")
async def ws_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()

    if session_id not in sessions:
        await ws.send_json({"error": "session not found"})
        await ws.close()
        return

    session = sessions[session_id]

    async def send_frames():
        try:
            for frame in session["generator"]:
                if session["stopped"]:
                    break
                while session["paused"] and not session["stopped"]:
                    await asyncio.sleep(0.05)
                if session["stopped"]:
                    break
                # テキスト帯の高さを全フレームで一定にする（行数が変わっても
                # データ構造が上下に動かないように）予約行数を各フレームに付ける
                frame["reserve_lines"] = session["reserve_lines"]
                await ws.send_json(frame)
                await asyncio.sleep(session["speed"])
        except Exception:
            pass

    async def recv_controls():
        try:
            while True:
                msg = await ws.receive_json()
                action = msg.get("action", "")
                if action == "set_speed":
                    session["speed"] = float(msg.get("speed", 0.08))
                elif action == "pause":
                    session["paused"] = True
                elif action == "resume":
                    session["paused"] = False
                elif action == "stop":
                    session["stopped"] = True
                    break
        except WebSocketDisconnect:
            session["stopped"] = True
        except Exception:
            session["stopped"] = True

    sender   = asyncio.create_task(send_frames())
    receiver = asyncio.create_task(recv_controls())

    done, pending = await asyncio.wait(
        [sender, receiver],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for t in pending:
        t.cancel()

    sessions.pop(session_id, None)
    try:
        await ws.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 静的ファイル
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    # index.html は毎回サーバーに更新の有無を確認させる。
    # (キャッシュ指定が無いとブラウザが古い index.html を使い続け、?v=N を上げた新しい JS が読み込まれない)
    return FileResponse(BASE_DIR / "static" / "index.html",
                        headers={"Cache-Control": "no-cache"})

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
