from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import os

def generate_rsa_keys():
    """Generate RSA private and public keys for JWT signing"""
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Generate public key
    public_key = private_key.public_key()
    
    # Serialize private key to PEM format
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key to PEM format
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Create keys directory if it doesn't exist
    keys_dir = "keys"
    if not os.path.exists(keys_dir):
        os.makedirs(keys_dir)
    
    # Save private key
    with open(os.path.join(keys_dir, "private_key.pem"), "wb") as f:
        f.write(private_pem)
    
    # Save public key
    with open(os.path.join(keys_dir, "public_key.pem"), "wb") as f:
        f.write(public_pem)
    
    print("RSA keys generated successfully!")
    print(f"Private key saved to: {os.path.join(keys_dir, 'private_key.pem')}")
    print(f"Public key saved to: {os.path.join(keys_dir, 'public_key.pem')}")

if __name__ == "__main__":
    generate_rsa_keys() 