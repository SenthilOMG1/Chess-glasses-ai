"""Read the chess position from a camera frame with Claude."""

import base64
import io
import json

import anthropic
import chess

MODEL = "claude-opus-5-5"

PROMPT = """This is a frame from a head-mounted camera looking at a physical chess board.
Read every square of the board.

Return the position as 8 ranks, from rank 8 down to rank 1. Each rank is exactly 8
characters, from the a-file to the h-file: K Q R B N P for white pieces, k q r b n p
for black pieces, and . for an empty square.

{orientation}
If you can't see the whole board clearly (blur, hands in the way, board out of frame),
set board_visible to false and fill the ranks with your best guess."""

SCHEMA = {
    "type": "object",
    "properties": {
        "board_visible": {"type": "boolean"},
        "ranks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["board_visible", "ranks"],
    "additionalProperties": False,
}


class BoardReader:
    def __init__(self, viewer_color=chess.WHITE):
        self.client = anthropic.Anthropic()
        side = "White" if viewer_color == chess.WHITE else "Black"
        self.prompt = PROMPT.format(
            orientation=f"The camera wearer is playing {side}, so {side}'s pieces "
            "start on the side of the board closest to the camera."
        )

    def read(self, image):
        """Return (board_visible, {square: piece symbol}) for a PIL image."""
        buf = io.BytesIO()
        image.convert("RGB").save(buf, format="JPEG", quality=85)
        data = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

        response = self.client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={
                "effort": "low",
                "format": {"type": "json_schema", "schema": SCHEMA},
            },
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {
                        "type": "base64", "media_type": "image/jpeg", "data": data}},
                    {"type": "text", "text": self.prompt},
                ],
            }],
        )
        if response.stop_reason == "refusal":
            return False, {}

        text = next(b.text for b in response.content if b.type == "text")
        result = json.loads(text)
        return result["board_visible"], parse_ranks(result["ranks"])


def parse_ranks(ranks):
    """Turn 8 rank strings (rank 8 first) into {square: piece symbol}."""
    pieces = {}
    for i, rank in enumerate(ranks[:8]):
        rank_index = 7 - i
        for file_index, ch in enumerate(rank.strip()[:8]):
            if ch != "." and ch.lower() in "kqrbnp":
                pieces[chess.square(file_index, rank_index)] = ch
    return pieces
