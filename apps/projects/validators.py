# Owner Dev: A
import zipfile

SYNC = (b"ID3", b"ADIF")
SIGNATURES = {
    ".pdf": (b"%PDF",), ".png": (b"\x89PNG\r\n\x1a\n",), ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",), ".webp": (b"RIFF",), ".wav": (b"RIFF",),
    ".ogg": (b"OggS",), ".flac": (b"fLaC",), ".docx": (b"PK\x03\x04",),
}
TEXT_EXT = {".txt", ".md", ".csv"}
MB = 1024 * 1024


def check_content(f, ext):
    """Returns a problem description, or None if the content matches the extension."""
    head = f.read(16)
    f.seek(0)
    if ext in TEXT_EXT:
        sample = f.read(8192)
        f.seek(0)
        return "does not look like a text file" if b"\x00" in sample else None
    if ext in (".mp3", ".aac"):
        ok = head.startswith(SYNC) or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0)
        return None if ok else "does not look like an audio file"
    sigs = SIGNATURES.get(ext)
    if not sigs or not head.startswith(sigs):
        return "has content that does not match its file type"
    if ext == ".webp" and head[8:12] != b"WEBP":
        return "has content that does not match its file type"
    if ext == ".wav" and head[8:12] != b"WAVE":
        return "has content that does not match its file type"
    if ext == ".docx":
        try:
            with zipfile.ZipFile(f) as z:
                if sum(i.file_size for i in z.infolist()) > 100 * MB:
                    return "is too large once unpacked"
        except zipfile.BadZipFile:
            return "is not a valid Word file"
        finally:
            f.seek(0)
    return None