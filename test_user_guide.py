#!/usr/bin/env python3
"""
Test cases for User Guide functionality in SRE Copilot.
Ensures all guides are accessible and search functionality works.
"""

import sys
import json
from datetime import datetime
from colorama import init, Fore, Style

# Add current directory to path
sys.path.append('/home/ec2-user/sre/sre_mcp')

# Import guide content
from user_guide_content import get_all_guides, get_guide, get_guide_titles

# Initialize colorama
init()

class UserGuideTester:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{text}")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
    def print_test(self, test_name, status, message=""):
        if status == "PASS":
            print(f"{Fore.GREEN}✅ {test_name}: PASSED{Style.RESET_ALL}")
            if message:
                print(f"   {message}")
            self.passed_tests += 1
        else:
            print(f"{Fore.RED}❌ {test_name}: FAILED - {message}{Style.RESET_ALL}")
            self.failed_tests += 1
        
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message
        })
    
    def test_01_all_guides_present(self):
        """Test 01: Verify all guides are present"""
        try:
            guides = get_all_guides()
            expected_guides = [
                "overview",
                "incident_analysis", 
                "knowledge_management",
                "generating_incidents",
                "recent_changes",
                "tips_tricks"
            ]
            
            all_present = True
            for guide_id in expected_guides:
                if guide_id not in guides:
                    all_present = False
                    self.print_test(f"Guide Present - {guide_id}", "FAIL", "Guide missing")
                else:
                    # Verify guide has required fields
                    guide = guides[guide_id]
                    if 'title' in guide and 'content' in guide:
                        self.print_test(f"Guide Present - {guide_id}", "PASS", 
                                      f"Title: {guide['title'][:50]}...")
                    else:
                        self.print_test(f"Guide Present - {guide_id}", "FAIL", 
                                      "Missing title or content")
                        all_present = False
                        
        except Exception as e:
            self.print_test("All Guides Present", "FAIL", str(e))
    
    def test_02_guide_content_length(self):
        """Test 02: Verify guides have substantial content"""
        try:
            guides = get_all_guides()
            
            for guide_id, guide in guides.items():
                content = guide.get('content', '')
                if len(content) > 500:  # Minimum content length
                    self.print_test(f"Content Length - {guide_id}", "PASS", 
                                  f"{len(content)} characters")
                else:
                    self.print_test(f"Content Length - {guide_id}", "FAIL", 
                                  f"Only {len(content)} characters")
                                  
        except Exception as e:
            self.print_test("Guide Content Length", "FAIL", str(e))
    
    def test_03_guide_titles(self):
        """Test 03: Verify get_guide_titles function"""
        try:
            titles = get_guide_titles()
            
            if isinstance(titles, list) and len(titles) > 0:
                self.print_test("Guide Titles Function", "PASS", 
                              f"Found {len(titles)} guide titles")
                
                # Verify format
                for guide_id, title in titles:
                    if not isinstance(guide_id, str) or not isinstance(title, str):
                        self.print_test("Guide Title Format", "FAIL", 
                                      f"Invalid format for {guide_id}")
                        return
                        
                self.print_test("Guide Title Format", "PASS", "All titles properly formatted")
            else:
                self.print_test("Guide Titles Function", "FAIL", "No titles returned")
                
        except Exception as e:
            self.print_test("Guide Titles", "FAIL", str(e))
    
    def test_04_get_specific_guide(self):
        """Test 04: Test get_guide function"""
        try:
            # Test existing guide
            guide = get_guide("overview")
            if guide and 'title' in guide:
                self.print_test("Get Specific Guide - Existing", "PASS", 
                              guide['title'])
            else:
                self.print_test("Get Specific Guide - Existing", "FAIL", 
                              "Overview guide not found")
                
            # Test non-existing guide
            guide = get_guide("non_existent")
            if guide and 'title' in guide and 'not found' in guide['title'].lower():
                self.print_test("Get Specific Guide - Non-existing", "PASS", 
                              "Properly handles missing guides")
            else:
                self.print_test("Get Specific Guide - Non-existing", "FAIL", 
                              "Should return 'not found' message")
                              
        except Exception as e:
            self.print_test("Get Specific Guide", "FAIL", str(e))
    
    def test_05_search_functionality(self):
        """Test 05: Test search through guides"""
        try:
            guides = get_all_guides()
            test_queries = [
                "root cause",
                "knowledge base",
                "incident",
                "aws",
                "monitoring"
            ]
            
            for query in test_queries:
                results = []
                for guide_id, guide in guides.items():
                    content = guide.get('content', '').lower()
                    title = guide.get('title', '').lower()
                    if query.lower() in content or query.lower() in title:
                        results.append(guide_id)
                
                if results:
                    self.print_test(f"Search - '{query}'", "PASS", 
                                  f"Found in {len(results)} guides: {', '.join(results)}")
                else:
                    self.print_test(f"Search - '{query}'", "FAIL", 
                                  "No results found")
                                  
        except Exception as e:
            self.print_test("Search Functionality", "FAIL", str(e))
    
    def test_06_guide_formatting(self):
        """Test 06: Check guide formatting"""
        try:
            guides = get_all_guides()
            
            for guide_id, guide in guides.items():
                content = guide.get('content', '')
                
                # Check for markdown headers
                has_headers = '##' in content or '###' in content
                # Check for bullet points
                has_bullets = '- ' in content or '* ' in content
                # Check for numbered lists
                has_numbers = '1.' in content or '2.' in content
                
                if has_headers and (has_bullets or has_numbers):
                    self.print_test(f"Formatting - {guide_id}", "PASS", 
                                  "Proper markdown formatting")
                else:
                    self.print_test(f"Formatting - {guide_id}", "FAIL", 
                                  "Missing proper formatting")
                                  
        except Exception as e:
            self.print_test("Guide Formatting", "FAIL", str(e))
    
    def test_07_guide_completeness(self):
        """Test 07: Check if guides cover key topics"""
        try:
            guides = get_all_guides()
            all_content = " ".join([g.get('content', '') for g in guides.values()]).lower()
            
            key_topics = {
                "authentication": "how to login",
                "generate incident": "creating test incidents",
                "analyze": "root cause analysis",
                "knowledge base": "kb management",
                "search": "searching functionality",
                "timeline": "event correlation",
                "business impact": "impact assessment",
                "recommendations": "suggested actions"
            }
            
            for topic, description in key_topics.items():
                if topic in all_content:
                    self.print_test(f"Topic Coverage - {description}", "PASS", 
                                  "Topic is covered")
                else:
                    self.print_test(f"Topic Coverage - {description}", "FAIL", 
                                  f"'{topic}' not found in guides")
                                  
        except Exception as e:
            self.print_test("Guide Completeness", "FAIL", str(e))
    
    def test_08_quick_start_present(self):
        """Test 08: Verify quick start information"""
        try:
            overview = get_guide("overview")
            content = overview.get('content', '').lower()
            
            quick_start_items = [
                "getting started",
                "generate",
                "analyze",
                "knowledge"
            ]
            
            found_items = sum(1 for item in quick_start_items if item in content)
            
            if found_items >= 3:
                self.print_test("Quick Start Information", "PASS", 
                              f"Found {found_items}/{len(quick_start_items)} quick start items")
            else:
                self.print_test("Quick Start Information", "FAIL", 
                              f"Only found {found_items}/{len(quick_start_items)} items")
                              
        except Exception as e:
            self.print_test("Quick Start", "FAIL", str(e))
    
    def test_09_guide_navigation(self):
        """Test 09: Test guide navigation structure"""
        try:
            titles = get_guide_titles()
            guides = get_all_guides()
            
            # Verify all guides have titles
            if len(titles) == len(guides):
                self.print_test("Guide Navigation Structure", "PASS", 
                              "All guides have navigation entries")
            else:
                self.print_test("Guide Navigation Structure", "FAIL", 
                              f"Mismatch: {len(titles)} titles vs {len(guides)} guides")
                              
            # Verify order makes sense (overview should be first)
            if titles and titles[0][0] == "overview":
                self.print_test("Guide Order", "PASS", 
                              "Overview is first as expected")
            else:
                self.print_test("Guide Order", "FAIL", 
                              "Overview should be the first guide")
                              
        except Exception as e:
            self.print_test("Guide Navigation", "FAIL", str(e))
    
    def test_10_actionable_content(self):
        """Test 10: Verify guides have actionable content"""
        try:
            guides = get_all_guides()
            
            action_indicators = [
                "click",
                "select",
                "enter",
                "navigate",
                "go to",
                "press",
                "choose",
                "step"
            ]
            
            for guide_id, guide in guides.items():
                content = guide.get('content', '').lower()
                action_count = sum(1 for indicator in action_indicators if indicator in content)
                
                if action_count >= 3:
                    self.print_test(f"Actionable Content - {guide_id}", "PASS", 
                                  f"Found {action_count} action words")
                else:
                    self.print_test(f"Actionable Content - {guide_id}", "FAIL", 
                                  f"Only {action_count} action words found")
                                  
        except Exception as e:
            self.print_test("Actionable Content", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all user guide tests"""
        self.print_header("User Guide Test Suite")
        
        print(f"{Fore.YELLOW}Running user guide tests...{Style.RESET_ALL}\n")
        
        # Run all tests
        self.test_01_all_guides_present()
        print()  # Space between test groups
        self.test_02_guide_content_length()
        print()
        self.test_03_guide_titles()
        self.test_04_get_specific_guide()
        self.test_05_search_functionality()
        print()
        self.test_06_guide_formatting()
        self.test_07_guide_completeness()
        self.test_08_quick_start_present()
        self.test_09_guide_navigation()
        self.test_10_actionable_content()
        
        # Summary
        self.print_header("Test Summary")
        
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"{Fore.GREEN}Passed: {self.passed_tests}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed_tests}{Style.RESET_ALL}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.failed_tests > 0:
            print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save results
        with open('/tmp/user_guide_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'passed': self.passed_tests,
                'failed': self.failed_tests,
                'results': self.test_results,
                'success': self.failed_tests == 0
            }, f, indent=2)
        
        print(f"\n📄 Test results saved to: /tmp/user_guide_test_results.json")
        
        # Final verdict
        print("\n" + "="*80)
        if self.failed_tests == 0:
            print(f"{Fore.GREEN}✅ ALL TESTS PASSED! User guides are complete and functional.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Some tests failed. Please review the user guide content.{Style.RESET_ALL}")
        print("="*80)
        
        return self.failed_tests == 0

def main():
    """Main test execution"""
    tester = UserGuideTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()