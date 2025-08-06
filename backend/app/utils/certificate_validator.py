"""
Certificate Validation Utilities

This module handles certificate validation for secure authentication
and license verification using the provided public key.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
from loguru import logger


class CertificateValidator:
    """Handles certificate validation and signature verification."""
    
    def __init__(self, certificate_path: Optional[str] = None):
        self.logger = logger
        self.certificate_path = certificate_path or "public_key.pem"
        self._public_key = None
    
    def load_public_key(self) -> bool:
        """
        Load the public key from the certificate file.
        
        Returns:
            bool: True if key loaded successfully, False otherwise
        """
        try:
            # Check if file exists
            cert_file = Path(self.certificate_path)
            if not cert_file.exists():
                self.logger.error(f"Certificate file not found: {self.certificate_path}")
                return False
            
            # Read and load the public key
            with open(cert_file, 'rb') as f:
                public_key_data = f.read()
            
            self._public_key = serialization.load_pem_public_key(public_key_data)
            
            # Verify it's an RSA key
            if not isinstance(self._public_key, rsa.RSAPublicKey):
                self.logger.error("Certificate is not an RSA public key")
                return False
            
            self.logger.info("Public key loaded successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading public key: {e}")
            return False
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """
        Verify a signature against the provided data.
        
        Args:
            data (str): Original data that was signed
            signature (str): Base64 encoded signature to verify
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            if not self._public_key:
                if not self.load_public_key():
                    return False
            
            # Decode signature from base64
            import base64
            signature_bytes = base64.b64decode(signature)
            data_bytes = data.encode('utf-8')
            
            # Verify signature using RSA-PSS
            self._public_key.verify(
                signature_bytes,
                data_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            self.logger.info("Signature verification successful")
            return True
            
        except InvalidSignature:
            self.logger.warning("Invalid signature provided")
            return False
        except Exception as e:
            self.logger.error(f"Error verifying signature: {e}")
            return False
    
    def verify_license_response(self, response_data: Dict[str, Any]) -> bool:
        """
        Verify the signature in a license verification response.
        
        Args:
            response_data (dict): Response from license verification endpoint
            
        Returns:
            bool: True if response signature is valid, False otherwise
        """
        try:
            # Extract signature and create verification data
            signature = response_data.get('signature')
            if not signature:
                self.logger.warning("No signature found in license response")
                return False
            
            # Create verification string from response data (excluding signature)
            verification_data = {
                'status': response_data.get('status'),
                'message': response_data.get('message'),
                'License ID': response_data.get('License ID')
            }
            
            # Sort keys for consistent verification
            verification_string = json.dumps(verification_data, sort_keys=True)
            
            return self.verify_signature(verification_string, signature)
            
        except Exception as e:
            self.logger.error(f"Error verifying license response: {e}")
            return False
    
    def get_certificate_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the loaded certificate.
        
        Returns:
            dict: Certificate information or None if not loaded
        """
        try:
            if not self._public_key:
                if not self.load_public_key():
                    return None
            
            key_size = self._public_key.key_size
            public_numbers = self._public_key.public_numbers()
            
            # Generate fingerprint
            public_key_der = self._public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            fingerprint = hashlib.sha256(public_key_der).hexdigest()[:16]
            
            return {
                'key_size': key_size,
                'algorithm': 'RSA',
                'fingerprint': fingerprint,
                'modulus_size': key_size,
                'exponent': public_numbers.e,
                'certificate_path': self.certificate_path,
                'is_loaded': True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting certificate info: {e}")
            return None
    
    def validate_certificate_chain(self, certificate_chain: list) -> Tuple[bool, str]:
        """
        Validate a certificate chain (placeholder for future enhancement).
        
        Args:
            certificate_chain (list): List of certificates in the chain
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # For now, just validate that we can load our public key
            if not self._public_key:
                if not self.load_public_key():
                    return False, "Failed to load public key"
            
            return True, "Certificate validation successful"
            
        except Exception as e:
            return False, f"Certificate validation failed: {e}"


class SecurityUtils:
    """Additional security utilities for authentication."""
    
    @staticmethod
    def generate_secure_hash(data: str, salt: str = "") -> str:
        """
        Generate a secure hash of the provided data.
        
        Args:
            data (str): Data to hash
            salt (str): Optional salt for additional security
            
        Returns:
            str: Hexadecimal hash string
        """
        combined_data = f"{salt}{data}{salt}".encode('utf-8')
        return hashlib.sha256(combined_data).hexdigest()
    
    @staticmethod
    def validate_license_uuid_format(license_uuid: str) -> bool:
        """
        Validate that the license UUID is in the correct format.
        
        Args:
            license_uuid (str): License UUID to validate
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        import re
        
        # UUID4 pattern: 8-4-4-4-12 hexadecimal digits
        uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        
        return bool(re.match(uuid_pattern, license_uuid))
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """
        Sanitize user input to prevent injection attacks.
        
        Args:
            input_string (str): Input to sanitize
            
        Returns:
            str: Sanitized input
        """
        if not isinstance(input_string, str):
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '&', '"', "'", ';', '(', ')', '{', '}']
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()


# Global instance for easy access
certificate_validator = CertificateValidator()
security_utils = SecurityUtils()


async def verify_license_signature(response_data: Dict[str, Any]) -> bool:
    """
    Async wrapper for license signature verification.
    
    Args:
        response_data (dict): License verification response
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    return certificate_validator.verify_license_response(response_data)


def get_certificate_status() -> Dict[str, Any]:
    """
    Get the current status of the certificate validator.
    
    Returns:
        dict: Certificate status information
    """
    info = certificate_validator.get_certificate_info()
    if info:
        return {
            'status': 'loaded',
            'info': info
        }
    else:
        return {
            'status': 'not_loaded',
            'error': 'Certificate not loaded or invalid'
        }