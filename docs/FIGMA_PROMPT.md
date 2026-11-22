# Figma Design Prompt — AI Resume Assistant (Premium SaaS Edition)

## Project Overview

An AI-powered resume analysis web app built with Streamlit (Python). Users paste their resume (or upload a PDF), optionally add a job description for ATS matching, and receive:

1. A **deterministic rubric score** (0-100) with weighted category breakdown
2. **AI-generated qualitative feedback** (summary, strengths, weaknesses, improvements)
3. **ATS keyword gap analysis** (matched vs missing keywords vs job description)
4. Interactive **charts** (gauge + radar)
5. **Download buttons** (PDF report + debug logs)

The current UI is functional but bland — standard Streamlit components with minimal custom CSS. The goal is not just a "nice dashboard" but a **premium, immersive AI workspace** — think Linear meets Vercel meets Notion. A design that feels expensive, layered, and responsive, making users say "wow" on first use and keeping them coming back.

---

## Design System (Upgraded Premium)

### Color Palette

| Token | Current (bland) | Upgraded (premium) | Purpose |
|-------|-----------------|-------------------|---------|
| Accent/Primary | `#3b82f6` (standard blue) | `linear-gradient(to right, #6366f1, #06b6d4)` (Indigo → Cyan) | "AI premium" feel for buttons, active states, primary actions |
| Glow effect | none | `box-shadow: 0 0 20px rgba(6, 182, 212, 0.3)` | Active input rings, highest score cards, hover states |
| Background | `#0f172a` (solid) | `#0a0f1d` (deeper navy) | Base canvas for the immersive dark mode |
| Surface | `#1e293b` (solid) | `rgba(30, 41, 59, 0.7) + backdrop-filter: blur(12px)` | Glassmorphism frosted cards that create depth |
| Card border | `#334155` (solid) | `rgba(255, 255, 255, 0.08)` (inner border) | High-end SaaS crisp edge (Linear/Vercel trick) |
| Danger | `#ef4444` (red) | `#f43f5e` (rose) | Pinker, modern, easier on the eyes in dark mode |
| Success | `#22c55e` (green) | `#10b981` (emerald) | Cooler, digital-green matching cyan accents |
| Warning | `#f59e0b` (amber) | `#f59e0b` (same) | Keep — already works well |
| Text primary | `#f1f5f9` | `#f8fafc` (brighter) | Better readability against darker backgrounds |
| Text secondary | `#94a3b8` | `#64748b` (slightly dimmer) | Better hierarchy contrast |

### Glassmorphism Specification
- **Nav bar & Sidebar:** `background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(16px); border-bottom: 1px solid rgba(255, 255, 255, 0.06);`
- **Cards:** `background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.06);`
- **Effect when scrolling:** Content behind the nav bar blurs through — creates a sense of depth and layering

### Glow Effects
- **Score gauge background:** Soft radial gradient glow behind the chart — `radial-gradient(ellipse at center, rgba(6, 182, 212, 0.15), transparent 60%)`
- **High scores (≥90):** Subtle golden glow ring `box-shadow: 0 0 30px rgba(250, 204, 21, 0.2)`
- **Primary button hover:** `box-shadow: 0 0 25px rgba(6, 182, 212, 0.4)`
- **Active input focus:** `box-shadow: 0 0 15px rgba(99, 102, 241, 0.3)`

### Typography
- **Headings & Score Numbers:** `Space Grotesk` or `Clash Display` — geometric, bold, high-impact for the 83/100 score display
- **Body text:** `Inter` (regular weight, 1.6 line-height) — proven readability
- **Monospace / Tags:** `JetBrains Mono` (keyword pills, code references)
- **Scale:** 11 / 13 / 14 / 16 / 18 / 24 / 32 / 48 / 64 px
- **Score numbers (hero):** 64px, bold, tight letter-spacing -0.02em

### Border Radius
- Cards: `16px`
- Buttons/inputs: `10px`
- Tags/badges: `6px`
- Modal/dialog: `20px`

