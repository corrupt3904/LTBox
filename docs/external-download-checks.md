# External download checks

The ignored tests named `weekly_fetch_*` are intended for scheduled CI. They
perform network reads only when explicitly selected (for example, `cargo test
weekly_fetch -- --ignored`). Each download is written beneath `tempfile` and is
discarded after the test. These checks never start an installer or updater,
write to an installation directory, invoke a privileged command, open a device
session, or access hardware.

## Non-root runtime coverage

| Check | Production selection path exercised | Download validation |
| --- | --- | --- |
| Windows Qualcomm userspace and kernel drivers | `select_latest_win_release` for x64, arm64, and x86 installer names in both driver specs | Every selected `.exe` downloads to a temporary file and is nonempty. |
| Linux Qualcomm kernel driver | `fetch_latest_linux_kernel_release` | The selected QUD zip downloads to a temporary file and is opened only to confirm that it contains a `.deb`. |
| Direct self-update | `release_asset_for_target` for Windows x64/arm64, Linux x64/arm64, and macOS x64/arm64 | Each archive and its `.sha256` sidecar download to temporary files; the existing sidecar parser and SHA-256 file hash are compared. |
| Canoe efisp GBL | `efisp_expected_asset` for PRC/ROW and normal/ARB variants | Every pinned EFI downloads to a temporary file and passes `verify_efisp_asset`. |

The Windows installer check confirms availability only. Authenticode verification
belongs to the production install path and is not run by this download-only
test. The Linux check deliberately does not extract or install the package.
The self-update check does not extract archives or invoke the updater entrypoint.

## Root contracts and schedule

`.github/workflows/external-downloads.yml` runs every Monday at 03:23 UTC
(12:23 KST) and supports manual dispatch. Root providers run as independent
matrix jobs with `fail-fast: false`; a broken provider does not hide others.
GitHub sends its normal failed-workflow notifications to subscribed users.
No issues or external messages are created automatically.

`weekly_fetch_root_providers` calls the production manager and payload staging
functions for Magisk, KernelSU, KernelSU-Next, SukiSU, ReSukiSU, APatch,
FolkPatch, and SKRoot Lite. It covers stable and nightly where supported,
including release-to-workflow fallback, APK manifests, ZIP member extraction,
and KSU arm64 ELF headers for android12-5.10, android13-5.15, android14-6.1,
and android15-6.6. The latest available nightly is pinned once for all inputs.
Missing assets, expired-only nightly builds, and fetch/extraction failures fail
the job. Locally supplied Magisk/KSU files and GKI images have no remote source.

Use `LTBOX_CHECK_PROVIDER=SukiSU` to restrict a local root check. The optional
`LTBOX_GITHUB_TOKEN` is used only by GitHub API requests; asset downloads use
the same unauthenticated production path (including nightly.link). CI supplies
its read-only GitHub token. Download logs are retained for 30 days.

## Explicit exclusions

Lenovo servers (OTA, QFIL, machine-info) are excluded at the user's request.
The scheduled workflow does not call these endpoints and needs no test serial,
firmware ID or MTM configuration.

This covers runtime download contracts. Cargo dependencies are locked and
covered by normal build/Dependabot jobs; developer-only font regeneration and
icon generation are build tooling, not runtime download providers. Arbitrary
user-supplied URLs/files cannot be enumerated by a scheduled upstream check.

## Why these checks exist

[Issue #102](https://github.com/miner7222/LTBox/issues/102) exposed SukiSU's
`_releases.apk` naming and release ZIP payloads. Earlier, `f172fb12` moved the
KernelSU LKM fallback to CI artifacts after v3.3.0 dropped release `.ko` files;
that change also handled architecture-prefixed assets. The weekly tests reuse
production selection functions so future naming changes fail the contract
instead of merely checking whether a repository still returns HTTP 200.

The initial full probe also caught Magisk moving from `ci.yml` to `build.yml`,
using SHA-named bundles beside `SHA-symbols`, and shipping both app and stub
APKs in one archive. Those selection failures were fixed and covered by a
regression test before rerunning the live Magisk contract successfully.
