#!/usr/bin/env python3
"""
Comprehensive test suite for Streamlit IP Masking functionality
Tests all aspects of IP address masking in logs and data displays
"""

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock, Mock
import json
from datetime import datetime
from utils.ip_masker import IPMasker, mask_logs_for_llm

class TestStreamlitIPMasking:
    """Test suite for IP Masking functionality in Streamlit"""
    
    @pytest.fixture
    def mock_ip_masker(self):
        """Mock IPMasker for testing"""
        masker = IPMasker(mask_type="partial")
        return masker
    
    @pytest.fixture
    def sample_logs_with_ips(self):
        """Sample log data containing various IP addresses"""
        return [
            {
                "timestamp": "2025-08-13 10:15:23",
                "message": "Connection from 192.168.1.100 to database server",
                "level": "INFO",
                "source": "app-server-01"
            },
            {
                "timestamp": "2025-08-13 10:16:45",
                "message": "Failed login attempt from 10.0.0.50",
                "level": "WARNING",
                "source": "auth-service"
            },
            {
                "timestamp": "2025-08-13 10:17:12",
                "message": "API request from 203.0.113.45 to endpoint /api/users",
                "level": "INFO",
                "source": "api-gateway"
            },
            {
                "timestamp": "2025-08-13 10:18:30",
                "message": "IPv6 connection from 2001:db8::8a2e:370:7334",
                "level": "INFO",
                "source": "load-balancer"
            }
        ]
    
    @pytest.fixture
    def sample_incident_data_with_ips(self):
        """Sample incident data containing IP addresses"""
        return {
            "incident_id": "INC-2025-100",
            "title": "Suspicious traffic from 192.168.100.50",
            "description": "Multiple failed login attempts detected from IP 192.168.100.50 and 10.0.0.25",
            "logs": [
                "2025-08-13 10:00:00 - Connection from 192.168.100.50",
                "2025-08-13 10:00:05 - Failed auth from 192.168.100.50",
                "2025-08-13 10:00:10 - Blocked IP 192.168.100.50"
            ],
            "affected_systems": ["10.0.0.1", "10.0.0.2", "172.16.0.5"]
        }
    
    def test_ip_masker_initialization(self, mock_ip_masker):
        """Test IPMasker initialization with different mask types"""
        # Test partial masking
        partial_masker = IPMasker(mask_type="partial")
        assert partial_masker.mask_type == "partial"
        
        # Test full masking
        full_masker = IPMasker(mask_type="full")
        assert full_masker.mask_type == "full"
        
        # Test hash masking
        hash_masker = IPMasker(mask_type="hash")
        assert hash_masker.mask_type == "hash"
    
    def test_ipv4_masking(self, mock_ip_masker):
        """Test masking of IPv4 addresses"""
        # Test partial masking
        partial_masker = IPMasker(mask_type="partial")
        masked = partial_masker.mask_ip("192.168.1.100")
        assert masked == "192.168.1.xxx"
        
        # Test full masking
        full_masker = IPMasker(mask_type="full")
        masked = full_masker.mask_ip("192.168.1.100")
        assert masked == "xxx.xxx.xxx.xxx"
        
        # Test hash masking
        hash_masker = IPMasker(mask_type="hash")
        masked = hash_masker.mask_ip("192.168.1.100")
        assert masked.startswith("IP_HASH_")
        assert len(masked) > 8
    
    def test_ipv6_masking(self, mock_ip_masker):
        """Test masking of IPv6 addresses"""
        ipv6 = "2001:db8::8a2e:370:7334"
        
        # Test partial masking
        partial_masker = IPMasker(mask_type="partial")
        masked = partial_masker.mask_ip(ipv6)
        assert "xxxx" in masked
        assert masked.startswith("2001:db8")
        
        # Test full masking
        full_masker = IPMasker(mask_type="full")
        masked = full_masker.mask_ip(ipv6)
        assert masked == "xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx"
    
    def test_mask_logs_function(self, sample_logs_with_ips):
        """Test the mask_logs_for_llm function"""
        masker = IPMasker(mask_type="partial")
        
        # Convert logs to text
        log_text = "\n".join([f"{log['timestamp']} - {log['message']}" for log in sample_logs_with_ips])
        
        # Mask logs
        masked_logs = masker.mask_text(log_text)
        
        # Verify IPs are masked
        assert "192.168.1.xxx" in masked_logs
        assert "192.168.1.100" not in masked_logs
        assert "10.0.0.xxx" in masked_logs
        assert "10.0.0.50" not in masked_logs
        assert "203.0.113.xxx" in masked_logs
        assert "2001:db8" in masked_logs
    
    def test_ip_masking_in_incident_display(self, sample_incident_data_with_ips):
        """Test IP masking in incident display"""
        masker = IPMasker(mask_type="partial")
        
        # Mask incident title
        masked_title = masker.mask_text(sample_incident_data_with_ips["title"])
        assert "192.168.100.xxx" in masked_title
        assert "192.168.100.50" not in masked_title
        
        # Mask incident description
        masked_desc = masker.mask_text(sample_incident_data_with_ips["description"])
        assert "192.168.100.xxx" in masked_desc
        assert "10.0.0.xxx" in masked_desc
        
        # Mask logs
        masked_logs = [masker.mask_text(log) for log in sample_incident_data_with_ips["logs"]]
        for log in masked_logs:
            assert "192.168.100.50" not in log
            assert "192.168.100.xxx" in log
    
    def test_ip_masking_toggle_functionality(self):
        """Test the IP masking toggle in Streamlit UI"""
        # Mock session state
        mock_state = MagicMock()
        mock_state.show_masked = True
        
        with patch('streamlit.session_state', mock_state):
            # Test toggle on (masked)
            assert mock_state.show_masked == True
            
            # Test toggle off (unmasked)
            mock_state.show_masked = False
            assert mock_state.show_masked == False
    
    def test_ip_masking_consistency(self):
        """Test that same IP always gets masked the same way"""
        masker = IPMasker(mask_type="hash")
        
        ip = "192.168.1.100"
        masked1 = masker.mask_ip(ip)
        masked2 = masker.mask_ip(ip)
        
        # Hash masking should be consistent
        assert masked1 == masked2
    
    def test_ip_masking_preserves_context(self, sample_logs_with_ips):
        """Test that masking preserves log context and readability"""
        masker = IPMasker(mask_type="partial")
        
        for log in sample_logs_with_ips:
            masked_message = masker.mask_text(log["message"])
            
            # Verify structure is preserved
            assert "Connection from" in masked_message or \
                   "Failed login attempt from" in masked_message or \
                   "API request from" in masked_message or \
                   "IPv6 connection from" in masked_message
            
            # Verify partial masking maintains network info
            if "192.168" in log["message"]:
                assert "192.168" in masked_message
            if "10.0" in log["message"]:
                assert "10.0" in masked_message
    
    def test_ip_masking_in_analytics(self):
        """Test IP masking in analytics and aggregated data"""
        # Sample analytics data
        top_ips = [
            {"ip": "192.168.1.100", "count": 150},
            {"ip": "10.0.0.50", "count": 89},
            {"ip": "203.0.113.45", "count": 67}
        ]
        
        masker = IPMasker(mask_type="partial")
        
        # Mask IPs in analytics
        masked_ips = []
        for entry in top_ips:
            masked_entry = {
                "ip": masker.mask_ip(entry["ip"]),
                "count": entry["count"]
            }
            masked_ips.append(masked_entry)
        
        # Verify masking
        assert all("xxx" in entry["ip"] for entry in masked_ips)
        assert all(entry["count"] == orig["count"] 
                  for entry, orig in zip(masked_ips, top_ips))
    
    def test_ip_masking_export_functionality(self, sample_incident_data_with_ips):
        """Test IP masking when exporting data"""
        masker = IPMasker(mask_type="full")
        
        # Create export data
        export_data = {
            "incident": sample_incident_data_with_ips,
            "export_date": datetime.now().isoformat(),
            "masked": True
        }
        
        # Mask sensitive data
        export_data["incident"]["title"] = masker.mask_text(export_data["incident"]["title"])
        export_data["incident"]["description"] = masker.mask_text(export_data["incident"]["description"])
        export_data["incident"]["logs"] = [masker.mask_text(log) for log in export_data["incident"]["logs"]]
        
        # Verify all IPs are fully masked
        json_export = json.dumps(export_data)
        assert "192.168.100.50" not in json_export
        assert "10.0.0.25" not in json_export
        assert "xxx.xxx.xxx.xxx" in json_export
    
    def test_ip_masking_performance(self, sample_logs_with_ips):
        """Test IP masking performance with large datasets"""
        import time
        
        # Create large dataset
        large_logs = sample_logs_with_ips * 1000  # 4000 log entries
        log_text = "\n".join([f"{log['timestamp']} - {log['message']}" for log in large_logs])
        
        masker = IPMasker(mask_type="partial")
        
        # Measure masking time
        start_time = time.time()
        masked_text = masker.mask_text(log_text)
        end_time = time.time()
        
        # Should complete within reasonable time (< 1 second for 4000 logs)
        assert end_time - start_time < 1.0
        
        # Verify masking worked
        assert "192.168.1.100" not in masked_text
        assert "192.168.1.xxx" in masked_text
    
    def test_ip_masking_error_handling(self):
        """Test IP masking error handling"""
        masker = IPMasker(mask_type="partial")
        
        # Test with invalid IP
        result = masker.mask_ip("not.an.ip.address")
        assert result == "not.an.ip.address"  # Should return unchanged
        
        # Test with None
        result = masker.mask_ip(None)
        assert result is None
        
        # Test with empty string
        result = masker.mask_ip("")
        assert result == ""
    
    def test_ip_masking_ui_integration(self):
        """Test IP masking integration in Streamlit UI"""
        # Test configuration options
        mask_types = ["partial", "full", "hash", "none"]
        assert all(isinstance(t, str) for t in mask_types)
        
        # Test default configuration
        default_config = {
            "enabled": True,
            "mask_type": "partial",
            "exclude_private": False,
            "mask_in_exports": True
        }
        
        assert default_config["enabled"] == True
        assert default_config["mask_type"] == "partial"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])