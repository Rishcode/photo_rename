
import argparse
import base64
import json
import re
import sys
import time
from pathlib import Path

import requests

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
MAX_NAME_LEN = 60

PROMPT = (
    "Describe this image in 3 to 6 words suitable for a filename. "
    "Use only concrete nouns and adjectives you can clearly see. "
    "No punctuation, no quotes, no file extension, just the words. "
    "Example: 'golden retriever on beach' or 'red brick cafe at night'."
)


def encode_image(path: Path) -> str:
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else f"image/{path.suffix.lower().lstrip('.')}"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def caption_image(path: Path, timeout: int = 120) -> str:
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": encode_image(path)}},
                ],
            }
        ],
        "temperature": 0.2,
        "max_tokens": 40,
    }
    r = requests.post(LM_STUDIO_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()




def unique_path(target: Path, taken: set) -> Path:
    if target not in taken and not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    n = 2
    while True:
        candidate = target.with_name(f"{stem}-{n}{suffix}")
        if candidate not in taken and not candidate.exists():
            return candidate
        n += 1


def check_server() -> bool:
    try:
        r = requests.get("http://localhost:1234/v1/models", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path, help="Folder containing photos")
    ap.add_argument("--apply", action="store_true", help="Actually rename (default is dry-run)")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subfolders")
    args = ap.parse_args()

    if not args.folder.is_dir():
        print(f"Not a directory: {args.folder}", file=sys.stderr)
        return 1

    if not check_server():
        print("LM Studio server not reachable at http://localhost:1234", file=sys.stderr)
        print("Start the server in LM Studio (Local Server tab → Start Server).", file=sys.stderr)
        return 1

    pattern = "**/*" if args.recursive else "*"
    photos = sorted(p for p in args.folder.glob(pattern) if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if not photos:
        print("No images found.")
        return 0

    print(f"Found {len(photos)} image(s). Mode: {'APPLY' if args.apply else 'DRY-RUN'}\n")

    planned = []
    taken = set()
    for i, src in enumerate(photos, 1):
        print(f"[{i}/{len(photos)}] {src.name} ... ", end="", flush=True)
        t0 = time.time()
        try:
            caption = caption_image(src)
        except Exception as e:
            print(f"FAILED: {e}")
            continue
        slug = slugify(caption)
        dst = unique_path(src.with_name(slug + src.suffix.lower()), taken)
        taken.add(dst)
        planned.append((src, dst))
        print(f"-> {dst.name}  ({time.time() - t0:.1f}s)")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to rename these files.")
        return 0

    print("\nApplying renames...")
    renamed = 0
    for src, dst in planned:
        if src == dst:
            continue
        try:
            src.rename(dst)
            renamed += 1
        except OSError as e:
            print(f"  skip {src.name}: {e}")
    print(f"Renamed {renamed} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
