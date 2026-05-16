---
name: High-Density Intelligence
colors:
  surface: '#131316'
  surface-dim: '#131316'
  surface-bright: '#39393c'
  surface-container-lowest: '#0e0e11'
  surface-container-low: '#1b1b1e'
  surface-container: '#1f1f22'
  surface-container-high: '#2a2a2d'
  surface-container-highest: '#353438'
  on-surface: '#e4e1e6'
  on-surface-variant: '#cec6b7'
  inverse-surface: '#e4e1e6'
  inverse-on-surface: '#303033'
  outline: '#979083'
  outline-variant: '#4b463b'
  surface-tint: '#d8c596'
  primary: '#fff0cc'
  on-primary: '#3a2f0d'
  primary-container: '#e6d3a3'
  on-primary-container: '#685a34'
  inverse-primary: '#6b5d37'
  secondary: '#d2bbff'
  on-secondary: '#3f008e'
  secondary-container: '#6001d1'
  on-secondary-container: '#c9aeff'
  tertiary: '#f2efff'
  on-tertiary: '#2f2e47'
  tertiary-container: '#d4d1f2'
  on-tertiary-container: '#5a5975'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#f5e1b0'
  primary-fixed-dim: '#d8c596'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#524621'
  secondary-fixed: '#eaddff'
  secondary-fixed-dim: '#d2bbff'
  on-secondary-fixed: '#25005a'
  on-secondary-fixed-variant: '#5a00c6'
  tertiary-fixed: '#e2dfff'
  tertiary-fixed-dim: '#c6c3e4'
  on-tertiary-fixed: '#1a1931'
  on-tertiary-fixed-variant: '#45445f'
  background: '#131316'
  on-background: '#e4e1e6'
  surface-variant: '#353438'
typography:
  display-lg:
    fontFamily: JetBrains Mono
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: JetBrains Mono
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: JetBrains Mono
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1'
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 16px
  margin: 24px
---

## Brand & Style

The design system is engineered for elite analytical environments where precision, clarity, and rapid information synthesis are paramount. The aesthetic is **High-Tech Minimalism**—a synthesis of corporate sophistication and developer-centric utility. It evokes a "command center" atmosphere, utilizing deep blacks and tactical grays to ensure the user's focus remains entirely on data signals.

The brand personality is authoritative, cold, and surgical. By stripping away decorative elements and focusing on structural integrity, the design system creates a low-friction interface for high-stakes decision-making. Gold accents are used sparingly as a "high-value" indicator, highlighting critical insights against the monochromatic backdrop.

## Colors

The palette is anchored in a true-dark foundation to maximize contrast and reduce eye strain during prolonged analysis. 

- **Foundational Neutrals:** We use a three-tier grayscale system (`Base`, `Elevated`, `Surface`) to establish spatial hierarchy without relying on heavy shadows.
- **The Gold Standard:** `Accent Gold` is reserved for primary actions, success states of high importance, and "Golden Signals"—the most critical data points in a dashboard.
- **Tactical Violet:** `Accent Violet` serves as a secondary identifier for interactive elements, specialized data categories, or AI-driven insights.
- **Semantic Signals:** Standardized colors for risk, warning, and health are saturated to ensure they "pop" against the dark background, demanding immediate attention.

## Typography

This design system employs a dual-font strategy to balance readability with a technical aesthetic.

- **JetBrains Mono** is utilized for headlines, labels, and all data-driven values. Its monospaced nature ensures that columns of numbers align perfectly in tables and dashboards, facilitating easier comparison.
- **Inter** is used for all body copy and long-form descriptions. It provides a clean, neutral balance to the more opinionated monospaced font, ensuring high legibility at smaller scales.

**Formatting Note:** Use uppercase sparingly for `label-sm` to create a sense of categorization and "metadata" headers. For mobile displays, `headline-lg` should scale down to 24px to maintain layout integrity.

## Layout & Spacing

The layout philosophy is built on a **Strict Grid System** that prioritizes information density. 

- **Grid:** Use a 12-column fluid grid for dashboard layouts. On desktop, sidebars are fixed at 240px, while the main content area expands to fill the viewport.
- **Rhythm:** An 8px base unit (with a 4px half-step for tight UI components) governs all padding and margins. 
- **Density:** In "Analysis Mode," internal padding for cards and tables should be reduced to `sm` (8px) to allow more data to fit on-screen. In "Review Mode," use `md` (16px) for increased whitespace.
- **Breakpoints:** 
  - Mobile (<768px): 4-column grid, 16px margins.
  - Tablet (768px - 1280px): 8-column grid, 24px margins.
  - Desktop (>1280px): 12-column grid, 24px margins.

## Elevation & Depth

The design system eschews traditional shadows in favor of **Tonal Layering** and **Low-Contrast Outlines**. Depth is communicated through color luminance rather than faux-lighting.

- **Level 0 (Base):** #0A0A0A (Global Background).
- **Level 1 (Elevated):** #121212 (Sidebars, secondary panels).
- **Level 2 (Surface):** #18181B (Primary content cards, modals).
- **Level 3 (Overlay):** #18181B with a 1px #27272A border (Active states, dropdowns).

**Borders:** Every interactive surface or container must have a 1px solid border (#27272A). This creates a "blueprint" look that feels engineered and structural. Use a subtle gold top-border (2px) on cards that contain critical intelligence alerts.

## Shapes

The shape language is "Soft-Technical." Elements use a **0.25rem (4px)** base radius. This minimal rounding provides just enough modern refinement to prevent the UI from feeling dated or harsh, while maintaining the structural rigor required for a data-heavy application.

- **Standard Elements:** 4px (Inputs, Cards, Buttons).
- **Large Elements:** 8px (Modals, Large Dashboard Widgets).
- **Pill:** Reserved exclusively for Status Chips (e.g., "Active," "Risk") to distinguish them from actionable buttons.

## Components

- **Buttons:** 
  - *Primary:* Solid #E6D3A3 background with #0A0A0A text.
  - *Secondary:* 1px border (#E6D3A3) with transparent background and #E6D3A3 text.
  - *Ghost:* No border, #A1A1AA text, shifts to #F5F5F5 on hover.
- **Input Fields:** #121212 background, 1px #27272A border. On focus, the border transitions to #E6D3A3 with a subtle outer glow of the same color (0 0 0 2px).
- **Cards:** Use the #18181B Surface color. Title bars should be separated by a 1px border. For "High Risk" cards, use a left-edge accent stripe in #EF4444.
- **Data Tables:** Zebra striping is not used. Instead, use thin 1px horizontal dividers (#27272A). Row hover state should use #121212. All numerical data must use `data-mono` typography.
- **Chips:** Small, uppercase `label-sm` text. Use low-opacity background tints of signal colors (e.g., Risk Chip: #EF4444 at 10% opacity with #EF4444 text).
- **Intelligence Badges:** Small circular indicators in the top right of cards using #7C3AED to denote AI-generated or "Smart" insights.