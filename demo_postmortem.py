#!/usr/bin/env python3
"""
Demo Script for Post-Mortem Analysis Feature
Shows how to generate comprehensive post-mortem reports
"""

import json
from datetime import datetime, timedelta
from postmortem.postmortem_agent import PostMortemAgent
from dataclasses import asdict


def demo_basic_postmortem():
    """Demonstrate basic post-mortem generation"""
    print("🔍 Demo: Basic Post-Mortem Generation")
    print("=" * 50)
    
    # Create incident data
    incident_data = {
        'incident_id': 'DEMO-001',
        'type': 'outage',
        'severity': 'CRITICAL',
        'description': 'Complete payment processing system outage affecting all transactions',
        'start_time': datetime.now() - timedelta(hours=2, minutes=30),
        'resolution_time': datetime.now().isoformat(),
        'service': 'payment-gateway',
        'detection_method': 'Automated monitoring alert',
        'immediate_actions': 'Activated incident response team, rolled back recent deployment'
    }
    
    # Generate post-mortem
    agent = PostMortemAgent()
    report = agent.analyze_incident(incident_data)
    
    # Display summary
    print(f"\n📋 Post-Mortem Report Generated")
    print(f"Title: {report.title}")
    print(f"Severity: {report.severity}")
    print(f"Duration: {report.duration_minutes} minutes")
    print(f"Users Impacted: {report.users_impacted:,}")
    print(f"Revenue Impact: {report.revenue_impact}")
    print(f"AI Confidence: {report.ai_confidence_score:.0%}")
    
    # Show root cause
    print(f"\n🔍 Root Cause: {report.root_cause}")
    
    # Show action items
    print(f"\n✅ Action Items ({len(report.action_items)}):")
    for item in report.action_items[:3]:
        print(f"  - [{item['priority']}] {item['title']}")
        
    return report


def demo_performance_postmortem():
    """Demonstrate performance incident post-mortem"""
    print("\n\n🚀 Demo: Performance Incident Post-Mortem")
    print("=" * 50)
    
    incident_data = {
        'incident_id': 'DEMO-002',
        'type': 'performance',
        'severity': 'HIGH',
        'description': 'API response times increased from 200ms to 5000ms during peak hours',
        'start_time': datetime.now() - timedelta(hours=4),
        'resolution_time': (datetime.now() - timedelta(hours=1)).isoformat(),
        'service': 'api-gateway',
        'raw_data': {
            'metrics': {
                'ResponseTime': [
                    {'Maximum': 5000, 'Average': 3500, 'Timestamp': (datetime.now() - timedelta(hours=3)).isoformat()},
                    {'Maximum': 4800, 'Average': 3200, 'Timestamp': (datetime.now() - timedelta(hours=2)).isoformat()}
                ],
                'CPUUtilization': [
                    {'Maximum': 95, 'Average': 85, 'Timestamp': (datetime.now() - timedelta(hours=3)).isoformat()}
                ]
            }
        }
    }
    
    agent = PostMortemAgent()
    report = agent.analyze_incident(incident_data)
    
    print(f"\n📊 Performance Analysis")
    print(f"Peak Response Time: 5000ms (25x normal)")
    print(f"CPU Utilization: 95% (critical)")
    
    print(f"\n💡 Lessons Learned:")
    for lesson in report.lessons_learned[:2]:
        print(f"  • {lesson}")
        
    print(f"\n🛡️ Preventive Measures:")
    for measure in report.preventive_measures[:2]:
        print(f"  • {measure}")
        
    return report


def demo_security_postmortem():
    """Demonstrate security incident post-mortem"""
    print("\n\n🔒 Demo: Security Incident Post-Mortem")
    print("=" * 50)
    
    incident_data = {
        'incident_id': 'DEMO-003',
        'type': 'security',
        'severity': 'HIGH',
        'description': 'Suspicious authentication attempts detected from multiple IPs',
        'start_time': datetime.now() - timedelta(hours=1),
        'resolution_time': datetime.now().isoformat(),
        'service': 'auth-service',
        'detection_method': 'WAF alert on brute force pattern'
    }
    
    agent = PostMortemAgent()
    report = agent.analyze_incident(incident_data)
    
    print(f"\n🔐 Security Impact")
    print(f"Users Potentially Affected: {report.users_impacted:,}")
    print(f"Compliance Risk: {report.revenue_impact}")
    
    print(f"\n✅ What Went Well:")
    for item in report.what_went_well[:2]:
        print(f"  • {item}")
        
    print(f"\n❌ What Went Wrong:")
    for item in report.what_went_wrong[:2]:
        print(f"  • {item}")
        
    return report


