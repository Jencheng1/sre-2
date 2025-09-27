#!/usr/bin/env python3
"""
Setup Java Spring Boot Actuator and JVM Metrics Monitoring
Configures metrics collection from SRE-DEMO instance and creates Grafana dashboards
"""

import boto3
import json
import requests
import time
from datetime import datetime, timedelta

class JavaMetricsSetup:
    def __init__(self):
        self.ssm_client = boto3.client('ssm', region_name='us-east-1')
        self.cloudwatch_client = boto3.client('cloudwatch', region_name='us-east-1')
        self.instance_id = "i-02bef13982a179478"  # SRE-DEMO
        
        # Grafana configuration
        self.grafana_url = "http://localhost:3000"
        self.grafana_user = "admin"
        self.grafana_pass = "admin123"
        
    def install_cloudwatch_agent_config(self):
        """Configure CloudWatch agent to collect JVM metrics"""
        print("📋 Creating CloudWatch Agent Configuration for JVM Metrics...")
        
        config = {
            "agent": {
                "metrics_collection_interval": 60,
                "run_as_user": "root"
            },
            "metrics": {
                "namespace": "JavaApp/SpringBoot",
                "metrics_collected": {
                    "procstat": [
                        {
                            "pattern": "java.*payment-service",
                            "measurement": [
                                "cpu_usage",
                                "memory_rss",
                                "memory_vms",
                                "num_threads"
                            ],
                            "metrics_collection_interval": 60
                        }
                    ],
                    "mem": {
                        "measurement": [
                            "mem_used_percent"
                        ],
                        "metrics_collection_interval": 60
                    }
                },
                "append_dimensions": {
                    "InstanceId": "${aws:InstanceId}",
                    "Application": "payment-service"
                }
            }
        }
        
        # Store configuration in SSM Parameter Store
        try:
            self.ssm_client.put_parameter(
                Name='/cloudwatch-agent/java-metrics-config',
                Value=json.dumps(config, indent=2),
                Type='String',
                Description='CloudWatch agent config for Java application metrics',
                Overwrite=True
            )
            print("✅ CloudWatch agent configuration stored in Parameter Store")
        except Exception as e:
            print(f"⚠️ Error storing config: {e}")
            
    def setup_spring_boot_actuator_script(self):
        """Create script to collect Spring Boot Actuator metrics"""
        print("\n📝 Creating Spring Boot Actuator Metrics Collection Script...")
        
        script_content = """#!/bin/bash
# Spring Boot Actuator Metrics Collector for CloudWatch

# Configuration
ACTUATOR_URL="http://localhost:8080/actuator/metrics"
NAMESPACE="JavaApp/SpringBoot"
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d ' ' -f 2)
APP_NAME="payment-service"

# Function to get metric value from actuator
get_metric() {
    local metric_name=$1
    curl -s "${ACTUATOR_URL}/${metric_name}" | jq -r '.measurements[0].value // 0'
}

# Function to push metric to CloudWatch
push_metric() {
    local metric_name=$1
    local value=$2
    local unit=${3:-"None"}
    
    aws cloudwatch put-metric-data \
        --namespace "$NAMESPACE" \
        --metric-name "$metric_name" \
        --value "$value" \
        --unit "$unit" \
        --dimensions InstanceId="$INSTANCE_ID",Application="$APP_NAME" \
        --region us-east-1
}

# Collect and push JVM metrics
while true; do
    echo "Collecting JVM metrics at $(date)"
    
    # Heap memory
    heap_used=$(get_metric "jvm.memory.used" | jq -r '.measurements[] | select(.statistic=="VALUE" and .tags.area=="heap") | .value // 0')
    heap_max=$(get_metric "jvm.memory.max" | jq -r '.measurements[] | select(.statistic=="VALUE" and .tags.area=="heap") | .value // 0')
    heap_percent=$(echo "scale=2; ($heap_used / $heap_max) * 100" | bc)
    push_metric "JVM_HeapUsedPercent" "$heap_percent" "Percent"
    
    # GC metrics
    gc_pause=$(get_metric "jvm.gc.pause" | jq -r '.measurements[] | select(.statistic=="MAX") | .value // 0')
    gc_count=$(get_metric "jvm.gc.live.data.size" | jq -r '.measurements[0].value // 0')
    push_metric "JVM_GCPauseTime" "$gc_pause" "Seconds"
    push_metric "JVM_GCCount" "$gc_count" "Count"
    
    # Thread metrics
    threads_live=$(get_metric "jvm.threads.live" | jq -r '.measurements[0].value // 0')
    threads_daemon=$(get_metric "jvm.threads.daemon" | jq -r '.measurements[0].value // 0')
    push_metric "JVM_ThreadsLive" "$threads_live" "Count"
    push_metric "JVM_ThreadsDaemon" "$threads_daemon" "Count"
    
    # Application metrics
    http_requests=$(get_metric "http.server.requests" | jq -r '.measurements[] | select(.statistic=="COUNT") | .value // 0')
    push_metric "App_HttpRequests" "$http_requests" "Count"
    
    # Custom cache metrics (if available)
    cache_size=$(get_metric "cache.size" | jq -r '.measurements[0].value // 0')
    if [ "$cache_size" != "0" ]; then
        push_metric "App_CacheSize" "$cache_size" "Count"
    fi
    
    echo "Metrics pushed to CloudWatch"
    
    # Sleep for 1 minute
    sleep 60
done
"""
        
        # Create the script file
        with open('/tmp/actuator_metrics_collector.sh', 'w') as f:
            f.write(script_content)
            
        print("✅ Actuator metrics collection script created")
        
        # Deploy script to instance using SSM
        print("\n🚀 Deploying script to SRE-DEMO instance...")
        
        try:
            response = self.ssm_client.send_command(
                InstanceIds=[self.instance_id],
                DocumentName='AWS-RunShellScript',
                Parameters={
                    'commands': [
                        'mkdir -p /opt/monitoring/scripts',
                        f'cat > /opt/monitoring/scripts/actuator_metrics.sh << "EOF"\n{script_content}\nEOF',
                        'chmod +x /opt/monitoring/scripts/actuator_metrics.sh',
                        'echo "Script deployed successfully"'
                    ]
                }
            )
            
            command_id = response['Command']['CommandId']
            print(f"✅ Script deployed (Command ID: {command_id})")
            
        except Exception as e:
            print(f"⚠️ Error deploying script: {e}")
            
    def create_java_grafana_dashboard(self):
        """Create Grafana dashboard for Java/JVM metrics"""
        print("\n📊 Creating Java Application Monitoring Dashboard in Grafana...")
        
        auth = (self.grafana_user, self.grafana_pass)
        
        # Get CloudWatch datasource
        r = requests.get(f"{self.grafana_url}/api/datasources", auth=auth)
        datasource = None
        
        if r.status_code == 200:
            datasources = r.json()
            for ds in datasources:
                if ds['type'] == 'cloudwatch':
                    datasource = ds
                    break
                    
        if not datasource:
            print("❌ No CloudWatch datasource found")
            return False
            
        dashboard = {
            "dashboard": {
                "title": "Java Spring Boot Application Monitoring",
                "uid": "java-app-monitoring",
                "tags": ["java", "jvm", "spring-boot", "memory"],
                "timezone": "browser",
                "panels": [
                    # Row 1: Key Metrics Overview
                    {
                        "id": 1,
                        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
                        "type": "stat",
                        "title": "JVM Heap Usage",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "JavaApp/SpringBoot",
                            "metricName": "JVM_HeapUsedPercent",
                            "dimensions": {"InstanceId": self.instance_id},
                            "statistic": "Average",
                            "period": "300",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 70},
                                        {"color": "red", "value": 85}
                                    ]
                                },
                                "color": {"mode": "thresholds"}
                            }
                        },
                        "options": {
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"]
                            },
                            "orientation": "auto",
                            "textMode": "auto",
                            "colorMode": "value",
                            "graphMode": "area"
                        }
                    },
                    {
                        "id": 2,
                        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
                        "type": "gauge",
                        "title": "CPU Utilization",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "AWS/EC2",
                            "metricName": "CPUUtilization",
                            "dimensions": {"InstanceId": self.instance_id},
                            "statistic": "Maximum",
                            "period": "300",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 60},
                                        {"color": "red", "value": 80}
                                    ]
                                }
                            }
                        },
                        "options": {
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"]
                            },
                            "showThresholdLabels": True,
                            "showThresholdMarkers": True
                        }
                    },
                    {
                        "id": 3,
                        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 0},
                        "type": "stat",
                        "title": "GC Pause Time",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "JavaApp/SpringBoot",
                            "metricName": "JVM_GCPauseTime",
                            "dimensions": {"InstanceId": self.instance_id},
                            "statistic": "Maximum",
                            "period": "300",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "ms",
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 100},
                                        {"color": "red", "value": 500}
                                    ]
                                },
                                "color": {"mode": "thresholds"}
                            }
                        }
                    },
                    # Row 2: Time Series
                    {
                        "id": 4,
                        "gridPos": {"h": 10, "w": 12, "x": 0, "y": 8},
                        "type": "timeseries",
                        "title": "Memory Usage Trends",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "JavaApp/SpringBoot",
                                "metricName": "JVM_HeapUsedPercent",
                                "dimensions": {"InstanceId": self.instance_id},
                                "statistic": "Average",
                                "period": "60",
                                "region": "default",
                                "refId": "A",
                                "alias": "Heap Used %"
                            },
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "JavaApp/SpringBoot",
                                "metricName": "HeapMemoryUsed",
                                "dimensions": {"InstanceId": self.instance_id},
                                "statistic": "Average",
                                "period": "60",
                                "region": "default",
                                "refId": "B",
                                "alias": "App Memory %"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "color": {"mode": "palette-classic"},
                                "custom": {
                                    "drawStyle": "line",
                                    "lineInterpolation": "smooth",
                                    "lineWidth": 2,
                                    "fillOpacity": 10,
                                    "gradientMode": "none",
                                    "spanNulls": True,
                                    "showPoints": "never"
                                }
                            }
                        },
                        "options": {
                            "tooltip": {"mode": "multi"},
                            "legend": {
                                "showLegend": True,
                                "displayMode": "list",
                                "placement": "bottom",
                                "calcs": ["mean", "lastNotNull", "max"]
                            }
                        }
                    },
                    {
                        "id": 5,
                        "gridPos": {"h": 10, "w": 12, "x": 12, "y": 8},
                        "type": "timeseries",
                        "title": "CPU vs GC Activity",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "AWS/EC2",
                                "metricName": "CPUUtilization",
                                "dimensions": {"InstanceId": self.instance_id},
                                "statistic": "Maximum",
                                "period": "60",
                                "region": "default",
                                "refId": "A",
                                "alias": "CPU %"
                            },
                            {
                                "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                                "namespace": "JavaApp/SpringBoot",
                                "metricName": "GCPauseTime",
                                "dimensions": {"InstanceId": self.instance_id},
                                "statistic": "Average",
                                "period": "60",
                                "region": "default",
                                "refId": "B",
                                "alias": "GC Pause (ms)"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "custom": {
                                    "drawStyle": "line",
                                    "lineInterpolation": "smooth",
                                    "lineWidth": 2,
                                    "fillOpacity": 10,
                                    "spanNulls": True
                                }
                            },
                            "overrides": [
                                {
                                    "matcher": {"id": "byName", "options": "CPU %"},
                                    "properties": [{"id": "unit", "value": "percent"}]
                                },
                                {
                                    "matcher": {"id": "byName", "options": "GC Pause (ms)"},
                                    "properties": [
                                        {"id": "unit", "value": "ms"},
                                        {"id": "custom.axisPlacement", "value": "right"}
                                    ]
                                }
                            ]
                        },
                        "options": {
                            "tooltip": {"mode": "multi"},
                            "legend": {
                                "showLegend": True,
                                "displayMode": "list",
                                "placement": "bottom"
                            }
                        }
                    },
                    # Row 3: Thread and Cache Metrics
                    {
                        "id": 6,
                        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 18},
                        "type": "timeseries",
                        "title": "JVM Thread Count",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "JavaApp/SpringBoot",
                            "metricName": "JVM_ThreadsLive",
                            "dimensions": {"InstanceId": self.instance_id},
                            "statistic": "Average",
                            "period": "60",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "short",
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    },
                    {
                        "id": 7,
                        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 18},
                        "type": "stat",
                        "title": "Transaction Cache Size",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "JavaApp/SpringBoot",
                            "metricName": "App_CacheSize",
                            "dimensions": {"InstanceId": self.instance_id},
                            "statistic": "Maximum",
                            "period": "300",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "short",
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"color": "green", "value": None},
                                        {"color": "yellow", "value": 10000},
                                        {"color": "red", "value": 50000}
                                    ]
                                },
                                "color": {"mode": "thresholds"}
                            }
                        }
                    },
                    {
                        "id": 8,
                        "gridPos": {"h": 8, "w": 8, "x": 16, "y": 18},
                        "type": "timeseries",
                        "title": "HTTP Request Rate",
                        "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                        "targets": [{
                            "datasource": {"type": "cloudwatch", "uid": datasource['uid']},
                            "namespace": "JavaApp/SpringBoot",
                            "metricName": "App_HttpRequests",
                            "dimensions": {"InstanceId": self.instance_id},
                            "statistic": "Sum",
                            "period": "60",
                            "region": "default",
                            "refId": "A"
                        }],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "reqps",
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    }
                ],
                "refresh": "10s",
                "time": {"from": "now-1h", "to": "now"}
            },
            "overwrite": True
        }
        
        # Create the dashboard
        r = requests.post(
            f"{self.grafana_url}/api/dashboards/db",
            auth=auth,
            json=dashboard
        )
        
        if r.status_code in [200, 201]:
            result = r.json()
            print(f"✅ Java monitoring dashboard created")
            print(f"   URL: {self.grafana_url}/d/{result['uid']}")
            return True
        else:
            print(f"❌ Failed to create dashboard: {r.text}")
            return False
            
    def generate_sample_jvm_metrics(self):
        """Generate sample JVM metrics to demonstrate the dashboard"""
        print("\n📈 Generating Sample JVM Metrics...")
        
        namespace = 'JavaApp/SpringBoot'
        current_time = datetime.utcnow()
        
        # Generate some sample data points
        for i in range(10):
            timestamp = current_time - timedelta(minutes=i*5)
            
            # Simulate memory growth
            heap_percent = 60 + (10 - i) * 3  # Growing from 60% to 90%
            gc_pause = 50 + (10 - i) * 10     # GC pause increases with memory
            threads = 150 + i * 2              # Thread count varies
            cache_size = 5000 + (10 - i) * 5000  # Cache growing
            
            self.cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': 'JVM_HeapUsedPercent',
                        'Value': heap_percent,
                        'Unit': 'Percent',
                        'Timestamp': timestamp,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': self.instance_id},
                            {'Name': 'Application', 'Value': 'payment-service'}
                        ]
                    },
                    {
                        'MetricName': 'JVM_GCPauseTime',
                        'Value': gc_pause,
                        'Unit': 'Milliseconds',
                        'Timestamp': timestamp,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': self.instance_id},
                            {'Name': 'Application', 'Value': 'payment-service'}
                        ]
                    },
                    {
                        'MetricName': 'JVM_ThreadsLive',
                        'Value': threads,
                        'Unit': 'Count',
                        'Timestamp': timestamp,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': self.instance_id},
                            {'Name': 'Application', 'Value': 'payment-service'}
                        ]
                    },
                    {
                        'MetricName': 'App_CacheSize',
                        'Value': cache_size,
                        'Unit': 'Count',
                        'Timestamp': timestamp,
                        'Dimensions': [
                            {'Name': 'InstanceId', 'Value': self.instance_id},
                            {'Name': 'Application', 'Value': 'payment-service'}
                        ]
                    }
                ]
            )
            
        print("✅ Sample JVM metrics generated")

