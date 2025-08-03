#!/usr/bin/env python3
"""
Demo script to showcase knowledge base functionality.
"""

import boto3
import json
import time
from datetime import datetime
from incident_scenarios import IncidentScenarios
from knowledge_base_documents import KnowledgeBaseDocuments

class KnowledgeBaseDemo:
    """Demo the knowledge base capabilities."""
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.scenarios = IncidentScenarios()
        self.kb_docs = KnowledgeBaseDocuments()
        
    def print_banner(self):
        """Print demo banner."""
        print("\n" + "="*80)
        print("🎯 SRE KNOWLEDGE BASE DEMO")
        print("="*80)
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nThis demo showcases:")
        print("  ✓ Incident scenarios with timelines and correlations")
        print("  ✓ Best practices and resolution guides")
        print("  ✓ Vector similarity search using OpenSearch")
        print("  ✓ Knowledge-enhanced root cause analysis")
        print("="*80 + "\n")
        
    def demo_incident_scenarios(self):
        """Demo incident scenarios with timelines."""
        print("\n📋 INCIDENT SCENARIOS")
        print("="*60)
        
        # Show a sample incident with timeline
        scenario = self.scenarios.get_scenario('PERF-001')
        print(f"\nIncident: {scenario['title']}")
        print(f"Category: {scenario['category']}")
        print(f"Severity: {scenario['severity']}")
        print(f"\nDescription: {scenario['description']}")
        
        print("\n⏱️ Timeline:")
        timeline = self.scenarios.generate_timeline_events(scenario)
        for event in timeline[:5]:  # Show first 5 events
            print(f"  {event['relative_time']}: {event['event']} [{event['type']}]")
            
        print(f"\n🎯 Root Cause: {scenario['root_cause']}")
        
        print("\n🔗 Correlated Changes:")
        for change in scenario['correlated_changes']:
            print(f"  - {change}")
            
        print(f"\n✅ Resolution: {scenario['resolution']}")
        
    def demo_best_practices(self):
        """Demo best practices documents."""
        print("\n\n📚 BEST PRACTICES")
        print("="*60)
        
        # Show a sample best practice
        bp = self.kb_docs.best_practices[0]  # Database Connection Pool
        print(f"\nBest Practice: {bp['title']}")
        print(f"Category: {bp['category']}")
        print(f"Tags: {', '.join(bp['tags'])}")
        
        # Show excerpt
        content_lines = bp['content'].split('\n')
        print("\nKey Points:")
        for line in content_lines[10:16]:  # Show some key practices
            if line.strip() and not line.strip().startswith('#'):
                print(f"  {line.strip()}")
                
    def demo_resolution_guides(self):
        """Demo resolution guides."""
        print("\n\n🛠️ RESOLUTION GUIDES")
        print("="*60)
        
        # Show a sample resolution guide
        rg = self.kb_docs.resolution_guides[0]  # Database Connection Pool Exhaustion
        print(f"\nResolution Guide: {rg['title']}")
        print(f"Category: {rg['category']}")
        
        # Extract immediate actions
        content = rg['content']
        if 'Immediate Actions:' in content:
            print("\nImmediate Actions:")
            immediate_section = content.split('Immediate Actions:')[1].split('\n\n')[0]
            lines = immediate_section.split('\n')[:5]
            for line in lines:
                if line.strip():
                    print(f"  {line.strip()}")
                    
    def demo_knowledge_search(self):
        """Demo knowledge base search capabilities."""
        print("\n\n🔍 KNOWLEDGE BASE SEARCH DEMO")
        print("="*60)
        
        test_queries = [
            {
                'query': 'database connection timeout performance issue',
                'type': 'incidents',
                'description': 'Finding similar performance incidents'
            },
            {
                'query': 'security group configuration best practices',
                'type': 'best_practices',
                'description': 'Finding security best practices'
            },
            {
                'query': 'how to resolve service outage',
                'type': 'resolution',
                'description': 'Finding outage resolution guide'
            }
        ]
        
        print("\nNote: These searches would use vector similarity in OpenSearch")
        print("to find the most relevant documents based on semantic meaning.\n")
        
        for test in test_queries:
            print(f"🔎 {test['description']}")
            print(f"   Query: '{test['query']}'")
            print(f"   Type: {test['type']}")
            print(f"   Would return: Top 5 most similar documents\n")
            
    def demo_contextual_analysis(self):
        """Demo knowledge-enhanced analysis."""
        print("\n🤖 KNOWLEDGE-ENHANCED ANALYSIS DEMO")
        print("="*60)
        
        incident_desc = "Application experiencing severe slowdown with database connection pool exhaustion"
        
        print(f"\nIncident: {incident_desc}")
        print("\nKnowledge Base would provide:")
        print("  ✓ 3 similar past incidents with their root causes")
        print("  ✓ 2 relevant best practices for prevention")
        print("  ✓ 1 specific resolution guide with step-by-step instructions")
        
        print("\nEnhanced Analysis would include:")
        print("  • Pattern matching with historical incidents")
        print("  • Proven resolution steps from past successes")
        print("  • Best practices to prevent recurrence")
        print("  • Correlation of changes and timeline events")
        
    def demo_correlation_insights(self):
        """Demo correlation insights from knowledge base."""
        print("\n\n🔗 CORRELATION INSIGHTS")
        print("="*60)
        
        print("\nThe knowledge base enables powerful correlations:")
        print("\n1. Change-to-Incident Correlation:")
        print("   • Security group change → Unauthorized access attempts")
        print("   • Database config change → Connection pool issues")
        print("   • Lambda deployment → Cold start performance impact")
        
        print("\n2. Pattern Recognition:")
        print("   • Similar incidents tend to have similar root causes")
        print("   • Specific error patterns indicate known issues")
        print("   • Timeline patterns help predict incident evolution")
        
        print("\n3. Preventive Insights:")
        print("   • Which changes commonly lead to incidents")
        print("   • What monitoring would have caught issues earlier")
        print("   • Which best practices prevent specific incident types")


def main():
    """Run the knowledge base demo."""
    demo = KnowledgeBaseDemo()
    demo.print_banner()
    
    # Run demo sections
    demo.demo_incident_scenarios()
    demo.demo_best_practices()
    demo.demo_resolution_guides()
    demo.demo_knowledge_search()
    demo.demo_contextual_analysis()
    demo.demo_correlation_insights()
    
    print("\n\n" + "="*80)
    print("💡 KEY BENEFITS")
    print("="*80)
    print("\n1. Faster Root Cause Analysis:")
    print("   • Instantly find similar past incidents")
    print("   • Apply proven resolution patterns")
    print("   • Reduce MTTR significantly")
    
    print("\n2. Knowledge Retention:")
    print("   • Capture institutional knowledge")
    print("   • Learn from every incident")
    print("   • Build comprehensive runbooks")
    
    print("\n3. Proactive Prevention:")
    print("   • Identify risky changes")
    print("   • Apply best practices consistently")
    print("   • Prevent incident recurrence")
    
    print("\n✅ Demo Complete!")
    print("\nTo deploy the knowledge base:")
    print("  1. Run: ./deploy_knowledge_base.sh")
    print("  2. Create OpenSearch domain (if needed)")
    print("  3. Run: python3 populate_knowledge_base.py")
    print("  4. Access via Streamlit UI at port 8501")
    print("\n")


if __name__ == "__main__":
    main()