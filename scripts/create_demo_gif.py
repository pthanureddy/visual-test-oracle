from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    out = ROOT / "docs" / "assets" / "demo.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    labels = ["Open checkout", "Click checkout", "Evaluate screenshot", "Vote verdict"]
    colors = ["#f6f7f9", "#dbeafe", "#dcfce7", "#eef2ff"]
    for label, color in zip(labels, colors):
        frame = Image.new("RGB", (720, 360), color)
        draw = ImageDraw.Draw(frame)
        draw.rounded_rectangle((96, 78, 624, 282), radius=12, fill="white", outline="#cbd5e1", width=2)
        draw.text((132, 122), "Visual Test Oracle", fill="#172033")
        draw.text((132, 170), label, fill="#1d4ed8")
        frames.append(frame)
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=700, loop=0)
    print(out)


if __name__ == "__main__":
    main()
