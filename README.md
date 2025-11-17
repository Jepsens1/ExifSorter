# ExifSorter: Python script for cleaning and organizing large collections of photos and videos.  

Python script that detects duplicate files, resolves filename conflicts, and sorts media into folders by year using **EXIF data** (for images) or **metadata tags** (for videos).

## Motivation
Family members have used Dropbox for 15+ years and used that for storing precious family photos and videos.
Over time the Dropbox share got so messy, duplicate files across different directories in the share, duplicate filenames across different directories but with different content.
The share size was **180GB** and it was impossible for me to easily sort this mess manually. So i created this Python script that helped me clean and organize files into year-based folders
And ended up reducing the share size down to **117GB**

## 🚀 Getting Started

### ⚙️ Requirements

* Python 3.8+ (I use 3.13.5)
* piexif
* ffmpeg

### Clone repository
```bash
git clone https://github.com/Jepsens1/ExifSorter
cd ExifSorter
```
### Create virtual environment
```
python -m venv .venv
```
#### Activate on Windows
```bash
# cmd
.venv\Scripts\activate

# PowerShell
.venv\Scripts\Activate.ps1
```
#### Activate on macOS / Linux
```bash
source .venv/bin/activate
```

### Install dependencies
#### Install piexif
```bash
pip install piexif
```
#### Install ffmpeg
```bash
# macOS (With Homebrew):
brew install ffmpeg

# Windows (With Chocolatey):
choco install ffmpeg

# Linux (Debian based)
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

## 📖 Usage
To run the script, run the following command in the terminal
```bash
python main.py /path/to/your/folder-to-sort
```

## ✨ Features
- 🔍 **Detect duplicates** (by SHA-256 hash) and move them into a dedicated `duplicates/` folder.
- 🗂 **Resolve filename conflicts** by renaming files or moving those without metadata to a special folder.
- 📸 **Read EXIF metadata** (DateTimeOriginal) from images.
- 🎥 **Extract creation date** from videos using `ffprobe`.
- 📅 **Auto-sort media** into year-based folders:
  - e.g. `2021/20210101_123456_photo.jpg`
- 🛠 Handles images without EXIF and videos without metadata by moving them into a `withoutexif/` folder.
- ⚡ Works recursively through subfolders.
