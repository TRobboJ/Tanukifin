# Dependency assessment — 20 November 2026

No finite audit can certify every dependency as safe. This review combines version/provenance checks, advisory screening and reducing unnecessary native-code exposure. No malware samples were used.

## Findings and changes

| Area | Assessment and action |
| --- | --- |
| Maven libraries | Initial OSV scan covered 61 declared coordinates with zero advisory matches. After dropping the optional native decoder, the catalog scan covered 60 with zero matches. These include test/build-only declarations, not just APK contents. CI additionally exports resolved transitive runtime and buildscript components and scans them before building. Download the run's `dependency-audit.json` for the exact package list, timestamp and result. |
| Native FFmpeg audio extension | The original `org.jellyfin.media3:media3-ffmpeg-decoder:1.8.0+1` points to Jellyfin media commit `84ef4b7201a9e1edfc699c31acbc505511a4af1f`. Its FFmpeg submodule is `d388c347d41e4eb516dec05910551c5461e65615`, whose RELEASE file identifies 6.0.2. A Maven-level clean scan does not cover every C/C++ codec compiled inside that AAR. The extension is removed rather than assumed safe. This is risk reduction, not a claim that an exploit was demonstrated. |
| Playback after removing FFmpeg | The platform MediaCodec decoders and Media3 remain. Device profiles no longer force DTS/MLP/TrueHD/AC3/EAC3/ALAC support when the device does not advertise it; AAC/MP3 and PCM remain supported. HLS fallback offers AAC/MP3. Jellyfin may transcode unsupported audio. Actual Fire TV playback, passthrough and subtitle combinations need device tests. |
| Dependency sources | Only Google Maven and Maven Central are used for app libraries. Local Maven and snapshot repositories are removed, and dynamic/changing dependency versions fail resolution. Build plugin repositories remain the official Gradle Plugin Portal, Maven Central and Google Maven. |
| Build actions | Checkout, Java setup, Gradle setup, artifact upload and download are pinned to full commits resolved from their official GitHub repositories. No third-party release action is used. Gradle build-scan publication and Develocity injection are explicitly disabled. Pinning controls updates; it does not prove the pinned implementation is flawless. |
| Signing exposure | Unsigned resolution, audit and compilation run without signing secrets. A separate fresh runner downloads the exact artifact ID from the same workflow run, checks source/version/checksums, inspects the APK, and signs it without executing Gradle or app build plugins. |
| APK inspection | CI verifies the Tanukifin application ID and an explicit permission allowlist, and rejects unexpected native libraries. The only permitted packaged native library name is AndroidX graphics path; FFmpeg cannot silently return. A new native dependency or permission requires explicit review/code change. |
| Remaining platform trust | Fire OS/Android WebView, system codecs, SDK/build-tools and hosted runner images still need maintenance. The app fails closed when origin-scoped WebView messaging/document-start support is absent. System components are not made secure simply by a clean Maven scan. |

## How the gate behaves

OSV is queried using exact Maven coordinates and versions. Any advisory match blocks the build for investigation/remediation. API errors, pagination or incomplete results also block; an unavailable scanner is not treated as a clean result. There is no suppression file or automatic bypass. Results, resolved coordinates and their SHA256 hashes accompany published APKs.

The gate does not detect arbitrary malicious behaviour, prove Maven artifact provenance, inspect every line of transitive source, or cover undisclosed vulnerabilities. It is not an independent reproducible-build proof or a hermetic dependency lock. Review new versions and new dependencies before merging; a pinned malicious release is still malicious.

## Primary sources inspected

- [OSV batch-query API](https://google.github.io/osv.dev/post-v1-querybatch/)
- [Jellyfin native decoder submodules at the reviewed commit](https://github.com/jellyfin/jellyfin-androidx-media/blob/84ef4b7201a9e1edfc699c31acbc505511a4af1f/.gitmodules)
- [FFmpeg 6.0.2 source identity](https://github.com/FFmpeg/FFmpeg/blob/d388c347d41e4eb516dec05910551c5461e65615/RELEASE)
- [FFmpeg security information](https://ffmpeg.org/security.html)
- [AndroidX Media security policy](https://github.com/androidx/media/security)
- [Jellyfin Android security policy](https://github.com/jellyfin/jellyfin-android/security)

The native-decoder review does not imply Jellyfin server-side FFmpeg is removed or changed. This PR only changes the TV client.
