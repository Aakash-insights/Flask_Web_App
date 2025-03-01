import os
import secrets

def generate_secret_key(file_path=None):
    """
    Generate and manage secret key with secure file handling
    """
    if not file_path:
        file_path = os.path.join(os.path.dirname(__file__), '.secret_key')
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read().strip()
        else:
            secret_key = secrets.token_urlsafe(32)
            with open(file_path, 'w') as f:
                f.write(secret_key)
            os.chmod(file_path, 0o600)  # Secure file permissions
            return secret_key
    except IOError as e:
        raise RuntimeError(f"Key file error: {str(e)}")