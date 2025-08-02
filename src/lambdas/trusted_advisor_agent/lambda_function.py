import json
import os
import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
support = boto3.client('support')
organizations = boto3.client('organizations')
bedrock = boto3.client('bedrock-runtime')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for AWS Trusted Advisor agent.
    Processes Trusted Advisor checks and returns analysis results.
    """
    try:
        # Extract parameters from the event
        action = event.get('action', 'get_service_quotas')
        check_id = event.get('check_id')
        max_results = event.get('max_results', 100)
        
        if action == 'get_service_quotas':
            return get_service_quotas(max_results)
        elif action == 'get_security_checks':
            return get_security_checks(max_results)
        elif action == 'get_cost_optimization':
            return get_cost_optimization(max_results)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unsupported action: {action}'})
            }
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_service_quotas(max_results: int) -> Dict[str, Any]:
    """Get service quota checks from Trusted Advisor."""
    try:
        # Get service quota checks
        response = support.describe_trusted_advisor_checks(
            language='en'
        )
        
        quota_checks = [
            check for check in response['checks']
            if check['category'] == 'service_limits'
        ]
        
        results = []
        for check in quota_checks[:max_results]:
            check_result = support.describe_trusted_advisor_check_result(
                checkId=check['id']
            )
            
            if check_result['result']['status'] == 'warning':
                results.append({
                    'check_id': check['id'],
                    'name': check['name'],
                    'description': check['description'],
                    'flagged_resources': check_result['result'].get('flaggedResources', []),
                    'severity': determine_quota_severity(check_result['result'])
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'service_quotas': results,
                'analysis': analyze_with_bedrock(results)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_service_quotas: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_security_checks(max_results: int) -> Dict[str, Any]:
    """Get security checks from Trusted Advisor."""
    try:
        # Get security checks
        response = support.describe_trusted_advisor_checks(
            language='en'
        )
        
        security_checks = [
            check for check in response['checks']
            if check['category'] == 'security'
        ]
        
        results = []
        for check in security_checks[:max_results]:
            check_result = support.describe_trusted_advisor_check_result(
                checkId=check['id']
            )
            
            if check_result['result']['status'] == 'warning':
                results.append({
                    'check_id': check['id'],
                    'name': check['name'],
                    'description': check['description'],
                    'flagged_resources': check_result['result'].get('flaggedResources', []),
                    'severity': determine_security_severity(check_result['result'])
                })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'security_checks': results,
                'analysis': analyze_with_bedrock(results)
            })
        }

    except Exception as e:
        logger.error(f"Error in get_security_checks: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_cost_optimization(max_results: int) -> Dict[str, Any]:
    """Get cost optimization checks from Trusted Advisor."""
    try:
        # Get cost optimization checks
        response = support.describe_trusted_advisor_checks(
            language='en'
        )
        checks = response.get('checks', [])
        if not checks:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No Trusted Advisor checks found',
                    'checks': []
                })
            }
        
        # Filter checks by type if specified
        if check_type != 'all':
            checks = [c for c in checks if c.get('category') == check_type]
        
        # Get check results
        check_results = []
        for check in checks[:max_results]:
            try:
                result = trusted_advisor.describe_trusted_advisor_check_result(
                    checkId=check['id']
                )
                check_results.append(result)
            except Exception as e:
                logger.error(f"Error getting check result for {check['id']}: {str(e)}")
                continue
        
        # Analyze results using Bedrock
        analysis = analyze_with_bedrock(bedrock_runtime, check_results)
        
        # Process results for specific issues
        issues = process_check_results(check_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'checks': check_results,
                'analysis': analysis,
                'issues': issues
            })
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_trusted_advisor_checks: {str(e)}")
        raise

def analyze_with_bedrock(bedrock_runtime, check_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use Bedrock to analyze patterns in Trusted Advisor check results."""
    try:
        # Prepare results for analysis
        results_text = "\n".join([
            f"Check: {r.get('checkId')} | Category: {r.get('category')} | "
            f"Status: {r.get('status')} | Resources: {len(r.get('flaggedResources', []))} | "
            f"Description: {r.get('metadata', [])}"
            for r in check_results[:20]  # Limit to 20 results for prompt size
        ])
        
        # Prepare prompt for Claude
        prompt = f"""
        Analyze the following AWS Trusted Advisor check results for potential issues, optimization opportunities, or security concerns:
        
        {results_text}
        
        Please identify:
        1. Any critical issues that need immediate attention
        2. Cost optimization opportunities
        3. Security and compliance concerns
        4. Performance improvement recommendations
        
        Format your response as JSON with the following structure:
        {{
            "critical_issues": [list of critical issues],
            "cost_optimizations": [list of cost optimizations],
            "security_concerns": [list of security concerns],
            "recommendations": [list of recommendations]
        }}
        """
        
        # Call Claude via Bedrock
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'prompt': prompt,
                'max_tokens': 1000,
                'temperature': 0.7
            })
        )
        
        # Parse and return the analysis
        response_body = json.loads(response['body'].read())
        return json.loads(response_body['completion'])
        
    except Exception as e:
        logger.error(f"Error in analyze_with_bedrock: {str(e)}")
        return {
            'error': str(e),
            'critical_issues': [],
            'cost_optimizations': [],
            'security_concerns': [],
            'recommendations': ['Error analyzing Trusted Advisor checks with Bedrock']
        }

