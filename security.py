"""Patient record encryption and input checks."""

import os
import re
from cryptography.fernet import Fernet

DATA_DIR = "data"
KEY_FILE = os.path.join(DATA_DIR, ".secret.key")
ENC_HISTORY = os.path.join(DATA_DIR, "patient_history_enc.csv")

os.makedirs(DATA_DIR, exist_ok=True)

INJECTION_PATTERNS = [
    r"<script.*?>",
    r"javascript:",
    r"on\w+\s*=",
    r"(--|;|\/\*|\*\/)",
    r"(DROP|DELETE|INSERT|UPDATE|SELECT|UNION|EXEC)\s",
    r"\.\./",
    r"eval\(",
    r"__import__",
]


def _load_or_create_key() -> bytes:
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key


def get_cipher() -> Fernet:
    return Fernet(_load_or_create_key())


def encrypt_value(plain_text: str) -> str:
    return get_cipher().encrypt(plain_text.encode()).decode()


def decrypt_value(cipher_text: str) -> str:
    try:
        return get_cipher().decrypt(cipher_text.encode()).decode()
    except Exception:
        return "[UNREADABLE]"


def encrypt_record(record: dict) -> dict:
    sensitive_fields = ["Name", "Age", "Sex", "Symptoms"]
    encrypted = record.copy()
    for field in sensitive_fields:
        if field in encrypted:
            encrypted[field] = encrypt_value(str(encrypted[field]))
    return encrypted


def decrypt_record(record: dict) -> dict:
    sensitive_fields = ["Name", "Age", "Sex", "Symptoms"]
    decrypted = record.copy()
    for field in sensitive_fields:
        if field in decrypted:
            decrypted[field] = decrypt_value(str(decrypted[field]))
    return decrypted


def sanitize_input(text: str, field_name: str = "input") -> dict:
    if not text or not isinstance(text, str):
        return {"valid": True, "clean_text": "", "warning": ""}

    if len(text) > 1000:
        return {
            "valid": False,
            "clean_text": "",
            "warning": f"{field_name} is too long (maximum 1000 characters).",
        }

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return {
                "valid": False,
                "clean_text": "",
                "warning": f"Invalid characters in {field_name}. Please re-enter using ordinary text.",
            }

    clean = re.sub(r"<[^>]+>", "", text)
    clean = clean.replace("\x00", "").strip()
    return {"valid": True, "clean_text": clean, "warning": ""}
