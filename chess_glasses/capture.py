"""Grab frames from the phone screen (the WhatsApp call showing the glasses' view)."""

import subprocess

from PIL import Image, ImageChops, ImageStat

# rish mangles binary stdout, so screenshots go through a file both sides can reach.
FRAME_PATH = "/sdcard/Download/.chess_glasses_frame.png"


class ScreenCapture:
    def __init__(self, crop=None, shell="rish"):
        """crop is (left, top, width, height) in screen pixels, or None for full screen."""
        self.crop = crop
        if shell == "rish":
            self.cmd = ["rish", "-c", f"screencap -p {FRAME_PATH}"]
        else:
            self.cmd = ["adb", "shell", "screencap", "-p", FRAME_PATH]

    def grab(self):
        subprocess.run(self.cmd, capture_output=True, timeout=15, check=True)
        with Image.open(FRAME_PATH) as image:
            image.load()
        if self.crop:
            left, top, width, height = self.crop
            image = image.crop((left, top, left + width, top + height))
        return image


def difference(a, b):
    """Mean pixel difference (0-255) between two frames, on small grayscale copies."""
    size = (64, 64)
    a = a.convert("L").resize(size)
    b = b.convert("L").resize(size)
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]
