# Security and build provenance

## WebView boundary

Only the selected server's exact HTTP(S) origin (scheme, hostname and effective port) can navigate inside the main WebView. User-info, malformed and non-HTTP(S) URLs are rejected, including `about:`, `data:`, `blob:`, `javascript:`, `file:` and `intent:` navigations. Explicit default ports compare equal. LAN HTTP remains supported, but use HTTPS across untrusted networks.

Native privileges use AndroidX origin-scoped web messaging and an explicit command allowlist. Native callbacks check the browser-reported source origin, main-frame flag and current top-level URL. The old unrestricted `addJavascriptInterface` registrations are removed. Document-start shims preserve the web client's synchronous capability getters while commands use one-way messages. Player preference snapshots refresh on resume.

A WebView without both `WEB_MESSAGE_LISTENER` and `DOCUMENT_START_SCRIPT` is refused with an update message; there is no insecure legacy fallback, even when the upstream version warning is ignored. Old Fire OS/WebView combinations may therefore be incompatible. File/content access and mixed content are disabled. Popups and arbitrary bridge intents are disabled. Off-origin HTTP(S) links only open outside the app following a main-frame user gesture. Redirects/embedded frames cannot automatically launch apps.

This is not an all-network allowlist. Server-selected remote CSS, images, video and scripts remain usable, but foreign resources cannot trigger native-script injection or credential extraction by choosing a matching URL path. Third-party scripts loaded by your trusted server execute with that server's web privileges. A compromised server, same-origin plugin or malicious custom script is still trusted web content: only connect to servers and plugins you trust. Cross-origin video redirects may still be used by the native player; that player's network policy is outside this navigation change.

Crash reports stay local and may contain sensitive exception text. Redact them before sharing.

## Release process

- Upstream source is fetched by the full commit in `upstream.json`, and checkout identity is verified before patching. Update the commit and patch together in a reviewed PR.
- All third-party workflow actions use full commit SHAs. Java has an explicit version; Gradle's distribution SHA256 is pinned in the selected upstream source.
- `.gitattributes` preserves the patch bytes. `scripts/prepare.py` refuses CRLF patches and applies them in a fresh LF checkout, including binary changes. Do not edit binary patch payloads manually; regenerate with `git diff --binary --full-index` from the pinned checkout.
- PR/push validation has read-only repository permissions and no signing secrets. It executes origin/bridge/release-guard tests and compiles an unsigned release APK.
- Publishing requires a manual workflow dispatch on `main`, an exact version confirmation and an explicit publish checkbox. Pushes/tags/PRs cannot publish. The signed build reruns tests. It verifies the APK signature, records source/patch/APK hashes and uploads build metadata and checksums.
- Existing tags and releases cause failure. Assets are not overwritten. A failed upload may leave a draft, which must be investigated before retrying. Use a new version for published changes.
- Dependency versions are resolved without dynamic/changing releases from Google Maven/Maven Central. Local/snapshot repositories are removed. OSV scans declared catalog and resolved runtime/buildscript coordinates before compilation and publication; findings, API errors and incomplete responses block the build. Reports and package manifests ship with releases. This is advisory screening, not a guarantee against malicious/unknown code.
- The optional FFmpeg native audio extension is removed, including its forced codec advertising. Device-supported audio and PCM/AAC/MP3 remain; other audio may need server transcoding. APK inspection rejects unexpected native libraries, permissions and package IDs.
- Signing runs on a separate fresh runner after the unsigned build. Build plugins never run on the signing runner. The signing keystore is decoded outside the repository, removed after signing, and excluded by `.gitignore`. The sole private-key alias is discovered automatically, so existing signing keys need not be renamed. Keep the same key and password backed up privately.

Pinned source and hashes improve traceability but do not prove independent source-to-APK reproducibility. The hosted runner image, Android SDK/build tools, Maven dependencies and signing infrastructure remain trust inputs. This PR does not claim a hermetic build, dependency vulnerability audit or independent binary equivalence. No production release should be inferred from an unsigned validation artifact.

## Before installing on a TV

1. Check origin and bridge tests pass, and the release APK compiles in Actions.
2. On a current Fire OS/Android WebView, test login, TV focus/pointer, native playback, subtitles, settings changes and reconnection over HTTPS (and LAN HTTP if used).
3. With a benign test server, confirm same-host different-port/scheme redirects, foreign iframe messages, custom schemes and popups cannot invoke native actions. Confirm themes still load as expected.
4. Check an outdated WebView is blocked. Install signed updates with the same key and a higher version code; test alongside the official client.

Device-level tests require an actual Fire TV or emulator and are not replaced by source/unit tests. New package ID `org.tanukifin.tv` deliberately starts with separate app data. Original-source credit and the GPL licence remain in README and LICENSE.md.
