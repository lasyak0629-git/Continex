# Owner Dev: A
import os


def scan(f):
    """Returns None if clean, or a message. Uses a ClamAV daemon when CLAMD_HOST is set.
    With CLAMD_REQUIRED=1 an unavailable scanner blocks uploads (fail closed)."""
    required = os.getenv("CLAMD_REQUIRED") == "1"
    host = os.getenv("CLAMD_HOST")
    if not host:
        return "could not be scanned: no virus scanner is configured." if required else None
    try:
        import clamd
        cd = clamd.ClamdNetworkSocket(host=host, port=int(os.getenv("CLAMD_PORT", "3310")), timeout=30)
        f.seek(0)
        status, sig = cd.instream(f).get("stream", ("ERROR", None))
        f.seek(0)
    except Exception:
        return "could not be scanned right now. Please try again shortly." if required else None
    if status == "FOUND":
        return f"was rejected: it contains malware ({sig})."
    return None if status == "OK" else "could not be scanned. Please try again."