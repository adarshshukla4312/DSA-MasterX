# GritX — Design System Specification

> **Version:** 2.0 — System B (Linear / Vercel Ultra-Clean)
> **Canvas:** Pitch-Black Dark Theme (`#000000`)
> **Aesthetic Lineage:** Resend → Linear → Vercel → Raycast
> **Last Updated:** August 2026

---

## 1. Design Philosophy

GritX is an engineering-grade algorithmic intelligence workspace.
It displays high-density information — Java/Python syntax, interactive MCQs,
5-column statistical matrices, 2-panel master-detail navigation, spaced-repetition
metrics, and live pipeline terminal logs — on a pitch-black canvas.

### Core Principles

1. **Function-Driven Design** — Every pixel earns its place. No decorative chrome.
2. **Optical Precision for Dark Mode** — Typography, tracking, and leading are
   calibrated to counteract optical irradiation (white text bleeding into black).
3. **Fluid Responsiveness** — CSS `clamp()` scales every display element from
   320px mobile to 4K ultrawide without breakpoint hacks.
4. **Premium Micro-Interactions** — Spring-based easing, tactile button presses,
   staggered entry animations, and terminal-style log rendering.

---

## 2. Color System

All colors are optimized for WCAG 2.1 AA+ contrast on `#000000` canvas.

### Surface Hierarchy

| Token                    | Value                        | Usage                              |
|--------------------------|------------------------------|-------------------------------------|
| `--color-canvas`         | `#000000`                    | App background                      |
| `--color-surface-deep`   | `#06060a`                    | Code blocks, terminal, inset panels |
| `--color-surface-card`   | `#0a0a0c`                    | Cards, modals, inputs               |
| `--color-surface-elevated`| `#101012`                   | Active nav items, elevated pills    |

### Text Hierarchy

| Token                | Value                          | Contrast vs `#000` | Usage                            |
|----------------------|--------------------------------|---------------------|----------------------------------|
| `--color-ink`        | `#fcfdff`                      | 19.8 : 1 (AAA)      | Display titles, headings, active |
| `--color-body`       | `rgba(252, 253, 255, 0.86)`    | 16.5 : 1 (AAA)      | Primary body text                |
| `--color-charcoal`   | `rgba(252, 253, 255, 0.70)`    | 12.4 : 1 (AAA)      | Secondary text, metadata         |
| `--color-mute`       | `#a1a4a5`                      | 8.2 : 1 (AA)        | Subtle labels                    |
| `--color-ash`        | `#888e90`                      | 6.1 : 1 (AA)        | Captions, timestamps, disabled   |
| `--color-stone`      | `#464a4d`                      | 3.2 : 1             | Decorative separators only       |

### Border System

| Token                     | Value                        | Usage                    |
|---------------------------|------------------------------|--------------------------|
| `--color-hairline`        | `rgba(255, 255, 255, 0.06)`  | Subtle dividers          |
| `--color-hairline-strong` | `rgba(255, 255, 255, 0.14)`  | Card borders, input borders |
| `--color-divider-soft`    | `rgba(255, 255, 255, 0.04)`  | Section separators       |

### Accent Palette

| Token                      | Value                         | Usage                         |
|----------------------------|-------------------------------|-------------------------------|
| `--color-accent-orange`    | `#ff801f`                     | New/pending status, hero glow |
| `--color-accent-yellow`    | `#ffc53d`                     | Medium difficulty, transcribed |
| `--color-accent-blue`      | `#3b9eff`                     | Links, extracted, active jobs |
| `--color-accent-green`     | `#11ff99`                     | Solved, easy, success         |
| `--color-accent-red`       | `#ff2047`                     | Hard difficulty, errors, danger |
| `--color-accent-violet`    | `#b088ff`                     | Visited links                 |

Each accent has an accompanying `*-glow` token for radial gradient atmospherics:
```
--color-accent-orange-glow: rgba(255, 89, 0, 0.22);
--color-accent-blue-glow:   rgba(0, 117, 255, 0.34);
--color-accent-green-glow:  rgba(34, 255, 153, 0.18);
--color-accent-red-glow:    rgba(255, 32, 71, 0.34);
```

---

## 3. Typography System

