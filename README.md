# Photo Namer

Rename photos using short AI-generated descriptions from a local LM Studio server.

## Requirements

- Python 3.9+
- LM Studio running a local vision-capable model
- Local server started at `http://localhost:1234`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start LM Studio:
   - Open LM Studio
   - Load a vision-capable model
   - Local Server tab -> Start Server

## Usage

Dry-run (default):

```bash
python rename_photos.py "C:\\path\\to\\photos"
```

Apply renames:

```bash
python rename_photos.py "C:\\path\\to\\photos" --apply
```

Recursive scan:

```bash
python rename_photos.py "C:\\path\\to\\photos" --recursive --apply
```

## How It Works

- Each image is sent to the local LM Studio server for a 3-6 word description.
- The description is slugified into a filename.
- Collisions are avoided by adding a numeric suffix.
- By default, the tool prints a plan without renaming.

## Supported Formats

`jpg`, `jpeg`, `png`, `webp`, `bmp`, `gif`

## Notes

- If the server is not reachable, the script exits with a clear message.
- Filenames are capped at 60 characters.
