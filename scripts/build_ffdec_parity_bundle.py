from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "reports" / "ffdec_parity_core_ha2"
BUNDLE_NAME = "ffdec_parity_core_ha2"
BUNDLE_ZIP = DEFAULT_OUT_DIR / f"{BUNDLE_NAME}.zip"
MANIFEST_JSON = DEFAULT_OUT_DIR / "manifest.json"
MANIFEST_MD = DEFAULT_OUT_DIR / "manifest.md"

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "experiments",
    "models",
    "recordings",
    "runs",
    "reports",
}
EXCLUDED_FILE_SUFFIXES = {".fla", ".swf"}

EXPECTED_PATHS = [
    "heliattack2_scripts",
    "reference_exports/ffdec_ha2/scripts_as",
    "reference_exports/ffdec_ha2/sprites_svg",
    "reference_exports/ffdec_ha2/shapes_svg",
    "reference_exports/ffdec_ha2/swf_xml",
    "reference_exports/ffdec_ha2/symbol_class",
    "reference_exports/ffdec_ha2/logs",
    "reference_exports/ffdec_ha2/images",
    "reference_exports/ffdec_ha2/sprites_png",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_111_Heli",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_109",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_137_hero",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_136",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_119",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_123",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_107",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_68_enemyBullet",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_318_tiles",
    "reference_exports/ffdec_ha2/sprites_svg/DefineSprite_25_bg",
    "reference_exports/ffdec_ha2/shapes",
    "reference_exports/ffdec_ha2/sprites",
    "reference_exports/ffdec_ha2/*.xml",
    "reference_exports/ffdec_ha2/**/swf.xml",
    "assets_ffdec/images",
    "assets_ffdec/sprites",
    "assets_ffdec/sprites/DefineSprite_111_Heli",
    "assets_ffdec/sprites/DefineSprite_137_hero",
    "assets_ffdec/sprites/DefineSprite_136",
    "assets_ffdec/sprites/DefineSprite_107",
    "assets_ffdec/sprites/DefineSprite_318_tiles",
    "assets_ffdec/sprites/DefineSprite_25_bg",
]

EXPECTED_ALT_HINTS = {
    "reference_exports/ffdec_ha2/shapes": ["reference_exports/ffdec_ha2/shapes_svg"],
    "reference_exports/ffdec_ha2/sprites": [
        "reference_exports/ffdec_ha2/sprites_svg",
        "reference_exports/ffdec_ha2/sprites_png",
    ],
    "reference_exports/ffdec_ha2/*.xml": ["reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml"],
    "reference_exports/ffdec_ha2/**/swf.xml": ["reference_exports/ffdec_ha2/swf_xml/heli_attack_2.swf.xml"],
}


@dataclass(frozen=True)
class ManifestEntry:
    expected_path: str
    status: str
    included_paths: list[str]
    missing_path: str | None = None
    alternative_paths: list[str] | None = None
    note: str | None = None


def repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def path_is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_repo_files() -> list[Path]:
    results: list[Path] = []
    for root, dirnames, filenames in os.walk(REPO_ROOT):
        root_path = Path(root)
        dirnames[:] = [name for name in dirnames if name not in EXCLUDED_DIRS]
        if path_is_excluded(root_path):
            continue
        for filename in filenames:
            path = root_path / filename
            if path.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
                continue
            if not path_is_excluded(path):
                results.append(path)
    return results


def find_alternatives(expected: str, repo_files: list[Path]) -> list[Path]:
    expected_path = Path(expected)
    expected_name = expected_path.name
    hints = [REPO_ROOT / alt for alt in EXPECTED_ALT_HINTS.get(expected, [])]
    found: list[Path] = []
    seen: set[Path] = set()

    for hint in hints:
        if hint.exists() and hint not in seen:
            found.append(hint)
            seen.add(hint)

    for path in repo_files:
        if expected_name and path.name == expected_name and path not in seen:
            found.append(path)
            seen.add(path)

    return found


