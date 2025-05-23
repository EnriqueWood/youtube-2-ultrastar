# YouTube to UltraStar Converter Script

> **Credit:** This script is a convenience wrapper for the [UltraSinger](https://github.com/rakuri255/UltraSinger/) project.  
> All credit for the core functionality goes to the UltraSinger authors and contributors.

## What This Script Does

This repository contains a simple Bash script that:

1. Prepares and configures a Docker environment for UltraSinger (CPU-only, for now).
2. Automatically mounts cache, output, and configuration directories.
3. Builds and runs the `rakuri255/ultrasinger:latest` container.
4. Downloads and converts a YouTube video into UltraStar-compatible files (MIDI, notes, lyrics).

It does **not** modify or include any of the original UltraSinger code—it merely automates the setup and execution steps.

## Usage

1. Ensure you have `docker` and `docker compose` installed.
2. Clone or download this repository.
3. Make the converter script executable:
   ```bash
   chmod +x convert
   ```
4. Usage:
   
   Basic: Run the script with a YouTube URL (or the path to an .mp3 file):
   
   ```bash
   ./convert "https://www.youtube.com/watch?v=VIDEO_ID"
   ```
   
   Advanced:
   ```bash
    ./convert <INPUT_SOURCE> [workdir] [--language xx] [additional UltraSinger flags]
    ```
    
    - INPUT_SOURCE: full URL to a YouTube video or mp3 song locally
    - workdir: directory where 'songs' will be created (default: $PWD)
    - --language xx: override language detection, (i.e `--language en` or `--language es`)
    - additional flags passed to UltraSinger
      
   ```bash
   ./convert "https://www.youtube.com/watch?v=VIDEO_ID" ~/myultrastarsongs/ --language en --whisper large-v2 --format_version 2.0.0
   ```
   
   For more documentation on additional UltraSinger flags, refer to the [UltraSigner repo](https://github.com/rakuri255/UltraSinger)
   
5. Find your UltraStar files.

   Your UltraStar files will be located on your current directory if you did not pass an argument, otherwise, they will be in the argument passed after the input path (~/myultrastarsongs/ in the advanced example)

## Disclaimer

This script is provided **as-is** and is intended solely to simplify the process of converting YouTube videos for use with UltraStar.  
Use it at your own risk. The author of this wrapper script **assumes no responsibility** for any damages, misuse, or legal issues that may arise from its use.  
Please respect YouTube’s Terms of Service and any applicable copyright laws when downloading or converting video content.
Please use only content you own or have permission to use—pirated material is strictly prohibited.
