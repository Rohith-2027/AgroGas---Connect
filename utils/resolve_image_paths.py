# utils/resolve_image_paths.py
"""
Resolve image_path entries in dataset/labels.csv by searching dataset/images for matching filenames.
Writes dataset/labels_resolved.csv with corrected relative paths (relative to dataset/ directory).
Safe: does not overwrite original labels.csv.
"""

import csv
from pathlib import Path
from collections import defaultdict
import sys

ROOT = Path.cwd()
SRC = ROOT / "dataset" / "labels.csv"
OUT = ROOT / "dataset" / "labels_resolved.csv"
IMG_ROOT = ROOT / "dataset" / "images"

# file extensions considered
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

def build_index(img_root: Path):
    """
    Walk dataset/images and index by basename -> list(paths)
    """
    idx = defaultdict(list)
    if not img_root.exists():
        print(f"ERROR: images root not found: {img_root}")
        return idx
    for p in img_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            idx[p.name].append(p)
    return idx

def normalize_path_str(s: str):
    s = (s or "").strip()
    return s.replace("\\", "/")

def main():
    if not SRC.exists():
        print("ERROR: dataset/labels.csv not found at", SRC)
        sys.exit(1)

    print("Indexing images under:", IMG_ROOT)
    idx = build_index(IMG_ROOT)
    print("Indexed", sum(len(v) for v in idx.values()), "image files. Unique basenames:", len(idx))

    rows = []
    with open(SRC, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    missing = 0
    resolved = 0
    ambiguous = 0
    unchanged = 0
    fixes = []

    for r in reader:
        orig = normalize_path_str(r.get("image_path",""))
        if not orig:
            missing += 1
            rows.append(r)
            continue

        # If path already points to an existing file relative to dataset/ directory, leave as-is
        candidate_path = (ROOT / orig).resolve()
        if candidate_path.exists():
            rows.append(r)
            unchanged += 1
            continue

        # Try basename lookup
        basename = Path(orig).name
        hits = idx.get(basename, [])
        if len(hits) == 1:
            new_rel = hits[0].resolve().relative_to(ROOT / "dataset")
            new_rel_str = str(new_rel).replace("\\","/")
            r["image_path"] = new_rel_str
            rows.append(r)
            resolved += 1
            fixes.append((orig, new_rel_str))
        elif len(hits) > 1:
            # ambiguous: multiple files with same basename. prefer the one whose parent folder name appears in orig
            chosen = None
            orig_lower = orig.lower()
            for h in hits:
                if h.parent.name.lower() in orig_lower:
                    chosen = h
                    break
            if chosen is None:
                # pick first but mark ambiguous
                chosen = hits[0]
                ambiguous += 1
            new_rel = chosen.resolve().relative_to(ROOT / "dataset")
            new_rel_str = str(new_rel).replace("\\","/")
            r["image_path"] = new_rel_str
            rows.append(r)
            fixes.append((orig, new_rel_str))
        else:
            # no hits: leave as-is
            missing += 1
            rows.append(r)

    # write resolved CSV
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("WROTE:", OUT)
    print(f"Resolved: {resolved}, Ambiguous resolved: {ambiguous}, Already correct: {unchanged}, Missing kept: {missing}")
    if fixes:
        print("\nSample fixes (first 20):")
        for a,b in fixes[:20]:
            print(f" {a}  ->  {b}")
    else:
        print("No path fixes applied.")

    print("\nNext steps:")
    print("  1) Inspect dataset/labels_resolved.csv. If OK, you can replace labels.csv:")
    print("     > copy dataset\\labels_resolved.csv dataset\\labels.csv")
    print("     (use OS copy command or rename in File Explorer)")
    print("  2) Re-run: python utils\\fill_missing_moisture_vs.py")
    print("  3) If still many missing, verify your dataset/images folder actually contains the image files (maybe they were stored elsewhere).")

if __name__ == '__main__':
    main()