def collect_paths_for_entry(expected: str, repo_files: list[Path]) -> ManifestEntry:
    target = REPO_ROOT / expected
    if "*" in expected or "?" in expected:
        matches = [path for path in repo_files if Path(repo_relative(path)).match(expected)]
        if matches:
            return ManifestEntry(
                expected_path=expected,
                status="found",
                included_paths=[repo_relative(path) for path in matches],
            )
        alternatives = find_alternatives(expected, repo_files)
        return ManifestEntry(
            expected_path=expected,
            status="missing",
            included_paths=[],
            missing_path=expected,
            alternative_paths=[repo_relative(path) for path in alternatives] or None,
        )

    if target.exists():
        if target.is_dir():
            included = [
                repo_relative(path)
                for path in repo_files
                if target in path.parents or path == target or str(path).startswith(str(target))
            ]
            included.sort()
            return ManifestEntry(
                expected_path=expected,
                status="found",
                included_paths=included,
                note="directory",
            )
        return ManifestEntry(
            expected_path=expected,
            status="found",
            included_paths=[repo_relative(target)],
            note="file",
        )

    alternatives = find_alternatives(expected, repo_files)
    return ManifestEntry(
        expected_path=expected,
        status="missing",
        included_paths=[],
        missing_path=expected,
        alternative_paths=[repo_relative(path) for path in alternatives] or None,
    )


def add_path_to_zip(zip_file: ZipFile, path: Path) -> None:
    if path.is_dir():
        return
    arcname = repo_relative(path)
    zip_file.write(path, arcname)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the HA2 FFDEC parity bundle.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    ffdec_root = REPO_ROOT / "reference_exports" / "ffdec_ha2"
    if not ffdec_root.is_dir():
        raise FileNotFoundError(
            f"FFDEC exports not found at {ffdec_root}. Export the HA2 FFDEC reference data first."
        )

    repo_files = iter_repo_files()
    entries = [collect_paths_for_entry(expected, repo_files) for expected in EXPECTED_PATHS]

    included_paths = sorted(
        {
            path
            for entry in entries
            for path in entry.included_paths
        }
    )

    bundle_zip = out_dir / f"{BUNDLE_NAME}.zip"
    manifest_json = out_dir / "manifest.json"
    manifest_md = out_dir / "manifest.md"
    readme_text = (
        "HA2 FFDEC parity bundle.\n\n"
        "Included categories:\n"
        "- ActionScript exports\n"
        "- sprite SVG/XML exports\n"
        "- shape SVG exports\n"
        "- symbol/class and placement dumps\n"
        "- rendered images and sprites\n"
        "- manifest files for found/missing/alternative paths\n"
    )
    manifest = {
        "bundle_name": BUNDLE_NAME,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "repo_root": repo_relative(REPO_ROOT),
        "bundle_zip": repo_relative(bundle_zip),
        "included_path_count": len(included_paths),
        "included_paths": included_paths,
        "entries": [asdict(entry) for entry in entries],
    }
    manifest_json_text = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_md_text = "\n".join(lines := [
        f"# {BUNDLE_NAME}",
        "",
        f"- bundle: `{repo_relative(bundle_zip)}`",
        f"- included paths: {len(included_paths)}",
        "",
        "## Entries",
    ])
    for entry in entries:
        lines.append(f"- `{entry.expected_path}`: {entry.status}")
        if entry.included_paths:
            for path in entry.included_paths[:5]:
                lines.append(f"  - included: `{path}`")
            if len(entry.included_paths) > 5:
                lines.append(f"  - included: ... {len(entry.included_paths) - 5} more")
        if entry.alternative_paths:
            for path in entry.alternative_paths:
                lines.append(f"  - alternative: `{path}`")
        if entry.note:
            lines.append(f"  - note: {entry.note}")
    manifest_md_text = "\n".join(lines) + "\n"

    with ZipFile(bundle_zip, "w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("README.txt", readme_text)
        zip_file.writestr("manifest.json", manifest_json_text)
        zip_file.writestr("manifest.md", manifest_md_text)
        for relative in included_paths:
            add_path_to_zip(zip_file, REPO_ROOT / relative)

    manifest_json.write_text(manifest_json_text, encoding="utf-8")
    manifest_md.write_text(manifest_md_text, encoding="utf-8")

    print(f"Bundle written: {bundle_zip}")
    print(f"Manifest JSON: {manifest_json}")
    print(f"Manifest MD: {manifest_md}")
    print(f"Included paths: {len(included_paths)}")


if __name__ == "__main__":
    main()
