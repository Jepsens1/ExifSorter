# Media Organizer

A Python tool for cleaning and organizing large collections of **photos and videos**.  
It detects duplicate files, resolves filename conflicts, and sorts media into folders by year using **EXIF data** (for images) or **metadata tags** (for videos).  

---

## ✨ Features
- 🔍 **Detect duplicates** (by SHA-256 hash) and move them into a dedicated `duplicates/` folder.
- 🗂 **Resolve filename conflicts** by renaming files or moving those without metadata to a special folder.
- 📸 **Read EXIF metadata** (DateTimeOriginal) from images.
- 🎥 **Extract creation date** from videos using `ffprobe`.
- 📅 **Auto-sort media** into year-based folders:
  - e.g. `2021/20210101_123456_photo.jpg`
- 🛠 Handles images without EXIF and videos without metadata by moving them into a `withoutexif/` folder.
- ⚡ Works recursively through subfolders.

---
## ⚙️ Requirements

* Python 3.8+ (I used 3.13.5)
* piexif
* ffmpeg (for ffprobe)

## 🚀 Usage
```bash
python main.py /path/to/your/media/folder
```
