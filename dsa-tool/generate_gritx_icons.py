"""
GritX App Icon Generator
Renders the official minimalist, rounded geometric GritX icon:
- Outer rounded squircle with subtle soft shadow & deep dark slate gradient
- Two bold rounded angle brackets < and > (programming element)
- Open book constructed from thick, smooth rounded geometric strokes (learning element)
- Generates SVG, high-res PNGs (512, 256, 128, 64, 48, 32, 16), and multi-size Windows .ico
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="gritx-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#141c2e"/>
      <stop offset="50%" stop-color="#0e1422"/>
      <stop offset="100%" stop-color="#080b12"/>
    </linearGradient>

    <!-- Emerald / Mint Accent Gradient -->
    <linearGradient id="gritx-accent" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#2dd4bf"/>
      <stop offset="60%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>

    <!-- Book Platinum Gradient -->
    <linearGradient id="gritx-book" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#e2e8f0"/>
    </linearGradient>

    <!-- Soft Ambient Drop Shadow -->
    <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="16" stdDeviation="24" flood-color="#000000" flood-opacity="0.45"/>
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#10b981" flood-opacity="0.12"/>
    </filter>

    <!-- Inner Stroke Gradient -->
    <linearGradient id="border-glow" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="rgba(255, 255, 255, 0.16)"/>
      <stop offset="100%" stop-color="rgba(255, 255, 255, 0.03)"/>
    </linearGradient>
  </defs>

  <!-- Base Icon Squircle with Shadow -->
  <rect x="36" y="36" width="440" height="440" rx="98" ry="98"
        fill="url(#gritx-bg)" filter="url(#soft-shadow)"/>
  <rect x="36" y="36" width="440" height="440" rx="98" ry="98"
        fill="none" stroke="url(#border-glow)" stroke-width="2.5"/>

  <!-- Coding Element: Angle Brackets < and > -->
  <!-- Left Bracket < -->
  <path d="M 198 142 L 150 186 L 198 230"
        fill="none" stroke="url(#gritx-accent)" stroke-width="26"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Right Bracket > -->
  <path d="M 314 142 L 362 186 L 314 230"
        fill="none" stroke="url(#gritx-accent)" stroke-width="26"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Main Symbol: Open Book with Rounded Geometric Strokes -->
  <!-- Left Page Top & Bottom Outline -->
  <path d="M 256 294 C 214 280, 166 282, 134 294 L 134 372 C 166 360, 214 362, 256 376 Z"
        fill="none" stroke="url(#gritx-book)" stroke-width="24"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Right Page Top & Bottom Outline -->
  <path d="M 256 294 C 298 280, 346 282, 378 294 L 378 372 C 346 360, 298 362, 256 376 Z"
        fill="none" stroke="url(#gritx-book)" stroke-width="24"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Center Spine -->
  <line x1="256" y1="294" x2="256" y2="376"
        stroke="url(#gritx-accent)" stroke-width="22" stroke-linecap="round"/>
</svg>
"""


