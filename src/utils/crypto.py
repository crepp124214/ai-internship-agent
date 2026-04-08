"""
加密工具模块
提供 API Key 的对称加密/解密功能
"""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet

from src.utils.config_loader import get_settings


# 模块级 Fernet 实例缓存
_fernet_instance: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    """延迟初始化 Fernet 实例"""
    global _fernet_instance
    if _fernet_instance is None:
        secret_key = get_settings().SECRET_KEY
        key_bytes = secret_key.encode("utf-8")

        # 密钥处理：不足32字节用urandom补足，超长截断
        if len(key_bytes) < 32:
            key_bytes = key_bytes + os.urandom(32 - len(key_bytes))
        elif len(key_bytes) > 32:
            key_bytes = key_bytes[:32]

        # 转换为 URL-safe base64 作为 Fernet 密钥
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        _fernet_instance = Fernet(fernet_key)

    return _fernet_instance


def encrypt_api_key(api_key: Optional[str]) -> Optional[str]:
    """
    加密 API Key

    Args:
        api_key: 明文 API Key

    Returns:
        Fernet 加密后的 base64 字符串，None 输入返回 None
    """
    if api_key is None:
        return None

    fernet = _get_fernet()
    encrypted_bytes = fernet.encrypt(api_key.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_api_key(encrypted: Optional[str]) -> Optional[str]:
    """
    解密 API Key

    Args:
        encrypted: Fernet 加密后的 base64 字符串

    Returns:
        明文 API Key，None 输入返回 None
    """
    if encrypted is None:
        return None

    fernet = _get_fernet()
    decrypted_bytes = fernet.decrypt(encrypted.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