### System B: Linear / Vercel Ultra-Clean

Selected after benchmarking 4 systems (Editorial Luxury, Linear/Vercel Modern,
Neo-Grotesque Developer, Swiss Precision Geometric). System B scored **9.60/10**
across technical code harmony, dark theme optical balance, data scannability,
MCQ reading comfort, visual distinctiveness, and information density.

### Font Stacks

| Token            | Stack                                                                         | Role                         |
|------------------|-------------------------------------------------------------------------------|------------------------------|
| `--font-display` | `'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif`                     | Display titles, hero, stats  |
| `--font-serif`   | `'Instrument Serif', Georgia, serif`                                          | Optional editorial accent    |
| `--font-sans-ui` | `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif` | UI headings, body, controls  |
| `--font-mono`    | `'Geist Mono', 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace`      | Code blocks, logs, data      |

### Google Fonts Import

```css
@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
```

### Typographic Scale — Scale C: Fluid Adaptive Hybrid (1.250–1.333)

Uses CSS `clamp()` for seamless 320px → 4K scaling. Based on a Major Third
(1.250) ratio with fluid viewport-aware interpolation.

#### Scale Tokens

| Token                       | Value                                         | Range         |
|-----------------------------|-----------------------------------------------|---------------|
| `--font-size-display-xxl`   | `clamp(2.500rem, 5.0vw + 0.50rem, 4.750rem)` | 40px → 76px   |
| `--font-size-display-xl`    | `clamp(2.000rem, 3.5vw + 0.50rem, 3.250rem)` | 32px → 52px   |
| `--font-size-display-lg`    | `clamp(1.750rem, 2.8vw + 0.25rem, 2.500rem)` | 28px → 40px   |
| `--font-size-display-md`    | `clamp(1.500rem, 2.0vw + 0.25rem, 2.000rem)` | 24px → 32px   |
| `--font-size-heading-lg`    | `clamp(1.250rem, 1.5vw + 0.25rem, 1.500rem)` | 20px → 24px   |
| `--font-size-heading-md`    | `clamp(1.125rem, 1.2vw + 0.20rem, 1.250rem)` | 18px → 20px   |
| `--font-size-heading-sm`    | `1.000rem`                                    | 16px (fixed)  |
| `--font-size-body-lg`       | `clamp(1.000rem, 0.8vw + 0.75rem, 1.125rem)` | 16px → 18px   |
| `--font-size-body-md`       | `0.875rem`                                    | 14px (fixed)  |
| `--font-size-body-sm`       | `0.8125rem`                                   | 13px (fixed)  |
| `--font-size-caption`       | `0.750rem`                                    | 12px (fixed)  |
| `--font-size-micro`         | `0.6875rem`                                   | 11px (fixed)  |
| `--font-size-nano`          | `0.625rem`                                    | 10px (fixed)  |
| `--font-size-mono-code`     | `0.84375rem`                                  | 13.5px (fixed)|
| `--font-size-stat-value`    | `clamp(1.750rem, 2.2vw, 2.350rem)`            | 28px → 37.6px |

### Optical Tracking (Letter-Spacing)

Governed by the **Inverse Density Rule**: large text gets tight negative tracking
to compensate for dark-mode light bleed; small text gets positive tracking for
legibility.

| Token              | Value      | Usage                                      |
|--------------------|------------|--------------------------------------------|
| `--tracking-tighter`| `-0.040em` | Display XXL/XL (76px–52px)                |
| `--tracking-tight`  | `-0.025em` | Display LG/MD (40px–32px)                 |
| `--tracking-snug`   | `-0.015em` | Heading LG/MD (24px–20px)                 |
| `--tracking-normal` | `-0.005em` | Heading SM, Body LG/MD (16px–14px)        |
| `--tracking-relaxed`| `+0.020em` | Caption (12px)                            |
| `--tracking-loose`  | `+0.040em` | Micro pills & badges (11px)               |
| `--tracking-caps`   | `+0.060em` | Uppercase table headers, nano labels (10px)|

### Optical Leading (Line-Height)

