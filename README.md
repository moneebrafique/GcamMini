# GCam Minimal Test

Isolates two open questions before we invest more time in the full
GCamPatch project:

1. Does our simplified smali-injection approach (move-object/from16 +
   single /range call) actually run correctly at all, with zero other
   changes?
2. Is the black screen caused by using the split `base.apk` (36MB, missing
   HDR+/portrait/lightcycle/etc. asset modules) instead of the full,
   self-contained system APK (272MB)?

This patch does ONLY the two changes required to install as a separate
package (rename + neuter the Pairip signature check) plus one
`android.util.Log.i()` call in `CameraActivity.onCreate()` -- no button, no
BottomBar edit, no custom Java classes at all.

## Test plan

Run this against **both** APKs, in two separate releases, and compare:

### Test A: against base.apk (what we've been using)
1. Create a release (e.g. tag `v1-base`) with `base.apk` renamed to
   `GoogleCamera.apk` attached.
2. Run the workflow with that tag.
3. Install, open, and see what happens.

### Test B: against the full system APK
1. On your PC: `adb pull /product/priv-app/GoogleCamera/GoogleCamera.apk`
   (this is the ~272MB single-file version you pulled earlier in our
   conversation).
2. Create a **different** release (e.g. tag `v1-full`) with this file
   attached (already named `GoogleCamera.apk`, no rename needed).
3. Run the workflow with that tag.
4. Install (as a different package, `com.example.gcammin`, so it won't
   conflict with anything else you've installed), open, and compare.

Note: decompiling/rebuilding the 272MB version will take noticeably
longer than the 36MB one -- give it several extra minutes.

## What the results tell us

| Test A (base.apk) | Test B (full APK) | Conclusion |
|---|---|---|
| Black screen | Works | base.apk is missing something CameraActivity needs (very likely a split module) |
| Black screen | Black screen | Not about which APK -- something else is still wrong with our patch approach itself |
| Works | (moot) | Our simplified injection approach is sound; the earlier black screen was something else (already-fixed register bug, stale build, etc.) |

## Checking logs either way

```
adb logcat | findstr "GCamMinTest"
```

If you see `"CameraActivity.onCreate reached (minimal test)"`, the Activity
is genuinely running -- if the screen is STILL black despite that log
appearing, the failure is happening later in the camera preview setup
itself (likely the missing-split-module theory), not at Activity startup.
If you never see that log line at all, the Activity itself never
successfully starts.
