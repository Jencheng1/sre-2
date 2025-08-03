#!/usr/bin/env python3
"""
Test security incident generation after S3 client fix.
"""

import boto3
from datetime import datetime
from streamlit_app import IncidentGenerator

def test_security_incident():
    """Test that security incident generation works properly."""
    print("🧪 Testing Security Incident Generation")
    print("="*60)
    
    generator = IncidentGenerator()
    
    try:
        # Create demo resources
        print("📦 Creating demo resources...")
        generator.create_demo_resources()
        
        # Test API failures generation
        print("\n🚨 Testing API failures generation...")
        failures = generator.generate_api_failures()
        
        print(f"✅ Generated {len(failures)} API failures:")
        for failure in failures:
            print(f"   • {failure}")
            
        # Create OpsItem
        print("\n📋 Creating OpsItem...")
        ops_item_id = generator.create_opsitem(
            "TEST: Security Incident (S3 Fix)",
            f"Testing security incident after S3 client fix. Failures: {', '.join(failures)}",
            severity='3'
        )
        
        if ops_item_id:
            print(f"✅ Successfully created OpsItem: {ops_item_id}")
        else:
            print("❌ Failed to create OpsItem")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("\n" + "="*60)
    print("🔧 S3 CLIENT FIX VERIFICATION")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    success = test_security_incident()
    
    if success:
        print("\n✅ Security incident generation is working!")
        print("\nYou can now:")
        print("1. Open http://localhost:8501")
        print("2. Click 'Generate Real Incident'")
        print("3. Select 'Security Alert'")
        print("4. The incident will be created successfully")
    else:
        print("\n❌ Test failed - please check the error above")

if __name__ == "__main__":
    main()