| Token              | Value | Usage                                |
|--------------------|-------|--------------------------------------|
| `--leading-none`   | 1.00  | Stat values, single-line metrics     |
| `--leading-display`| 1.06  | Display XXL hero titles              |
| `--leading-tight`  | 1.15  | Display XL/LG titles                 |
| `--leading-snug`   | 1.30  | Heading LG/MD section headers        |
| `--leading-normal` | 1.55  | Body MD primary text                 |
| `--leading-relaxed`| 1.70  | Body LG lead paragraphs, code blocks |
| `--leading-code`   | 1.70  | Monospace code & terminal logs       |

### Master Typography Class Matrix

```
┌────────────────────┬──────────────────┬───────────────────────────┬────────┬─────────────┬────────────────┬───────────────────────────────────┐
│ CSS Class          │ Font Family      │ Font Size                 │ Weight │ Line-Height │ Letter-Spacing │ Optical Role                      │
├────────────────────┼──────────────────┼───────────────────────────┼────────┼─────────────┼────────────────┼───────────────────────────────────┤
│ .display-xxl       │ --font-display   │ clamp(40px, ..., 76px)    │ 700    │ 1.06        │ -0.040em       │ Home Hero Title                   │
│ .display-xl        │ --font-display   │ clamp(32px, ..., 52px)    │ 600    │ 1.12        │ -0.040em       │ Page Glow Headers                 │
│ .display-lg        │ --font-display   │ clamp(28px, ..., 40px)    │ 600    │ 1.18        │ -0.025em       │ Modal Headers / Highlights        │
│ .display-md        │ --font-display   │ clamp(24px, ..., 32px)    │ 600    │ 1.22        │ -0.025em       │ Major Section Titles              │
│ .heading-lg        │ --font-sans-ui   │ clamp(20px, ..., 24px)    │ 600    │ 1.30        │ -0.015em       │ Section Headers                   │
│ .heading-md        │ --font-sans-ui   │ clamp(18px, ..., 20px)    │ 600    │ 1.30        │ -0.015em       │ Card Titles / Modal Subtitles     │
│ .heading-sm        │ --font-sans-ui   │ 16px                      │ 600    │ 1.40        │ -0.005em       │ Problem Titles / MCQ Stems        │
│ .body-lg           │ --font-sans-ui   │ clamp(16px, ..., 18px)    │ 400    │ 1.70        │ -0.005em       │ Hero Descriptions / Lead Text     │
│ .body-md           │ --font-sans-ui   │ 14px                      │ 400    │ 1.55        │ -0.005em       │ Standard Body / MCQ Options       │
│ .body-sm           │ --font-sans-ui   │ 13px                      │ 400    │ 1.50        │  0.000em       │ Card Metadata / Approach Details  │
│ .caption           │ --font-sans-ui   │ 12px                      │ 500    │ 1.40        │ +0.020em       │ Timestamps / Sub-labels           │
│ .mono              │ --font-mono      │ 13.5px                    │ 400    │ 1.70        │  0.000em       │ Code Reconstruction / Terminal    │
│ .stat-card .value  │ --font-display   │ clamp(28px, ..., 37.6px)  │ 700    │ 1.15        │ -0.040em       │ Dashboard Metric Values           │
│ .status-pill       │ --font-sans-ui   │ 11px                      │ 500    │ 1.35        │ +0.040em       │ Status Badges & Tags              │
│ .tag-pill           │ --font-sans-ui   │ 11px                      │ 500    │ 1.35        │ +0.020em       │ Topic Tags / Pattern Labels       │
└────────────────────┴──────────────────┴───────────────────────────┴────────┴─────────────┴────────────────┴───────────────────────────────────┘
```

### Monospace & Code Features

```css
.code-block {
  font-family: var(--font-mono);
  font-size: var(--font-size-mono-code);       /* 13.5px */
  line-height: var(--leading-code);             /* 1.70 */
  letter-spacing: -0.01em;
  font-feature-settings: "zero" 1, "calt" 1;   /* Slashed zero + code alternates */
  font-variant-numeric: tabular-nums;
  tab-size: 4;
}
```

---

## 4. Spacing & Radius

### Border Radius

