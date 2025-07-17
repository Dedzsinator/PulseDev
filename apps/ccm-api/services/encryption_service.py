import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import json

class EncryptionService:
    def __init__(self, password: str = None):
        """Initialize encryption service with AES-256-GCM equivalent using Fernet"""
        if password is None:
            password = os.getenv('CCM_ENCRYPTION_KEY', 'default_ccm_key_change_in_prod')
        
        # Generate key from password
        salt = b'ccm_salt_change_this'  # In production, use random salt per user
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
    
    def encrypt_context(self, data: dict) -> str:
        """Encrypt context data"""
        try:
            json_data = json.dumps(data, default=str)
            encrypted_data = self.cipher.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")
    
    def decrypt_context(self, encrypted_data: str) -> dict:
        """Decrypt context data"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")
    
    def is_sensitive_path(self, file_path: str) -> bool:
        """Check if file path contains sensitive information"""
        sensitive_patterns = [
            '.env', '.secret', 'node_modules', '.git',
            'password', 'token', 'key', 'secret',
            '__pycache__', '.cache', 'logs'
        ]
        return any(pattern in file_path.lower() for pattern in sensitive_patterns)