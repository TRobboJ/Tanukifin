# Tanukifin

Tanukifin is an independent fork of **[Phoenicxfin by Hanson (@hansonds)](https://github.com/hansonds/Phoenicxfin)**, a Jellyfin client for Fire TV and Android TV with support for server themes and web plugins.

See the **[original repository and documentation](https://github.com/hansonds/Phoenicxfin#readme)** for the original project, features, setup and credits. Tanukifin is not affiliated with or endorsed by its original author or the Jellyfin project.

## Changes in this fork

- Tanukifin app/package identity (`org.tanukifin.tv`), no original promotional banner/artwork, and a minimal T launcher tile.
- Exact server-origin navigation and an origin-scoped native bridge. A current WebView supporting scoped messaging and document-start scripts is required; unsupported versions are blocked.
- Pinned upstream/action commits, dependency advisory checks and APK permission/native-library checks.
- Reviewed transitive dependency fixes are pinned in `dependency-versions.json` and applied to both runtime and build-tool resolution.
- No bundled FFmpeg audio extension. Unsupported audio may require Jellyfin server transcoding; allow audio transcoding for the account used on your TV.
- Releases require an explicit manual action. Builds and dependency checks run without signing secrets; signing uses a separate fresh runner.

## Install

Download **Tanukifin.apk** from [this repository's releases](https://github.com/TRobboJ/Tanukifin/releases). For Downloader, use:

```text
https://github.com/TRobboJ/Tanukifin/releases/latest/download/Tanukifin.apk
```

The original project's Downloader code installs its app, not this fork. Tanukifin installs separately, with its own login/settings.

## Build and publish

The app is the official Jellyfin Android commit pinned in `upstream.json`, plus `tanukifin.patch`.

1. Back up your PKCS12 signing keystore outside the repository. It must contain exactly one private key; its alias is detected automatically.
2. Add Actions secrets `KEYSTORE_BASE64` and `KEYSTORE_PASSWORD` in this repository's settings.
3. Update `VERSION` in a reviewed PR and merge into `main`. PR/push checks build an unsigned APK and never publish.
4. Run **Actions → Publish Tanukifin** on `main`, enter the exact version, and check the publish confirmation.

Existing tags/releases are rejected rather than overwritten. Releases include the signed APK, SHA256 checksums, build metadata, resolved dependencies and the advisory scan report. No advisory matches is not a guarantee that all code is safe; keep the TV's system software updated. Actual TV playback and compatibility still need device testing.

## Licence and credits

Original work by [Hanson](https://github.com/hansonds), [Jellyfin Android contributors](https://github.com/jellyfin/jellyfin-android), AndroidX Media3 / ExoPlayer and their open-source dependencies. See the [original project](https://github.com/hansonds/Phoenicxfin#credits) for further credits and [LICENSE.md](LICENSE.md) for the GPL licence.