### Shadows
- Card (light mode): `0 4px 24px rgba(0,0,0,0.08)`
- Card (dark mode): `0 4px 24px rgba(0,0,0,0.4)`
- Elevated: `0 8px 40px rgba(0,0,0,0.5)`
- Button hover: `0 4px 20px rgba(6, 182, 212, 0.4)`
- Inner glow (cards): `inset 0 1px 0 rgba(255, 255, 255, 0.06)`

### Icons
- Lucide or Phosphor icon set — consistent 20px outlined
- Navigation icons: 24px

---

## Layout & Pages

### 1. Global Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Top Navigation Bar (fixed, 64px) — glassmorphism                    │
│  ┌─────┐  ┌──────────────────────┐  ┌────────────────────────────┐  │
│  │Logo │  │ Page Title           │  │ Theme toggle · Avatar · ⋮  │  │
│  │ 32px│  │ (breadcrumb style)   │  │ (glassmorphism bg)        │  │
│  └─────┘  └──────────────────────┘  └────────────────────────────┘  │
│  [⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜]  ← 1px border-bottom, translucent           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────┐  ┌──────────────────────────────────────────────┐  │
│  │            │  │                                              │  │
│  │ Sidebar    │  │  Main Content Area                           │  │
│  │ (300px)    │  │                                              │  │
│  │ glassmorph │  │  (scrollable, max-width 1200px, centered)    │  │
│  │            │  │                                              │  │
│  │ • Mode     │  │  Background: #0a0f1d with subtle mesh/grain  │  │
│  │   selector │  │                                              │  │
│  │ • Upload   │  │                                              │  │
│  │ • Textarea │  │                                              │  │
│  │ • Analyze  │  │                                              │  │
│  │            │  │                                              │  │
│  └────────────┘  └──────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Top Navigation Bar (glassmorphism):**
- Fixed position, 64px height, full width
- `background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(16px);`
- Bottom border: `1px solid rgba(255, 255, 255, 0.06)`
- Left: Logo mark (32×32 rounded gradient icon) + "ResumeAI" bold in Space Grotesk
- Center: Page title with breadcrumb style (faint `/` separator)
- Right: Theme toggle (sun/moon icon swap) + avatar circle (36px) + overflow menu (⋯)
- Content below blurs through as user scrolls

**Left Sidebar (300px, glassmorphism):**
- Fixed position, full height minus nav bar
- `background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px);`
- Right border: `1px solid rgba(255, 255, 255, 0.06)`
- Contains the **input area** — always visible while scrolling results

**Main Content Area:**
- Background: `#0a0f1d` (deeper navy than sidebar)
- Optional subtle noise/grain texture overlay (very faint, 3% opacity)
- Max-width 1200px, centered with auto margins
- Smooth scroll behavior

---

### 2. Input Section (Sidebar)

```
┌────────────────────────────────┐
│  Sidebar (300px)               │
│  ─────────────────              │
│                                │
│  ● Resume Analysis             │  ← pill toggle, selected gradient
│  ○ ATS Job Match               │  ← outline style, unselected
│                                │
│  ┌──────────────────────────┐  │
│  │  📄 Upload Resume (PDF)  │  │  ← dashed border, glass bg
│  │  ┌──────────────────┐    │  │
│  │  │  ☁️ Upload       │    │  │  ← centroid icon, 48px
│  │  │ Drag & drop or   │    │  │
│  │  │ click to browse   │    │  │
│  │  │ Max 10MB · PDF   │    │  │
│  │  └──────────────────┘    │  │
│  │                          │  │
│  │  — or —                  │  │
│  │                          │  │
│  │  ┌──────────────────┐    │  │
│  │  │ Paste your resume │    │  │  ← glass bg, focus glow
│  │  │ here...           │    │  │
│  │  └──────────────────┘    │  │
│  └──────────────────────────┘  │
│                                │
│  ┌──────────────────────────┐  │
│  │  Job Description (ATS)   │  │  ← appears when ATS selected
│  │  ┌──────────────────┐    │  │
│  │  │ Paste job desc... │    │  │
│  │  └──────────────────┘    │  │
│  └──────────────────────────┘  │
│                                │
│  ┌──────────────────────────┐  │
│  │  🚀 Analyze Resume       │  │  ← gradient btn, full width, glow
│  └──────────────────────────┘  │
│                                │
│  Settings ⚙  ·  Help ?  · v1.2│
└────────────────────────────────┘
```

