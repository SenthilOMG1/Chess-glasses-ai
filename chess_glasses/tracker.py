"""Turn noisy board readings into legal moves.

The vision model gets a square wrong now and then, so instead of trusting
its reading outright, we compare it against every position one legal move
away and keep the move that fits best.
"""

import chess

# How many more squares "no move" must get wrong than the best move before
# we believe a move was played.
MIN_MARGIN = 2


def mismatch(board, reading):
    """Count squares where the board and the reading disagree."""
    count = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        actual = piece.symbol() if piece else None
        if actual != reading.get(square):
            count += 1
    return count


def match_move(board, reading):
    """Return the legal move the reading shows, or None if nothing moved."""
    no_move = mismatch(board, reading)
    scored = []
    for move in board.legal_moves:
        board.push(move)
        scored.append((mismatch(board, reading), move))
        board.pop()
    if not scored:
        return None

    scored.sort(key=lambda s: s[0])
    best_score, best_move = scored[0]
    if no_move - best_score < MIN_MARGIN:
        return None
    # Two moves fitting equally well means the reading is ambiguous.
    if len(scored) > 1 and scored[1][0] == best_score:
        return None
    return best_move