| Token          | Value    | Usage                          |
|----------------|----------|--------------------------------|
| `--radius-none`| `0px`    | Full-bleed elements            |
| `--radius-xs`  | `4px`    | Tiny controls, scrollbar thumb |
| `--radius-sm`  | `6px`    | Small buttons, code copy btn   |
| `--radius-md`  | `8px`    | Buttons, inputs, nav links     |
| `--radius-lg`  | `12px`   | Cards, code blocks, hero       |
| `--radius-xl`  | `16px`   | Modals                         |
| `--radius-full`| `9999px` | Pills, badges, progress bars   |

### Spacing Scale

```css
.gap-sm  { gap: 0.5rem; }   /* 8px  */
.gap-md  { gap: 1rem; }     /* 16px */
.gap-lg  { gap: 1.5rem; }   /* 24px */
.gap-xl  { gap: 2rem; }     /* 32px */
.section { margin-bottom: 2.5rem; }  /* 40px */
```

---

## 5. Motion & Animation

### Easing Functions

| Token            | Value                             | Usage                    |
|------------------|-----------------------------------|--------------------------|
| `--ease-spring`  | `cubic-bezier(0.16, 1, 0.3, 1)`  | Primary spring easing    |
| `--ease-in-out`  | `cubic-bezier(0.4, 0, 0.2, 1)`   | Standard material easing |
| `--ease-out`     | `cubic-bezier(0, 0, 0.2, 1)`     | Exit animations          |

### Duration Tokens

| Token                | Value                          | Usage                  |
|----------------------|--------------------------------|------------------------|
| `--transition-fast`  | `0.15s var(--ease-spring)`     | Hover, focus, active   |
| `--transition-normal`| `0.22s var(--ease-spring)`     | Page transitions, modals |
| `--transition-slow`  | `0.35s var(--ease-spring)`     | Complex multi-step     |

### Entry Animations

- **`fadeSlideUp`**: `opacity: 0 → 1`, `translateY(12px → 0)` — used for page enters
- **`.stagger-in`**: Sequential child delays (20ms → 170ms) for list/grid mounts
- **`.page-enter`**: Applied to every page on route transition
- **Anime.js**: External library for processing section card mount/dismount animations

### Micro-Interactions

| Element        | Hover                              | Active               | Disabled               |
|----------------|------------------------------------|-----------------------|------------------------|
| `.btn-primary` | `brightness(1.1)`, `translateY(-1px)` | `scale(0.97)`       | `opacity: 0.38`, no pointer |
| `.btn-ghost`   | `bg: rgba(255,255,255,0.06)`, border brighten | `scale(0.97)`, `bg: rgba(255,255,255,0.1)` | `opacity: 0.38` |
| `.btn-danger`  | `bg: #ff4d6a`                      | `scale(0.97)`         | `opacity: 0.38`        |
| `.btn-icon`    | `bg: surface-elevated`, color ink  | `scale(0.95)`         | `opacity: 0.38`        |
| `.glass-card`  | `border-color: rgba(255,255,255,0.3)` | —                  | —                      |
| `.stat-card`   | border brighten, `bg +0.02`, `translateY(-2px)` | `scale(0.98)` | —                    |
| `.nav-link`    | `bg: surface-elevated`, color ink  | `scale(0.98)`         | —                      |

---

## 6. Component Specifications

### Buttons

| Variant       | Height | Font Size | Padding      | Radius       |
|---------------|--------|-----------|--------------|--------------|
| `.btn-primary`| 36px   | 13.5px    | 8px 16px     | `--radius-md` |
| `.btn-ghost`  | 36px   | 13.5px    | 8px 16px     | `--radius-md` |
| `.btn-danger` | 36px   | 13.5px    | 8px 16px     | `--radius-md` |
| `.btn-sm`     | 28px   | 12px      | 4px 10px     | `--radius-md` |
| `.btn-icon`   | 36px   | —         | 0 (centered) | `--radius-md` |

**Loading State (`.btn-loading`)**: Text becomes transparent, replaced by a
14px spinning border ring. `pointer-events: none` prevents double-clicks.

### Form Controls

