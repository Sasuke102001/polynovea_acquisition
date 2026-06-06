# POLYNOVEA ACQUISITION PLATFORM — DESIGN SYSTEM

## Visual Direction: Cinematic Intelligence

The interface feels like a premium intelligence terminal with cinematic spatial depth.
Think: Bloomberg Terminal × Christopher Nolan production design.
Controlled, dimensional, premium. NOT sci-fi neon. NOT cheap glassmorphism.

---

## Color Palette

### Backgrounds (layered depth)
- Primary Background: #0A0A0A (deep black canvas)
- Secondary Background: #121212 (slightly elevated layer)
- Card Surface: #18181B (soft graphite — cards, panels, drawers)
- Border: #27272A (muted slate — subtle separation)

### Typography
- Primary Text: #F5F5F5 (soft white)
- Secondary Text: #A1A1AA (muted gray — labels, metadata)
- Disabled Text: #71717A (neutral gray)

### Accent Colors
- Authority Accent: #E6D3A3 (Champagne Gold — headings, key numbers, active states)
- Secondary Gold: #9A8F6A (Muted Gold — secondary emphasis)
- Intelligence Accent: #7C3AED (Deep Violet — used sparingly: graph highlights, score indicators, system callouts)

### Functional Signals
- Positive: #10B981 (emerald green — high scores, good signals)
- Warning: #F59E0B (amber — medium signals, watch items)
- Critical: #FB7185 (coral red — low scores, risk signals)

---

## Typography

- Headings: Clash Display — intentional, strong, premium weight
- Body / Labels: Inter — readable, clean, structured
- Data / Monospace: JetBrains Mono — scores, IDs, metrics

### Hierarchy Rules
- Page titles: Clash Display, 28–36px, #E6D3A3 (gold)
- Section headers: Clash Display, 18–22px, #F5F5F5
- Body text: Inter, 14–16px, #A1A1AA
- Score numbers: JetBrains Mono, bold, #F5F5F5 or color-coded
- Labels / badges: Inter, 11–12px, uppercase, letter-spaced

---

## 3D Cinematic Depth System

### Layering Philosophy
Surfaces exist at distinct Z-levels. Each layer is visually separated by:
- subtle box-shadow using deep black (not colored shadows)
- slight background color elevation (#0A0A0A → #121212 → #18181B)
- thin #27272A borders at layer transitions

### Card Design
- Background: #18181B
- Border: 1px solid #27272A
- Corner radius: 12px
- Shadow: 0 8px 32px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.04) inset
- On hover: border shifts to #E6D3A3 at 30% opacity, subtle lift effect

### Score Rings / Radial Charts
- Background track: #27272A
- Active arc: gradient from #E6D3A3 to #9A8F6A (gold range) or #7C3AED (intelligence signal)
- Center number: JetBrains Mono, large, #F5F5F5
- Label below: Inter, 11px, #A1A1AA uppercase

### Tables & Data Grids
- Row background: alternating #0A0A0A / #121212
- Header: #18181B with #27272A bottom border
- Active row: left border 2px #E6D3A3, background #18181B
- Text: #F5F5F5 primary, #A1A1AA secondary

### Navigation
- Sidebar/Tab bar background: #0A0A0A
- Active tab: #E6D3A3 text + 2px bottom/left border #E6D3A3
- Inactive tab: #71717A text, hover #A1A1AA
- Tab icons: minimal, single-weight

---

## Layout Structure

### Page Layout
- Left sidebar navigation: 64px wide, icon-only with tooltips
- Top header: venue name (Clash Display, gold), area + city (Inter, muted gray), score summary chips
- Content area: full bleed, dark canvas
- Tab navigation: horizontal below header, flush left

### Spacing
- Section padding: 24px
- Card gap: 16px
- Content max-width: 1280px
- Mobile: single column, bottom tab bar

### Cinematic Focal Point Rule
Each screen has ONE primary focal element that commands visual weight:
- Overview: the fitness score radial cluster
- Audience: the segment distribution arc
- Marketing: the channel priority ranking
- Competitors: the threat radar
- Transform: the opportunity matrix
- Campaign: the active campaign timeline
- Deep Analysis: the council debate view
- Demo: the conversation thread

---

## Component Patterns

### Fitness Score Badge
- Circular ring, 80px diameter
- Arc fill based on score (0–1 → 0–360°)
- Score in center: JetBrains Mono bold
- Label below: Inter 11px uppercase
- Color: ≥0.6 emerald, 0.4–0.6 amber, <0.4 coral

### Segment Tag
- Pill shape, 6px radius
- Background: #18181B border #27272A
- Primary segment: gold text + gold border at 40%
- Secondary: muted gray

### Channel Card
- Full-width card, #18181B
- Left accent bar: 3px, color-coded by priority
- Header: channel name in Clash Display
- Sub: audience match percentage
- Right: priority badge (HIGH/MEDIUM/LOW)

### Competitor Row
- Horizontal card, subtle divider
- Left: venue name + type badge
- Center: similarity score bar (violet gradient)
- Right: threat level indicator

### Chat Interface (Demo)
- Full screen dark canvas
- Message bubbles: user right (#18181B + gold border), AI left (#121212)
- CTA line: gold italic, centered, padded
- Input: #18181B, gold focus ring, send icon

---

## What This Interface Must NEVER Do
- No cheap glassmorphism (blurred frosted panels)
- No neon glow effects
- No rainbow gradients
- No excessive animation or particle effects
- No startup-generic blue/white color scheme
- No clutter — every element earns its place
- No oversized decorative icons

## What It Must Always Do
- Preserve hierarchy — the eye should always know where to look first
- Preserve restraint — gold is used for emphasis, not decoration
- Preserve depth — layers should feel physically stacked, not flat
- Preserve intelligence — the interface communicates operational credibility
