import subprocess
import piexif
from helpers.console import print_error


def get_file_datetime(filepath):
    ext = filepath.suffix.lower()
    if ext in [".jpg", ".jpeg", ".png", ".heic"]:
        dt = _get_exif_datetime(filepath)
        if dt:
            return dt.replace(":", "").replace(" ", "_")
    elif ext in [".mp4", ".mov", ".avi", ".mkv", ".mod", ".mpg"]:
        return _get_video_creation_date(filepath)
    return None


def _get_exif_datetime(filepath):
    try:
        exif_dict = piexif.load(str(filepath))
        datetime_original = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
        if datetime_original:
            return datetime_original.decode("utf-8")
        datetime_digital = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeDigitized)
        if datetime_digital:
            return datetime_digital.decode("utf-8")
    except Exception as ex:
        print_error(f"ERROR: Could not read EXIF for {filepath}: {ex}")
    return None


def _get_video_creation_date(filepath):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format_tags=creation_time",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(filepath),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output = result.stdout.strip()
        if output:
            return output.replace("-", "").replace(":", "").replace("T", "_")[:15]

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream_tags=creation_time",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(filepath),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output = result.stdout.strip()
        if output:
            return output.replace("-", "").replace(":", "").replace("T", "_")[:15]
    except Exception as ex:
        print_error(f"ERROR: Failed to read Metadata (video): {filepath.name}: {ex}")
    return None
