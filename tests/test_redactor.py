# OWNER: Dev B
from apps.ingestion.redactor import redact

def test_password_removed():
    out, n = redact("Registrar login password: Hunter2!")
    assert "Hunter2" not in out and n >= 1

def test_api_key_removed():
    out, _ = redact("key sk-abcdefghijklmnopqrstuvwx")
    assert "sk-abcdef" not in out