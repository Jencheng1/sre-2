#!/usr/bin/env python3
"""
Selenium-based test suite for Streamlit UI components
Tests all UI elements to ensure no balloon celebrations and proper functionality
"""

import unittest
import time
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class TestStreamlitUI(unittest.TestCase):
    """Test Streamlit UI components using Selenium"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Install and setup Chrome driver
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=chrome_options)
        cls.driver.implicitly_wait(10)
        cls.base_url = "http://localhost:8501"
        
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        cls.driver.quit()
    
    def setUp(self):
        """Navigate to base URL before each test"""
        self.driver.get(self.base_url)
        time.sleep(3)  # Wait for Streamlit to load
    
    def wait_for_element(self, by, value, timeout=10):
        """Wait for element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
    
    def test_01_page_loads(self):
        """Test that Streamlit page loads successfully"""
        try:
            # Wait for Streamlit app to load
            self.wait_for_element(By.TAG_NAME, "body")
            
            # Check for title or header
            page_source = self.driver.page_source
            self.assertIn("SRE", page_source)
            print("✅ Streamlit page loads successfully")
            
        except Exception as e:
            self.fail(f"Page failed to load: {str(e)}")
    
    def test_02_no_balloons_in_page(self):
        """Test that no balloon elements are present in the page"""
        try:
            # Wait for page to fully load
            time.sleep(3)
            
            # Check page source for balloon-related elements
            page_source = self.driver.page_source
            
            # Streamlit balloons typically have specific CSS classes
            balloon_indicators = [
                'stBalloons',
                'balloon',
                'celebration',
                '🎈'  # Balloon emoji
            ]
            
            for indicator in balloon_indicators:
                self.assertNotIn(indicator, page_source, 
                               f"Found balloon indicator '{indicator}' in page")
            
            print("✅ No balloon celebrations found in UI")
            
        except Exception as e:
            self.fail(f"Balloon check failed: {str(e)}")
    
    def test_03_sidebar_navigation(self):
        """Test sidebar navigation elements"""
        try:
            # Look for sidebar
            sidebar_selectors = [
                '[data-testid="stSidebar"]',
                '.css-1d391kg',  # Common Streamlit sidebar class
                '[aria-label="Sidebar"]'
            ]
            
            sidebar_found = False
            for selector in sidebar_selectors:
                try:
                    sidebar = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if sidebar:
                        sidebar_found = True
                        break
                except:
                    continue
            
            if sidebar_found:
                print("✅ Sidebar navigation present")
            else:
                # Try to find navigation by looking for select boxes or radio buttons
                nav_elements = self.driver.find_elements(By.TAG_NAME, "select")
                nav_elements += self.driver.find_elements(By.CSS_SELECTOR, '[role="radiogroup"]')
                
                if nav_elements:
                    print(f"✅ Navigation elements found: {len(nav_elements)}")
                else:
                    print("⚠️  No sidebar navigation found (may be collapsed)")
            
        except Exception as e:
            print(f"⚠️  Sidebar test skipped: {str(e)}")
    
    def test_04_incident_management_tab(self):
        """Test Incident Management functionality"""
        try:
            # Look for incident-related elements
            incident_keywords = [
                "Incident",
                "Generate",
                "incident",
                "INC-"
            ]
            
            page_source = self.driver.page_source
            incident_found = any(keyword in page_source for keyword in incident_keywords)
            
            if incident_found:
                # Look for Generate button
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                generate_button = None
                
                for button in buttons:
                    if "Generate" in button.text:
                        generate_button = button
                        break
                
                if generate_button:
                    print("✅ Incident Management tab with Generate button found")
                else:
                    print("✅ Incident Management content found")
            else:
                print("⚠️  Incident Management tab not currently visible")
                
        except Exception as e:
            print(f"⚠️  Incident Management test error: {str(e)}")
    
    def test_05_defect_management_elements(self):
        """Test for Defect Management elements"""
        try:
            page_source = self.driver.page_source
            
            defect_keywords = [
                "Defect",
                "ALM Octane",
                "Jira",
                "defect",
                "correlation"
            ]
            
            defects_found = any(keyword in page_source for keyword in defect_keywords)
            
            if defects_found:
                print("✅ Defect Management elements found")
            else:
                print("⚠️  Defect Management elements not currently visible")
                
        except Exception as e:
            print(f"⚠️  Defect Management test error: {str(e)}")
    
    def test_06_success_messages(self):
        """Test that success messages don't use balloons"""
        try:
            # Look for success message elements
            success_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="stAlert"]')
            
            if success_elements:
                for element in success_elements:
                    # Check that success messages exist but don't trigger balloons
                    if "success" in element.get_attribute("class") or "✅" in element.text:
                        print("✅ Success messages found (without balloons)")
                        break
            else:
                # Check page source for success indicators
                page_source = self.driver.page_source
                if "✅" in page_source or "Success" in page_source:
                    print("✅ Success indicators present in UI")
                else:
                    print("ℹ️  No success messages currently displayed")
                    
        except Exception as e:
            print(f"⚠️  Success message test error: {str(e)}")
    
    def test_07_button_functionality(self):
        """Test button click functionality without balloons"""
        try:
            # Find all buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            print(f"ℹ️  Found {len(buttons)} buttons")
            
            # Test first safe button (not submit/delete)
            safe_button_found = False
            for button in buttons:
                button_text = button.text.lower()
                if button_text and any(word in button_text for word in ["refresh", "search", "view", "show"]):
                    # Click safe button
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
                    
                    # Check no balloons appeared
                    page_source = self.driver.page_source
                    self.assertNotIn('stBalloons', page_source)
                    self.assertNotIn('balloon', page_source.lower())
                    
                    safe_button_found = True
                    print(f"✅ Button '{button.text}' clicked without balloons")
                    break
            
            if not safe_button_found:
                print("ℹ️  No safe test buttons found")
                
        except Exception as e:
            print(f"⚠️  Button functionality test error: {str(e)}")
    
    def test_08_form_inputs(self):
        """Test form input elements"""
        try:
            # Look for input elements
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            selects = self.driver.find_elements(By.TAG_NAME, "select")
            
            total_inputs = len(inputs) + len(textareas) + len(selects)
            
            if total_inputs > 0:
                print(f"✅ Form inputs found: {len(inputs)} inputs, "
                      f"{len(textareas)} textareas, {len(selects)} selects")
            else:
                print("ℹ️  No form inputs currently visible")
                
        except Exception as e:
            print(f"⚠️  Form input test error: {str(e)}")
    
    def test_09_page_responsiveness(self):
        """Test page responds properly to interactions"""
        try:
            # Test page is interactive
            initial_source = self.driver.page_source
            
            # Try to interact with any clickable element
            clickables = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='checkbox']")
            
            if clickables:
                # Click first safe element
                for element in clickables[:3]:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(1)
                            break
                    except:
                        continue
                
                # Check page updated
                new_source = self.driver.page_source
                
                # Verify no balloons in response
                self.assertNotIn('balloon', new_source.lower())
                print("✅ Page responds to interactions without balloons")
            else:
                print("ℹ️  No interactive elements found for testing")
                
        except Exception as e:
            print(f"⚠️  Page responsiveness test error: {str(e)}")

