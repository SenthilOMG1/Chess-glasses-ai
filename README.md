# Chess-glasses-ai

Play over-the-board chess with smart glasses as your second pair of eyes.
The glasses stream what you see to your phone through a WhatsApp video call.
The phone reads the board, works out the moves, and speaks the best reply
into your ear.

Everything runs on an Android phone in Termux. No computer is needed.

## How it works

1. **Capture.** A WhatsApp video call started from the glasses shows their
   camera on the phone screen. Screenshots are taken through Shizuku (`rish`),
   or through `adb` if you prefer.
2. **Wait for a steady view.** Frames are compared locally, and the board is
   only read once your head has held still for a moment and the view has
   changed since the last read. That keeps API calls (and cost) down.
3. **Read the board.** Claude looks at the frame and reports what's on every
   square.
4. **Match a legal move.** The program knows the current position, so it
   checks the reading against every position one legal move away and picks
   the closest. A couple of misread squares won't throw it off.
5. **Reply.** Stockfish finds the best move, and Android text-to-speech says
   it ("knight g 1 to f 3"), which plays through the glasses' speakers.

## Setup (Termux)

```sh
pkg install python python-pillow stockfish termux-api rust
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...        # from console.anthropic.com
```

You also need:

- **Shizuku** running, with `rish` set up in Termux, for screenshots.
- The **Termux:API** app, for `termux-tts-speak`. Without it, moves are only
  printed.

## Use

Start a WhatsApp video call from the glasses and switch the camera to the
glasses. Make the glasses' view the big picture on screen, not the small
preview.

```sh
# 1. Save a screenshot, then find the video area on it
python -m chess_glasses snap

# 2. Check that the board reads correctly
python -m chess_glasses read /sdcard/Download/chess_glasses_snap.png

# 3. Play (crop is left,top,width,height of the video on screen)
python -m chess_glasses run --color white --crop 0,300,1260,1700
```

Useful options for `run`:

| Option | Default | What it does |
| --- | --- | --- |
| `--think` | 1.0 | Seconds Stockfish spends on each move |
| `--settle` | 1.5 | Seconds the view must hold still before a read |
| `--fen` | start position | Start from a position that's already in progress |
| `--shell adb` | `rish` | Take screenshots through adb instead of Shizuku |

## Fair play

Use this for practice, analysis, or a fun demo with friends who know about
it. Using engine help in a rated or tournament game is cheating.
