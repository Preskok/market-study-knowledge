#!/usr/bin/env python3
"""
Build aliases.json from SiteKeys.ts (the canonical source) + aliases-manual.json (nicknames).

The string value of each enum entry is the canonical slug. Aliases are auto-generated
from the enum key name (e.g. AUTO_CONNECT → 'auto connect', 'autoconnect', 'auto-connect').
Manual nicknames in aliases-manual.json override on collision.

Run as part of build.sh. Don't edit aliases.json by hand — it's regenerated.

Also reports:
- SiteKeys entries missing a sites/[slug].md (need a stub)
- sites/[slug].md files that aren't in SiteKeys (orphans / merged / renamed)
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_KEYS_TS = Path("/Users/filipozbolt/Projects/market-study/src/shared/const/SiteKeys.ts")
SITES_DIR = ROOT / "sites"
ALIASES_PATH = ROOT / "aliases.json"
MANUAL_PATH = ROOT / "aliases-manual.json"

# Match `KEY = 'value'` lines inside the four site-key enums
ENUM_LINE_RE = re.compile(r"^\s*([A-Z_0-9]+)\s*=\s*['\"]([a-z0-9\-]+)['\"]\s*,?\s*(?://.*)?$")
ENUM_OPEN_RE = re.compile(r"^\s*export\s+enum\s+(\w+SiteKey\w*)")

# Enums to read. Skip TestingAdSiteKeysEnum and DUMMY_SITE — those are noise.
INCLUDED_ENUMS = {
    "AvailableAdSiteKeysEnum",
    "LegacyAdSiteKeysEnum",
    "RentACarSiteKeyEnum",
}


def parse_site_keys() -> dict[str, str]:
    """Return dict of {ENUM_KEY: 'slug-value'} from SiteKeys.ts (filtered to relevant enums)."""
    if not SITE_KEYS_TS.exists():
        print(f"ERROR: {SITE_KEYS_TS} not found", file=sys.stderr)
        sys.exit(1)

    keys: dict[str, str] = {}
    current_enum = None
    in_enum = False

    for line in SITE_KEYS_TS.read_text().splitlines():
        m = ENUM_OPEN_RE.match(line)
        if m:
            current_enum = m.group(1)
            in_enum = True
            continue
        if in_enum and "}" in line and "{" not in line:
            in_enum = False
            current_enum = None
            continue
        if in_enum and current_enum in INCLUDED_ENUMS:
            m = ENUM_LINE_RE.match(line)
            if m:
                enum_key, slug = m.group(1), m.group(2)
                keys[enum_key] = slug

    return keys


def aliases_for(enum_key: str, slug: str) -> set[str]:
    """Generate plausible aliases for one site, all lowercase."""
    out = set()

    # The canonical slug itself, plus hyphen variants
    out.add(slug)
    out.add(slug.replace("-", " "))
    out.add(slug.replace("-", ""))

    # The enum key in lowercase, plus underscore variants
    ek = enum_key.lower()
    out.add(ek)
    out.add(ek.replace("_", " "))
    out.add(ek.replace("_", "-"))
    out.add(ek.replace("_", ""))

    return {a.strip() for a in out if a.strip()}


def load_manual() -> dict[str, str]:
    if not MANUAL_PATH.exists():
        return {}
    try:
        raw = json.loads(MANUAL_PATH.read_text())
        return {k: v for k, v in raw.items() if not k.startswith("_")}
    except Exception as e:
        print(f"WARN: couldn't parse {MANUAL_PATH}: {e}")
        return {}


def main():
    enum_to_slug = parse_site_keys()
    print(f"Parsed {len(enum_to_slug)} site keys from SiteKeys.ts")

    canonical_slugs = set(enum_to_slug.values())

    # Build auto-aliases
    auto: dict[str, str] = {}
    collisions = []
    for enum_key, slug in enum_to_slug.items():
        for alias in aliases_for(enum_key, slug):
            if alias in auto and auto[alias] != slug:
                collisions.append((alias, auto[alias], slug))
            else:
                auto[alias] = slug

    if collisions:
        print(f"WARN: {len(collisions)} alias collision(s) between SiteKeys entries:")
        for a, s1, s2 in collisions[:10]:
            print(f"  '{a}' wanted by both '{s1}' and '{s2}' (kept '{s1}')")

    # Merge manual on top
    manual = load_manual()
    merged = {**auto, **manual}

    # Validate manual aliases point to known canonical slugs (or to a slug we have a file for)
    site_files = {p.stem for p in SITES_DIR.glob("*.md") if p.stem != "_index"}
    valid_targets = canonical_slugs | site_files

    bad_manual = {k: v for k, v in manual.items() if v not in valid_targets}
    if bad_manual:
        print(f"WARN: {len(bad_manual)} manual alias(es) point to unknown site:")
        for k, v in list(bad_manual.items())[:10]:
            print(f"  '{k}' -> '{v}' (no SiteKeys entry, no sites/{v}.md)")

    # Write merged
    ALIASES_PATH.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {ALIASES_PATH.name}: {len(merged)} aliases -> {len(set(merged.values()))} unique sites")

    # Cross-check site files vs SiteKeys
    print()
    print("=== Coverage report ===")

    missing_files = sorted(canonical_slugs - site_files)
    if missing_files:
        print(f"\n{len(missing_files)} SiteKeys entries WITHOUT a sites/<slug>.md:")
        for slug in missing_files:
            print(f"  - {slug}")
        print("  → add sites/<slug>.md stubs (template in any existing site file)")

    orphan_files = sorted(site_files - canonical_slugs)
    if orphan_files:
        print(f"\n{len(orphan_files)} sites/*.md files NOT in SiteKeys:")
        for slug in orphan_files:
            print(f"  - sites/{slug}.md")
        print("  → either rename to a canonical slug, or merge into one and add an alias")

    if not missing_files and not orphan_files:
        print("All SiteKeys entries have a sites/*.md and vice versa. Clean.")


if __name__ == "__main__":
    main()
