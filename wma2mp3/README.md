# wma2mp3

Batch-convert WMA audio files to MP3. Part of [file-alchemy](../).

## Requirements

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/) (`brew install ffmpeg` on macOS)

## Usage

```bash
# Convert every .wma in a folder (MP3s are written next to the originals)
python3 wma2mp3/wma2mp3.py ~/Music/old

# Recurse into subfolders and write to a separate folder, mirroring structure
python3 wma2mp3/wma2mp3.py ~/Music/old -r -o ~/Music/mp3

# Higher bitrate, overwrite existing MP3s, 8 parallel jobs
python3 wma2mp3/wma2mp3.py song1.wma song2.wma -b 320k -f -j 8
```

| Option | Description |
| --- | --- |
| `-o, --out-dir` | Output directory (default: alongside each source file) |
| `-b, --bitrate` | MP3 bitrate (default: `192k`) |
| `-r, --recursive` | Search directories recursively |
| `-f, --overwrite` | Overwrite existing MP3s (default: skip them) |
| `-j, --jobs` | Number of parallel conversions (default: 4) |
| `--delete-source` | Delete each WMA after a successful conversion |

Tags (artist, title, album, and so on) are copied into ID3v2.3 tags.

Each MP3 is written to a temporary `.part` file and renamed when it is
complete, so an interrupted run never leaves a truncated `.mp3` behind.
