"""
System Information Collection Utilities

This module provides secure methods to collect system information
for license verification purposes.
"""

import psutil
import socket
import hashlib
import platform
from typing import Dict, List, Optional
from loguru import logger


class SystemInfoCollector:
    """Collects system information for authentication and license verification."""
    
    def __init__(self):
        self.logger = logger
    
    def get_mac_address(self) -> Optional[str]:
        """
        Get the primary MAC address of the system.
        
        Returns:
            str: MAC address in standard format (XX:XX:XX:XX:XX:XX)
            None: If MAC address cannot be determined
        """
        try:
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            
            # Priority order for interface selection
            priority_interfaces = ['eth0', 'en0', 'wlan0', 'Wi-Fi', 'Ethernet']
            
            # First, try priority interfaces
            for interface_name in priority_interfaces:
                if interface_name in interfaces:
                    for addr in interfaces[interface_name]:
                        if addr.family == psutil.AF_LINK:
                            mac = addr.address
                            if mac and mac != '00:00:00:00:00:00':
                                return self._normalize_mac_address(mac)
            
            # If no priority interface found, get first valid MAC
            for interface_name, addresses in interfaces.items():
                if interface_name.startswith('lo'):  # Skip loopback
                    continue
                    
                for addr in addresses:
                    if addr.family == psutil.AF_LINK:
                        mac = addr.address
                        if mac and mac != '00:00:00:00:00:00':
                            return self._normalize_mac_address(mac)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting MAC address: {e}")
            return None
    
    def get_ip_address(self) -> Optional[str]:
        """
        Get the primary IP address of the system.
        
        Returns:
            str: Primary IP address
            None: If IP address cannot be determined
        """
        try:
            # Create a socket to determine the primary IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to a remote address (doesn't actually connect)
                s.connect(('8.8.8.8', 80))
                ip_address = s.getsockname()[0]
                return ip_address
                
        except Exception as e:
            self.logger.error(f"Error getting IP address: {e}")
            # Fallback method
            try:
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
                return ip_address if ip_address != '127.0.0.1' else None
            except Exception as fallback_e:
                self.logger.error(f"Fallback IP detection failed: {fallback_e}")
                return None
    
    def get_system_fingerprint(self) -> Dict[str, str]:
        """
        Generate a unique system fingerprint for license verification.
        
        Returns:
            dict: System fingerprint data
        """
        try:
            mac_address = self.get_mac_address()
            ip_address = self.get_ip_address()
            
            # Create a hash of system information
            system_info = f"{platform.system()}_{platform.machine()}_{mac_address}"
            fingerprint_hash = hashlib.sha256(system_info.encode()).hexdigest()[:16]
            
            return {
                'macAddress': mac_address or 'unknown',
                'ipAddress': ip_address or 'unknown',
                'fingerprint': fingerprint_hash,
                'platform': platform.system(),
                'machine': platform.machine(),
                'hostname': socket.gethostname()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating system fingerprint: {e}")
            return {
                'macAddress': 'unknown',
                'ipAddress': 'unknown',
                'fingerprint': 'unknown',
                'platform': 'unknown',
                'machine': 'unknown',
                'hostname': 'unknown'
            }
    
    def get_network_interfaces(self) -> List[Dict[str, str]]:
        """
        Get detailed information about all network interfaces.
        
        Returns:
            list: List of network interface information
        """
        interfaces = []
        try:
            net_if_addrs = psutil.net_if_addrs()
            
            for interface_name, addresses in net_if_addrs.items():
                interface_info = {'name': interface_name, 'addresses': []}
                
                for addr in addresses:
                    if addr.family == socket.AF_INET:  # IPv4
                        interface_info['addresses'].append({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                    elif addr.family == psutil.AF_LINK:  # MAC
                        interface_info['addresses'].append({
                            'type': 'MAC',
                            'address': self._normalize_mac_address(addr.address)
                        })
                
                if interface_info['addresses']:
                    interfaces.append(interface_info)
            
            return interfaces
            
        except Exception as e:
            self.logger.error(f"Error getting network interfaces: {e}")
            return []
    
    def _normalize_mac_address(self, mac: str) -> str:
        """
        Normalize MAC address to standard format.
        
        Args:
            mac (str): MAC address in any format
            
        Returns:
            str: Normalized MAC address (XX:XX:XX:XX:XX:XX)
        """
        if not mac:
            return ""
        
        # Remove common separators and convert to uppercase
        clean_mac = mac.replace(':', '').replace('-', '').replace('.', '').upper()
        
        # Insert colons every 2 characters
        if len(clean_mac) == 12:
            return ':'.join(clean_mac[i:i+2] for i in range(0, 12, 2))
        
        return mac  # Return original if format is unexpected


# Global instance for easy access
system_info_collector = SystemInfoCollector()


async def get_system_info_for_auth() -> Dict[str, str]:
    """
    Get system information required for authentication.
    
    Returns:
        dict: System information for license verification
    """
    return system_info_collector.get_system_fingerprint()


def get_mac_address() -> Optional[str]:
    """Convenience function to get MAC address."""
    return system_info_collector.get_mac_address()


def get_ip_address() -> Optional[str]:
    """Convenience function to get IP address."""
    return system_info_collector.get_ip_address()