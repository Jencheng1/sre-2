#!/usr/bin/env python3
"""
Demo: Change Manager to Incident Correlation
Shows how changes lead to incidents with full timeline and correlation
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import random

# Initialize colorama
init()

class ChangeIncidentDemo:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.cloudtrail_client = boto3.client('cloudtrail', region_name='us-east-1')
        self.logs_client = boto3.client('logs', region_name='us-east-1')
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.ec2_client = boto3.client('ec2', region_name='us-east-1')
        
    def print_header(self, text):
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{text}")
        print(f"{'='*80}{Style.RESET_ALL}\n")
        
    def print_timeline(self, events):
        """Print a visual timeline of events."""
        print(f"\n{Fore.YELLOW}📅 Timeline of Events:{Style.RESET_ALL}")
        print("─" * 80)
        
        for event in events:
            time_str = event['time'].strftime('%H:%M:%S')
            icon = self.get_event_icon(event['type'])
            color = self.get_event_color(event['type'])
            
            print(f"{color}{time_str} {icon} {event['description']}{Style.RESET_ALL}")
            if 'details' in event:
                for detail in event['details']:
                    print(f"         └─ {detail}")
        print("─" * 80)
        
    def get_event_icon(self, event_type):
        icons = {
            'change': '🔧',
            'deployment': '🚀',
            'config': '⚙️',
            'warning': '⚠️',
            'error': '❌',
            'incident': '🚨',
            'metric': '📊',
            'customer': '👥'
        }
        return icons.get(event_type, '•')
        
    def get_event_color(self, event_type):
        colors = {
            'change': Fore.BLUE,
            'deployment': Fore.CYAN,
            'config': Fore.MAGENTA,
            'warning': Fore.YELLOW,
            'error': Fore.RED,
            'incident': Fore.RED,
            'metric': Fore.GREEN,
            'customer': Fore.WHITE
        }
        return colors.get(event_type, '')
        
    def create_change_record(self):
        """Create a change record in SSM."""
        change_details = {
            'ChangeRequestId': f'CHG-{random.randint(10000, 99999)}',
            'Title': 'Database Configuration Update - Connection Pool Increase',
            'Description': """
Increasing database connection pool size to handle increased load.

Changes:
1. Update RDS parameter group: max_connections from 100 to 500
2. Update application config: db.pool.max from 50 to 250
3. Deploy new application version with connection pooling changes

