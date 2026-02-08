---
description: AlphaPulse Frontend Style Guide - Dark Trading Theme
---

# AlphaPulse Frontend Style Guide

This guide defines the visual language and component styles for the AlphaPulse trading platform, based on the `test3.html` reference.

## 1. Color Palette

The theme implements a dark, data-heavy interface optimized for trading.

### CSS Variables
These should be defined in `index.css`:

```css
:root {
  --bg-main: #0f172a;  /* Slate 900 - Main Background */
  --bg-card: #1e293b;  /* Slate 800 - Card/Panel Background */
  --accent: #3b82f6;   /* Blue 500 - Primary Action/Highlight */
  --long: #10b981;     /* Emerald 500 - Long/Profit */
  --short: #ef4444;    /* Red 500 - Short/Loss */
  --wait: #f59e0b;     /* Amber 500 - Warning/Pending */
  --text-main: #e2e8f0; /* Slate 200 - Primary Text */
  --text-muted: #94a3b8; /* Slate 400 - Secondary Text */
}
```

### Tailwind Equivalents
- **Background**: `bg-slate-900` (Main), `bg-slate-800` (Card)
- **Text**: `text-slate-200` (Primary), `text-slate-400` (Secondary)
- **Status**: `text-green-400`/`bg-green-500` (Long), `text-red-400`/`bg-red-500` (Short)

## 2. Typography

- **Font Family**: 'Inter', sans-serif
- **Headings**: Bold, Slate 300/400
- **Monospace**: For numerical data, IDs, and code blocks

## 3. UI Components

### Signal Card
Used in the sidebar list of signals.

- **Base**: `p-4 rounded bg-slate-800 border-l-4 border-transparent transition-all`
- **Hover**: `hover:bg-slate-700 cursor-pointer`
- **Active**: `bg-[#26344a] border-l-blue-500`

### Badges
Small status indicators.

- **Base**: `px-2 py-0.5 rounded text-[0.7rem] font-bold uppercase border`
- **Long**: `bg-green-500/20 text-green-400 border-green-500`
- **Short**: `bg-red-500/20 text-red-400 border-red-500`
- **Risk Low**: `bg-green-500/10 text-green-400 border-transparent`
- **Risk Med**: `bg-amber-500/10 text-amber-500 border-transparent`
- **Risk High**: `bg-red-500/10 text-red-500 border-transparent opacity-80 decoration-line-through`

### Timeline
Vertical progress tracking for signals.

- **Container**: `pl-5 pb-5 border-l-2 border-slate-700 relative last:border-l-0`
- **Dot**: `absolute -left-[6px] top-0 w-2.5 h-2.5 rounded-full`
  - *Active/Profit*: `bg-green-500 shadow-[0_0_8px_var(--long)]`
  - *Loss*: `bg-red-500 shadow-[0_0_8px_var(--short)]`
  - *Pending*: `bg-slate-500`

## 4. Layout Structure

- **Sidebar**: `w-1/3 min-w-[350px] bg-slate-900 border-r border-slate-700`
- **Main Panel**: `flex-1 bg-slate-900 flex flex-col`
- **Header**: `p-6 border-b border-slate-700 bg-slate-800/30`
- **Content Area**: Split view or full width, `bg-slate-900` or `bg-[#282c34]` for code panels.

## 5. Scrollbars
Custom "Scroll Hide" style for cleaner look.

```css
.scroll-hide::-webkit-scrollbar { width: 4px; }
.scroll-hide::-webkit-scrollbar-track { background: transparent; }
.scroll-hide::-webkit-scrollbar-thumb { background: #334155; border-radius: 2px; }
```
