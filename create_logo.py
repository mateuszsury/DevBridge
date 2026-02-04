"""
DevBridge Logo Generator v2
Professional, modern logo representing seamless terminal connectivity.
A glowing bridge connecting two terminals with data flow.
"""

from PIL import Image, ImageDraw, ImageFilter
import math
import os

# Color palette - warm developer theme
COLORS = {
    'core_white': '#FFFFFF',
    'glow_bright': '#FFB875',
    'glow_mid': '#FF9B4E',
    'glow_outer': '#E07830',
    'bridge_main': '#FF9B4E',
    'bridge_light': '#FFCC99',
    'terminal_green': '#4ADE80',
    'terminal_dim': '#22C55E',
    'data_blue': '#60A5FA',
    'dark_bg': '#0D1117',
    'accent': '#FF9B4E',
}

def hex_to_rgb(hex_color):
    """Convert hex to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def draw_glowing_arc(img, center_x, center_y, radius, start_angle, end_angle, width, size):
    """Draw a glowing arc (bridge cable)."""
    arc = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Multiple glow layers
    glow_configs = [
        (width * 4, COLORS['glow_outer'], 20),
        (width * 3, COLORS['glow_outer'], 40),
        (width * 2, COLORS['glow_mid'], 80),
        (width * 1.5, COLORS['glow_bright'], 140),
        (width, COLORS['bridge_light'], 255),
    ]

    for w, color, alpha in glow_configs:
        layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        rgb = hex_to_rgb(color)

        bbox = [
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius
        ]

        layer_draw.arc(bbox, start=start_angle, end=end_angle,
                       fill=(*rgb, alpha), width=int(w))

        if w > width:
            blur = int(w * 0.3)
            layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))

        arc = Image.alpha_composite(arc, layer)

    return Image.alpha_composite(img, arc)

def draw_suspension_cable(img, start, end, sag, width, size):
    """Draw a suspension cable with catenary curve."""
    cable = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    cable_draw = ImageDraw.Draw(cable)

    # Calculate catenary points
    points = []
    num_points = 50
    for i in range(num_points + 1):
        t = i / num_points
        x = start[0] + (end[0] - start[0]) * t
        # Parabolic sag
        y = start[1] + (end[1] - start[1]) * t + sag * math.sin(t * math.pi)
        points.append((x, y))

    # Draw glowing cable
    for layer_w, alpha in [(width * 3, 30), (width * 2, 60), (width * 1.5, 120), (width, 255)]:
        layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        rgb = hex_to_rgb(COLORS['glow_mid'])

        if len(points) > 1:
            layer_draw.line(points, fill=(*rgb, alpha), width=int(layer_w))

        if layer_w > width:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=int(layer_w * 0.3)))

        cable = Image.alpha_composite(cable, layer)

    return Image.alpha_composite(img, cable)

def draw_tower(img, x, y, tower_width, tower_height, size):
    """Draw a glowing bridge tower."""
    tower = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Tower glow
    for layer_w, alpha in [(tower_width * 2, 30), (tower_width * 1.5, 70), (tower_width, 200)]:
        layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        rgb = hex_to_rgb(COLORS['bridge_main'])

        # Main tower body
        offset = (layer_w - tower_width) / 2
        layer_draw.rounded_rectangle([
            x - layer_w/2, y,
            x + layer_w/2, y + tower_height
        ], radius=int(layer_w/3), fill=(*rgb, alpha))

        # Tower top (wider)
        top_width = layer_w * 1.3
        layer_draw.rounded_rectangle([
            x - top_width/2, y - layer_w/2,
            x + top_width/2, y + layer_w
        ], radius=int(layer_w/3), fill=(*rgb, alpha))

        if layer_w > tower_width:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=int(layer_w * 0.2)))

        tower = Image.alpha_composite(tower, layer)

    # Tower light at top
    light = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    light_draw = ImageDraw.Draw(light)
    light_r = tower_width * 0.4

    for r, alpha in [(light_r * 3, 40), (light_r * 2, 80), (light_r * 1.5, 150), (light_r, 255)]:
        light_draw.ellipse([
            x - r, y - tower_width/2 - r,
            x + r, y - tower_width/2 + r
        ], fill=(*hex_to_rgb(COLORS['core_white']), alpha))

    light = light.filter(ImageFilter.GaussianBlur(radius=int(light_r * 0.5)))
    tower = Image.alpha_composite(tower, light)

    return Image.alpha_composite(img, tower)

def draw_road_deck(img, y, width, height, margin, size):
    """Draw the glowing bridge road deck."""
    deck = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Deck glow layers
    for h_mult, alpha in [(3, 25), (2, 50), (1.5, 100), (1, 220)]:
        layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        rgb = hex_to_rgb(COLORS['glow_mid'])

        h = height * h_mult
        layer_draw.rounded_rectangle([
            margin * 0.3, y - h/2,
            size - margin * 0.3, y + h/2
        ], radius=int(h/2), fill=(*rgb, alpha))

        if h_mult > 1:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=int(h * 0.3)))

        deck = Image.alpha_composite(deck, layer)

    return Image.alpha_composite(img, deck)

def draw_terminal_icon(img, x, y, icon_size, is_left, size):
    """Draw a stylized terminal icon with glow."""
    terminal = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    # Terminal window background glow
    for s_mult, alpha in [(1.4, 30), (1.2, 60), (1, 180)]:
        layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)

        s = icon_size * s_mult
        rgb = hex_to_rgb(COLORS['terminal_dim'])

        layer_draw.rounded_rectangle([
            x - s/2, y - s/2,
            x + s/2, y + s/2
        ], radius=int(s/6), fill=(*rgb, alpha))

        if s_mult > 1:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=int(s * 0.1)))

        terminal = Image.alpha_composite(terminal, layer)

    # Draw prompt ">" symbol
    term_draw = ImageDraw.Draw(terminal)
    prompt_size = icon_size * 0.4
    prompt_x = x - prompt_size * 0.3
    prompt_y = y

    rgb_white = hex_to_rgb(COLORS['core_white'])

    # Draw ">" as lines
    line_width = max(2, int(icon_size * 0.08))
    term_draw.line([
        (prompt_x - prompt_size/3, prompt_y - prompt_size/3),
        (prompt_x + prompt_size/4, prompt_y),
        (prompt_x - prompt_size/3, prompt_y + prompt_size/3)
    ], fill=(*rgb_white, 255), width=line_width, joint="miter")

    # Draw cursor "_"
    cursor_x = prompt_x + prompt_size/2
    cursor_width = prompt_size * 0.4
    cursor_height = line_width
    term_draw.rectangle([
        cursor_x, prompt_y + prompt_size/4,
        cursor_x + cursor_width, prompt_y + prompt_size/4 + cursor_height
    ], fill=(*rgb_white, 255))

    return Image.alpha_composite(img, terminal)

def draw_data_particles(img, start_x, end_x, y, num_particles, size):
    """Draw flowing data particles across the bridge."""
    particles = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    for i in range(num_particles):
        t = (i + 0.5) / num_particles
        x = start_x + (end_x - start_x) * t

        # Slight wave motion
        wave_y = y + math.sin(t * math.pi * 3) * (size * 0.015)

        # Particle glow
        particle_r = size * 0.012
        for r_mult, alpha in [(3, 40), (2, 80), (1.5, 150), (1, 255)]:
            layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer)

            r = particle_r * r_mult
            # Alternate colors
            color = COLORS['data_blue'] if i % 2 == 0 else COLORS['core_white']
            rgb = hex_to_rgb(color)

            layer_draw.ellipse([
                x - r, wave_y - r,
                x + r, wave_y + r
            ], fill=(*rgb, alpha))

            if r_mult > 1:
                layer = layer.filter(ImageFilter.GaussianBlur(radius=int(r * 0.4)))

            particles = Image.alpha_composite(particles, layer)

    return Image.alpha_composite(img, particles)

def create_devbridge_logo(size=512):
    """Create the main DevBridge logo - a glowing suspension bridge."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    center = size // 2
    margin = size // 10

    # Bridge dimensions
    tower_width = size // 18
    tower_height = size // 3
    deck_y = center + size // 6
    deck_height = size // 25

    # Tower positions
    left_tower_x = margin + size // 5
    right_tower_x = size - margin - size // 5
    tower_top_y = center - size // 8

    # 1. Draw road deck
    img = draw_road_deck(img, deck_y, size - margin * 2, deck_height, margin, size)

    # 2. Draw main suspension cables (catenary)
    cable_top_y = tower_top_y - tower_width

    # Left side cables
    img = draw_suspension_cable(img,
        (left_tower_x, cable_top_y),
        (margin * 0.5, deck_y - deck_height),
        size * 0.08, tower_width // 3, size)

    # Right side cables
    img = draw_suspension_cable(img,
        (right_tower_x, cable_top_y),
        (size - margin * 0.5, deck_y - deck_height),
        size * 0.08, tower_width // 3, size)

    # Main cable between towers
    img = draw_suspension_cable(img,
        (left_tower_x, cable_top_y),
        (right_tower_x, cable_top_y),
        size * 0.15, tower_width // 2.5, size)

    # Vertical suspender cables
    num_suspenders = 7
    for i in range(num_suspenders):
        t = (i + 1) / (num_suspenders + 1)
        x = left_tower_x + (right_tower_x - left_tower_x) * t
        # Calculate cable y position (catenary)
        cable_y = cable_top_y + size * 0.15 * math.sin(t * math.pi)

        # Draw vertical cable
        cable = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        cable_draw = ImageDraw.Draw(cable)

        w = tower_width // 5
        rgb = hex_to_rgb(COLORS['glow_mid'])

        for lw, alpha in [(w * 2, 40), (w * 1.5, 100), (w, 200)]:
            layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer)
            layer_draw.line([(x, cable_y), (x, deck_y - deck_height/2)],
                          fill=(*rgb, alpha), width=int(lw))
            if lw > w:
                layer = layer.filter(ImageFilter.GaussianBlur(radius=int(lw * 0.3)))
            cable = Image.alpha_composite(cable, layer)

        img = Image.alpha_composite(img, cable)

    # 3. Draw towers
    img = draw_tower(img, left_tower_x, tower_top_y, tower_width, tower_height, size)
    img = draw_tower(img, right_tower_x, tower_top_y, tower_width, tower_height, size)

    # 4. Draw terminal icons on each side
    terminal_size = size // 8
    terminal_y = tower_top_y + tower_height // 3

    img = draw_terminal_icon(img, margin + terminal_size/2 + size * 0.02,
                             terminal_y, terminal_size, True, size)
    img = draw_terminal_icon(img, size - margin - terminal_size/2 - size * 0.02,
                             terminal_y, terminal_size, False, size)

    # 5. Draw data particles flowing across
    img = draw_data_particles(img, left_tower_x, right_tower_x,
                              cable_top_y + size * 0.08, 9, size)

    return img

def create_simple_icon(size=512):
    """Create a simplified icon for small sizes."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))

    center = size // 2
    margin = size // 8

    # Simple arc bridge
    arc_width = size // 10

    # Glow layers for arc
    for w_mult, alpha in [(3, 30), (2, 60), (1.5, 120), (1, 255)]:
        layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)

        w = int(arc_width * w_mult)
        rgb = hex_to_rgb(COLORS['bridge_main'])

        bbox = [margin, margin, size - margin, size - margin]
        layer_draw.arc(bbox, start=200, end=340, fill=(*rgb, alpha), width=w)

        if w_mult > 1:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=int(w * 0.25)))

        img = Image.alpha_composite(img, layer)

    # Two pillars
    pillar_w = arc_width * 0.8
    pillar_h = size // 3
    deck_y = center + size // 5

    for px in [margin + size // 5, size - margin - size // 5]:
        for pw, alpha in [(pillar_w * 2, 40), (pillar_w * 1.5, 100), (pillar_w, 220)]:
            layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            layer_draw = ImageDraw.Draw(layer)
            rgb = hex_to_rgb(COLORS['bridge_main'])

            layer_draw.rounded_rectangle([
                px - pw/2, center - size//10,
                px + pw/2, deck_y
            ], radius=int(pw/3), fill=(*rgb, alpha))

            if pw > pillar_w:
                layer = layer.filter(ImageFilter.GaussianBlur(radius=int(pw * 0.2)))

            img = Image.alpha_composite(img, layer)

    # Road deck
    deck_h = arc_width // 2
    for h_mult, alpha in [(2.5, 35), (1.8, 80), (1, 230)]:
        layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)

        h = deck_h * h_mult
        rgb = hex_to_rgb(COLORS['glow_mid'])

        layer_draw.rounded_rectangle([
            margin * 0.5, deck_y - h/2,
            size - margin * 0.5, deck_y + h/2
        ], radius=int(h/2), fill=(*rgb, alpha))

        if h_mult > 1:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=int(h * 0.3)))

        img = Image.alpha_composite(img, layer)

    return img

def create_favicon_sizes(logo):
    """Create multiple favicon sizes."""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        if s <= 48:
            resized = create_simple_icon(s * 4).resize((s, s), Image.Resampling.LANCZOS)
        else:
            resized = logo.resize((s, s), Image.Resampling.LANCZOS)
        images.append(resized)
    return images

def main():
    output_dir = "assets"
    os.makedirs(output_dir, exist_ok=True)

    print("[*] Creating DevBridge logo v2 - Glowing Suspension Bridge...")

    # Main logo (high quality)
    logo = create_devbridge_logo(1024)
    logo_512 = logo.resize((512, 512), Image.Resampling.LANCZOS)
    logo_512.save(os.path.join(output_dir, "logo.png"), "PNG")
    print("[OK] Created logo.png (512x512)")

    # Different sizes
    for s in [256, 128, 64]:
        if s >= 128:
            resized = logo.resize((s, s), Image.Resampling.LANCZOS)
        else:
            resized = create_simple_icon(256).resize((s, s), Image.Resampling.LANCZOS)
        resized.save(os.path.join(output_dir, f"logo-{s}.png"), "PNG")
        print(f"[OK] Created logo-{s}.png ({s}x{s})")

    # Social preview
    from PIL import ImageFont
    social = Image.new('RGBA', (1280, 640), COLORS['dark_bg'])
    logo_social = create_devbridge_logo(380)

    paste_x = (1280 - 380) // 2
    paste_y = 50
    social.paste(logo_social, (paste_x, paste_y), logo_social)

    draw = ImageDraw.Draw(social)

    try:
        font_large = ImageFont.truetype("arial.ttf", 68)
        font_medium = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # Title
    title = "DevBridge"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    tw = bbox[2] - bbox[0]
    draw.text(((1280 - tw) // 2, 450), title, fill=COLORS['core_white'], font=font_large)

    # Tagline
    tagline = "Your Terminal Sessions, Everywhere"
    bbox2 = draw.textbbox((0, 0), tagline, font=font_medium)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((1280 - tw2) // 2, 530), tagline, fill=COLORS['accent'], font=font_medium)

    # Subtitle
    subtitle = "Seamless remote development across all your devices"
    bbox3 = draw.textbbox((0, 0), subtitle, font=font_small)
    tw3 = bbox3[2] - bbox3[0]
    draw.text(((1280 - tw3) // 2, 575), subtitle, fill="#888888", font=font_small)

    social.save(os.path.join(output_dir, "social-preview.png"), "PNG")
    print("[OK] Created social-preview.png (1280x640)")

    # Favicon
    favicon_images = create_favicon_sizes(logo)
    favicon_images[0].save(
        os.path.join(output_dir, "favicon.ico"),
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        append_images=favicon_images[1:]
    )
    print("[OK] Created favicon.ico")

    # Copy to webterm/static if exists
    static_dir = "webterm/static"
    if os.path.exists(static_dir):
        logo_512.save(os.path.join(static_dir, "logo.png"), "PNG")
        favicon_images[0].save(
            os.path.join(static_dir, "favicon.ico"),
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
            append_images=favicon_images[1:4]
        )
        print(f"[OK] Copied to {static_dir}/")

    print("\n[DONE] All DevBridge logos created!")
    print(f"[DIR] {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    main()