**Mode toggle:**
- Two pill buttons side by side, equal width
- **Selected:** `background: linear-gradient(to right, #6366f1, #06b6d4);` white text, subtle glow
- **Unselected:** `background: transparent; border: 1px solid rgba(255,255,255,0.12);` text `#94a3b8`
- Smooth slide transition on switch (0.3s ease)
- Hover unselected: border brightens to `rgba(255,255,255,0.25)`

**File upload zone:**
- Dashed border (2px, `rgba(255,255,255,0.12)`)
- Background: `rgba(30, 41, 59, 0.3)`
- Upload icon (48px, `#64748b`)
- Text: "Drag & drop or click to browse" + "Max 10MB · PDF" in small gray
- **Drag-over state:** Background pulses to `rgba(6, 182, 212, 0.1)`, border turns cyan
- Hover: subtle background brightening
- After file selected: shows filename with green checkmark, small "×" remove button

**Text areas:**
- Background: `rgba(30, 41, 59, 0.4)`
- Text: `#e2e8f0`, placeholder: `#475569`
- Border: `1px solid rgba(255,255,255,0.08)`
- Focus: border turns `#6366f1` + `box-shadow: 0 0 15px rgba(99, 102, 241, 0.3)`
- Rounded: `10px`
- Min height: 140px (resume), 100px (job description)

**Analyze Button:**
- Full width, 52px height
- `background: linear-gradient(to right, #6366f1, #06b6d4);`
- White text, bold 600, 16px
- Border-radius: 10px
- `box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);`
- Hover: `transform: translateY(-1px); box-shadow: 0 6px 25px rgba(6, 182, 212, 0.4);`
- Loading state: spinner animation replaces icon, button text changes to "Analyzing..."
- Disabled state: opacity 0.5, no hover effects

**Sidebar footer:**
- Small text `#475569`, 12px
- Separator line above

---

### 3. Results Dashboard (Main Content Area)