def main():
    """Setup Java metrics monitoring"""
    print("🚀 Setting up Java Spring Boot Metrics Monitoring")
    print("=" * 60)
    
    setup = JavaMetricsSetup()
    
    # Step 1: Configure CloudWatch agent
    setup.install_cloudwatch_agent_config()
    
    # Step 2: Setup actuator metrics script
    setup.setup_spring_boot_actuator_script()
    
    # Step 3: Create Grafana dashboard
    if setup.create_java_grafana_dashboard():
        print("\n✅ Java monitoring setup complete!")
        
        # Step 4: Generate sample metrics
        setup.generate_sample_jvm_metrics()
        
        print("\n📊 Monitoring URLs:")
        print(f"   Java Dashboard: {setup.grafana_url}/d/java-app-monitoring")
        print(f"   EC2 CPU Dashboard: {setup.grafana_url}/d/ec2-max-cpu")
        
        print("\n📝 Next Steps:")
        print("1. Run the memory leak test case:")
        print("   python3 java_memory_leak_test_case.py")
        print("2. View the correlation in Streamlit CPU Spike Demo")
        print("3. Monitor JVM metrics in the Grafana dashboard")
        
        print("\n⚡ Metrics Being Collected:")
        print("   - JVM Heap Memory Usage")
        print("   - Garbage Collection Pause Times")
        print("   - Thread Count")
        print("   - Transaction Cache Size")
        print("   - HTTP Request Rate")
        print("   - CPU Utilization (correlated)")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())