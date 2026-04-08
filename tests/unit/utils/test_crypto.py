import pytest
from src.utils.crypto import encrypt_api_key, decrypt_api_key


def test_encrypt_decrypt_round_trip():
    original = "sk-test-123456"
    encrypted = encrypt_api_key(original)
    assert encrypted != original
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == original


def test_encrypt_none_returns_none():
    assert encrypt_api_key(None) is None


def test_decrypt_none_returns_none():
    assert decrypt_api_key(None) is None


def test_different_ciphertexts():
    """Fernet 使用随机 IV，即使相同明文也会产生不同密文"""
    enc1 = encrypt_api_key("sk-test")
    enc2 = encrypt_api_key("sk-test")
    assert enc1 != enc2