def render_icon_raster(size: int = 512) -> Image.Image:
    """
    Renders the GritX icon at 4x supersampling using PIL and downsamples with Lanczos filter.
    Produces crisp, perfectly anti-aliased geometry with subtle shadow and gradients.
    """
    SCALE = 4
    W = size * SCALE
    H = size * SCALE

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Coordinates scaled up
    pad = int(36 * (W / 512.0))
    box_w = W - 2 * pad
    box_h = H - 2 * pad
    radius = int(98 * (W / 512.0))

    # Shadow layer
    shadow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    shadow_offset = int(14 * (W / 512.0))
    s_draw.rounded_rectangle(
        [pad, pad + shadow_offset, pad + box_w, pad + box_h + shadow_offset],
        radius=radius,
        fill=(0, 0, 0, 180)
    )
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=int(22 * (W / 512.0))))

    # Composite shadow onto canvas
    img.alpha_composite(shadow_img)
    draw = ImageDraw.Draw(img)

    # Squircle Background Gradient
    # We create a gradient mask and apply it
    grad_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad_img)

    for y in range(pad, pad + box_h):
        factor = (y - pad) / float(box_h)
        # Gradient from #141c2e (20, 28, 46) to #080b12 (8, 11, 18)
        r = int(20 * (1 - factor) + 8 * factor)
        g = int(28 * (1 - factor) + 11 * factor)
        b = int(46 * (1 - factor) + 18 * factor)
        g_draw.line([(pad, y), (pad + box_w, y)], fill=(r, g, b, 255))

    # Mask to squircle shape
    mask = Image.new("L", (W, H), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([pad, pad, pad + box_w, pad + box_h], radius=radius, fill=255)

    img.paste(grad_img, (0, 0), mask)
    draw = ImageDraw.Draw(img)

    # Subtle inner border stroke
    border_width = max(2, int(2.5 * (W / 512.0)))
    draw.rounded_rectangle(
        [pad, pad, pad + box_w, pad + box_h],
        radius=radius,
        outline=(255, 255, 255, 30),
        width=border_width
    )

    # Helper function to convert 512-grid coords to scaled canvas
    def c(x, y):
        return (int(x * (W / 512.0)), int(y * (H / 512.0)))

    bracket_stroke = int(26 * (W / 512.0))
    book_stroke = int(24 * (W / 512.0))
    spine_stroke = int(22 * (W / 512.0))

    # Colors
    c_bracket = (16, 185, 129, 255)   # #10b981 emerald
    c_book = (248, 250, 252, 255)      # #f8fafc crisp slate white
    c_spine = (45, 212, 191, 255)      # #2dd4bf mint highlight

    # Left bracket <
    pts_left = [c(198, 142), c(150, 186), c(198, 230)]
    # Right bracket >
    pts_right = [c(314, 142), c(362, 186), c(314, 230)]

    def draw_thick_lines(points, color, width):
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            draw.line([p1, p2], fill=color, width=width)
        for pt in points:
            r = width // 2
            draw.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], fill=color)

    draw_thick_lines(pts_left, c_bracket, bracket_stroke)
    draw_thick_lines(pts_right, c_bracket, bracket_stroke)

    # Left Page of Open Book
    # Curve simulation with segments
    def generate_page_curve(y_start, y_end, is_left=True):
        steps = 20
        top_pts = []
        bot_pts = []
        for i in range(steps + 1):
            t = i / float(steps)
            # x ranges from 256 to 134 (if left) or 256 to 378 (if right)
            if is_left:
                x = 256 - t * (256 - 134)
            else:
                x = 256 + t * (378 - 256)
            # Arch formula: sin curve dip
            dip = math.sin(t * math.pi) * 14.0
            y_top = 294 + (t * (294 - 294)) - dip
            y_bot = 376 + (t * (372 - 376)) - dip
            top_pts.append(c(x, y_top))
            bot_pts.append(c(x, y_bot))
        return top_pts, bot_pts

    left_top, left_bot = generate_page_curve(294, 372, is_left=True)
    right_top, right_bot = generate_page_curve(294, 372, is_left=False)

    # Draw left page
    left_polygon = left_top + list(reversed(left_bot))
    draw_thick_lines(left_top, c_book, book_stroke)
    draw_thick_lines(left_bot, c_book, book_stroke)
    draw_thick_lines([left_top[-1], left_bot[-1]], c_book, book_stroke)

    # Draw right page
    draw_thick_lines(right_top, c_book, book_stroke)
    draw_thick_lines(right_bot, c_book, book_stroke)
    draw_thick_lines([right_top[-1], right_bot[-1]], c_book, book_stroke)

    # Center Spine
    draw_thick_lines([c(256, 294), c(256, 376)], c_spine, spine_stroke)

    # Downsample using Lanczos
    final_img = img.resize((size, size), Image.Resampling.LANCZOS)
    return final_img


def main():
    frontend_dir = Path("dsa-tool/frontend")
    icons_dir = frontend_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Save SVG
    svg_path = icons_dir / "gritx_icon.svg"
    svg_path.write_text(SVG_TEMPLATE.strip(), encoding="utf-8")
    print(f"Generated: {svg_path}")

    # Also save to frontend root as favicon.svg
    (frontend_dir / "favicon.svg").write_text(SVG_TEMPLATE.strip(), encoding="utf-8")

    # Generate multi-res PNGs
    sizes = [512, 256, 128, 64, 48, 32, 16]
    images = {}
    for s in sizes:
        img = render_icon_raster(s)
        png_path = icons_dir / f"gritx_{s}.png"
        img.save(png_path, "PNG")
        images[s] = img
        print(f"Generated: {png_path} ({s}x{s})")

    # Primary 512 & 256 in frontend root
    images[512].save(frontend_dir / "gritx_icon.png", "PNG")
    images[32].save(frontend_dir / "favicon-32x32.png", "PNG")
    images[16].save(frontend_dir / "favicon-16x16.png", "PNG")

    # Generate multi-size Windows .ico (containing 16, 32, 48, 64, 128, 256)
    ico_path = icons_dir / "gritx.ico"
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_images = [images[s[0]] for s in ico_sizes]
    
    ico_images[0].save(
        ico_path,
        format="ICO",
        sizes=ico_sizes,
        append_images=ico_images[1:]
    )
    print(f"Generated Windows Multi-Resolution ICO: {ico_path}")

    # Copy to frontend root favicon.ico
    ico_images[0].save(
        frontend_dir / "favicon.ico",
        format="ICO",
        sizes=ico_sizes,
        append_images=ico_images[1:]
    )
    print(f"Generated frontend favicon.ico")

    # Copy to repo root for desktop executable icon
    ico_images[0].save(
        Path("dsa-tool/gritx.ico"),
        format="ICO",
        sizes=ico_sizes,
        append_images=ico_images[1:]
    )
    print(f"Generated root dsa-tool/gritx.ico")


if __name__ == "__main__":
    main()
