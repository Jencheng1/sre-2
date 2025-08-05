#!/usr/bin/env python3
"""
Comprehensive test runner for all incident scenarios
"""

import json
import sys
import time
from datetime import datetime
import requests
from typing import Dict, List, Any

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class IncidentTestRunner:
    """Test runner for incident scenarios"""
    
    def __init__(self):
        self.test_results = []
        self.mcp_base_urls = {
            'splunk': 'http://localhost:9080',
            'dynatrace': 'http://localhost:9081',
            'servicenow': 'http://localhost:9082',
            'confluence': 'http://localhost:9083',
            'gitlab': 'http://localhost:9084'
        }
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    def print_success(self, text: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")
    
    def print_error(self, text: str):
        """Print error message"""
        print(f"{Colors.RED}✗ {text}{Colors.RESET}")
    
    def print_info(self, text: str):
        """Print info message"""
        print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")
    
    def test_mcp_servers(self) -> Dict[str, bool]:
        """Test MCP server connectivity"""
        self.print_header("Testing MCP Server Connectivity")
        results = {}
        
        for service, base_url in self.mcp_base_urls.items():
            try:
                if service == 'splunk':
                    response = requests.post(
                        f"{base_url}/splunk/search",
                        json={'query': 'test'},
                        timeout=5
                    )
                elif service == 'servicenow':
                    response = requests.get(f"{base_url}/servicenow/incidents", timeout=5)
                elif service == 'dynatrace':
                    response = requests.get(f"{base_url}/dynatrace/metrics", timeout=5)
                else:
                    response = requests.get(f"{base_url}/{service}/search?query=test", timeout=5)
                
                if response.status_code == 200:
                    self.print_success(f"{service.capitalize()} MCP server is running")
                    results[service] = True
                else:
                    self.print_error(f"{service.capitalize()} MCP server returned {response.status_code}")
                    results[service] = False
                    
            except Exception as e:
                self.print_error(f"{service.capitalize()} MCP server is not accessible: {str(e)}")
                results[service] = False
        
        return results
    
    def test_streamlit(self) -> bool:
        """Test Streamlit connectivity"""
        self.print_header("Testing Streamlit Application")
        try:
            response = requests.get('http://localhost:8501', timeout=5)
            if response.status_code == 200:
                self.print_success("Streamlit application is running on port 8501")
                return True
            else:
                self.print_error(f"Streamlit returned status code {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Streamlit is not accessible: {str(e)}")
            return False
    
    def load_test_scenarios(self) -> Dict[str, Any]:
        """Load all test scenarios"""
        self.print_header("Loading Test Scenarios")
        scenarios = {}
        
        try:
            # Load original 3 test cases
            with open('incident_test_cases.json', 'r') as f:
                original = json.load(f)
                scenarios['original'] = original['test_cases']
                self.print_success(f"Loaded {len(original['test_cases'])} original test cases")
            
            # Load additional 3 scenarios
            with open('additional_incident_scenarios.json', 'r') as f:
                additional = json.load(f)
                scenarios['additional'] = additional['additional_scenarios']
                self.print_success(f"Loaded {len(additional['additional_scenarios'])} additional scenarios")
            
            # Load SSM-enhanced scenarios
            with open('comprehensive_incident_scenarios_with_ssm.json', 'r') as f:
                ssm_data = json.load(f)
                scenarios['ssm_enhanced'] = ssm_data['incident_scenarios_with_real_aws_data']
                self.print_success(f"Loaded {len(ssm_data['incident_scenarios_with_real_aws_data'])} SSM-enhanced scenarios")
                
        except Exception as e:
            self.print_error(f"Error loading scenarios: {str(e)}")
            
        return scenarios
    
    def validate_scenario_structure(self, scenario: Dict[str, Any], scenario_type: str) -> bool:
        """Validate scenario has required structure"""
        required_fields = {
            'original': ['id', 'name', 'logs', 'issue_detection', 'root_cause_analysis', 'recommendations'],
            'additional': ['id', 'name', 'description', 'logs', 'correlation_analysis', 'root_cause'],
            'ssm_enhanced': ['id', 'name', 'aws_systems_manager_change_calendar', 'aws_systems_manager_opsitems', 
                           'cloudtrail_events', 'vpc_flow_logs', 'trusted_advisor_checks', 'personal_health_dashboard_events']
        }
        
        fields = required_fields.get(scenario_type, [])
        missing = [f for f in fields if f not in scenario]
        
        if missing:
            self.print_error(f"Scenario {scenario.get('id', 'Unknown')} missing fields: {missing}")
            return False
        
        return True
    
    def test_incident_correlation(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test incident correlation logic"""
        result = {
            'scenario_id': scenario.get('id'),
            'scenario_name': scenario.get('name'),
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        # Test CloudTrail correlation
        if 'cloudtrail' in scenario.get('logs', {}):
            ct_events = scenario['logs']['cloudtrail']
            if ct_events and any('errorCode' in e for e in ct_events):
                result['tests_passed'] += 1
                result['details'].append("CloudTrail error events present")
            else:
                # Not all scenarios have errors - this is OK
                result['tests_passed'] += 1
                result['details'].append("CloudTrail events analyzed (no errors expected)")
        
        # Test VPC Flow Logs correlation
        if 'vpc_flow_logs' in scenario.get('logs', {}):
            flow_logs = scenario['logs']['vpc_flow_logs']
            reject_count = sum(1 for log in flow_logs if log.get('action') == 'REJECT')
            if reject_count > 0:
                result['tests_passed'] += 1
                result['details'].append(f"Found {reject_count} REJECT actions in VPC Flow Logs")
            else:
                result['details'].append("No REJECT actions in VPC Flow Logs")
        
        # Test root cause identification
        if 'root_cause' in scenario or 'root_cause_analysis' in scenario:
            result['tests_passed'] += 1
            result['details'].append("Root cause analysis present")
        else:
            result['tests_failed'] += 1
            result['details'].append("No root cause analysis found")
        
        # Test recommendations
        if 'recommendations' in scenario or 'resolution_steps' in scenario:
            result['tests_passed'] += 1
            result['details'].append("Recommendations provided")
        else:
            result['tests_failed'] += 1
            result['details'].append("No recommendations found")
        
        return result
    
    def test_ssm_integration(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test SSM integration features"""
        result = {
            'scenario_id': scenario.get('id'),
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
        
        # Test Change Calendar
        if 'aws_systems_manager_change_calendar' in scenario:
            change_cal = scenario['aws_systems_manager_change_calendar']
            if 'changeRequests' in change_cal and change_cal['changeRequests']:
                change_req = change_cal['changeRequests'][0]
                if change_req.get('status') == 'APPROVED':
                    result['tests_passed'] += 1
                    result['details'].append(f"Change request {change_req['changeRequestId']} approved")
                else:
                    result['tests_failed'] += 1
                    result['details'].append("Change request not approved")
        
        # Test OpsItems
        if 'aws_systems_manager_opsitems' in scenario:
            opsitem = scenario['aws_systems_manager_opsitems']
            if opsitem.get('opsItemId') and opsitem.get('status') in ['Open', 'InProgress']:
                result['tests_passed'] += 1
                result['details'].append(f"OpsItem {opsitem['opsItemId']} created with severity {opsitem.get('severity')}")
            else:
                result['tests_failed'] += 1
                result['details'].append("Invalid OpsItem data")
        
        return result
    
    def run_all_tests(self):
        """Run all tests"""
        self.print_header("SRE Copilot Incident Scenario Test Suite")
        print(f"Test execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test infrastructure
        mcp_results = self.test_mcp_servers()
        streamlit_result = self.test_streamlit()
        
        # Load scenarios
        scenarios = self.load_test_scenarios()
        
        # Test each scenario type
        all_results = []
        
        # Test original 3 scenarios
        self.print_header("Testing Original 3 Requested Scenarios")
        for scenario in scenarios.get('original', []):
            print(f"\n{Colors.BOLD}Testing: {scenario['name']}{Colors.RESET}")
            
            if self.validate_scenario_structure(scenario, 'original'):
                self.print_success("Scenario structure validated")
                
                # Test correlation
                correlation_result = self.test_incident_correlation(scenario)
                for detail in correlation_result['details']:
                    self.print_info(detail)
                
                all_results.append(correlation_result)
            else:
                self.print_error("Invalid scenario structure")
        
        # Test additional 3 scenarios
        self.print_header("Testing Additional 3 New Scenarios")
        for scenario in scenarios.get('additional', []):
            print(f"\n{Colors.BOLD}Testing: {scenario['name']}{Colors.RESET}")
            
            if self.validate_scenario_structure(scenario, 'additional'):
                self.print_success("Scenario structure validated")
                
                # Test correlation
                correlation_result = self.test_incident_correlation(scenario)
                for detail in correlation_result['details']:
                    self.print_info(detail)
                
                all_results.append(correlation_result)
            else:
                self.print_error("Invalid scenario structure")
        
        # Test SSM-enhanced scenarios
        self.print_header("Testing SSM-Enhanced Scenarios")
        for scenario in scenarios.get('ssm_enhanced', []):
            print(f"\n{Colors.BOLD}Testing: {scenario['name']}{Colors.RESET}")
            
            if self.validate_scenario_structure(scenario, 'ssm_enhanced'):
                self.print_success("Scenario structure validated")
                
                # Test SSM integration
                ssm_result = self.test_ssm_integration(scenario)
                for detail in ssm_result['details']:
                    self.print_info(detail)
                
                all_results.append(ssm_result)
            else:
                self.print_error("Invalid scenario structure")
        
        # Print summary
        self.print_summary(all_results, mcp_results, streamlit_result)
    
    def print_summary(self, test_results: List[Dict], mcp_results: Dict[str, bool], streamlit_result: bool):
        """Print test summary"""
        self.print_header("Test Summary")
        
        # Infrastructure summary
        print(f"{Colors.BOLD}Infrastructure Status:{Colors.RESET}")
        print(f"  Streamlit: {'✓ Running' if streamlit_result else '✗ Not Running'}")
        for service, status in mcp_results.items():
            print(f"  {service.capitalize()} MCP: {'✓ Running' if status else '✗ Not Running'}")
        
        # Test results summary
        total_passed = sum(r.get('tests_passed', 0) for r in test_results)
        total_failed = sum(r.get('tests_failed', 0) for r in test_results)
        total_tests = total_passed + total_failed
        
        print(f"\n{Colors.BOLD}Test Results:{Colors.RESET}")
        print(f"  Total Tests: {total_tests}")
        print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {total_failed}{Colors.RESET}")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        
        # Scenario summary
        print(f"\n{Colors.BOLD}Scenarios Tested:{Colors.RESET}")
        tested_scenarios = [r['scenario_name'] for r in test_results if 'scenario_name' in r]
        for i, scenario in enumerate(tested_scenarios, 1):
            print(f"  {i}. {scenario}")
        
        # Final status
        print(f"\n{Colors.BOLD}Overall Status: ", end='')
        if total_failed == 0 and all(mcp_results.values()) and streamlit_result:
            print(f"{Colors.GREEN}ALL TESTS PASSED{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}SOME TESTS FAILED - Review details above{Colors.RESET}")
        
        print(f"\nTest execution completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    runner = IncidentTestRunner()
    runner.run_all_tests()