| Element     | Height | Font Size | Padding      | Focus Ring                                              |
|-------------|--------|-----------|--------------|---------------------------------------------------------|
| `.input`    | 38px   | 13.5px    | 8px 14px     | `box-shadow: 0 0 0 1px ink, 0 0 12px rgba(255,255,255,0.08)` |
| `.select`   | 38px   | 13.5px    | 8px 14px     | Same as input                                           |
| `textarea`  | auto   | 13.5px    | 8px 14px     | Same as input                                           |
| `range`     | 6px    | —         | —            | Thumb: 18px circle, grab cursor                         |

**Invalid State**: `border-color: accent-red`, `box-shadow: 0 0 0 1px accent-red`.

### Cards

| Variant       | Background          | Border                | Padding   | Radius       |
|---------------|--------------------|-----------------------|-----------|--------------|
| `.glass-card`  | `surface-card`     | `hairline-strong`     | 1.5rem    | `--radius-lg` |
| `.stat-card`   | `surface-card`     | `hairline-strong`     | 1.5rem    | `--radius-lg` |
| `.lecture-card` | `surface-card`    | `hairline-strong`     | 1.25rem 1.5rem | `--radius-lg` |

### Pills & Badges

| Variant        | Font Size | Tracking    | Padding     | Radius          |
|----------------|-----------|-------------|-------------|-----------------|
| `.status-pill` | 11px      | `+0.040em`  | 3px 10px    | `--radius-full` |
| `.badge-pill`  | 11px      | `+0.040em`  | 3px 10px    | `--radius-full` |
| `.tag-pill`    | 11px      | `+0.020em`  | 3px 9px     | `--radius-full` |
| `.tab-badge`   | 10.5px    | —           | 2px 6px     | `--radius-full` |

Status pill color coding:
- `.new` → orange
- `.transcribed` → yellow
- `.extracted` → blue
- `.identified` / `.matched` / `.completed` → green
- `.outdated` → ash

### Modals

```
Max-width: 520px | Width: 92% | Radius: --radius-xl (16px)
Background: surface-card | Border: hairline-strong
Padding: 2rem | Shadow: 0 24px 48px rgba(0,0,0,0.8)
Overlay: rgba(0,0,0,0.75) + backdrop-filter: blur(8px)
Entry: scale(0.95) translateY(8px) → scale(1) translateY(0)
```

### Toast Notifications

```
Position: fixed bottom-right (24px offset)
Background: surface-elevated | Border: hairline-strong | Radius: --radius-md
Min-width: 280px | Max-width: 400px
Shadow: 0 12px 24px rgba(0,0,0,0.6)
Entry: translateX(100%) → translateX(0) with spring easing
Variant border-left (3px): success=green, error=red, info=blue
```

---

## 7. Layout Architecture

