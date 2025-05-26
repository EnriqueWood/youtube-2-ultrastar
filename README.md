# YouTube to UltraStar Converter Script

> **Credit:** This script is a convenience wrapper for the [UltraSinger](https://github.com/rakuri255/UltraSinger/) project.  
> All credit for the core functionality goes to the UltraSinger authors and contributors.

## What This Script Does

This repository contains a simple Bash script that:

1. Prepares and configures a Docker environment for UltraSinger (CPU-only, for now).
2. Automatically mounts cache, output, and configuration directories.
3. Builds and runs the `rakuri255/ultrasinger:latest` container.
4. Supports both YouTube URLs and local media files (MP3/MP4).
5. Forwards additional UltraSinger flags for custom model/options (e.g., `--language en`).
6. Auto-installs MuseScore 3 in the container for sheet music (MusicXML, PDF not supported yet).

It does **not** modify or include any of the original UltraSinger code—it simply automates the setup and execution steps.

## Requirements

- Docker

## GUI Usage

In addition to the command-line script, this project includes a graphical interface (GUI) designed for ease of use.

Make sure you have Docker already installed on your system or the program will not allow you to continue without it.
Once you have docker installed, paste the URL of the Youtube video or the path to your local mp3/mp4 local file
and press 

## Usage for Linux Users

1. Ensure you have `docker` and `docker compose` installed.
2. Download or clone this repository.
3. Make the converter script executable:
   ```bash
   chmod +x convert
   ```
4. Run the script:

   **Basic (YouTube URL only):**
   ```bash
   ./convert "https://www.youtube.com/watch?v=VIDEO_ID"
   ```

   **Local file (MP3/MP4):**
   ```bash
   ./convert "/full/path/to/song.mp4"
   ```

   **Advanced:**
   ```bash
   ./convert <INPUT_SOURCE> [workdir] [--language xx] [additional UltraSinger flags]
   ```
   - `INPUT_SOURCE`: YouTube URL or full path to local MP3/MP4.
   - `workdir`: directory where `songs/` will be created (default: current directory).
   - `--language xx`: override language detection (e.g., `--language en` or `--language es`).
   - Additional flags (e.g., `--whisper large-v2`, `--format_version 2.0.0`) will be forwarded to UltraSinger.

   Example:
   ```bash
   ./convert "https://www.youtube.com/watch?v=VIDEO_ID" ~/my_songs --language en --whisper large-v2 --format_version 2.0.0
   ```

5. Find your UltraStar files in `songs/output/` under the chosen working directory.

## Disclaimer

This script is provided **as-is** and is intended solely to simplify the process of converting YouTube videos or local media for use with UltraStar.  
Use it at your own risk. The author of this wrapper script **assumes no responsibility** for any damages, misuse, or legal issues that may arise from its use.  
Please respect YouTube’s Terms of Service and any applicable copyright laws when downloading or converting video content.  
Use only content you own or have permission to use—pirated material is strictly prohibited.
