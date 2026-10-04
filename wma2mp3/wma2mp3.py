#!/usr/bin/env python3
"""Batch-convert WMA files to MP3 using ffmpeg."""

import argparse
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def find_wma_files(inputs, recursive):
    """Yield (file, base_dir) pairs for every .wma file in the given inputs."""
    for item in inputs:
        path = Path(item).expanduser()
        if path.is_file() and path.suffix.lower() == ".wma":
            yield path, path.parent
        elif path.is_dir():
            pattern = "**/*" if recursive else "*"
            for f in sorted(path.glob(pattern)):
                if f.is_file() and f.suffix.lower() == ".wma":
                    yield f, path
        else:
            print(f"warning: skipping {item} (not a .wma file or directory)", file=sys.stderr)


def output_path_for(src, base_dir, out_dir):
    """Work out where the MP3 goes, mirroring subfolders when out_dir is set."""
    if out_dir is None:
        return src.with_suffix(".mp3")
    return (out_dir / src.relative_to(base_dir)).with_suffix(".mp3")


def convert(src, dst, bitrate, overwrite):
    """Convert one file. Returns (src, status, message)."""
    if dst.exists() and not overwrite:
        return src, "skipped", f"{dst} already exists"
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Write to a .part file and rename on success, so an interrupted run
    # never leaves a truncated .mp3 that later runs would skip.
    part = dst.with_name(dst.name + ".part")
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(src),
        "-vn",
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        "-map_metadata", "0",
        "-id3v2_version", "3",
        "-f", "mp3",
        str(part),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return src, "failed", result.stderr.strip()
        part.replace(dst)
    finally:
        part.unlink(missing_ok=True)
    return src, "converted", str(dst)


def main():
    parser = argparse.ArgumentParser(description="Batch-convert WMA files to MP3.")
    parser.add_argument("inputs", nargs="+", help="WMA files and/or directories")
    parser.add_argument("-o", "--out-dir", type=Path,
                        help="output directory (default: next to each source file)")
    parser.add_argument("-b", "--bitrate", default="192k", help="MP3 bitrate (default: 192k)")
    parser.add_argument("-r", "--recursive", action="store_true", help="search directories recursively")
    parser.add_argument("-f", "--overwrite", action="store_true", help="overwrite existing MP3 files")
    parser.add_argument("-j", "--jobs", type=int, default=4, help="parallel conversions (default: 4)")
    parser.add_argument("--delete-source", action="store_true",
                        help="delete each WMA after it converts successfully")
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None:
        sys.exit("error: ffmpeg not found. Install it (e.g. `brew install ffmpeg`).")

    out_dir = args.out_dir.expanduser() if args.out_dir else None
    jobs = [(src, output_path_for(src, base, out_dir))
            for src, base in find_wma_files(args.inputs, args.recursive)]
    if not jobs:
        print("No .wma files found.")
        return

    counts = {"converted": 0, "skipped": 0, "failed": 0}
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = [pool.submit(convert, src, dst, args.bitrate, args.overwrite) for src, dst in jobs]
        for future in as_completed(futures):
            src, status, message = future.result()
            counts[status] += 1
            print(f"[{status}] {src}" + (f": {message}" if status != "converted" else f" -> {message}"))
            if status == "converted" and args.delete_source:
                src.unlink()

    print(f"\nDone: {counts['converted']} converted, {counts['skipped']} skipped, {counts['failed']} failed.")
    sys.exit(1 if counts["failed"] else 0)


if __name__ == "__main__":
    main()
