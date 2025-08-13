#!/usr/bin/env python3
"""
IP Address Masking Utility for Log Security
Masks IP addresses in logs before sending to LLMs/agents
"""

import re
import json
import ipaddress
from typing import Dict, List, Union, Tuple


class IPMasker:
    """Handles IP address masking in logs and text content"""
    
    # Regex patterns for different IP formats
    IPV4_PATTERN = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    IPV6_PATTERN = r'(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
    
    # Common IP patterns in AWS logs
    AWS_IP_PATTERNS = [
        # ELB access logs: client:port -> target:port
        r'(\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}\b)',
        # VPC Flow logs format
        r'srcaddr=(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
        r'dstaddr=(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
        # CloudFront logs
        r'c-ip\s+(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
        # Common log formats
        r'from\s+(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
        r'to\s+(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
        r'client[_\s]+ip[:\s]+(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
        r'source[_\s]+ip[:\s]+(\b(?:\d{1,3}\.){3}\d{1,3}\b)',
        r'remote[_\s]+addr[:\s]+(\b(?:\d{1,3}\.){3}\d{1,3}\b)'
    ]
    
    def __init__(self, mask_type: str = "partial"):
        """
        Initialize IP Masker
        
        Args:
            mask_type: Type of masking - "partial", "full", or "hash"
        """
        self.mask_type = mask_type
        self.ip_mapping = {}  # Store original -> masked mapping for consistency
        self.masked_count = 0
        
    def mask_ip(self, ip: str) -> str:
        """
        Mask a single IP address
        
        Args:
            ip: IP address to mask
            
        Returns:
            Masked IP address
        """
        # Check if we've already masked this IP for consistency
        if ip in self.ip_mapping:
            return self.ip_mapping[ip]
            
        try:
            # Validate IP address
            ip_obj = ipaddress.ip_address(ip)
            
            if self.mask_type == "full":
                if isinstance(ip_obj, ipaddress.IPv4Address):
                    masked = "XXX.XXX.XXX.XXX"
                else:
                    masked = "XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX"
            elif self.mask_type == "partial":
                if isinstance(ip_obj, ipaddress.IPv4Address):
                    # Keep first two octets, mask last two
                    octets = ip.split('.')
                    masked = f"{octets[0]}.{octets[1]}.XXX.XXX"
                else:
                    # Keep first 4 segments for IPv6
                    segments = ip.split(':')
                    masked = ':'.join(segments[:4] + ['XXXX'] * (len(segments) - 4))
            elif self.mask_type == "hash":
                # Use a consistent hash-based replacement
                import hashlib
                hash_val = int(hashlib.md5(ip.encode()).hexdigest()[:8], 16)
                if isinstance(ip_obj, ipaddress.IPv4Address):
                    masked = f"10.{(hash_val >> 16) & 255}.{(hash_val >> 8) & 255}.{hash_val & 255}"
                else:
                    masked = f"fd00::{hash_val:x}"
            else:
                masked = ip
                
            self.ip_mapping[ip] = masked
            self.masked_count += 1
            return masked
            
        except ValueError:
            # Not a valid IP, return as-is
            return ip
            
    def mask_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Mask all IP addresses in text
        
        Args:
            text: Text containing IP addresses
            
        Returns:
            Tuple of (masked_text, mapping_dict)
        """
        if not text:
            return text, {}
            
        masked_text = text
        found_ips = {}
        
        # Find and mask IPv4 addresses
        ipv4_matches = re.finditer(self.IPV4_PATTERN, text)
        for match in ipv4_matches:
            original_ip = match.group()
            masked_ip = self.mask_ip(original_ip)
            if original_ip != masked_ip:
                masked_text = masked_text.replace(original_ip, masked_ip)
                found_ips[original_ip] = masked_ip
                
        # Find and mask IPv6 addresses
        ipv6_matches = re.finditer(self.IPV6_PATTERN, text)
        for match in ipv6_matches:
            original_ip = match.group()
            masked_ip = self.mask_ip(original_ip)
            if original_ip != masked_ip:
                masked_text = masked_text.replace(original_ip, masked_ip)
                found_ips[original_ip] = masked_ip
                
        return masked_text, found_ips
        
    def mask_json(self, data: Union[dict, list, str]) -> Union[dict, list, str]:
        """
        Recursively mask IP addresses in JSON data
        
        Args:
            data: JSON data (dict, list, or string)
            
        Returns:
            Masked JSON data
        """
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                masked_data[key] = self.mask_json(value)
            return masked_data
        elif isinstance(data, list):
            return [self.mask_json(item) for item in data]
        elif isinstance(data, str):
            masked_text, _ = self.mask_text(data)
            return masked_text
        else:
            return data
            
    def mask_log_entries(self, log_entries: List[Dict]) -> List[Dict]:
        """
        Mask IP addresses in CloudWatch log entries
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            List of masked log entries
        """
        masked_entries = []
        
        for entry in log_entries:
            masked_entry = entry.copy()
            
            # Mask message field
            if 'message' in masked_entry:
                masked_entry['message'], _ = self.mask_text(masked_entry['message'])
                
            # Mask any JSON data in the message
            if 'message' in masked_entry:
                try:
                    # Try to parse as JSON
                    msg_data = json.loads(masked_entry['message'])
                    masked_msg_data = self.mask_json(msg_data)
                    masked_entry['message'] = json.dumps(masked_msg_data)
                except (json.JSONDecodeError, TypeError):
                    # Not JSON, already masked as text
                    pass
                    
            masked_entries.append(masked_entry)
            
        return masked_entries
        
    def get_masking_stats(self) -> Dict[str, int]:
        """
        Get statistics about masking operations
        
        Returns:
            Dictionary with masking statistics
        """
        return {
            'total_ips_masked': self.masked_count,
            'unique_ips': len(self.ip_mapping),
            'mask_type': self.mask_type
        }
        
    def reset(self):
        """Reset the masker state"""
        self.ip_mapping.clear()
        self.masked_count = 0


def mask_logs_for_llm(logs: Union[str, list, dict], mask_type: str = "partial") -> Union[str, list, dict]:
    """
    Convenience function to mask logs before sending to LLM
    
    Args:
        logs: Log data to mask
        mask_type: Type of masking to apply
        
    Returns:
        Masked log data
    """
    masker = IPMasker(mask_type=mask_type)
    
    if isinstance(logs, str):
        masked_logs, _ = masker.mask_text(logs)
        return masked_logs
    elif isinstance(logs, list):
        if logs and isinstance(logs[0], dict):
            # List of log entries
            return masker.mask_log_entries(logs)
        else:
            # List of strings
            return [masker.mask_text(log)[0] for log in logs]
    elif isinstance(logs, dict):
        return masker.mask_json(logs)
    else:
        return logs


# Example usage and testing
if __name__ == "__main__":
    # Test data
    test_logs = [
        "Error connecting to database at 192.168.1.100:5432",
        "Request from client IP: 10.0.0.5 to server 172.16.0.10",
        "IPv6 connection from 2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        {"message": "Failed login from 192.168.100.50", "level": "ERROR"},
        "VPC Flow: srcaddr=10.0.1.100 dstaddr=10.0.2.200 action=ACCEPT"
    ]
    
    # Test masking
    masker = IPMasker(mask_type="partial")
    
    print("Testing IP Masking:")
    print("-" * 50)
    
    for log in test_logs:
        if isinstance(log, str):
            masked, mapping = masker.mask_text(log)
            print(f"Original: {log}")
            print(f"Masked:   {masked}")
            if mapping:
                print(f"Mapping:  {mapping}")
        else:
            masked = masker.mask_json(log)
            print(f"Original: {log}")
            print(f"Masked:   {masked}")
        print()
        
    print(f"Masking Stats: {masker.get_masking_stats()}")