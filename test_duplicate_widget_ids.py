#!/usr/bin/env python3
"""
Test to check for duplicate widget IDs in Streamlit application.
This test scans the streamlit_app.py file to identify potential duplicate widget keys.
"""

import re
import sys
from collections import defaultdict
from colorama import init, Fore, Style

# Initialize colorama
init()

class DuplicateWidgetIDChecker:
    def __init__(self, file_path='/home/ec2-user/sre/sre_mcp/streamlit_app.py'):
        self.file_path = file_path
        self.widget_patterns = [
            # Pattern for st.button with key parameter
            (r'st\.button\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'button'),
            # Pattern for st.text_input with key parameter
            (r'st\.text_input\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'text_input'),
            # Pattern for st.selectbox with key parameter
            (r'st\.selectbox\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'selectbox'),
            # Pattern for st.checkbox with key parameter
            (r'st\.checkbox\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'checkbox'),
            # Pattern for st.radio with key parameter
            (r'st\.radio\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'radio'),
            # Pattern for st.slider with key parameter
            (r'st\.slider\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'slider'),
            # Pattern for st.text_area with key parameter
            (r'st\.text_area\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'text_area'),
            # Pattern for st.number_input with key parameter
            (r'st\.number_input\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'number_input'),
            # Pattern for st.date_input with key parameter
            (r'st\.date_input\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'date_input'),
            # Pattern for st.time_input with key parameter
            (r'st\.time_input\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'time_input'),
            # Pattern for st.file_uploader with key parameter
            (r'st\.file_uploader\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'file_uploader'),
            # Pattern for st.multiselect with key parameter
            (r'st\.multiselect\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'multiselect'),
            # Pattern for st.select_slider with key parameter
            (r'st\.select_slider\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'select_slider'),
            # Pattern for st.color_picker with key parameter
            (r'st\.color_picker\([^)]*key\s*=\s*["\']([^"\']+)["\']', 'color_picker'),
        ]
        self.found_keys = defaultdict(list)  # key -> list of (line_no, widget_type)
        self.dynamic_keys = []  # Keys that use variables or f-strings
        
    def read_file(self):
        """Read the Streamlit app file."""
        with open(self.file_path, 'r') as f:
            return f.readlines()
            
    def analyze_keys(self):
        """Analyze the file for widget keys."""
        lines = self.read_file()
        
        for line_no, line in enumerate(lines, 1):
            # Check each widget pattern
            for pattern, widget_type in self.widget_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    key = match.group(1)
                    
                    # Check if key uses f-string or variables (dynamic key)
                    if '{' in key or 'f"' in line or "f'" in line:
                        self.dynamic_keys.append((line_no, widget_type, key, line.strip()))
                    else:
                        self.found_keys[key].append((line_no, widget_type))
                        
    def find_potential_issues(self):
        """Find potential duplicate key issues."""
        issues = {
            'static_duplicates': [],
            'suspicious_patterns': [],
            'missing_dynamic_context': []
        }
        
        # Find static duplicates
        for key, occurrences in self.found_keys.items():
            if len(occurrences) > 1:
                issues['static_duplicates'].append({
                    'key': key,
                    'occurrences': occurrences
                })
                
        # Find suspicious patterns (keys that should probably be dynamic)
        common_keys = ['submit', 'save', 'delete', 'update', 'create', 'edit', 'remove', 
                      'add', 'search', 'filter', 'apply', 'cancel', 'close', 'open']
        
        for key, occurrences in self.found_keys.items():
            # Check if key is a common action that might need context
            for common in common_keys:
                if common in key.lower() and len(occurrences) >= 1:
                    # Check if it's not already dynamic
                    is_dynamic = any(key in str(dk) for dk in self.dynamic_keys)
                    if not is_dynamic:
                        issues['suspicious_patterns'].append({
                            'key': key,
                            'reason': f"Common action key '{common}' might need unique context",
                            'occurrences': occurrences
                        })
                        
        # Check dynamic keys for potential issues
        for line_no, widget_type, key_pattern, line in self.dynamic_keys:
            # Check if dynamic key has enough context
            if not any(ctx in key_pattern for ctx in ['id', 'idx', 'index', 'suffix', 'prefix', 'type', 'name']):
                issues['missing_dynamic_context'].append({
                    'line': line_no,
                    'widget': widget_type,
                    'key_pattern': key_pattern,
                    'code': line
                })
                
        return issues
        
    def generate_report(self):
        """Generate a comprehensive report of findings."""
        print(f"\n{Fore.CYAN}{'='*80}")
        print("Streamlit Widget ID Duplicate Check Report")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
        self.analyze_keys()
        issues = self.find_potential_issues()
        
        # Summary
        total_widgets = sum(len(v) for v in self.found_keys.values()) + len(self.dynamic_keys)
        print(f"{Fore.BLUE}Summary:{Style.RESET_ALL}")
        print(f"  Total widgets with keys: {total_widgets}")
        print(f"  Unique static keys: {len(self.found_keys)}")
        print(f"  Dynamic keys: {len(self.dynamic_keys)}")
        print()
        
        # Static duplicates
        if issues['static_duplicates']:
            print(f"{Fore.RED}❌ CRITICAL: Found duplicate widget IDs:{Style.RESET_ALL}")
            for dup in issues['static_duplicates']:
                print(f"\n  Key: '{dup['key']}'")
                for line_no, widget_type in dup['occurrences']:
                    print(f"    - Line {line_no}: st.{widget_type}")
        else:
            print(f"{Fore.GREEN}✅ No static duplicate widget IDs found{Style.RESET_ALL}")
            
        print()
        
        # Suspicious patterns
        if issues['suspicious_patterns']:
            print(f"{Fore.YELLOW}⚠️  WARNING: Potentially problematic key patterns:{Style.RESET_ALL}")
            seen_keys = set()
            for pattern in issues['suspicious_patterns']:
                if pattern['key'] not in seen_keys:
                    seen_keys.add(pattern['key'])
                    print(f"\n  Key: '{pattern['key']}'")
                    print(f"  Reason: {pattern['reason']}")
                    for line_no, widget_type in pattern['occurrences']:
                        print(f"    - Line {line_no}: st.{widget_type}")
                        
        # Dynamic keys analysis
        print(f"\n{Fore.BLUE}Dynamic Keys Analysis:{Style.RESET_ALL}")
        if self.dynamic_keys:
            print(f"  Found {len(self.dynamic_keys)} dynamic keys")
            print("\n  Examples of dynamic keys:")
            for i, (line_no, widget_type, key_pattern, _) in enumerate(self.dynamic_keys[:5]):
                print(f"    - Line {line_no}: st.{widget_type} with key containing '{key_pattern}'")
        else:
            print("  No dynamic keys found")
            
        # Recommendations
        print(f"\n{Fore.CYAN}Recommendations:{Style.RESET_ALL}")
        print("1. Always use dynamic keys for widgets inside loops or reusable components")
        print("2. Include context in key names (e.g., f'button_{item_id}' instead of 'button')")
        print("3. For action buttons, include the entity ID (e.g., f'delete_{user_id}')")
        print("4. Consider using session state keys with prefixes for different sections")
        print("5. Test the app thoroughly after making changes to ensure no runtime duplicates")
        
        # Final status
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        if issues['static_duplicates']:
            print(f"{Fore.RED}❌ FAILED: Found {len(issues['static_duplicates'])} duplicate widget IDs{Style.RESET_ALL}")
            return False
        else:
            print(f"{Fore.GREEN}✅ PASSED: No duplicate widget IDs detected{Style.RESET_ALL}")
            return True
            
    def fix_suggestions(self):
        """Generate fix suggestions for common patterns."""
        print(f"\n{Fore.CYAN}Fix Suggestions:{Style.RESET_ALL}")
        print("\nFor buttons in loops or dynamic content:")
        print("  # Bad:")
        print('  if st.button("Delete", key="delete"):\n')
        print("  # Good:")
        print('  if st.button("Delete", key=f"delete_{item_id}"):\n')
        
        print("\nFor widgets in tabs:")
        print("  # Bad:")
        print('  with tab1:\n    st.text_input("Name", key="name")\n')
        print("  # Good:")
        print('  with tab1:\n    st.text_input("Name", key="tab1_name")\n')
        
        print("\nFor reusable components:")
        print("  # Bad:")
        print('  def render_form():\n    st.text_input("Email", key="email")\n')
        print("  # Good:")
        print('  def render_form(prefix):\n    st.text_input("Email", key=f"{prefix}_email")\n')

def main():
    """Run the duplicate widget ID check."""
    checker = DuplicateWidgetIDChecker()
    passed = checker.generate_report()
    checker.fix_suggestions()
    
    # Exit with appropriate code
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()