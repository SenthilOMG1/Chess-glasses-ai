"""Chess glasses: watch a real board through the glasses, say the best reply.

    python -m chess_glasses run --color white
    python -m chess_glasses snap            # save a screenshot to pick a crop
    python -m chess_glasses read FRAME.png  # test board reading on one image
"""

import argparse
import shutil
import sys
import time

import chess
import chess.engine
from PIL import Image

from .capture import ScreenCapture, difference
from .speech import describe, say
from .tracker import match_move
from .vision import BoardReader

# Frames closer than this (mean pixel diff) count as "the camera is holding still".
STILL = 6.0
# Skip a reading if the frame barely changed since the last one we read.
SAME_AS_LAST = 4.0


def parse_crop(text):
    if not text:
        return None
    parts = [int(p) for p in text.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("crop must be left,top,width,height")
    return tuple(parts)


def best_move(engine, board, think):
    result = engine.play(board, chess.engine.Limit(time=think))
    return result.move


def run(args):
    color = chess.WHITE if args.color == "white" else chess.BLACK
    board = chess.Board(args.fen) if args.fen else chess.Board()
    camera = ScreenCapture(parse_crop(args.crop), shell=args.shell)
    reader = BoardReader(color)
    engine = chess.engine.SimpleEngine.popen_uci(shutil.which("stockfish") or "stockfish")

    print(f"Playing {args.color}. Watching the board. Ctrl+C to stop.")
    if board.turn == color:
        move = best_move(engine, board, args.think)
        say(describe(board, move))

    previous = None
    last_read = None
    still_since = None
    try:
        while not board.is_game_over():
            frame = camera.grab()
            now = time.monotonic()

            if previous is not None and difference(frame, previous) < STILL:
                still_since = still_since or now
            else:
                still_since = None
            previous = frame

            steady = still_since is not None and now - still_since >= args.settle
            changed = last_read is None or difference(frame, last_read) >= SAME_AS_LAST
            if not (steady and changed):
                time.sleep(args.interval)
                continue

            last_read = frame
            visible, reading = reader.read(frame)
            if not visible:
                print("Board not clearly visible, waiting.")
                continue

            move = match_move(board, reading)
            if move is None:
                continue

            mover = "You" if board.turn == color else "Opponent"
            print(f"{mover} played {board.san(move)}")
            board.push(move)

            if board.turn == color and not board.is_game_over():
                reply = best_move(engine, board, args.think)
                say(describe(board, reply))
    except KeyboardInterrupt:
        pass
    finally:
        engine.quit()

    print(f"Final position: {board.fen()}")
    if board.is_game_over():
        print(f"Game over: {board.result()}")


def snap(args):
    camera = ScreenCapture(parse_crop(args.crop), shell=args.shell)
    camera.grab().save(args.out)
    print(f"Saved {args.out}")


def read(args):
    reader = BoardReader(chess.WHITE if args.color == "white" else chess.BLACK)
    visible, reading = reader.read(Image.open(args.image))
    board = chess.Board(None)
    for square, symbol in reading.items():
        board.set_piece_at(square, chess.Piece.from_symbol(symbol))
    print(f"Board visible: {visible}")
    print(board.unicode(invert_color=True, empty_square="·"))
    print(board.board_fen())


def main():
    parser = argparse.ArgumentParser(prog="chess_glasses")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--crop", help="left,top,width,height of the video on screen")
        p.add_argument("--shell", choices=["rish", "adb"], default="rish",
                       help="how to take screenshots (Shizuku rish or adb)")

    p = sub.add_parser("run", help="watch the board and call out moves")
    common(p)
    p.add_argument("--color", choices=["white", "black"], required=True)
    p.add_argument("--fen", help="start from this position instead of the opening")
    p.add_argument("--think", type=float, default=1.0, help="Stockfish seconds per move")
    p.add_argument("--settle", type=float, default=1.5,
                   help="seconds the view must hold still before reading the board")
    p.add_argument("--interval", type=float, default=0.5, help="seconds between frames")
    p.set_defaults(func=run)

    p = sub.add_parser("snap", help="save one screenshot")
    common(p)
    p.add_argument("--out", default="/sdcard/Download/chess_glasses_snap.png")
    p.set_defaults(func=snap)

    p = sub.add_parser("read", help="read the board from one image")
    p.add_argument("image")
    p.add_argument("--color", choices=["white", "black"], default="white")
    p.set_defaults(func=read)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
