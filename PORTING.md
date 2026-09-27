# WebDisplays + WaterFrames 26.2 Port

Target: Minecraft 26.2, NeoForge.

## Scope lock

- Port the original WebDisplays behavior, blocks, multiblock screen model, GUI and interactions.
- Port WaterFrames to NeoForge 26.2.
- Keep WaterFrames/WaterMedia as the media path. Do not replace it with Rinku, MCEF video playback, JCodec, or a custom decoder.
- Add exactly one user-facing extension to the WebDisplays URL flow: a local-file chooser in the existing Shift + right-click URL/config screen.
- Local media selection must remain client-local and must not expose arbitrary filesystem browsing to a server.
- Preserve WebDisplays URL/browser functionality rather than replacing it with a custom screen mod.

## Upstream baselines

- WebDisplays: CinemaMod/webdisplays branch 1.20, pinned at 594c4decf3059841106f8418c424d2362b430968.
- WaterFrames: SrRapero720/waterframes branch 1.21.5, pinned at 9e01478f93b7c01a325e9bc344f62ac8a19bd07d.

Port changes live outside the upstream submodules so upstream code remains auditable.