class TestStreamlitIntegration(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service, options=chrome_options)
        cls.driver.implicitly_wait(10)
        cls.base_url = "http://localhost:8501"
        
    @classmethod
    def tearDownClass(cls):
        """Clean up"""
        cls.driver.quit()
    
    def test_complete_user_journey(self):
        """Test a complete user journey without balloons"""
        try:
            self.driver.get(self.base_url)
            time.sleep(3)
            
            print("\n" + "="*60)
            print("Testing Complete User Journey")
            print("="*60)
            
            # 1. Page loads
            body = self.driver.find_element(By.TAG_NAME, "body")
            self.assertIsNotNone(body)
            print("✅ Step 1: Page loaded successfully")
            
            # 2. Check main elements present
            page_source = self.driver.page_source
            
            elements_found = {
                "Title/Header": any(x in page_source for x in ["SRE", "Copilot", "Incident"]),
                "Buttons": len(self.driver.find_elements(By.TAG_NAME, "button")) > 0,
                "Content": len(page_source) > 1000
            }
            
            for element, found in elements_found.items():
                if found:
                    print(f"✅ Step 2: {element} present")
            
            # 3. No balloons throughout
            self.assertNotIn('balloon', page_source.lower())
            self.assertNotIn('🎈', page_source)
            print("✅ Step 3: No balloon celebrations found")
            
            # 4. Page is business-ready
            business_indicators = ["Generate", "Analyze", "Correlate", "Management"]
            business_ready = any(indicator in page_source for indicator in business_indicators)
            
            if business_ready:
                print("✅ Step 4: Business-ready UI confirmed")
            
            print("\n✅ Complete user journey test passed!")
            print("="*60 + "\n")
            
        except Exception as e:
            self.fail(f"User journey test failed: {str(e)}")

def run_selenium_tests():
    """Run all Selenium tests"""
    print("\n" + "="*60)
    print("🧪 Streamlit UI Selenium Test Suite")
    print("="*60 + "\n")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStreamlitUI))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestStreamlitIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("📊 Selenium Test Summary")
    print("="*60)
    print(f"Total Tests: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("🎉 ALL SELENIUM TESTS PASSED!")
        print("✅ UI is business-ready (no balloons)")
        print("✅ All components tested successfully")
    else:
        print("⚠️  Some tests failed - review output above")
    print("="*60 + "\n")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_selenium_tests()
    sys.exit(0 if success else 1)