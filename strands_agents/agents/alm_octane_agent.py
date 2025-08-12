"""
ALM Octane Strands Agent for defect management and quality assurance
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests

from strands_agents.base.base_agent import BaseStrandsAgent

class ALMOctaneStrandsAgent(BaseStrandsAgent):
    """ALM Octane agent for defect tracking, test management, and quality metrics"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("alm_octane", config)
        self.base_url = config.get("base_url", "http://localhost:9085")
        self.test_mode = config.get("test_mode", True)
        
        # Initialize tools
        self._register_tools()
        
        self.logger.info(f"Initialized {self.name} Strands Agent")
    
    def _register_tools(self):
        """Register ALM Octane-specific tools"""
        self.tools = {
            "get_defects": self._create_tool(
                name="get_defects",
                description="Retrieve defects from ALM Octane with filtering options",
                parameters={
                    "status": "Defect status filter (e.g., 'New', 'In Progress', 'Fixed')",
                    "severity": "Severity filter (e.g., 'Critical', 'High', 'Medium', 'Low')",
                    "assigned_to": "Assignee filter",
                    "project": "Project filter",
                    "limit": "Maximum number of defects to retrieve (default: 50)"
                },
                handler=self._get_defects
            ),
            "create_defect": self._create_tool(
                name="create_defect",
                description="Create a new defect in ALM Octane",
                parameters={
                    "name": "Defect title/name",
                    "description": "Detailed description of the defect",
                    "severity": "Defect severity (Critical, High, Medium, Low)",
                    "priority": "Defect priority (Critical, High, Medium, Low)",
                    "assigned_to": "Person assigned to fix the defect",
                    "project": "Project where defect belongs",
                    "component": "Component/module affected",
                    "environment": "Environment where defect was found",
                    "steps_to_reproduce": "Steps to reproduce the defect",
                    "expected_result": "Expected behavior",
                    "actual_result": "Actual behavior observed"
                },
                handler=self._create_defect
            ),
            "update_defect": self._create_tool(
                name="update_defect",
                description="Update an existing defect",
                parameters={
                    "defect_id": "ID of the defect to update",
                    "status": "New status for the defect",
                    "assigned_to": "New assignee",
                    "severity": "Updated severity",
                    "comments": "Additional comments"
                },
                handler=self._update_defect
            ),
            "get_test_runs": self._create_tool(
                name="get_test_runs",
                description="Retrieve test runs and execution results",
                parameters={
                    "release": "Release filter",
                    "status": "Test run status filter",
                    "suite": "Test suite filter",
                    "limit": "Maximum number of test runs (default: 50)"
                },
                handler=self._get_test_runs
            ),
            "get_defect_trends": self._create_tool(
                name="get_defect_trends",
                description="Get defect trend analytics over time",
                parameters={
                    "time_range": "Time range for trends (e.g., '-30d', '-7d')",
                    "project": "Project filter for trends"
                },
                handler=self._get_defect_trends
            ),
            "get_quality_metrics": self._create_tool(
                name="get_quality_metrics",
                description="Get comprehensive quality metrics",
                parameters={
                    "project": "Project filter",
                    "release": "Release filter"
                },
                handler=self._get_quality_metrics
            ),
            "get_requirement_coverage": self._create_tool(
                name="get_requirement_coverage",
                description="Get test coverage for requirements",
                parameters={
                    "requirement_id": "ID of the requirement"
                },
                handler=self._get_requirement_coverage
            )
        }
    
    def _get_defects(self, **kwargs) -> Dict[str, Any]:
        """Get defects from ALM Octane"""
        try:
            self.logger.info(f"Getting ALM Octane defects with filters: {kwargs}")
            
            # Build query parameters
            params = {}
            if kwargs.get('status', 'all') != 'all':
                params['status'] = kwargs['status']
            if kwargs.get('severity', 'all') != 'all':
                params['severity'] = kwargs['severity']
            if kwargs.get('assigned_to', 'all') != 'all':
                params['assigned_to'] = kwargs['assigned_to']
            if kwargs.get('project', 'all') != 'all':
                params['project'] = kwargs['project']
            if kwargs.get('limit'):
                params['limit'] = kwargs['limit']
            
            response = requests.get(f"{self.base_url}/octane/defects", params=params, timeout=30)
            response.raise_for_status()
            
            defects = response.json()
            
            # Process and enrich the data
            result = {
                "total_defects": len(defects),
                "defects": defects,
                "summary": self._summarize_defects(defects)
            }
            
            self.logger.info(f"Retrieved {len(defects)} defects from ALM Octane")
            return result
            
        except Exception as e:
            error_msg = f"Failed to get ALM Octane defects: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _create_defect(self, **kwargs) -> Dict[str, Any]:
        """Create a new defect in ALM Octane"""
        try:
            self.logger.info(f"Creating new defect: {kwargs.get('name', 'Unnamed defect')}")
            
            defect_data = {
                "name": kwargs.get("name", "New Defect"),
                "description": kwargs.get("description", ""),
                "severity": kwargs.get("severity", "Medium"),
                "priority": kwargs.get("priority", "Medium"),
                "assigned_to": kwargs.get("assigned_to", "Unassigned"),
                "project": kwargs.get("project", "Default Project"),
                "component": kwargs.get("component", "General"),
                "environment": kwargs.get("environment", "Production"),
                "steps_to_reproduce": kwargs.get("steps_to_reproduce", ""),
                "expected_result": kwargs.get("expected_result", ""),
                "actual_result": kwargs.get("actual_result", ""),
                "created_by": "SRE Copilot"
            }
            
            response = requests.post(
                f"{self.base_url}/octane/defects",
                json=defect_data,
                timeout=30
            )
            response.raise_for_status()
            
            created_defect = response.json()
            
            self.logger.info(f"Created defect {created_defect.get('id')} in ALM Octane")
            return {
                "success": True,
                "defect": created_defect,
                "message": f"Successfully created defect {created_defect.get('id')}"
            }
            
        except Exception as e:
            error_msg = f"Failed to create defect in ALM Octane: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def _update_defect(self, **kwargs) -> Dict[str, Any]:
        """Update an existing defect"""
        try:
            defect_id = kwargs.get("defect_id")
            if not defect_id:
                return {"error": "defect_id is required", "success": False}
            
            self.logger.info(f"Updating defect {defect_id}")
            
            update_data = {}
            if kwargs.get("status"):
                update_data["status"] = kwargs["status"]
            if kwargs.get("assigned_to"):
                update_data["assigned_to"] = kwargs["assigned_to"]
            if kwargs.get("severity"):
                update_data["severity"] = kwargs["severity"]
            
            response = requests.put(
                f"{self.base_url}/octane/defects/{defect_id}",
                json=update_data,
                timeout=30
            )
            response.raise_for_status()
            
            updated_defect = response.json()
            
            # Add comment if provided
            if kwargs.get("comments"):
                comment_data = {
                    "text": kwargs["comments"],
                    "author": "SRE Copilot"
                }
                requests.post(
                    f"{self.base_url}/octane/defects/{defect_id}/comments",
                    json=comment_data,
                    timeout=30
                )
            
            self.logger.info(f"Updated defect {defect_id}")
            return {
                "success": True,
                "defect": updated_defect,
                "message": f"Successfully updated defect {defect_id}"
            }
            
        except Exception as e:
            error_msg = f"Failed to update defect: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def _get_test_runs(self, **kwargs) -> Dict[str, Any]:
        """Get test runs from ALM Octane"""
        try:
            self.logger.info(f"Getting test runs with filters: {kwargs}")
            
            params = {}
            if kwargs.get('release', 'all') != 'all':
                params['release'] = kwargs['release']
            if kwargs.get('status', 'all') != 'all':
                params['status'] = kwargs['status']
            if kwargs.get('suite', 'all') != 'all':
                params['suite'] = kwargs['suite']
            if kwargs.get('limit'):
                params['limit'] = kwargs['limit']
            
            response = requests.get(f"{self.base_url}/octane/test-runs", params=params, timeout=30)
            response.raise_for_status()
            
            test_runs = response.json()
            
            result = {
                "total_test_runs": len(test_runs),
                "test_runs": test_runs,
                "summary": self._summarize_test_runs(test_runs)
            }
            
            self.logger.info(f"Retrieved {len(test_runs)} test runs")
            return result
            
        except Exception as e:
            error_msg = f"Failed to get test runs: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _get_defect_trends(self, **kwargs) -> Dict[str, Any]:
        """Get defect trend analytics"""
        try:
            self.logger.info(f"Getting defect trends for: {kwargs}")
            
            params = {
                "time_range": kwargs.get("time_range", "-30d"),
                "project": kwargs.get("project", "all")
            }
            
            response = requests.get(f"{self.base_url}/octane/analytics/defect-trends", params=params, timeout=30)
            response.raise_for_status()
            
            trends = response.json()
            
            # Add analysis
            trends["analysis"] = self._analyze_defect_trends(trends.get("trends", []))
            
            self.logger.info("Retrieved defect trends analytics")
            return trends
            
        except Exception as e:
            error_msg = f"Failed to get defect trends: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _get_quality_metrics(self, **kwargs) -> Dict[str, Any]:
        """Get quality metrics from ALM Octane"""
        try:
            self.logger.info(f"Getting quality metrics for: {kwargs}")
            
            params = {}
            if kwargs.get("project", "all") != "all":
                params["project"] = kwargs["project"]
            if kwargs.get("release", "all") != "all":
                params["release"] = kwargs["release"]
            
            response = requests.get(f"{self.base_url}/octane/analytics/quality-metrics", params=params, timeout=30)
            response.raise_for_status()
            
            metrics = response.json()
            
            # Add quality assessment
            metrics["quality_assessment"] = self._assess_quality(metrics.get("metrics", {}))
            
            self.logger.info("Retrieved quality metrics")
            return metrics
            
        except Exception as e:
            error_msg = f"Failed to get quality metrics: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _get_requirement_coverage(self, **kwargs) -> Dict[str, Any]:
        """Get test coverage for a requirement"""
        try:
            requirement_id = kwargs.get("requirement_id")
            if not requirement_id:
                return {"error": "requirement_id is required"}
            
            self.logger.info(f"Getting coverage for requirement {requirement_id}")
            
            response = requests.get(
                f"{self.base_url}/octane/requirements/{requirement_id}/coverage",
                timeout=30
            )
            response.raise_for_status()
            
            coverage = response.json()
            
            # Add coverage analysis
            coverage["coverage_analysis"] = self._analyze_coverage(coverage)
            
            self.logger.info(f"Retrieved coverage for requirement {requirement_id}")
            return coverage
            
        except Exception as e:
            error_msg = f"Failed to get requirement coverage: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _summarize_defects(self, defects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize defect data"""
        if not defects:
            return {"message": "No defects found"}
        
        summary = {
            "total_count": len(defects),
            "by_status": {},
            "by_severity": {},
            "by_project": {},
            "critical_issues": 0
        }
        
        for defect in defects:
            # Count by status
            status = defect.get("status", "Unknown")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count by severity
            severity = defect.get("severity", "Unknown")
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # Count by project
            project = defect.get("project", "Unknown")
            summary["by_project"][project] = summary["by_project"].get(project, 0) + 1
            
            # Count critical issues
            if severity in ["Critical", "High"]:
                summary["critical_issues"] += 1
        
        return summary
    
    def _summarize_test_runs(self, test_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize test run data"""
        if not test_runs:
            return {"message": "No test runs found"}
        
        summary = {
            "total_runs": len(test_runs),
            "by_status": {},
            "total_tests": 0,
            "total_passed": 0,
            "total_failed": 0,
            "pass_rate": 0
        }
        
        for run in test_runs:
            status = run.get("status", "Unknown")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            summary["total_tests"] += run.get("test_count", 0)
            summary["total_passed"] += run.get("passed_count", 0)
            summary["total_failed"] += run.get("failed_count", 0)
        
        if summary["total_tests"] > 0:
            summary["pass_rate"] = round((summary["total_passed"] / summary["total_tests"]) * 100, 1)
        
        return summary
    
    def _analyze_defect_trends(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze defect trends"""
        if not trends:
            return {"message": "No trend data available"}
        
        recent_trends = trends[-7:]  # Last 7 days
        avg_new = sum(t.get("new_defects", 0) for t in recent_trends) / len(recent_trends)
        avg_resolved = sum(t.get("resolved_defects", 0) for t in recent_trends) / len(recent_trends)
        
        analysis = {
            "trend_direction": "improving" if avg_resolved > avg_new else "concerning",
            "avg_new_per_day": round(avg_new, 1),
            "avg_resolved_per_day": round(avg_resolved, 1),
            "backlog_trend": "growing" if avg_new > avg_resolved else "shrinking"
        }
        
        return analysis
    
    def _assess_quality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall quality based on metrics"""
        assessment = {"score": 0, "level": "Unknown", "recommendations": []}
        
        # Quality scoring based on key metrics
        score = 0
        max_score = 0
        
        # Defect density (lower is better)
        if "defect_density" in metrics:
            density = metrics["defect_density"]
            max_score += 25
            if density < 0.5:
                score += 25
            elif density < 1.0:
                score += 20
            elif density < 1.5:
                score += 15
            elif density < 2.0:
                score += 10
            else:
                assessment["recommendations"].append("High defect density - focus on quality improvements")
        
        # Test coverage (higher is better)
        if "test_coverage" in metrics:
            coverage = metrics["test_coverage"]
            max_score += 25
            if coverage >= 90:
                score += 25
            elif coverage >= 80:
                score += 20
            elif coverage >= 70:
                score += 15
            else:
                assessment["recommendations"].append("Low test coverage - increase test automation")
        
        # Defect removal efficiency (higher is better)
        if "defect_removal_efficiency" in metrics:
            efficiency = metrics["defect_removal_efficiency"]
            max_score += 25
            if efficiency >= 95:
                score += 25
            elif efficiency >= 90:
                score += 20
            elif efficiency >= 85:
                score += 15
            else:
                assessment["recommendations"].append("Low defect removal efficiency - improve testing processes")
        
        # Test pass rate (higher is better)
        if "test_pass_rate" in metrics:
            pass_rate = metrics["test_pass_rate"]
            max_score += 25
            if pass_rate >= 95:
                score += 25
            elif pass_rate >= 90:
                score += 20
            elif pass_rate >= 85:
                score += 15
            else:
                assessment["recommendations"].append("Low test pass rate - investigate test failures")
        
        if max_score > 0:
            assessment["score"] = round((score / max_score) * 100)
            
            if assessment["score"] >= 80:
                assessment["level"] = "Excellent"
            elif assessment["score"] >= 70:
                assessment["level"] = "Good"
            elif assessment["score"] >= 60:
                assessment["level"] = "Fair"
            else:
                assessment["level"] = "Poor"
        
        return assessment
    
    def _analyze_coverage(self, coverage: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze requirement coverage"""
        analysis = {"status": "Unknown", "recommendations": []}
        
        coverage_pct = coverage.get("coverage_percentage", 0)
        failed_tests = coverage.get("failed_tests", 0)
        blocked_tests = coverage.get("blocked_tests", 0)
        
        if coverage_pct >= 90 and failed_tests == 0:
            analysis["status"] = "Excellent"
        elif coverage_pct >= 80 and failed_tests <= 1:
            analysis["status"] = "Good"
        elif coverage_pct >= 70:
            analysis["status"] = "Fair"
        else:
            analysis["status"] = "Poor"
        
        if coverage_pct < 80:
            analysis["recommendations"].append("Increase test coverage for this requirement")
        if failed_tests > 0:
            analysis["recommendations"].append(f"Address {failed_tests} failing test(s)")
        if blocked_tests > 0:
            analysis["recommendations"].append(f"Resolve {blocked_tests} blocked test(s)")
        
        return analysis
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": "ALM Octane agent for defect management and quality assurance",
            "tools": list(self.tools.keys()),
            "categories": [
                "defect_management",
                "quality_assurance", 
                "test_management",
                "analytics",
                "requirements_traceability"
            ],
            "integrations": ["alm_octane", "test_automation", "quality_gates"],
            "test_mode": self.test_mode
        }