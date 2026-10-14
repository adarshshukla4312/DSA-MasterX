"""
GritX App Icon Generator (Bigger & Bolder Geometry)
Renders the official minimalist, rounded geometric GritX icon:
- Outer rounded squircle with slim margin & deep dark slate gradient
- Bold, prominent angle brackets < and > (programming element) filling ~80% width
- Bold, expansive open book with thick rounded geometric strokes (learning element)
- Specially optimized for high visibility at small taskbar sizes (16x16, 24x24, 32x32)
- Generates SVG, high-res PNGs (512, 256, 128, 64, 48, 32, 16), and multi-size Windows .ico
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="gritx-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#161f33"/>
      <stop offset="50%" stop-color="#0f1626"/>
      <stop offset="100%" stop-color="#070a12"/>
    </linearGradient>

    <!-- Radiant Emerald Accent Gradient -->
    <linearGradient id="gritx-accent" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34d399"/>
      <stop offset="50%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>

    <!-- Book Crisp White Gradient -->
    <linearGradient id="gritx-book" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#e2e8f0"/>
    </linearGradient>

    <!-- Soft Ambient Drop Shadow -->
    <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#000000" flood-opacity="0.5"/>
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#10b981" flood-opacity="0.18"/>
    </filter>

    <!-- Inner Stroke Gradient -->
    <linearGradient id="border-glow" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="rgba(255, 255, 255, 0.22)"/>
      <stop offset="100%" stop-color="rgba(255, 255, 255, 0.04)"/>
    </linearGradient>
  </defs>

  <!-- Base Icon Squircle (Slim margin for maximized visual footprint) -->
  <rect x="18" y="18" width="476" height="476" rx="112" ry="112"
        fill="url(#gritx-bg)" filter="url(#soft-shadow)"/>
  <rect x="18" y="18" width="476" height="476" rx="112" ry="112"
        fill="none" stroke="url(#border-glow)" stroke-width="3"/>

  <!-- Coding Element: Big, Prominent Angle Brackets < and > -->
  <!-- Left Bracket < -->
  <path d="M 184 76 L 86 156 L 184 236"
        fill="none" stroke="url(#gritx-accent)" stroke-width="38"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Right Bracket > -->
  <path d="M 328 76 L 426 156 L 328 236"
        fill="none" stroke="url(#gritx-accent)" stroke-width="38"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Main Symbol: Large Open Book with Bold Rounded Strokes -->
  <!-- Left Page Outline -->
  <path d="M 256 274 C 196 248, 126 250, 72 270 L 72 416 C 126 396, 196 398, 256 424 Z"
        fill="none" stroke="url(#gritx-book)" stroke-width="36"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Right Page Outline -->
  <path d="M 256 274 C 316 248, 386 250, 440 270 L 440 416 C 386 396, 316 398, 256 424 Z"
        fill="none" stroke="url(#gritx-book)" stroke-width="36"
        stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Center Spine -->
  <line x1="256" y1="274" x2="256" y2="424"
        stroke="url(#gritx-accent)" stroke-width="32" stroke-linecap="round"/>
</svg>
"""