```
┌───────────────────────────────────────────────────────────────────────┐
│  ✅ Resume analysis complete     [Just now]    [Share] [Download] [⋮] │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│  │ ██████████ │ │ ██████████ │ │ ██████████ │ │ ██████████ │        │
│  │ OVERALL    │ │ ATS MATCH  │ │ FORMATTING │ │ACHIEVEMENTS│        │
│  │   SCORE    │ │            │ │            │ │            │        │
│  │     83     │ │    100     │ │     70     │ │     60     │        │
│  │   / 100    │ │   / 100    │ │   / 100    │ │   / 100    │        │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │
│                                                                        │
│  ┌─────────────────────────┐  ┌─────────────────────────┐            │
│  │    ╭──────╮             │  │        ╱╲              │            │
│  │   ╱  83   ╲    glow     │  │       ╱  ╲  Formatting │            │
│  │  │  /100  │  radial bg  │  │      ╱    ╲            │            │
│  │   ╲      ╱             │  │     ╱      ╲ ATS Match │            │
│  │    ╰──────╯             │  │    ╱────────╲          │            │
│  │    Score Gauge          │  │   ╱  Radar   ╲         │            │
│  │                         │  │  ╱   Chart    ╲        │            │
│  └─────────────────────────┘  └─────────────────────────┘            │
│                                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐│
│  │  ▼ Rubric Scoring (deterministic — weighted criteria)             ││
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   ││
│  │  │Format│ │ATS   │ │Experi│ │Achiev│ │Skills│                   ││
│  │  │ 7/10 │ │ 10/10 │ │ 9/10 │ │ 6/10 │ │ 8/10 │                   ││
│  │  │ 15%  │ │ 20%  │ │ 25%  │ │ 20%  │ │ 20%  │                   ││
│  │  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘                   ││
│  │                                                                   ││
│  │  Resume Statistics:                                               ││
│  │  [Word: 641] [Bullets: 15] [Measurable: 3] [Years: 4]           ││
│  │  Sections: experience, education, skills, projects                ││
│  │                                                                   ││
│  │  Rubric Notes:  • Strong section structure ...                   ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐│
│  │  📌 Summary                                                       ││
│  │  "Junior IT support candidate with recent development..."         ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ┌──────────────────────────┐  ┌──────────────────────────┐           │
│  │  💪 Strengths            │  │  ⚠️ Weaknesses           │           │
│  │  ─── green left bar ───  │  │  ─── amber left bar ───  │           │
│  │  • Excellent technical   │  │  • Limited direct exp    │           │
│  │  • Demonstrated problem  │  │  • No documented hw...   │           │
│  │  • Strong collaboration  │  │  • Lacks specific...     │           │
│  └──────────────────────────┘  └──────────────────────────┘           │
│                                                                        │
│  ┌───────────────────────────────────────────────────────────────────┐│
│  │  🚀 Improvements                                                  ││
│  │  ─── blue left bar ────                                           ││
│  │  • Emphasize transferable debugging skills                        ││
│  │  • Highlight any hardware interaction experience                  ││
│  │  • Consider obtaining CompTIA A+ or Microsoft Fundamentals        ││
│  └───────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ──────────────────── ATS Keyword Gap Analysis ────────────────────   │
│                                                                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                       │
│  │ Keyword    │ │  Matched   │ │  Missing    │                       │
│  │ Coverage   │ │  Keywords  │ │  Keywords   │                       │
│  │   1.1%     │ │     1      │ │     90      │                       │
│  └────────────┘ └────────────┘ └────────────┘                       │
│                                                                        │
│  🔴 Critical Missing                                                  │
│  [⚠ audio] [⚠ basics] [⚠ computer] [⚠ conference] [⚠ desktop]       │
│  [⚠ engineer] [⚠ hardware] [⚠ install] [⚠ network] [⚠ room]          │
│                                                                        │
│  🟡 Other Missing                                                     │
│  [ccna] [desk help] [desktop network] [engineer basics] [...]         │
│                                                                        │
│  ✅ Matched Keywords                                                   │
│  [✓ support]                                                           │
│                                                                        │
│  💡 Tip: Aim for at least 60% keyword coverage. Current: 1.1%         │
│                                                                        │
│  ───────────────────────────────────────────────────────────────────── │
│  [📥 Download PDF Report]          [📋 Download Debug Logs]           │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

**Score Cards Row (4 cards — glassmorphism):**
- Each card: `background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(8px); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px;`
- Top accent bar (4px): green (≥70), amber (40-69), rose (<40)
- Hero number: 64px, Space Grotesk, bold, line-height 1
- Label: uppercase, 11px, letter-spacing 1.5px, `#64748b`
- "/100" label: 14px, `#475569`
- Hover: `transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.3);`
- Transition: all 0.2s ease

**Charts Row (2 columns, equal width):**
- **Left: Score Gauge** — Semi-circular, 0-100 scale
  - Background behind gauge: `radial-gradient(ellipse at center, rgba(6, 182, 212, 0.1), transparent 70%)`
  - Color zones: rose (0-40) → amber (40-70) → emerald (70-100)
  - Needle: white, thin
  - Number in center: Space Grotesk
  - Plotly transparent background to let card glassmorphism show through

- **Right: Radar Chart** — 5-axis polygon
  - Fill: `rgba(99, 102, 241, 0.25)`, border: `#6366f1` (2px)
  - Axis labels on white/gray
  - Plotly transparent background

