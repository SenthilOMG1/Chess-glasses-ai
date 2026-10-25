"""Say moves out loud so they come through the glasses' speakers."""

import re
import shutil
import subprocess

import chess

PIECE_NAMES = {
    chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
    chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king",
}


def describe(board, move):
    """Plain-English move, e.g. 'knight g1 to f3, check'."""
    if board.is_castling(move):
        text = "castle kingside" if chess.square_file(move.to_square) == 6 else "castle queenside"
    else:
        piece = PIECE_NAMES[board.piece_type_at(move.from_square)]
        frm = chess.square_name(move.from_square)
        to = chess.square_name(move.to_square)
        verb = "takes" if board.is_capture(move) else "to"
        text = f"{piece} {frm} {verb} {to}"
        if move.promotion:
            text += f", promote to {PIECE_NAMES[move.promotion]}"
    board.push(move)
    if board.is_checkmate():
        text += ", checkmate"
    elif board.is_check():
        text += ", check"
    board.pop()
    # Spell squares out so TTS says "e 4" rather than a word.
    return re.sub(r"\b([a-h])([1-8])\b", r"\1 \2", text)


def say(text):
    print(f"[say] {text}")
    if shutil.which("termux-tts-speak"):
        try:
            subprocess.run(["termux-tts-speak", text], timeout=20)
        except subprocess.TimeoutExpired:
            print("[say] termux-tts-speak timed out. Is the Termux:API app installed?")
