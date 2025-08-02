import json
import logging
import statistics
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def detect_anomalies(metrics_data, time_range):
    """Detect anomalies in metrics data using statistical methods."""
    try:
        # Parse metrics data (assuming it's a list of {timestamp, value} objects)
        values = [float(point.get('value', 0)) for point in metrics_data]
        
        if not values:
            return []
            
        # Calculate basic statistics
        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        threshold = mean + (2 * stdev)  # 2 standard deviations
        
        # Find anomalies
        anomalies = []
        for i, point in enumerate(metrics_data):
            value = float(point.get('value', 0))
            if value > threshold:
                anomalies.append({
                    "type": "threshold_breach",
                    "timestamp": point.get('timestamp'),
                    "value": value,
                    "threshold": threshold,
                    "deviation": (value - mean) / stdev if stdev > 0 else 0
                })
                
        return anomalies
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise

def analyze_trends(metrics_data, time_range):
    """Analyze trends in metrics data."""
    try:
        # Calculate moving averages and trends
        window_size = max(1, len(metrics_data) // 10)  # 10% of data points
        values = [float(point.get('value', 0)) for point in metrics_data]
        
        if not values:
            return []
            
        # Calculate moving average
        moving_avg = []
        for i in range(len(values) - window_size + 1):
            window = values[i:i + window_size]
            avg = sum(window) / window_size
            moving_avg.append(avg)
        
        # Detect trends
        trends = []
        if len(moving_avg) > 1:
            overall_change = moving_avg[-1] - moving_avg[0]
            percent_change = (overall_change / moving_avg[0]) * 100 if moving_avg[0] != 0 else 0
            
            trend_type = "increasing" if overall_change > 0 else "decreasing"
            if abs(percent_change) < 5:
                trend_type = "stable"
                
            trends.append({
                "type": trend_type,
                "time_range": time_range,
                "percent_change": round(percent_change, 2),
                "start_value": round(moving_avg[0], 2),
                "end_value": round(moving_avg[-1], 2)
            })
            
        return trends
    except Exception as e:
        logger.error(f"Error analyzing trends: {e}")
        raise

def analyze_metrics(metrics_data, time_range):
    """Analyze metrics data for trends and anomalies."""
    try:
        # Detect anomalies
        anomalies = detect_anomalies(metrics_data, time_range)
        
        # Analyze trends
        trends = analyze_trends(metrics_data, time_range)
        
        # Calculate summary statistics
        values = [float(point.get('value', 0)) for point in metrics_data]
        summary = {
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "avg": statistics.mean(values) if values else 0,
            "median": statistics.median(values) if values else 0,
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }
        
        return {
            "anomalies": anomalies,
            "trends": trends,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error analyzing metrics: {e}")
        raise

def lambda_handler(event, context):
    """Lambda function handler."""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract parameters from the event
        body = json.loads(event.get('body', '{}'))
        metrics_data = body.get('metrics_data')
        time_range = body.get('time_range')
        
        if not metrics_data or not time_range:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: metrics_data or time_range'
                })
            }
            
        # Analyze metrics
        results = analyze_metrics(metrics_data, time_range)
        
        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        } 