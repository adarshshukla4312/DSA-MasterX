"""
GritX — Resend Design System Theme & Components
Strictly adheres to DESIGN.md specs: true black canvas (#000000), editorial serif typography,
signature white CTA pills, 1px translucent hairline borders (no drop shadows), and low-opacity atmospheric glows.
"""
import streamlit as st

def inject_custom_theme():
    """Injects Google Fonts, Resend CSS tokens, component overrides, and atmospheric glow styles."""
    st.markdown("""
    <head>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    </head>
    <style>
        /* ------------------------------------------------------------------
           RESEND DESIGN SYSTEM TOKENS (DESIGN.md)
           ------------------------------------------------------------------ */
        :root {
            --color-primary: #fcfdff;
            --color-primary-on: #000000;
            --color-ink: #fcfdff;
            --color-body: rgba(252, 253, 255, 0.86);
            --color-charcoal: rgba(252, 253, 255, 0.7);
            --color-mute: #a1a4a5;
            --color-ash: #888e90;
            --color-stone: #464a4d;
            --color-canvas: #000000;
            --color-surface-card: #0a0a0c;
            --color-surface-elevated: #101012;
            --color-surface-deep: #06060a;
            --color-hairline: rgba(255, 255, 255, 0.06);
            --color-hairline-strong: rgba(255, 255, 255, 0.14);
            --color-divider-soft: rgba(255, 255, 255, 0.04);
            --color-surface-light: #f1f7fe;

            --color-accent-orange: #ff801f;
            --color-accent-orange-glow: rgba(255, 89, 0, 0.22);
            --color-accent-yellow: #ffc53d;
            --color-accent-blue: #3b9eff;
            --color-accent-blue-glow: rgba(0, 117, 255, 0.34);
            --color-accent-green: #11ff99;
            --color-accent-green-glow: rgba(34, 255, 153, 0.18);
            --color-accent-red: #ff2047;
            --color-accent-red-glow: rgba(255, 32, 71, 0.34);

            --radius-none: 0px;
            --radius-xs: 4px;
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            --radius-full: 9999px;

            --font-serif: 'Instrument Serif', 'Tiempos Headline', Georgia, serif;
            --font-sans-marketing: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
            --font-sans-ui: 'Inter', -apple-system, sans-serif;
            --font-mono: 'Geist Mono', 'JetBrains Mono', monospace;
        }

        /* ------------------------------------------------------------------
           CANVAS & TYPOGRAPHY RESET
           ------------------------------------------------------------------ */
        html, body, [class*="css"] {
            font-family: var(--font-sans-ui) !important;
            color: var(--color-ink) !important;
            background-color: var(--color-canvas) !important;
        }

        .stApp {
            background-color: var(--color-canvas) !important;
            background-image: none !important;
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1280px;
        }

        /* Headers & Headings */
        h1, h2, h3 {
            color: var(--color-ink) !important;
            font-weight: 400 !important;
        }

        .resend-display-xxl {
            font-family: var(--font-serif);
            font-size: 76px;
            line-height: 1.0;
            letter-spacing: -0.96px;
            color: var(--color-ink);
            margin: 0;
        }

        .resend-display-xl {
            font-family: var(--font-serif);
            font-size: 56px;
            line-height: 1.0;
            letter-spacing: -0.768px;
            color: var(--color-ink);
            margin: 0;
        }

        /* ------------------------------------------------------------------
           SIDEBAR STYLING (Resend Dark Surface Deep)
           ------------------------------------------------------------------ */
        [data-testid="stSidebar"] {
            background-color: var(--color-surface-deep) !important;
            background-image: none !important;
            border-right: 1px solid var(--color-hairline-strong) !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
            font-family: var(--font-serif) !important;
            color: var(--color-ink) !important;
            background: none !important;
            -webkit-text-fill-color: var(--color-ink) !important;
            font-size: 2rem !important;
            letter-spacing: -0.5px !important;
            font-weight: 400 !important;
        }

        /* ------------------------------------------------------------------
           CARDS & CONTAINERS (Hairline borders, no drop shadows)
           ------------------------------------------------------------------ */
        .glass-card, div[data-testid="stForm"] {
            background-color: var(--color-surface-card) !important;
            border: 1px solid var(--color-hairline-strong) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1.5rem !important;
            margin-bottom: 1.2rem !important;
            box-shadow: none !important;
            backdrop-filter: none !important;
            transition: border-color 0.2s ease;
        }

        .glass-card:hover {
            border-color: var(--color-ink) !important;
            box-shadow: none !important;
            transform: none !important;
        }

        /* Expander Containers */
        [data-testid="stExpander"] {
            background-color: var(--color-surface-card) !important;
            border: 1px solid var(--color-hairline-strong) !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: none !important;
            margin-bottom: 1rem !important;
        }

        [data-testid="stExpander"] > details > summary {
            font-family: var(--font-sans-ui) !important;
            font-weight: 500 !important;
            color: var(--color-ink) !important;
        }

        /* ------------------------------------------------------------------
           STAT CARDS
           ------------------------------------------------------------------ */
        .stat-card-v2 {
            background-color: var(--color-surface-card);
            border: 1px solid var(--color-hairline-strong);
            border-radius: var(--radius-lg);
            padding: 1.5rem 1rem;
            text-align: center;
            box-shadow: none;
            transition: border-color 0.2s ease;
        }

        .stat-card-v2:hover {
            border-color: var(--color-ink);
            transform: none;
            box-shadow: none;
        }

        .stat-number-v2 {
            font-family: var(--font-sans-marketing);
            font-size: 2.6rem;
            font-weight: 400;
            letter-spacing: -1.5px;
            color: var(--color-ink);
            background: none;
            -webkit-text-fill-color: var(--color-ink);
        }

        .stat-label-v2 {
            color: var(--color-ash);
            font-size: 0.8rem;
            font-family: var(--font-sans-ui);
            font-weight: 400;
            letter-spacing: 0.5px;
            margin-top: 0.4rem;
        }

        /* ------------------------------------------------------------------
           BUTTONS (Resend Signature White CTA & Translucent Ghost)
           ------------------------------------------------------------------ */
        .stButton > button {
            background-color: var(--color-primary) !important;
            color: var(--color-primary-on) !important;
            border: none !important;
            border-radius: var(--radius-md) !important;
            font-family: var(--font-sans-ui) !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            height: 36px !important;
            padding: 8px 16px !important;
            box-shadow: none !important;
            transition: all 0.15s ease !important;
        }

        .stButton > button:hover {
            background-color: var(--color-surface-light) !important;
            color: var(--color-primary-on) !important;
            box-shadow: none !important;
            transform: translateY(-1px) !important;
        }

        .stButton > button:active {
            background-color: var(--color-surface-light) !important;
            transform: translateY(0) !important;
        }

        /* Secondary Action Button (Ghost / Outline) */
        .stButton > button[kind="secondary"] {
            background-color: var(--color-surface-elevated) !important;
            color: var(--color-ink) !important;
            border: 1px solid var(--color-hairline-strong) !important;
            box-shadow: none !important;
        }

        .stButton > button[kind="secondary"]:hover {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
            color: var(--color-ink) !important;
        }

        /* ------------------------------------------------------------------
           INPUT ELEMENTS & SELECTBOXES
           ------------------------------------------------------------------ */
        .stTextInput > div > div > input, 
        .stSelectbox > div > div, 
        .stNumberInput > div > div > input,
        textarea {
            background-color: var(--color-surface-card) !important;
            border: 1px solid var(--color-hairline-strong) !important;
            border-radius: var(--radius-md) !important;
            color: var(--color-ink) !important;
            font-family: var(--font-sans-ui) !important;
            font-size: 14px !important;
            height: 40px !important;
        }

        .stTextInput > div > div > input:focus, 
        .stSelectbox > div > div:focus,
        textarea:focus {
            border-color: var(--color-ink) !important;
            box-shadow: none !important;
        }

        /* ------------------------------------------------------------------
           CODE WINDOWS & MONOSPACE
           ------------------------------------------------------------------ */
        code, pre, [data-testid="stCodeBlock"] {
            font-family: var(--font-mono) !important;
            font-size: 13px !important;
            line-height: 1.6 !important;
        }

        [data-testid="stCodeBlock"] {
            background-color: var(--color-surface-deep) !important;
            border: 1px solid var(--color-hairline-strong) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1rem !important;
        }

        /* ------------------------------------------------------------------
           STATUS BADGES & PILLS
           ------------------------------------------------------------------ */
        .badge-pill, .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: var(--color-surface-elevated);
            color: var(--color-body);
            font-family: var(--font-sans-ui);
            font-size: 12px;
            font-weight: 400;
            border-radius: var(--radius-full);
            padding: 4px 12px;
            border: 1px solid var(--color-hairline-strong);
            text-transform: none;
            letter-spacing: 0;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--color-accent-green);
            border-radius: var(--radius-full);
            display: inline-block;
            box-shadow: 0 0 6px var(--color-accent-green-glow);
        }

        .status-new { background-color: var(--color-surface-elevated); color: var(--color-accent-orange); border-color: rgba(255, 89, 0, 0.3); }
        .status-transcribed { background-color: var(--color-surface-elevated); color: var(--color-accent-yellow); border-color: rgba(255, 197, 61, 0.3); }
        .status-extracted { background-color: var(--color-surface-elevated); color: var(--color-accent-blue); border-color: rgba(0, 117, 255, 0.3); }
        .status-identified { background-color: var(--color-surface-elevated); color: var(--color-accent-green); border-color: rgba(34, 255, 153, 0.3); }
        .status-outdated { background-color: var(--color-surface-elevated); color: var(--color-ash); border-color: var(--color-hairline); }

        /* Difficulty Tags */
        .diff-easy { color: var(--color-accent-green) !important; font-weight: 500; }
        .diff-medium { color: var(--color-accent-yellow) !important; font-weight: 500; }
        .diff-hard { color: var(--color-accent-red) !important; font-weight: 500; }

        /* ------------------------------------------------------------------
           ATMOSPHERIC GLOW BANNERS (RESEND SIGNATURE DEPTH)
           ------------------------------------------------------------------ */
        .resend-hero-banner {
            background-color: var(--color-canvas);
            background-image: radial-gradient(circle at 50% 0%, var(--color-accent-orange-glow) 0%, transparent 65%);
            border: 1px solid var(--color-hairline-strong);
            border-radius: var(--radius-lg);
            padding: 3rem 2.5rem;
            margin-bottom: 2.5rem;
            position: relative;
        }

        .resend-glow-blue {
            background-image: radial-gradient(circle at 50% 0%, var(--color-accent-blue-glow) 0%, transparent 65%);
        }

        .resend-glow-green {
            background-image: radial-gradient(circle at 50% 0%, var(--color-accent-green-glow) 0%, transparent 65%);
        }

        .resend-glow-red {
            background-image: radial-gradient(circle at 50% 0%, var(--color-accent-red-glow) 0%, transparent 65%);
        }

        /* ------------------------------------------------------------------
           PROGRESS BAR & SCROLLBAR
           ------------------------------------------------------------------ */
        .stProgress > div > div > div > div {
            background-color: var(--color-primary) !important;
            border-radius: var(--radius-full) !important;
        }

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: var(--color-canvas);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--color-surface-elevated);
            border-radius: var(--radius-full);
            border: 1px solid var(--color-hairline);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--color-stone);
        }

        /* Hide Streamlit Chrome */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
