# Changelog

## 1.1.2
- If the app ever closes unexpectedly, it now shows the error details the next time you open it, so problems can be reported and fixed
- TV player extras (title logo, "Ends at" time, remote keys) can no longer close the app if something goes wrong
- Title logo download now times out instead of hanging on slow connections

## 1.1.1
- The app now only shows the Jellyfin server you connected to. Other websites are never opened inside the app
- External website links (IMDb, TMDb and similar) are hidden
- Styled anime subtitles (ASS/SSA) now direct play by default on TVs, so the server doesn't have to convert those videos
- Fixed a possible crash when a link was opened on a device without a web browser

## 1.1.0
- New TV video player controls, laid out like the official Jellyfin Fire TV player:
  title logo and episode line, clock, "Ends at" time, big progress bar, two rows of large buttons
- Rewind / fast-forward buttons and a Zoom button (Fit, Zoom, Stretch)
- Phones keep the original player layout

## 1.0.1
- New wide phoenix artwork for the Fire TV / Android TV home screen tile and banner
- Bigger phoenix icon on TV launchers

## 1.0.0
First public release.

- Jellyfin web interface in TV layout, with full support for custom CSS themes and web plugins
- Violet focus glow that follows the remote
- Pointer mode on the â˜° Menu button for hard-to-reach buttons
- Native Media3 / ExoPlayer video player with remote controls: seek, play/pause, skip intro, Back to hide controls, Menu for subtitles
- Fire TV / Android TV launcher banner and phoenix app icon
- No picture-in-picture, battery prompt, rotation or lock buttons on TVs
- Installs alongside the official Jellyfin app
- Based on Jellyfin Android v2.7.3
# 1.2.0 â€” Tanukifin

- Rename the app, package, patch, release assets and documentation to Tanukifin.
- Remove the original promotional banner and artwork; use a minimal T launcher tile.
- Restrict navigation to the exact server origin and replace global native bridges with origin-scoped, main-frame-only messaging.
- Build validation without signing secrets; require explicit manual publication on main.
- Pin upstream/action commits, preserve LF patch bytes and reject release/tag replacement.
- Publish build metadata and SHA256 checksums alongside signed APKs.
