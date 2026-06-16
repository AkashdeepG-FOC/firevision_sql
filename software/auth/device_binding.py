import uuid
import platform
import hashlib

def get_device_fingerprint() -> str:
    """
    Generate a unique hardware fingerprint for the current device.
    Uses MAC address, machine architecture, and platform details.
    """
    # uuid.getnode() returns the MAC address. If not available, it generates a random one.
    # To make it more stable across network changes, we could use WMI on Windows,
    # but getnode is a good cross-platform start.
    mac = str(uuid.getnode())
    system_info = f"{platform.system()}-{platform.machine()}-{platform.processor()}"
    
    # Combine and hash to create a fixed-length fingerprint
    raw_fingerprint = f"{mac}|{system_info}"
    return hashlib.sha256(raw_fingerprint.encode('utf-8')).hexdigest()

def verify_device_fingerprint(stored_fingerprint: str) -> bool:
    """Verify if the current device matches the stored fingerprint."""
    if not stored_fingerprint:
        return False
    current = get_device_fingerprint()
    return current == stored_fingerprint