Risk: Medium - Potential memory usage increase
Rollback: Revert parameter group and redeploy previous version
""",
            'ApprovedBy': 'AutoApproval-Policy',
            'ScheduledTime': datetime.utcnow().isoformat(),
            'ChangeType': 'Standard',
            'Risk': 'Medium'
        }
        
        # Create as OpsItem with change metadata
        response = self.ssm_client.create_ops_item(
            Title=f"[CHANGE] {change_details['Title']}",
            Description=change_details['Description'],
            Source='Change-Manager',
            Severity='3',
            OperationalData={
                'ChangeRequestId': {'Value': change_details['ChangeRequestId'], 'Type': 'String'},
                'ChangeType': {'Value': change_details['ChangeType'], 'Type': 'String'},
                'Risk': {'Value': change_details['Risk'], 'Type': 'String'},
                'ScheduledTime': {'Value': change_details['ScheduledTime'], 'Type': 'String'}
            }
        )
        
        change_details['OpsItemId'] = response['OpsItemId']
        return change_details
        
    def simulate_change_execution(self, change_details):
        """Simulate executing the change with realistic events."""
        events = []
        base_time = datetime.utcnow()
        
        # T-0: Change approved and started
        events.append({
            'time': base_time,
            'type': 'change',
            'description': f"Change {change_details['ChangeRequestId']} execution started",
            'details': [
                'Automated approval based on standard change policy',
                'Maintenance window: Active'
            ]
        })
        
        # T+2min: RDS parameter group updated
        events.append({
            'time': base_time + timedelta(minutes=2),
            'type': 'config',
            'description': 'RDS parameter group updated',
            'details': [
                'Parameter: max_connections changed from 100 to 500',
                'Pending reboot required for changes to take effect'
            ]
        })
        
        # T+5min: Application deployment started
        events.append({
            'time': base_time + timedelta(minutes=5),
            'type': 'deployment',
            'description': 'Application deployment initiated',
            'details': [
                'Version: v2.5.0 with new connection pool settings',
                'Rolling deployment: 33% of instances'
            ]
        })
        
        # T+8min: First warnings appear
        events.append({
            'time': base_time + timedelta(minutes=8),
            'type': 'warning',
            'description': 'Connection pool warnings in application logs',
            'details': [
                'New instances attempting to create 250 connections',
                'RDS still using old parameter (100 max connections)',
                'Connection refused errors starting'
            ]
        })
        
        # T+10min: Errors escalate
        events.append({
            'time': base_time + timedelta(minutes=10),
            'type': 'error',
            'description': 'Database connection errors spike',
            'details': [
                'Error rate: 45% of requests failing',
                'Connection pool exhausted on all new instances',
                'Old instances (66%) still functioning normally'
            ]
        })
        
        # T+12min: Customer impact
        events.append({
            'time': base_time + timedelta(minutes=12),
            'type': 'customer',
            'description': 'Customer complaints begin',
            'details': [
                'Support tickets: 15 and rising',
                'Error: "Service temporarily unavailable"',
                'Affected regions: us-east-1, eu-west-1'
            ]
        })
        
        # T+15min: Incident declared
        events.append({
            'time': base_time + timedelta(minutes=15),
            'type': 'incident',
            'description': 'Critical incident declared',
            'details': [
                f'Root cause: Change {change_details["ChangeRequestId"]} - configuration mismatch',
                'Impact: 45% of requests failing',
                'Action: Rollback initiated'
            ]
        })
        
        return events
        
    def create_correlated_incident(self, change_details, timeline_events):
        """Create an incident that's correlated with the change."""
        # Find the incident event
        incident_time = next(e['time'] for e in timeline_events if e['type'] == 'incident')
        
        incident_data = {
            'Title': 'CRITICAL: Database Connection Failures - Production Impact',
            'Description': f"""
Critical database connectivity issues affecting production services.

Current Status:
- Error rate: 45% of all requests
- Affected services: api-gateway, user-service, order-processor
- Customer impact: HIGH - Users unable to complete transactions
- Started: {(incident_time - timedelta(minutes=7)).strftime('%H:%M')} UTC

Timeline:
{self.format_timeline_for_opsitem(timeline_events)}

Initial Investigation:
- Recent change: {change_details['ChangeRequestId']} - Database configuration update
- Issue: Application deployed with new connection pool size (250) but RDS still limited to 100
- Root cause: RDS parameter group change requires instance reboot, not performed

Correlation:
- Change ID: {change_details['ChangeRequestId']}
- Change OpsItem: {change_details['OpsItemId']}
- Time from change to incident: 15 minutes
""",
            'Source': 'Automated-Detection',
            'Severity': '1',
            'OperationalData': {
                'RelatedChangeId': {'Value': change_details['ChangeRequestId'], 'Type': 'String'},
                'RelatedOpsItemId': {'Value': change_details['OpsItemId'], 'Type': 'String'},
                'RootCause': {'Value': 'Configuration mismatch between application and database', 'Type': 'String'},
                'TimeToIncident': {'Value': '15 minutes', 'Type': 'String'},
                'CustomerImpact': {'Value': 'HIGH', 'Type': 'String'}
            }
        }
        
        response = self.ssm_client.create_ops_item(**incident_data)
        incident_data['OpsItemId'] = response['OpsItemId']
        
        return incident_data
        
    def format_timeline_for_opsitem(self, events):
        """Format timeline for OpsItem description."""
        timeline_str = ""
        for event in events:
            time_str = event['time'].strftime('%H:%M')
            timeline_str += f"- {time_str}: {event['description']}\n"
        return timeline_str
        
    def create_cloudwatch_metrics(self, timeline_events):
        """Create CloudWatch metrics that show the incident pattern."""
        print(f"\n{Fore.GREEN}📊 Creating CloudWatch metrics to show incident pattern...{Style.RESET_ALL}")
        
        # This would create actual metrics, but for demo we'll show what would be created
        metrics_created = [
            "DatabaseConnections: Sharp increase at T+5min, hitting limit at T+8min",
            "ApplicationErrors: Spike from 0% to 45% between T+8min and T+10min",
            "ResponseTime: Increase from 200ms to timeout (30s) at T+10min",
            "ActiveConnections: Plateau at 100 (RDS limit) from T+8min onwards"
        ]
        
        for metric in metrics_created:
            print(f"  • {metric}")
            
    def demonstrate_correlation(self, change_details, incident_details):
        """Show the correlation between change and incident."""
        print(f"\n{Fore.MAGENTA}🔗 Change-to-Incident Correlation:{Style.RESET_ALL}")
        print("─" * 80)
        
        print(f"{Fore.BLUE}CHANGE:{Style.RESET_ALL}")
        print(f"  • ID: {change_details['ChangeRequestId']}")
        print(f"  • Type: {change_details['ChangeType']}")
        print(f"  • Risk: {change_details['Risk']}")
        print(f"  • What: Database configuration update")
        
        print(f"\n{Fore.YELLOW}↓ 15 minutes later ↓{Style.RESET_ALL}\n")
        
        print(f"{Fore.RED}INCIDENT:{Style.RESET_ALL}")
        print(f"  • ID: {incident_details['OpsItemId']}")
        print(f"  • Severity: Critical")
        print(f"  • Impact: 45% error rate")
        print(f"  • Root Cause: Configuration mismatch from change")
        
        print(f"\n{Fore.GREEN}CORRELATION EVIDENCE:{Style.RESET_ALL}")
        print(f"  ✓ Timing: Incident started 15 min after change")
        print(f"  ✓ Component: Same database affected by change")
        print(f"  ✓ Pattern: Connection errors match config mismatch")
        print(f"  ✓ Logs: Show new pool size (250) > RDS limit (100)")
        
        print("─" * 80)
        
    def run_demo(self):
        """Run the complete change-to-incident demo."""
        self.print_header("Change Manager → Incident Correlation Demo")
        
        # Step 1: Create a change
        print(f"{Fore.GREEN}Step 1: Creating a change request in Change Manager{Style.RESET_ALL}")
        change_details = self.create_change_record()
        print(f"✅ Change created: {change_details['ChangeRequestId']}")
        print(f"   OpsItem: {change_details['OpsItemId']}")
        
        # Step 2: Simulate change execution
        print(f"\n{Fore.GREEN}Step 2: Executing the change{Style.RESET_ALL}")
        timeline_events = self.simulate_change_execution(change_details)
        time.sleep(2)
        
        # Step 3: Show timeline
        self.print_timeline(timeline_events)
        
        # Step 4: Create correlated incident
        print(f"\n{Fore.GREEN}Step 3: Critical incident detected!{Style.RESET_ALL}")
        incident_details = self.create_correlated_incident(change_details, timeline_events)
        print(f"🚨 Incident created: {incident_details['OpsItemId']}")
        
        # Step 5: Create metrics
        self.create_cloudwatch_metrics(timeline_events)
        
        # Step 6: Show correlation
        self.demonstrate_correlation(change_details, incident_details)
        
        # Step 7: Index to Knowledge Base
        print(f"\n{Fore.GREEN}Step 4: Indexing to Knowledge Base{Style.RESET_ALL}")
        self.index_to_kb(incident_details)
        
        # Summary
        self.print_header("Demo Complete!")
        print("✨ What we demonstrated:")
        print("  1. Created a change request with proper tracking")
        print("  2. Showed realistic timeline of change execution")
        print("  3. Demonstrated how configuration mismatch led to incident")
        print("  4. Created correlated incident with full context")
        print("  5. Indexed everything to Knowledge Base for future learning")
        
        print(f"\n📝 In Streamlit, you can now:")
        print(f"  • See the timeline visualization in the incident analysis")
        print(f"  • View the correlation between change {change_details['ChangeRequestId']} and the incident")
        print(f"  • Search KB for similar change-related incidents")
        print(f"  • Use this pattern to prevent future incidents")
        
        return change_details, incident_details
        
    def index_to_kb(self, incident_details):
        """Index the incident to Knowledge Base."""
        try:
            # Get the OpsItem details
            response = self.ssm_client.get_ops_item(OpsItemId=incident_details['OpsItemId'])
            ops_item = response['OpsItem']
            
            # Convert datetime objects
            ops_item_serializable = {}
            for key, value in ops_item.items():
                if isinstance(value, datetime):
                    ops_item_serializable[key] = value.isoformat()
                else:
                    ops_item_serializable[key] = value
            
            # Index to KB
            response = self.lambda_client.invoke(
                FunctionName='sre-knowledge-base-agent-lambda',
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    'action': 'index_opsitem',
                    'ops_item': ops_item_serializable
                })
            )
            
            if json.loads(response['Payload'].read()).get('statusCode') == 200:
                print("✅ Incident indexed to Knowledge Base with full correlation data")
            else:
                print("⚠️  Failed to index to Knowledge Base")
                
        except Exception as e:
            print(f"⚠️  KB indexing error: {str(e)}")


if __name__ == "__main__":
    demo = ChangeIncidentDemo()
    try:
        change_details, incident_details = demo.run_demo()
        
        # Save details for reference
        with open('/tmp/demo_correlation.json', 'w') as f:
            json.dump({
                'change': change_details,
                'incident': incident_details,
                'correlation': {
                    'time_to_incident': '15 minutes',
                    'root_cause': 'Configuration mismatch',
                    'pattern': 'Change → Config Mismatch → Service Degradation → Incident'
                }
            }, f, indent=2, default=str)
            
    except Exception as e:
        print(f"{Fore.RED}Demo failed: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()