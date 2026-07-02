from PIL import Image, ImageDraw
import os


def create_icon():
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer circle - Olive / Forest Green
    draw.ellipse([8, 8, 248, 248], fill=(44, 85, 48, 255))
    # Inner circle - Amber / Gold
    draw.ellipse([54, 54, 202, 202], fill=(212, 175, 55, 255))
    # Paw pads - dark green
    green = (26, 53, 29, 255)
    draw.ellipse([96, 120, 140, 168], fill=green)  # main pad
    draw.ellipse([88, 92, 116, 124], fill=green)  # toe 1
    draw.ellipse([118, 80, 146, 112], fill=green)  # toe 2
    draw.ellipse([150, 84, 178, 116], fill=green)  # toe 3
    draw.ellipse([176, 104, 204, 136], fill=green)  # toe 4
    os.makedirs("static/img", exist_ok=True)
    out_path = "static/img/icon.ico"
    img.save(
        out_path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    )
    print(f"Icon created at: {out_path}")


if __name__ == "__main__":
    create_icon()
