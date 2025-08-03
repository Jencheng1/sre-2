#!/usr/bin/env python3
"""Test script to identify and fix duplicate key issues in Streamlit app."""

import re
import sys
from collections import defaultdict

def find_duplicate_keys(filename):
    """Find potential duplicate widget keys in Streamlit app."""
    
    with open(filename, 'r') as f:
        content = f.read()
    
    # Find all widget declarations with keys
    widget_patterns = [
        # Forms
        r'st\.form\(["\']([^"\']+)["\']',
        r'with\s+st\.form\(["\']([^"\']+)["\']',
        # Buttons
        r'st\.button\([^,]+,\s*key=["\']([^"\']+)["\']',
        # Select boxes
        r'st\.selectbox\([^,]+,[^,]+,\s*key=["\']([^"\']+)["\']',
        # Text inputs
        r'st\.text_input\([^,]+,\s*key=["\']([^"\']+)["\']',
        r'st\.text_area\([^,]+,\s*key=["\']([^"\']+)["\']',
        # Checkboxes
        r'st\.checkbox\([^,]+,\s*key=["\']([^"\']+)["\']',
        # Other widgets
        r'key=["\']([^"\']+)["\']'
    ]
    
    # Track all keys and their locations
    key_locations = defaultdict(list)
    
    lines = content.split('\n')
    for line_num, line in enumerate(lines, 1):
        for pattern in widget_patterns:
            matches = re.findall(pattern, line)
            for key in matches:
                # Skip f-string keys as they're likely unique
                if not ('{' in key or 'f"' in line or "f'" in line):
                    key_locations[key].append((line_num, line.strip()))
    
    # Find duplicates
    duplicates = {}
    for key, locations in key_locations.items():
        if len(locations) > 1:
            duplicates[key] = locations
    
    return duplicates

def analyze_dynamic_keys(filename):
    """Analyze keys that should be dynamic but might not be."""
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    issues = []
    
    # Look for loops or repeated sections that might need dynamic keys
    for i, line in enumerate(lines):
        # Check for loops
        if 'for ' in line and ' in ' in line:
            # Look ahead for widget declarations
            for j in range(i+1, min(i+20, len(lines))):
                if 'st.button(' in lines[j] or 'st.selectbox(' in lines[j] or 'st.checkbox(' in lines[j]:
                    if 'key=' in lines[j] and not ('{' in lines[j] or 'f"' in lines[j] or "f'" in lines[j]):
                        issues.append({
                            'line': j+1,
                            'type': 'static_key_in_loop',
                            'code': lines[j].strip()
                        })
    
    return issues

def generate_fix_report(duplicates, dynamic_issues):
    """Generate a report of issues and suggested fixes."""
    
    print("=== Streamlit Key Duplication Analysis ===\n")
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicate keys:\n")
        for key, locations in duplicates.items():
            print(f"Duplicate key: '{key}'")
            for line_num, code in locations:
                print(f"  Line {line_num}: {code[:80]}...")
            print(f"  Fix: Make keys unique by adding suffixes or using dynamic values\n")
    else:
        print("No duplicate static keys found.\n")
    
    if dynamic_issues:
        print(f"\nFound {len(dynamic_issues)} potential dynamic key issues:\n")
        for issue in dynamic_issues:
            print(f"Line {issue['line']}: {issue['type']}")
            print(f"  Code: {issue['code'][:80]}...")
            print(f"  Fix: Use f-string or format() to make key dynamic\n")
    
    # Generate fixes
    print("\n=== Suggested Fixes ===\n")
    
    fix_count = 1
    for key, locations in duplicates.items():
        print(f"{fix_count}. Fix duplicate key '{key}':")
        for i, (line_num, code) in enumerate(locations):
            suggested_key = f"{key}_{i+1}" if i > 0 else key
            print(f"   Line {line_num}: Change key='{key}' to key='{suggested_key}'")
        fix_count += 1
        print()

def main():
    """Main function."""
    filename = '/home/ec2-user/sre/sre_mcp/streamlit_app.py'
    
    print("Analyzing Streamlit app for duplicate keys...")
    
    duplicates = find_duplicate_keys(filename)
    dynamic_issues = analyze_dynamic_keys(filename)
    
    generate_fix_report(duplicates, dynamic_issues)
    
    if duplicates or dynamic_issues:
        print("\n⚠️  Issues found that need to be fixed!")
        return 1
    else:
        print("\n✅ No duplicate key issues found!")
        return 0

if __name__ == "__main__":
    sys.exit(main())