def demo_markdown_export(report):
    """Demonstrate markdown export"""
    print("\n\n📝 Demo: Markdown Export")
    print("=" * 50)
    
    agent = PostMortemAgent()
    markdown = agent.generate_markdown_report(report)
    
    # Show first part of markdown
    lines = markdown.split('\n')
    print("Generated Markdown Preview:")
    print("-" * 30)
    for line in lines[:20]:
        print(line)
    print("... (truncated)")
    
    # Save to file
    filename = f"postmortem_{report.incident_id}.md"
    with open(filename, 'w') as f:
        f.write(markdown)
    print(f"\n✅ Full report saved to: {filename}")
    
    return markdown


def demo_json_export(report):
    """Demonstrate JSON export"""
    print("\n\n💾 Demo: JSON Export")
    print("=" * 50)
    
    report_dict = asdict(report)
    json_str = json.dumps(report_dict, indent=2)
    
    # Show structure
    print("JSON Structure:")
    print("-" * 30)
    print("{")
    for key in list(report_dict.keys())[:10]:
        value = report_dict[key]
        if isinstance(value, (str, int, float, bool)):
            print(f'  "{key}": {json.dumps(value)},')
        else:
            print(f'  "{key}": [...],')
    print("  ...")
    print("}")
    
    # Save to file
    filename = f"postmortem_{report.incident_id}.json"
    with open(filename, 'w') as f:
        f.write(json_str)
    print(f"\n✅ JSON data saved to: {filename}")
    
    return json_str


def demo_timeline_visualization():
    """Show timeline data structure"""
    print("\n\n⏱️ Demo: Timeline Visualization")
    print("=" * 50)
    
    timeline_events = [
        {'time': '2024-01-15T10:00:00', 'event': 'First error detected in logs', 'severity': 'warning'},
        {'time': '2024-01-15T10:05:00', 'event': 'Error rate exceeded threshold', 'severity': 'critical'},
        {'time': '2024-01-15T10:10:00', 'event': 'Incident response team alerted', 'severity': 'info'},
        {'time': '2024-01-15T10:15:00', 'event': 'Root cause identified', 'severity': 'info'},
        {'time': '2024-01-15T10:30:00', 'event': 'Mitigation applied', 'severity': 'info'},
        {'time': '2024-01-15T10:45:00', 'event': 'Service restored', 'severity': 'info'},
        {'time': '2024-01-15T11:00:00', 'event': 'Incident resolved', 'severity': 'info'}
    ]
    
    print("Timeline Events:")
    for event in timeline_events:
        severity_icon = '🔴' if event['severity'] == 'critical' else '🟡' if event['severity'] == 'warning' else '🟢'
        print(f"{severity_icon} {event['time']} - {event['event']}")
    
    print("\n📈 This timeline would be visualized as an interactive chart in Streamlit")


def main():
    """Run all demos"""
    print("🚀 Post-Mortem Analysis Feature Demo")
    print("=" * 70)
    print("This demo shows the comprehensive post-mortem analysis capabilities")
    print("=" * 70)
    
    # Run demos
    basic_report = demo_basic_postmortem()
    performance_report = demo_performance_postmortem()
    security_report = demo_security_postmortem()
    
    # Export demos
    demo_markdown_export(basic_report)
    demo_json_export(basic_report)
    
    # Timeline demo
    demo_timeline_visualization()
    
    print("\n\n✨ Demo Complete!")
    print("=" * 70)
    print("Key Features Demonstrated:")
    print("  ✅ AI-powered incident analysis")
    print("  ✅ Multiple incident types (outage, performance, security)")
    print("  ✅ Comprehensive report generation")
    print("  ✅ Action item tracking")
    print("  ✅ Timeline visualization")
    print("  ✅ Markdown and JSON export")
    print("  ✅ Impact analysis and metrics")
    print("\n🎯 Access the full UI at: http://localhost:8501")
    print("   Navigate to the '📋 Post-Mortem' tab")


if __name__ == "__main__":
    main()