**Rubric Scoring (expandable section):**
- Glass card with ▼ chevron toggle, default expanded
- 5 compact metric pills in a row
- Statistics row: 4 inline metrics with small labels
- Bullet list: each note with `•` bullet, `#94a3b8` color

**Summary Box:**
- Full-width glass card with 4px left accent border (`#64748b`)
- Text: 16px, line-height 1.7, `#e2e8f0`
- Subtle gradient background

**Feedback Cards (side by side or stacked on mobile):**
- **Strengths (💪):** Left border `#10b981`, background `rgba(16, 185, 129, 0.08)`
- **Weaknesses (⚠️):** Left border `#f59e0b`, background `rgba(245, 158, 11, 0.08)`
- **Improvements (🚀):** Left border `#6366f1`, background `rgba(99, 102, 241, 0.08)`
- Each card: border-radius 12px, padding 20px, 4-6 bullet items
- Bullet text: 14px, `#cbd5e1`

**ATS Keyword Gap Analysis (conditional):**
- 3 metric cards row: Coverage % (color-coded), Matched count (emerald), Missing count (rose)
- **Critical missing:** `background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.2);` with ⚠ icon
- **Other missing:** `background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2);`
- **Matched:** `background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);` with ✓ icon
- Keywords displayed as **inline pill tags** — not bullet list (see component section)
- Hover on tags: `transform: translateY(-2px)` — makes data feel interactive
- Tip box: `background: rgba(99, 102, 241, 0.08); border-left: 4px solid #6366f1;` with 💡 icon

**Download Buttons Row:**
- Two buttons side by side at the bottom of results
- Primary: "📥 Download PDF Report" — gradient Indigo→Cyan, full glow
- Secondary: "📋 Download Debug Logs" — outlined style, 1px `rgba(255,255,255,0.12)` border
- Both: 48px height, 14px font, rounded 10px

---

### 4. States

**Empty State (before first analysis):**
- Centered layout in main content area
- Large illustration or icon (128px) — abstract document/magnifying glass
- Headline: "Ready to level up your resume?"
- Subtext: "Paste your resume in the sidebar, choose your mode, and get AI-powered feedback in seconds."
- Three suggestion cards below:
  - "📄 Quick Resume Scan" — paste a short resume
  - "🎯 ATS Match Check" — compare against a job description
  - "💡 See an Example" — load sample resume data
- Cards are glassmorphism, hover lifts slightly

**Loading State (during analysis):**
- **Skeleton loaders** instead of text spinner:
  - 4 pulsing skeleton blocks where score cards will appear
  - 2 pulsing skeleton blocks where charts will appear
  - Progress bar with indeterminate animation (gradient sweep)
  - Status text below: "🧠 Building knowledge index..." / "🤖 Analyzing resume..."
  - Status updates animate in sequence (fade in/out)
- Sidebar remains visible but Analyze button shows spinner + disabled state
- Top bar shows subtle loading indicator

**Success State:**
- Green checkmark banner at top: `background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);`
- "✅ Resume analysis complete" + relative timestamp
- All results animate into view with staggered entrance (cards first, then charts, then feedback)

**Error State:**
- Red rose banner: `background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.2);`
- "❌ Analysis failed" + concise error description
- Expandable accordion: "📋 Technical Details" with model status breakdown
- "Try Again" button that scrolls back to sidebar input
- Model status shown in a table: model name | status icon | error message

**Mobile / Narrow Screen (<768px):**
- Sidebar collapses to full-width section at top
- Score cards stack 2×2
- Charts stack vertically
- Feedback cards stack vertically (full width)
- Keyword tags wrap naturally
- Top nav bar becomes simpler (just logo + theme toggle)

---

### 5. Animations & Micro-interactions