def process_check_results(check_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process AWS Trusted Advisor check results for specific issues."""
    issues = []
    
    for result in check_results:
        try:
            check_id = result.get('checkId', '')
            category = result.get('category', '')
            status = result.get('status', '')
            flagged_resources = result.get('flaggedResources', [])
            
            # Process service quota checks
            if category == 'service_limits':
                for resource in flagged_resources:
                    issue = {
                        'id': f"{check_id}-{resource.get('resourceId', '')}",
                        'check_id': check_id,
                        'category': category,
                        'status': status,
                        'severity': determine_severity(status),
                        'issue_type': 'service_quota',
                        'resource_id': resource.get('resourceId', ''),
                        'metadata': resource.get('metadata', {})
                    }
                    issues.append(issue)
            
            # Process security checks
            elif category == 'security':
                for resource in flagged_resources:
                    issue = {
                        'id': f"{check_id}-{resource.get('resourceId', '')}",
                        'check_id': check_id,
                        'category': category,
                        'status': status,
                        'severity': 'high',
                        'issue_type': 'security_issue',
                        'resource_id': resource.get('resourceId', ''),
                        'metadata': resource.get('metadata', {})
                    }
                    issues.append(issue)
            
            # Process cost optimization checks
            elif category == 'cost_optimizing':
                for resource in flagged_resources:
                    issue = {
                        'id': f"{check_id}-{resource.get('resourceId', '')}",
                        'check_id': check_id,
                        'category': category,
                        'status': status,
                        'severity': 'medium',
                        'issue_type': 'cost_optimization',
                        'resource_id': resource.get('resourceId', ''),
                        'metadata': resource.get('metadata', {})
                    }
                    issues.append(issue)
                
        except Exception as e:
            logger.error(f"Error processing check result: {str(e)}")
            continue
    
    return issues

def determine_severity(status: str) -> str:
    """Determine the severity of a Trusted Advisor check result."""
    if status == 'error':
        return 'high'
    elif status == 'warning':
        return 'medium'
    else:
        return 'low'

def get_service_quotas() -> Dict[str, Any]:
    """Get service quota checks from Trusted Advisor."""
    try:
        # Get all checks
        checks = support.describe_trusted_advisor_checks(
            language='en'
        )
        
        service_quota_checks = []
        for check in checks.get('checks', []):
            if check.get('category') == 'service_limits':
                # Get check results
                result = support.describe_trusted_advisor_check_result(
                    checkId=check.get('id', '')
                )
                
                # Process check results
                for resource in result.get('result', {}).get('flaggedResources', []):
                    quota = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'check_id': check.get('id', ''),
                        'check_name': check.get('name', ''),
                        'service': check.get('metadata', [])[1] if len(check.get('metadata', [])) > 1 else '',
                        'region': check.get('metadata', [])[2] if len(check.get('metadata', [])) > 2 else '',
                        'current_usage': resource.get('metadata', [])[1] if len(resource.get('metadata', [])) > 1 else '',
                        'limit': resource.get('metadata', [])[2] if len(resource.get('metadata', [])) > 2 else '',
                        'severity': determine_quota_severity(resource)
                    }
                    service_quota_checks.append(quota)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'service_quotas': service_quota_checks,
                'count': len(service_quota_checks)
            })
        }
    except Exception as e:
        print(f"Error retrieving service quotas: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error retrieving service quotas: {str(e)}'})
        }

def get_security_checks() -> Dict[str, Any]:
    """Get security checks from Trusted Advisor."""
    try:
        # Get all checks
        checks = support.describe_trusted_advisor_checks(
            language='en'
        )
        
        security_checks = []
        for check in checks.get('checks', []):
            if check.get('category') == 'security':
                # Get check results
                result = support.describe_trusted_advisor_check_result(
                    checkId=check.get('id', '')
                )
                
                # Process check results
                for resource in result.get('result', {}).get('flaggedResources', []):
                    security = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'check_id': check.get('id', ''),
                        'check_name': check.get('name', ''),
                        'resource_id': resource.get('metadata', [])[0] if resource.get('metadata') else '',
                        'resource_type': resource.get('metadata', [])[1] if len(resource.get('metadata', [])) > 1 else '',
                        'issue': resource.get('metadata', [])[2] if len(resource.get('metadata', [])) > 2 else '',
                        'severity': determine_security_severity(check, resource)
                    }
                    security_checks.append(security)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'security_checks': security_checks,
                'count': len(security_checks)
            })
        }
    except Exception as e:
        print(f"Error retrieving security checks: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error retrieving security checks: {str(e)}'})
        }

def get_cost_optimization() -> Dict[str, Any]:
    """Get cost optimization checks from Trusted Advisor."""
    try:
        # Get all checks
        checks = support.describe_trusted_advisor_checks(
            language='en'
        )
        
        cost_checks = []
        for check in checks.get('checks', []):
            if check.get('category') == 'cost_optimizing':
                # Get check results
                result = support.describe_trusted_advisor_check_result(
                    checkId=check.get('id', '')
                )
                
                # Process check results
                for resource in result.get('result', {}).get('flaggedResources', []):
                    cost = {
                        'id': str(uuid.uuid4()),
                        'timestamp': datetime.utcnow().isoformat(),
                        'check_id': check.get('id', ''),
                        'check_name': check.get('name', ''),
                        'resource_id': resource.get('metadata', [])[0] if resource.get('metadata') else '',
                        'resource_type': resource.get('metadata', [])[1] if len(resource.get('metadata', [])) > 1 else '',
                        'potential_savings': resource.get('metadata', [])[2] if len(resource.get('metadata', [])) > 2 else '',
                        'severity': determine_cost_severity(resource)
                    }
                    cost_checks.append(cost)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'cost_checks': cost_checks,
                'count': len(cost_checks)
            })
        }
    except Exception as e:
        print(f"Error retrieving cost optimization checks: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Error retrieving cost optimization checks: {str(e)}'})
        }

def determine_quota_severity(resource: Dict[str, Any]) -> str:
    """Determine the severity of service quota issues."""
    try:
        current_usage = float(resource.get('metadata', [])[1] if len(resource.get('metadata', [])) > 1 else 0)
        limit = float(resource.get('metadata', [])[2] if len(resource.get('metadata', [])) > 2 else 0)
        
        if limit > 0:
            usage_percentage = (current_usage / limit) * 100
            
            if usage_percentage >= 90:
                return 'high'
            elif usage_percentage >= 75:
                return 'medium'
    except (ValueError, ZeroDivisionError):
        pass
    
    return 'low'

def determine_security_severity(check: Dict[str, Any], resource: Dict[str, Any]) -> str:
    """Determine the severity of security issues."""
    # High severity security checks
    high_severity_checks = [
        'Security Groups - Specific Ports Unrestricted',
        'IAM Users',
        'Root Account Usage',
        'MFA on Root Account'
    ]
    
    # Medium severity security checks
    medium_severity_checks = [
        'Security Groups - Unrestricted Access',
        'IAM Password Policy',
        'IAM Access Keys',
        'S3 Bucket Permissions'
    ]
    
    check_name = check.get('name', '')
    if check_name in high_severity_checks:
        return 'high'
    elif check_name in medium_severity_checks:
        return 'medium'
    
    return 'low'

def determine_cost_severity(resource: Dict[str, Any]) -> str:
    """Determine the severity of cost optimization issues."""
    try:
        potential_savings = float(resource.get('metadata', [])[2].replace('$', '').replace(',', '') 
                                if len(resource.get('metadata', [])) > 2 else 0)
        
        if potential_savings >= 1000:
            return 'high'
        elif potential_savings >= 100:
            return 'medium'
    except (ValueError, AttributeError):
        pass
    
    return 'low' 