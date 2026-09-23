#!/usr/bin/env python3
"""
MINIMAL test patch: only the two changes required to install as a separate
app at all (package rename + neutering the signature check), plus a single
one-line log write in onCreate (using only android.util.Log to logcat, not
even our own file-logging class -- so this test needs zero extra Java
classes at all).

Deliberately does NOT touch BottomBar or add any button. If this version
still shows a black screen, we know the problem is unrelated to any of our
button-injection code -- most likely the missing split modules (HDR+,
portrait, etc.) that base.apk doesn't include.

Run from the repo root: python3 patch-scripts/minimal_patch.py decompiled/
"""
import re
import sys
from pathlib import Path

OLD_PACKAGE = "com.google.android.GoogleCamera"
NEW_PACKAGE = "com.example.gcammin"
OLD_AUTHORITY_2 = "com.google.android.apps.camera.specialtypes.SpecialTypesProvider"
NEW_AUTHORITY_2 = "com.example.gcammin.specialtypes.SpecialTypesProvider"


def find_smali_file(decompiled: Path, relative_path: str) -> Path:
    candidates = sorted(decompiled.glob("smali*/" + relative_path))
    if not candidates:
        print(f"ERROR: could not find {relative_path} in any smali* directory under {decompiled}")
        print("Available smali* directories:", [p.name for p in decompiled.glob("smali*") if p.is_dir()])
        sys.exit(1)
    return candidates[0]


def patch_manifest(decompiled: Path) -> None:
    manifest = decompiled / "AndroidManifest.xml"
    text = manifest.read_text(encoding="utf-8")
    before = text
    text = text.replace(OLD_PACKAGE, NEW_PACKAGE)
    text = text.replace(OLD_AUTHORITY_2, NEW_AUTHORITY_2)
    if text == before:
        print("WARNING: manifest patch made no changes -- check OLD_PACKAGE constant")
    manifest.write_text(text, encoding="utf-8")
    print(f"Patched manifest: {manifest}")


def patch_signature_check(decompiled: Path) -> None:
    path = find_smali_file(decompiled, "com/pairip/SignatureCheck.smali")
    text = path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"\.method public static verifyIntegrity\(Landroid/content/Context;\)V\n"
        r"\s*\.(?:registers|locals) \d+\n"
        r"(?:.*\n)*?"
        r"\.end method",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        print("ERROR: could not find verifyIntegrity method to patch")
        sys.exit(1)

    replacement = (
        ".method public static verifyIntegrity(Landroid/content/Context;)V\n"
        "    .locals 0\n"
        "    return-void\n"
        ".end method"
    )
    patched = text[: match.start()] + replacement + text[match.end() :]
    path.write_text(patched, encoding="utf-8")
    print(f"Patched signature check: {path}")


def patch_minimal_log(decompiled: Path) -> None:
    """
    Adds ONE call to android.util.Log.i() -- a plain platform API, no
    custom class needed at all -- as the very first instruction in
    CameraActivity.onCreate(). Uses only a const-string (v0) and the
    already-safe move-object/from16 + /range pattern.
    """
    path = find_smali_file(
        decompiled,
        "com/google/android/apps/camera/legacy/app/activity/main/CameraActivity.smali",
    )
    text = path.read_text(encoding="utf-8")

    method_pattern = re.compile(
        r"\.method protected onCreate\(Landroid/os/Bundle;\)V\n"
        r"\s*\.(?:registers|locals) \d+\n",
        re.MULTILINE,
    )
    match = method_pattern.search(text)
    if not match:
        print("ERROR: could not find CameraActivity.onCreate() to patch")
        sys.exit(1)

    injected = """    # --- gcammin: minimal test log ---
    const-string v0, "GCamMinTest"

    const-string v1, "CameraActivity.onCreate reached (minimal test)"

    invoke-static/range {v0 .. v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I
    # --- end gcammin ---

"""

    insertion_point = match.end()
    patched = text[:insertion_point] + injected + text[insertion_point:]
    path.write_text(patched, encoding="utf-8")
    print(f"Patched CameraActivity.onCreate() with minimal log call: {path}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: minimal_patch.py <decompiled_dir>")
        sys.exit(1)

    decompiled = Path(sys.argv[1])
    patch_manifest(decompiled)
    patch_signature_check(decompiled)
    patch_minimal_log(decompiled)


if __name__ == "__main__":
    main()