### App Shell

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (260px fixed)  │  Main Content (flex: 1)       │
│  bg: surface-deep       │  padding: 2rem 3rem 4rem      │
│  border-right: hairline │  max-width: 1280px            │
│                         │                               │
│  ┌── Logo ──┐           │                               │
│  ├── HW Badge ──┤       │                               │
│  ├── Nav Links ──┤      │                               │
│  ├── Divider ──┤        │                               │
│  └── Stats Grid ──┘     │                               │
└─────────────────────────────────────────────────────────┘
```

### Responsive Breakpoints

| Breakpoint    | Behavior                                                  |
|---------------|-----------------------------------------------------------|
| `> 1024px`    | Full sidebar + main content side-by-side                  |
| `≤ 1024px`    | Sidebar collapses off-screen, mobile header appears       |
| `≤ 1200px`    | Two-panel layout stacks to single column                  |
| `≤ 768px`     | All grids collapse to single column                       |
| `pointer: coarse` | Touch targets min-height 44px (Apple HIG / WCAG)     |

### Grid System

```css
.grid-2 { grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
.grid-3 { grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.grid-4 { grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
.grid-5 { grid-template-columns: repeat(5, 1fr); gap: 1.5rem; }
```

### Two-Panel Layout (Problems / Practice)

```
Left Panel:  320px sticky | max-height: calc(100vh - 200px) | overflow-y: auto
Right Panel: flex: 1 | overflow-y: auto
Collapses to single column at ≤ 1200px
```

---

## 8. Focus & Accessibility

### Focus Management (WCAG 2.1 AA)

```css
/* Mouse clicks: no visible focus ring */
:focus:not(:focus-visible) {
  outline: none !important;
  box-shadow: none !important;
}

/* Keyboard navigation: subtle double-ring */
:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 2px var(--color-canvas),
              0 0 0 3px rgba(255, 255, 255, 0.3) !important;
}
```

### Visited Link States

```css
.external-link:visited { color: var(--color-accent-violet); }
```

### Disabled States

All interactive elements: `opacity: 0.38`, `cursor: not-allowed`, `pointer-events: none`.

### Selection

```css
::selection {
  background-color: var(--color-accent-blue);
  color: #fff;
}
```

---

## 9. Page-Level Typography Application

### Home (`#/`)

| Element              | Class / Token             | Spec                              |
|----------------------|---------------------------|-----------------------------------|
| Hero title           | `.display-xxl`            | Plus Jakarta Sans 700, 40–76px fluid |
| Hero description     | `.body-lg`                | Inter 400, 16–18px fluid, leading 1.70 |
| Stat card value      | `.stat-card .value`       | Plus Jakarta Sans 700, 28–37.6px fluid, tabular-nums |
| Stat card label      | `.stat-card .label`       | Inter 500, 13px, color ash        |
| Workflow card title  | `.heading-sm`             | Inter 600, 16px                   |
| Workflow card desc   | `.body-sm`                | Inter 400, 13px, color charcoal   |

### Lecture Library (`#/library`)

| Element              | Spec                                                |
|----------------------|-----------------------------------------------------|
| Lecture card title   | 15.5px, weight 600, leading 1.35, tracking snug     |
| Lecture metadata     | 12px mono, color ash                                |
| Tag pills            | 11px, weight 500, tracking +0.020em                 |
| Search input         | 13.5px, padding-left 40px (search icon inset)       |
| Processing log       | 12px mono, leading 1.65, bg `#050508`, terminal-style |

### Identified Problems (`#/problems`)

| Element                  | Spec                                              |
|--------------------------|---------------------------------------------------|
| Left panel lecture item  | 13.5px, weight 500, leading 1.40, ellipsis truncation |
| Problem count pill       | 11px mono, flex-shrink: 0                          |
| Problem card header      | `.heading-sm` — 16px, weight 600                   |
| Approach / Core Trick    | 13px, weight 400, leading 1.55, color charcoal    |
| Code block               | Geist Mono 13.5px, leading 1.70, slashed zeros    |
| LeetCode search link     | 13px, color accent-blue, visited → accent-violet   |

### Practice Sheets (`#/practice`)

| Element              | Spec                                                    |
|----------------------|---------------------------------------------------------|
| Tab bar item         | 13px, weight 500, tracking snug, active border 2px #fff |
| MCQ question stem    | 16px, weight 500, leading 1.65                          |
| MCQ option card      | 14px, weight 400, leading 1.50, min-height 44px         |
| Concept ladder step  | Title: 14px weight 600; Why: 12px color ash              |

### Revision Dashboard (`#/dashboard`)

| Element                | Spec                                                   |
|------------------------|--------------------------------------------------------|
| 5-col metric values    | 28–37.6px fluid, weight 700, tabular-nums              |
| Table header `th`      | 11.5px uppercase, tracking +0.060em, weight 600        |
| Table body `td`        | 13.5px, leading 1.45, pattern names weight 550         |
| Review card pattern    | 15.5px, weight 600, tracking -0.015em                  |
| Review meta stats      | 11.5px mono, gap 1.25rem                               |

---

## 10. Iconography

- **Library:** Lucide Icons (SVG, inline via JS helper)
- **Default stroke-width:** 1.75px
- **Size tokens:**

| Class      | Size  |
|------------|-------|
| `.icon-sm` | 14px  |
| `.icon-md` | 16px  |
| `.icon-lg` | 20px  |
| `.icon-xl` | 24px  |

---

## 11. Scrollbar & Selection

```css
::-webkit-scrollbar       { width: 8px; height: 8px; }
::-webkit-scrollbar-track  { background: var(--color-canvas); }
::-webkit-scrollbar-thumb  { background: var(--color-surface-elevated);
                             border: 1px solid var(--color-hairline);
                             border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--color-stone); }
```

---

## 12. Loading States

### Skeleton Shimmer

```css
.skeleton {
  background-color: var(--color-surface-card);
  /* Animated shimmer gradient overlay */
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
  animation: shimmer 1.5s infinite linear;
}
```

### Button Spinner

14px border ring spinning at 0.6s linear infinite. Primary variant uses
`--color-primary-on` border; ghost/danger use `#ffffff`.

### Progress Bar

6px height, full-radius, `surface-deep` track, `primary` fill with
spring-eased width transition.

---

## 13. Pipeline & Processing UI

### Active Processing Section

- Container: `linear-gradient(180deg, rgba(59,158,255,0.05) 0%, rgba(13,14,18,0.95) 100%)`
- Border: `rgba(59, 158, 255, 0.28)` with `box-shadow: 0 0 28px rgba(59,158,255,0.07)`
- Pulse dot: 8px blue circle with `pulseGlow` keyframe animation
- Processing lecture cards get `border-color: rgba(59,158,255,0.4)` + blue glow shadow

### Terminal Log Panel

```
Background: #050508 | Border: rgba(255,255,255,0.08) | Radius: --radius-md
Font: Geist Mono 12px | Line-height: 1.65 | Max-height: 220px (scroll)
Shadow: inset 0 2px 8px rgba(0,0,0,0.5)
Each row: timestamp (accent-blue 11px) + log text (#d6d9e0)
Entry animation: logRowFadeIn 0.22s ease
```

### Cancel Confirmation Modal

Red-tinted header with `alert-triangle` icon. Two actions:
- "Continue Processing" (ghost, closes modal)
- "Cancel Processing" (danger, proceeds with API cancel + artifact cleanup)

---

## 14. Backend Pipeline Architecture

### Processing Pipeline (3 Steps)

1. **Step 1/3: Whisper Transcription** — Audio extraction via FFmpeg → 10-min chunk
   segmentation → faster-whisper model with DSA domain prompt & VAD filtering
2. **Step 2/3: LLM Concept Extraction** — Transcript → structured JSON via streaming
   LLM API (topics, problems discussed, code reconstruction)
3. **Step 3/3: Unified Identification** — LLM reasoning for problem matching,
   concept ladder generation, and MCQ synthesis

### Robustness Features

- **Non-daemon threads** (`daemon=False`) — pipeline survives browser reloads
- **Retry with exponential backoff** — 3 attempts per step (2s → 4s → 8s)
- **Cancellation checkpoints** — `_check_cancelled()` between every step
- **Atomic cleanup on cancel** — transcript JSON, audio WAV/chunks deleted, DB reset to `new`
- **Error recovery** — DB resets to `new` on failure, enabling immediate retry
- **Frontend confirmation modal** — prevents accidental cancellation

### State Management

- **Runtime:** `ACTIVE_JOBS` dict with thread-safe `_jobs_lock`
- **Persistent:** SQLite DB via `db/schema.py` (WAL mode, foreign keys)
- **Sync:** `/api/lectures` merges ACTIVE_JOBS status into response
- **Polling:** Frontend polls `/api/lectures/{id}/job` every 2s for live logs

---

## 15. Design Evolution History

| Version | System | Display Font          | UI Font | Code Font    | Scale              |
|---------|--------|-----------------------|---------|--------------|---------------------|
| 0.1     | Original Resend | Domaine Display | ABC Favorit / Inter | Geist Mono | Fixed px (Resend spec) |
| 1.0     | System A Hybrid | Instrument Serif | Inter + Plus Jakarta Sans | Geist Mono | Major Third 1.250 fixed |
| **2.0** | **System B Modern** | **Plus Jakarta Sans** | **Inter** | **Geist Mono** | **Scale C: Fluid Adaptive clamp()** |

Key migrations in v2.0:
- Replaced Instrument Serif display headers with Plus Jakarta Sans for cohesive
  developer-tool aesthetic across algorithmic content
- Introduced CSS `clamp()` fluid scaling for all display and heading tokens
- Added comprehensive optical tracking and leading token systems
- Calibrated all typography for dark-mode irradiation compensation
- Added Anime.js for processing section animations
- Hardened pipeline with retry logic, atomic cancellation cleanup, and confirmation modals