def render_icon_raster(size: int = 512) -> Image.Image:
    """
    Renders the GritX icon at 4x supersampling using PIL and downsamples with Lanczos filter.
    Produces bold, crisp geometry that remains distinct and readable on the Windows taskbar.
    """
    SCALE = 4
    W = size * SCALE
    H = size * SCALE

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Slim squircle padding (18px at 512 = ~3.5% margin)
    pad = int(18 * (W / 512.0))
    box_w = W - 2 * pad
    box_h = H - 2 * pad
    radius = int(112 * (W / 512.0))

    # Ambient drop shadow
    shadow_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    shadow_offset = int(10 * (W / 512.0))
    s_draw.rounded_rectangle(
        [pad, pad + shadow_offset, pad + box_w, pad + box_h + shadow_offset],
        radius=radius,
        fill=(0, 0, 0, 190)
    )
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=int(16 * (W / 512.0))))

    # Composite shadow
    img.alpha_composite(shadow_img)
    draw = ImageDraw.Draw(img)

    # Squircle Background Gradient
    grad_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grad_img)

    for y in range(pad, pad + box_h):
        factor = (y - pad) / float(box_h)
        # Gradient from #161f33 (22, 31, 51) to #070a12 (7, 10, 18)
        r = int(22 * (1 - factor) + 7 * factor)
        g = int(31 * (1 - factor) + 10 * factor)
        b = int(51 * (1 - factor) + 18 * factor)
        g_draw.line([(pad, y), (pad + box_w, y)], fill=(r, g, b, 255))

    # Mask to squircle shape
    mask = Image.new("L", (W, H), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.rounded_rectangle([pad, pad, pad + box_w, pad + box_h], radius=radius, fill=255)

    img.paste(grad_img, (0, 0), mask)
    draw = ImageDraw.Draw(img)

    # Inner border stroke
    border_width = max(2, int(3.0 * (W / 512.0)))
    draw.rounded_rectangle(
        [pad, pad, pad + box_w, pad + box_h],
        radius=radius,
        outline=(255, 255, 255, 40),
        width=border_width
    )

    def c(x, y):
        return (int(x * (W / 512.0)), int(y * (H / 512.0)))

    # Bolder stroke widths
    bracket_stroke = int(38 * (W / 512.0))
    book_stroke = int(36 * (W / 512.0))
    spine_stroke = int(32 * (W / 512.0))

    # Colors
    c_bracket = (16, 185, 129, 255)   # #10b981 emerald
    c_book = (255, 255, 255, 255)      # Crisp pure white
    c_spine = (52, 211, 153, 255)      # #34d399 mint highlight

    # Big angle brackets
    pts_left = [c(184, 76), c(86, 156), c(184, 236)]
    pts_right = [c(328, 76), c(426, 156), c(328, 236)]

    def draw_thick_lines(points, color, width):
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            draw.line([p1, p2], fill=color, width=width)
        for pt in points:
            r = width // 2
            draw.ellipse([pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r], fill=color)

    draw_thick_lines(pts_left, c_bracket, bracket_stroke)
    draw_thick_lines(pts_right, c_bracket, bracket_stroke)

    # Large Open Book Pages
    def generate_page_curve(is_left=True):
        steps = 24
        top_pts = []
        bot_pts = []
        for i in range(steps + 1):
            t = i / float(steps)
            if is_left:
                x = 256 - t * (256 - 72)
            else:
                x = 256 + t * (440 - 256)
            dip = math.sin(t * math.pi) * 18.0
            y_top = 274 + (t * (270 - 274)) - dip
            y_bot = 424 + (t * (416 - 424)) - dip
            top_pts.append(c(x, y_top))
            bot_pts.append(c(x, y_bot))
        return top_pts, bot_pts

    left_top, left_bot = generate_page_curve(is_left=True)
    right_top, right_bot = generate_page_curve(is_left=False)

    # Draw left page
    draw_thick_lines(left_top, c_book, book_stroke)
    draw_thick_lines(left_bot, c_book, book_stroke)
    draw_thick_lines([left_top[-1], left_bot[-1]], c_book, book_stroke)

    # Draw right page
    draw_thick_lines(right_top, c_book, book_stroke)
    draw_thick_lines(right_bot, c_book, book_stroke)
    draw_thick_lines([right_top[-1], right_bot[-1]], c_book, book_stroke)

    # Center Spine
    draw_thick_lines([c(256, 274), c(256, 424)], c_spine, spine_stroke)

    # Downsample with Lanczos
    return img.resize((size, size), Image.Resampling.LANCZOS)


def main():
    frontend_dir = Path("dsa-tool/frontend")
    icons_dir = frontend_dir / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    # Save SVG
    svg_path = icons_dir / "gritx_icon.svg"
    svg_path.write_text(SVG_TEMPLATE.strip(), encoding="utf-8")
    print(f"Generated: {svg_path}")

    # Favicon.svg
    (frontend_dir / "favicon.svg").write_text(SVG_TEMPLATE.strip(), encoding="utf-8")

    # Generate multi-res PNGs
    sizes = [512, 256, 128, 64, 48, 32, 24, 16]
    images = {}
    for s in sizes:
        img = render_icon_raster(s)
        png_path = icons_dir / f"gritx_{s}.png"
        img.save(png_path, "PNG")
        images[s] = img
        print(f"Generated: {png_path} ({s}x{s})")

    # Primary icons
    images[512].save(frontend_dir / "gritx_icon.png", "PNG")
    images[32].save(frontend_dir / "favicon-32x32.png", "PNG")
    images[16].save(frontend_dir / "favicon-16x16.png", "PNG")

    # Generate multi-size Windows .ico (including 24x24 for Windows taskbar!)
    ico_path = icons_dir / "gritx.ico"
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)]
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
    print("Generated frontend favicon.ico")

    # Copy to root and dsa-tool for Windows executable
    ico_images[0].save(
        Path("dsa-tool/gritx.ico"),
        format="ICO",
        sizes=ico_sizes,
        append_images=ico_images[1:]
    )
    ico_images[0].save(
        Path("gritx.ico"),
        format="ICO",
        sizes=ico_sizes,
        append_images=ico_images[1:]
    )
    print("Generated root gritx.ico & dsa-tool/gritx.ico")


if __name__ == "__main__":
    main()
