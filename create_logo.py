"""
DevBridge Logo Generator
Creates a simple, modern logo representing a bridge connecting terminals/code.
"""

from PIL import Image, ImageDraw, ImageFont
import math
import os

# Colors - Claude-inspired warm theme
ORANGE = "#FF9B4E"
DARK_BG = "#1a1a2e"
LIGHT_ORANGE = "#FFB875"
WHITE = "#FFFFFF"

def create_logo(size=512, bg_transparent=True):
    """Create the main DevBridge logo."""

    # Create image with transparency or dark background
    if bg_transparent:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    else:
        img = Image.new('RGBA', (size, size), DARK_BG)

    draw = ImageDraw.Draw(img)

    # Calculate dimensions
    center_x = size // 2
    center_y = size // 2
    margin = size // 8

    # Bridge arch parameters
    arch_width = size - (margin * 2)
    arch_height = size // 3
    arch_top = center_y - arch_height // 2
    arch_bottom = center_y + arch_height // 3

    # Draw bridge arch (main arc)
    arch_bbox = [
        margin,
        arch_top,
        size - margin,
        arch_top + arch_height * 2
    ]

    # Draw thick orange arch
    line_width = size // 16

    # Main bridge arc
    draw.arc(arch_bbox, start=180, end=360, fill=ORANGE, width=line_width)

    # Bridge pillars (two vertical lines)
    pillar_width = line_width
    pillar_height = size // 4

    # Left pillar
    left_pillar_x = margin + line_width
    draw.rectangle([
        left_pillar_x - pillar_width//2,
        center_y,
        left_pillar_x + pillar_width//2,
        center_y + pillar_height
    ], fill=ORANGE)

    # Right pillar
    right_pillar_x = size - margin - line_width
    draw.rectangle([
        right_pillar_x - pillar_width//2,
        center_y,
        right_pillar_x + pillar_width//2,
        center_y + pillar_height
    ], fill=ORANGE)

    # Bridge deck (horizontal line)
    deck_y = center_y + pillar_height - line_width//2
    draw.rectangle([
        margin,
        deck_y,
        size - margin,
        deck_y + line_width//2
    ], fill=LIGHT_ORANGE)

    # Terminal cursor/prompt on the left (representing code/terminal)
    cursor_size = size // 10
    cursor_x = margin + size // 6
    cursor_y = arch_top + arch_height // 3

    # Draw "> _" terminal prompt symbol
    prompt_width = size // 20

    # ">" symbol
    draw.polygon([
        (cursor_x, cursor_y),
        (cursor_x + cursor_size//2, cursor_y + cursor_size//3),
        (cursor_x, cursor_y + cursor_size//1.5)
    ], fill=WHITE)

    # "_" cursor
    draw.rectangle([
        cursor_x + cursor_size//2 + prompt_width//2,
        cursor_y + cursor_size//2,
        cursor_x + cursor_size + prompt_width,
        cursor_y + cursor_size//1.5
    ], fill=WHITE)

    # Terminal cursor on the right (mirror)
    cursor_x_right = size - margin - size // 6 - cursor_size

    # ">" symbol on right
    draw.polygon([
        (cursor_x_right, cursor_y),
        (cursor_x_right + cursor_size//2, cursor_y + cursor_size//3),
        (cursor_x_right, cursor_y + cursor_size//1.5)
    ], fill=WHITE)

    # "_" cursor on right
    draw.rectangle([
        cursor_x_right + cursor_size//2 + prompt_width//2,
        cursor_y + cursor_size//2,
        cursor_x_right + cursor_size + prompt_width,
        cursor_y + cursor_size//1.5
    ], fill=WHITE)

    # Connection dots on the bridge (data flowing)
    dot_radius = size // 40
    for i in range(5):
        dot_x = margin + (arch_width // 6) * (i + 1)
        # Calculate y position on the arc
        progress = (i + 1) / 6
        arc_y = arch_top + arch_height - math.sin(progress * math.pi) * (arch_height * 0.8)

        draw.ellipse([
            dot_x - dot_radius,
            arc_y - dot_radius,
            dot_x + dot_radius,
            arc_y + dot_radius
        ], fill=WHITE)

    return img


def create_simple_logo(size=512):
    """Create a simpler, more iconic version of the logo."""

    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center = size // 2
    margin = size // 6

    # Main bridge arc
    line_width = size // 12

    # Draw a stylized bridge shape
    arch_bbox = [
        margin,
        margin + size // 8,
        size - margin,
        size - margin - size // 8
    ]

    # Main arc (bridge top)
    draw.arc(arch_bbox, start=200, end=340, fill=ORANGE, width=line_width)

    # Two pillars
    pillar_width = line_width * 0.8
    pillar_start_y = center
    pillar_end_y = size - margin

    # Left pillar
    left_x = margin + size // 5
    draw.rounded_rectangle([
        left_x - pillar_width//2,
        pillar_start_y,
        left_x + pillar_width//2,
        pillar_end_y
    ], radius=pillar_width//4, fill=ORANGE)

    # Right pillar
    right_x = size - margin - size // 5
    draw.rounded_rectangle([
        right_x - pillar_width//2,
        pillar_start_y,
        right_x + pillar_width//2,
        pillar_end_y
    ], radius=pillar_width//4, fill=ORANGE)

    # Bridge deck
    deck_height = line_width // 2
    deck_y = pillar_end_y - deck_height
    draw.rounded_rectangle([
        margin // 2,
        deck_y,
        size - margin // 2,
        deck_y + deck_height
    ], radius=deck_height//2, fill=LIGHT_ORANGE)

    # Terminal bracket symbols < > on sides
    bracket_size = size // 8
    bracket_width = size // 25
    bracket_y = margin + size // 6

    # Left bracket <
    draw.line([
        (margin + bracket_size, bracket_y),
        (margin, bracket_y + bracket_size//2),
        (margin + bracket_size, bracket_y + bracket_size)
    ], fill=WHITE, width=bracket_width, joint="curve")

    # Right bracket >
    draw.line([
        (size - margin - bracket_size, bracket_y),
        (size - margin, bracket_y + bracket_size//2),
        (size - margin - bracket_size, bracket_y + bracket_size)
    ], fill=WHITE, width=bracket_width, joint="curve")

    return img


def create_favicon_sizes(logo):
    """Create multiple sizes for favicon."""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []

    for size in sizes:
        resized = logo.resize((size, size), Image.Resampling.LANCZOS)
        images.append(resized)

    return images


def main():
    # Create output directory
    output_dir = "assets"
    os.makedirs(output_dir, exist_ok=True)

    print("[*] Creating DevBridge logos...")

    # Create main logo (512x512)
    logo = create_simple_logo(512)
    logo.save(os.path.join(output_dir, "logo.png"), "PNG")
    print("[OK] Created logo.png (512x512)")

    # Create larger version for README (256x256)
    logo_256 = logo.resize((256, 256), Image.Resampling.LANCZOS)
    logo_256.save(os.path.join(output_dir, "logo-256.png"), "PNG")
    print("[OK] Created logo-256.png (256x256)")

    # Create logo with dark background for social preview
    logo_bg = create_simple_logo(1280)

    # Create social preview image (1280x640)
    social = Image.new('RGBA', (1280, 640), DARK_BG)
    # Center the logo
    logo_for_social = create_simple_logo(400)
    social.paste(logo_for_social, (440, 120), logo_for_social)

    # Add text "DevBridge" below logo
    draw = ImageDraw.Draw(social)
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 72)
        small_font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
        small_font = font

    # Draw title
    title = "DevBridge"
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(((1280 - text_width) // 2, 520), title, fill=WHITE, font=font)

    # Draw tagline
    tagline = "Your Terminal Sessions, Everywhere"
    bbox2 = draw.textbbox((0, 0), tagline, font=small_font)
    tagline_width = bbox2[2] - bbox2[0]
    draw.text(((1280 - tagline_width) // 2, 590), tagline, fill=LIGHT_ORANGE, font=small_font)

    social.save(os.path.join(output_dir, "social-preview.png"), "PNG")
    print("[OK] Created social-preview.png (1280x640)")

    # Create favicon.ico with multiple sizes
    favicon_images = create_favicon_sizes(logo)
    favicon_images[0].save(
        os.path.join(output_dir, "favicon.ico"),
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        append_images=favicon_images[1:]
    )
    print("[OK] Created favicon.ico (multi-size)")

    # Also save to webterm/static for the web app
    static_dir = "webterm/static"
    if os.path.exists(static_dir):
        logo.save(os.path.join(static_dir, "logo.png"), "PNG")
        favicon_images[0].save(
            os.path.join(static_dir, "favicon.ico"),
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
            append_images=favicon_images[1:4]
        )
        print(f"[OK] Copied to {static_dir}/")

    print("\n[DONE] All logos created successfully!")
    print(f"[DIR] Output directory: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()