| Element | Animation | Duration | Trigger |
|---------|-----------|----------|---------|
| Score cards | Fade in + slide up, staggered (100ms delay per card) | 0.4s | Page load / analysis complete |
| Hero numbers | Count-up from 0 to final value with `st.empty()` loop | 0.6s | After cards rendered |
| Charts | Draw animation (gauge needle sweeps in, radar polygon traces) | 0.8s | After cards settle |
| Mode switch | Slide translateX with opacity crossfade | 0.3s | On toggle click |
| Upload zone | Background pulse to cyan + border color change | 0.2s | On drag-over |
| Keyword tags | Scale-in from 0.8 to 1.0, staggered (30ms delay) | 0.2s | On section render |
| Tag hover | `translateY(-2px)` + shadow increase | 0.15s | On mouse hover |
| Analyze button | Loading spinner replaces icon, button text changes | instant | On click |
| Score card hover | `translateY(-3px)` + shadow deepens | 0.2s | On mouse hover |
| Scrollbar | Thin (`6px`), dark (`#334155` thumb, transparent track) | — | Always visible |
| Error accordion | Smooth height expansion | 0.3s | On click |

**All animations use `transition: all 0.2s ease`** or specific CSS `@keyframes` for more complex sequences.

**Count-up score pseudo-implementation (Streamlit-compatible):**
```python
# In app.py when rendering the score:
placeholder = st.empty()
for i in range(0, rubric_score + 1, max(1, rubric_score // 10)):
    placeholder.metric("Overall Score", f"{i}/100")
    time.sleep(0.02)
placeholder.metric("Overall Score", f"{rubric_score}/100")
```

---

### 6. Specific Components

**Keyword Tag Component:**
```
[✓ support]    → bg: rgba(16,185,129,0.12), border: rgba(16,185,129,0.3), text: #10b981
[⚠ network]   → bg: rgba(244,63,94,0.12),  border: rgba(244,63,94,0.3),  text: #f43f5e
[admin]        → bg: rgba(245,158,11,0.12), border: rgba(245,158,11,0.3), text: #f59e0b
```
- `display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 6px; font-size: 13px;`
- Icon (✓ or ⚠) 14px, margin-right 4px
- Margin: 3px around each tag
- Smooth wrap onto next line
- Hover: `transform: translateY(-2px); cursor: default;`

**Score Card Component:**
```
┌──────────────────────┐
│ ▄▄▄▄▄▄▄▄▄▄           │  ← 4px top accent bar
│ ATS MATCH            │  ← 11px uppercase
│                      │
│     100              │  ← 64px Space Grotesk bold
│   / 100              │  ← 14px gray
└──────────────────────┘
```
- Width: 25% (flex: 1)
- Padding: 24px 16px 20px
- Glass background, border-radius 16px
- Top bar: border-top: 4px solid [scoreColor]

**Rubric Metric Pill:**
```
┌───────────────────┐
│  ATS Readiness    │
│     10/10         │
│      20%          │
└───────────────────┘
```
- Compact, ~18% width, centered text
- Category name: 12px, `#94a3b8`
- Score: 24px, bold, `#f8fafc`
- Weight: 11px, `#475569`

**Feedback Card Component:**
```
┌──────────────────────────────────────────────────┐
│ ▌ 💪 Strengths                                   │  ← 4px left bar
│ ▌                                                 │     + icon + title
│ ▌ • Excellent technical skills...                │
│ ▌ • Demonstrated problem-solving...              │
│ ▌ • Strong collaboration in team environments     │
└──────────────────────────────────────────────────┘
```
- Left bar: 4px, colored by type (green/amber/blue)
- Title: 16px bold, colored to match bar
- List items: 14px, `#cbd5e1`, line-height 1.6
- Spacing between items: 6px

**Skeleton Loader Component:**
```
┌──────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     │  ← pulsing gradient
│ ▓▓▓▓▓▓▓▓▓           │     animation: shimmer
│    ▓▓▓▓▓             │     -translateX bg sweep
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    │
└──────────────────────┘
```
- Background: `linear-gradient(90deg, rgba(30,41,59,0.5) 25%, rgba(30,41,59,0.8) 50%, rgba(30,41,59,0.5) 75%);`
- `background-size: 200% 100%; animation: shimmer 1.5s infinite;`
- Border-radius: inherit from parent card

