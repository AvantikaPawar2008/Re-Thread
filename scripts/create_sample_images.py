"""Generate 3 realistic sample garment and tag test images in samples/ directory."""

import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

samples_dir = Path(__file__).resolve().parent.parent / "samples"
samples_dir.mkdir(exist_ok=True)


def create_sample_1_repair():
    # 1. Navy Cotton Pants with torn seam
    img = Image.new("RGB", (600, 800), color=(28, 42, 64))
    draw = ImageDraw.Draw(img)
    # Draw trouser silhouette
    draw.polygon([(180, 80), (420, 80), (450, 750), (330, 750), (300, 320), (270, 750), (150, 750)], fill=(35, 52, 78))
    # Waistband and pockets
    draw.line([(180, 140), (420, 140)], fill=(20, 30, 48), width=3)
    draw.line([(200, 140), (220, 220)], fill=(20, 30, 48), width=2)
    draw.line([(400, 140), (380, 220)], fill=(20, 30, 48), width=2)
    # Visible tear / damage on left leg
    draw.polygon([(210, 460), (225, 450), (235, 475), (220, 490), (205, 480)], fill=(12, 18, 28))
    draw.line([(205, 455), (240, 485)], fill=(180, 60, 60), width=3)
    draw.text((250, 470), "MENDABLE SEAM TEAR (5%)", fill=(255, 200, 200))
    img.save(samples_dir / "sample_1_repair_pants.jpg", "JPEG", quality=90)

    # Tag for Sample 1
    tag = Image.new("RGB", (400, 400), color=(245, 243, 238))
    t_draw = ImageDraw.Draw(tag)
    t_draw.rectangle([(20, 20), (380, 380)], outline=(180, 180, 180), width=2)
    t_draw.text((60, 60), "FABINDIA", fill=(40, 40, 40))
    t_draw.text((60, 120), "100% COTTON", fill=(20, 20, 20))
    t_draw.text((60, 160), "MADE IN INDIA", fill=(80, 80, 80))
    t_draw.text((60, 200), "WASH AT 40C", fill=(80, 80, 80))
    t_draw.text((60, 240), "DO NOT BLEACH", fill=(80, 80, 80))
    tag.save(samples_dir / "sample_1_repair_tag.jpg", "JPEG", quality=90)


def create_sample_2_resell():
    # 2. Levi's Denim Jacket in great condition
    img = Image.new("RGB", (600, 800), color=(235, 238, 242))
    draw = ImageDraw.Draw(img)
    # Jacket body
    draw.polygon([(150, 200), (220, 120), (380, 120), (450, 200), (430, 680), (170, 680)], fill=(58, 96, 150))
    # Sleeves
    draw.polygon([(150, 200), (90, 550), (140, 570), (190, 350)], fill=(50, 85, 135))
    draw.polygon([(450, 200), (510, 550), (460, 570), (410, 350)], fill=(50, 85, 135))
    # Collar & buttons
    draw.polygon([(250, 120), (300, 220), (350, 120)], fill=(40, 70, 115))
    for y in (260, 340, 420, 500, 580):
        draw.ellipse([(293, y), (307, y + 14)], fill=(180, 160, 90))
    # Chest pockets
    draw.rectangle([(200, 260), (260, 320)], outline=(40, 70, 115), width=2)
    draw.rectangle([(340, 260), (400, 320)], outline=(40, 70, 115), width=2)
    # Red Levi's tab
    draw.rectangle([(258, 280), (265, 300)], fill=(220, 30, 30))
    draw.text((180, 720), "GENTLY USED DENIM JACKET (NO DEFECTS)", fill=(40, 60, 90))
    img.save(samples_dir / "sample_2_resell_jacket.jpg", "JPEG", quality=90)

    # Tag for Sample 2
    tag = Image.new("RGB", (400, 400), color=(250, 250, 250))
    t_draw = ImageDraw.Draw(tag)
    t_draw.rectangle([(20, 20), (380, 380)], outline=(190, 190, 190), width=2)
    t_draw.text((60, 50), "LEVI'S", fill=(210, 20, 20))
    t_draw.text((60, 85), "ORIGINAL RIVETED QUALITY", fill=(60, 60, 60))
    t_draw.text((60, 140), "98% COTTON", fill=(30, 30, 30))
    t_draw.text((60, 175), "2% ELASTANE", fill=(30, 30, 30))
    t_draw.text((60, 230), "RN 010123 / CA 00342", fill=(90, 90, 90))
    tag.save(samples_dir / "sample_2_resell_tag.jpg", "JPEG", quality=90)


def create_sample_3_recycle():
    # 3. Heavily worn polyester fleece / t-shirt
    img = Image.new("RGB", (600, 800), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    # Tee silhouette with faded grayish color
    draw.polygon([(160, 180), (230, 130), (370, 130), (440, 180), (510, 280), (460, 320), (420, 260), (420, 700), (180, 700), (180, 260), (140, 320), (90, 280)], fill=(130, 130, 135))
    # Pilling / wear texture across body
    for x in range(200, 400, 25):
        for y in range(250, 650, 35):
            draw.point((x + (y % 7), y), fill=(95, 95, 100))
            draw.point((x + 2, y + 1), fill=(160, 160, 165))
    # Heavy frayed hem and collar
    draw.line([(180, 700), (420, 700)], fill=(70, 70, 75), width=4)
    draw.text((160, 730), "HEAVILY WORN & PILLED SYNTHETIC TEE", fill=(90, 90, 95))
    img.save(samples_dir / "sample_3_recycle_tee.jpg", "JPEG", quality=90)

    # Tag for Sample 3
    tag = Image.new("RGB", (400, 400), color=(240, 238, 235))
    t_draw = ImageDraw.Draw(tag)
    t_draw.rectangle([(20, 20), (380, 380)], outline=(180, 180, 180), width=2)
    t_draw.text((60, 60), "BASIC WEAR", fill=(80, 80, 80))
    t_draw.text((60, 120), "100% POLYESTER", fill=(20, 20, 20))
    t_draw.text((60, 160), "MACHINE WASH WARM", fill=(90, 90, 90))
    t_draw.text((60, 200), "TUMBLE DRY LOW", fill=(90, 90, 90))
    tag.save(samples_dir / "sample_3_recycle_tag.jpg", "JPEG", quality=90)


if __name__ == "__main__":
    create_sample_1_repair()
    create_sample_2_resell()
    create_sample_3_recycle()
    print("Created 6 sample garment and tag images in samples/ directory.")

