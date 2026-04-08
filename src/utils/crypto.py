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

# 固定盐值，用于从 SECRET_KEY 派生确定性加密密钥
_FERNET_SALT = b"ai-internship-agent-v1"


def _get_fernet() -> Fernet:
    """延迟初始化 Fernet 实例"""
    global _fernet_instance
    if _fernet_instance is None:
        secret_key = get_settings().SECRET_KEY
        key_bytes = secret_key.encode("utf-8")

        # 使用固定盐派生确定性密钥，确保相同 SECRET_KEY 始终产生相同加密密钥
        combined = _FERNET_SALT + key_bytes
        if len(combined) > 32:
            combined = combined[:32]
        else:
            combined = combined.ljust(32, b'\0')

        # 转换为 URL-safe base64 作为 Fernet 密钥
        fernet_key = base64.urlsafe_b64encode(combined)
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