---

### 7. Light Mode Variant

- Background: `#f8fafc`
- Surface: white with `rgba(0,0,0,0.06)` border
- Cards: white, `box-shadow: 0 1px 3px rgba(0,0,0,0.06)`
- Text primary: `#0f172a`
- Text secondary: `#64748b`
- Same glassmorphism effect but with white translucent backgrounds
- Theme toggle (moon/sun icon) in top nav bar
- CSS variable swap on `[data-theme="dark"]` / `[data-theme="light"]`

---

## Technical Constraints for Implementation

1. **Must be implementable in Streamlit HTML/CSS** — no React, no JS frameworks
2. CSS is injected via `st.markdown("<style>...</style>", unsafe_allow_html=True)`
3. **Streamlit targeting:** Use attribute selectors for reliable styling:
   - `[data-testid="stSidebar"]` for sidebar
   - `[data-testid="stHeader"]` for top bar
   - `[data-testid="stMetricValue"]` for metric values
4. **Plotly charts:** Must set `paper_bgcolor="rgba(0,0,0,0)"` and `plot_bgcolor="rgba(0,0,0,0)"` to let glassmorphism show through
5. **Dark/light mode:** Toggle via `<script>` setting `document.documentElement.setAttribute('data-theme', 'dark')` on button click, CSS uses `.feedback-card { background: var(--card-bg); }`
6. **Fonts:** Import Space Grotesk + Inter via `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');`
7. **Skeleton loaders:** Pure CSS `@keyframes shimmer` — no JS needed
8. **Animations:** All CSS `@keyframes` and `transition` — no animation libraries
9. **Responsive:** Use `@media (max-width: 768px)` breakpoints for mobile layout
10. **No external dependencies** beyond Streamlit + Plotly + standard libraries

---

## Deliverables Needed from Figma

1. **Figma prototype** with these screens:
   - Empty state (home page before analysis)
   - Resume Analysis results (full scroll)
   - ATS Job Match results (with keyword tags)
   - Loading state (skeleton loaders)
   - Error state
   - Mobile responsive view (all states)

2. **Component library** including:
   - ScoreCard (4 variants: emerald/amber/rose by score)
   - KeywordTag (3 variants: matched/critical/other)
   - FeedbackCard (3 variants: strengths/weaknesses/improvements)
   - RubricMetricPill
   - GaugeChart (in context with glow background)
   - RadarChart (in context with transparent bg)
   - UploadZone (empty + filled states)
   - Glassmorphism TextArea (focus + idle states)
   - GradientButton (idle + hover + loading states)
   - SkeletonLoader (4 variants: card/chart/text/tag)

3. **CSS tokens export** as CSS custom properties for direct implementation:
   ```css
   :root {
     --color-bg: #0a0f1d;
     --color-surface: rgba(30, 41, 59, 0.6);
     --color-accent-gradient: linear-gradient(to right, #6366f1, #06b6d4);
     --color-glow: rgba(6, 182, 212, 0.3);
     --color-success: #10b981;
     --color-danger: #f43f5e;
     --glass-blur: blur(12px);
     --card-border: 1px solid rgba(255, 255, 255, 0.06);
     --font-heading: 'Space Grotesk', sans-serif;
     --font-body: 'Inter', sans-serif;
   }
   ```

---

## Inspiration & References

- **Linear** — dark mode glassmorphism, tag components, inner border trick
- **Vercel** — score/metric card design, spacing, typography contrast
- **Notion** — clean card layouts, subtle dividers, whitespace management
- **Resumatic** — resume analysis layout patterns
- **Tailwind UI** — component structure and design token organization
- **Arc Browser** — glassmorphism navigation, frosted glass effects
- **Raycast** — premium dark mode, micro-interactions, keyboard-friendly feel

---

## Goal

Transform from a functional data-processing script into a **premium, monetizable web product** that feels expensive, responsive, and delightful. Users should feel the quality the moment they paste their resume — before they even click Analyze.