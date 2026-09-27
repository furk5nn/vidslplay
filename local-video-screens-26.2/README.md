# Local Video Screens (Minecraft 26.2 / NeoForge)

A client-local video screen prototype using Rinku 3.0.4.

## Behavior

1. Place `localvideoscreens:screen_block` blocks in a filled rectangle on one plane.
2. Sneak + right-click the face you want to use as the display surface.
3. Click **Video seç**.
4. Pick a local video file using the native OS file picker.
5. One Rinku/Chromium browser is created for the entire rectangle, not per block.
6. Breaking any block belonging to the active rectangle closes the browser/session on the next lightweight validity check.

## Performance design

- One logical screen = one Rinku browser.
- Browser OSR is capped to 30 FPS.
- Browser surface is capped at 1280x720.
- Rinku owns Chromium paint handling / dirty-rect texture updates.
- No custom video decoder, no busy loop, no per-frame Java pixel copy loop.
- Screen integrity is checked only every 10 client ticks.
- Only one textured world quad is submitted per logical screen.
- Quads farther than 128 blocks are not submitted to the renderer.

## Build

Requires Java 25. The project targets:

- Minecraft 26.2
- NeoForge 26.2.0.88
- Rinku 3.0.4-26.2

Run `gradle build` (or use a Gradle wrapper after generating one) on a machine with Java 25.

## Current scope

This first version intentionally has no web navigation and no in-world browser mouse controls. Local-file selection and playback are the focus.
