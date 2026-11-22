# Architecture visual assets

- **architecture.gif**: animated README preview with five illustrative flow stages.
- **architecture.svg**: accessible static topology with title/description.
- **architecture-explorer.html**: self-contained offline interactive CSS 3D-style explorer. Download/open in a modern browser; GitHub's file view shows source, not an executable page. No hosting or app settings are required.
- **generate_visuals.py**: deterministic static/GIF generator using Pillow. It does not query services or user records.

The explorer offers five workflow tours, pause/play, next-step, flat/3D view and individual service details. `prefers-reduced-motion` starts the tour paused and removes connector animation. Narrow screens use a readable flat card grid; connectors are hidden there and the written workflow remains available. No keyboard shortcuts are intercepted. Data shown is illustrative, not production telemetry.

## Regenerate previews

From the repo root with Pillow installed (already part of the API dependency lock):

```bash
python docs/visuals/generate_visuals.py
```

The generator uses Linux DejaVu font paths; adapt them to installed equivalents on other systems. The approved logo is read from the application public assets. The HTML embeds the same logo as data and uses no external scripts, fonts, analytics or network API calls. Update its content separately when architecture contracts change. Keep a static alternative and textual documentation alongside animations.

## Offline checks

From the repo root after `npm ci` in `apps/web`:

```bash
python docs/check_docs.py
node docs/visuals/check_explorer.cjs
```

## Verification for this documentation release

- Local Markdown links resolved, SVG parsed, optimized GIF decoded as 29 frames.
- HTML controls exercised in jsdom: all five tours, next-step, pause, flat view and seven service details.
- GIF first frame visually inspected for legibility and topology; generated frame content checked for bounds.
- A local headless browser render was attempted but the execution environment denied a browser singleton socket. No browser screenshot or real-device visual acceptance is claimed. A maintainer should check the HTML on desktop/mobile browsers before treating visual QA as complete.
