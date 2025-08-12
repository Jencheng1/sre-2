"""
Jira Strands Agent for defect management and issue tracking
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests

from strands_agents.base.base_agent import BaseStrandsAgent

class JiraStrandsAgent(BaseStrandsAgent):
    """Jira agent for issue tracking, defect management, and agile project management"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("jira", config)
        self.base_url = config.get("base_url", "http://localhost:9086")
        self.test_mode = config.get("test_mode", True)
        
        # Initialize tools
        self._register_tools()
        
        self.logger.info(f"Initialized {self.name} Strands Agent")
    
    def _register_tools(self):
        """Register Jira-specific tools"""
        self.tools = {
            "get_issues": self._create_tool(
                name="get_issues",
                description="Retrieve issues from Jira with filtering options",
                parameters={
                    "project": "Project key filter",
                    "status": "Status filter (e.g., 'Open', 'In Progress', 'Done')",
                    "priority": "Priority filter (e.g., 'Critical', 'High', 'Medium')",
                    "assignee": "Assignee filter",
                    "issue_type": "Issue type filter (e.g., 'Bug', 'Story', 'Task')",
                    "limit": "Maximum number of issues to retrieve (default: 50)"
                },
                handler=self._get_issues
            ),
            "create_issue": self._create_tool(
                name="create_issue",
                description="Create a new issue in Jira",
                parameters={
                    "project": "Project key where issue will be created",
                    "summary": "Issue summary/title",
                    "description": "Detailed issue description",
                    "issue_type": "Issue type (Bug, Story, Task, Epic, etc.)",
                    "priority": "Issue priority (Blocker, Critical, High, Medium, Low)",
                    "assignee": "Person assigned to the issue",
                    "reporter": "Person reporting the issue",
                    "environment": "Environment information",
                    "components": "Components affected (list)",
                    "labels": "Issue labels (list)"
                },
                handler=self._create_issue
            ),
            "update_issue": self._create_tool(
                name="update_issue",
                description="Update an existing issue",
                parameters={
                    "issue_key": "Jira issue key (e.g., PROJ-123)",
                    "summary": "Updated summary",
                    "description": "Updated description",
                    "priority": "Updated priority",
                    "assignee": "New assignee"
                },
                handler=self._update_issue
            ),
            "transition_issue": self._create_tool(
                name="transition_issue",
                description="Transition an issue to a new status",
                parameters={
                    "issue_key": "Jira issue key (e.g., PROJ-123)",
                    "transition": "Transition name or ID",
                    "resolution": "Resolution if closing issue",
                    "comment": "Optional comment for the transition"
                },
                handler=self._transition_issue
            ),
            "add_comment": self._create_tool(
                name="add_comment",
                description="Add a comment to an issue",
                parameters={
                    "issue_key": "Jira issue key (e.g., PROJ-123)",
                    "body": "Comment text",
                    "author": "Comment author"
                },
                handler=self._add_comment
            ),
            "search_issues": self._create_tool(
                name="search_issues",
                description="Search issues using JQL (Jira Query Language)",
                parameters={
                    "jql": "JQL query string",
                    "max_results": "Maximum number of results (default: 50)"
                },
                handler=self._search_issues
            ),
            "get_defect_metrics": self._create_tool(
                name="get_defect_metrics",
                description="Get defect-related metrics and analytics",
                parameters={
                    "project": "Project key filter",
                    "time_range": "Time range for metrics (e.g., '-30d', '-7d')"
                },
                handler=self._get_defect_metrics
            ),
            "get_sprint_burndown": self._create_tool(
                name="get_sprint_burndown",
                description="Get sprint burndown chart data",
                parameters={
                    "sprint_id": "Sprint ID"
                },
                handler=self._get_sprint_burndown
            ),
            "get_velocity_data": self._create_tool(
                name="get_velocity_data",
                description="Get team velocity data",
                parameters={
                    "board_id": "Board ID for velocity calculation"
                },
                handler=self._get_velocity_data
            ),
            "get_projects": self._create_tool(
                name="get_projects",
                description="Get all Jira projects",
                parameters={},
                handler=self._get_projects
            )
        }
    
    def _get_issues(self, **kwargs) -> Dict[str, Any]:
        """Get issues from Jira"""
        try:
            self.logger.info(f"Getting Jira issues with filters: {kwargs}")
            
            # Build query parameters
            params = {}
            for key in ['project', 'status', 'priority', 'assignee', 'issue_type', 'limit']:
                if kwargs.get(key, 'all') != 'all':
                    params[key] = kwargs[key]
            
            response = requests.get(f"{self.base_url}/jira/issues", params=params, timeout=30)
            response.raise_for_status()
            
            issues = response.json()
            
            # Process and enrich the data
            result = {
                "total_issues": len(issues),
                "issues": issues,
                "summary": self._summarize_issues(issues)
            }
            
            self.logger.info(f"Retrieved {len(issues)} issues from Jira")
            return result
            
        except Exception as e:
            error_msg = f"Failed to get Jira issues: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _create_issue(self, **kwargs) -> Dict[str, Any]:
        """Create a new issue in Jira"""
        try:
            self.logger.info(f"Creating new Jira issue: {kwargs.get('summary', 'Unnamed issue')}")
            
            issue_data = {
                "project": kwargs.get("project", "PROJ"),
                "summary": kwargs.get("summary", "New Issue"),
                "description": kwargs.get("description", ""),
                "issue_type": kwargs.get("issue_type", "Bug"),
                "priority": kwargs.get("priority", "Medium"),
                "assignee": kwargs.get("assignee", "Unassigned"),
                "reporter": kwargs.get("reporter", "SRE Copilot"),
                "environment": kwargs.get("environment", ""),
                "components": kwargs.get("components", []),
                "labels": kwargs.get("labels", [])
            }
            
            response = requests.post(
                f"{self.base_url}/jira/issues",
                json=issue_data,
                timeout=30
            )
            response.raise_for_status()
            
            created_issue = response.json()
            
            self.logger.info(f"Created issue {created_issue.get('key')} in Jira")
            return {
                "success": True,
                "issue": created_issue,
                "message": f"Successfully created issue {created_issue.get('key')}"
            }
            
        except Exception as e:
            error_msg = f"Failed to create Jira issue: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def _update_issue(self, **kwargs) -> Dict[str, Any]:
        """Update an existing issue"""
        try:
            issue_key = kwargs.get("issue_key")
            if not issue_key:
                return {"error": "issue_key is required", "success": False}
            
            self.logger.info(f"Updating issue {issue_key}")
            
            update_data = {}
            for field in ['summary', 'description', 'priority', 'assignee']:
                if kwargs.get(field):
                    update_data[field] = kwargs[field]
            
            response = requests.put(
                f"{self.base_url}/jira/issues/{issue_key}",
                json=update_data,
                timeout=30
            )
            response.raise_for_status()
            
            updated_issue = response.json()
            
            self.logger.info(f"Updated issue {issue_key}")
            return {
                "success": True,
                "issue": updated_issue,
                "message": f"Successfully updated issue {issue_key}"
            }
            
        except Exception as e:
            error_msg = f"Failed to update Jira issue: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def _transition_issue(self, **kwargs) -> Dict[str, Any]:
        """Transition an issue to a new status"""
        try:
            issue_key = kwargs.get("issue_key")
            if not issue_key:
                return {"error": "issue_key is required", "success": False}
            
            transition = kwargs.get("transition")
            if not transition:
                return {"error": "transition is required", "success": False}
            
            self.logger.info(f"Transitioning issue {issue_key} to {transition}")
            
            transition_data = {
                "transition": {"name": transition},
                "resolution": kwargs.get("resolution", "Fixed")
            }
            
            response = requests.post(
                f"{self.base_url}/jira/issues/{issue_key}/transitions",
                json=transition_data,
                timeout=30
            )
            response.raise_for_status()
            
            transitioned_issue = response.json()
            
            # Add comment if provided
            if kwargs.get("comment"):
                comment_data = {
                    "body": kwargs["comment"],
                    "author": "SRE Copilot"
                }
                requests.post(
                    f"{self.base_url}/jira/issues/{issue_key}/comments",
                    json=comment_data,
                    timeout=30
                )
            
            self.logger.info(f"Transitioned issue {issue_key} to {transition}")
            return {
                "success": True,
                "issue": transitioned_issue,
                "message": f"Successfully transitioned issue {issue_key} to {transition}"
            }
            
        except Exception as e:
            error_msg = f"Failed to transition Jira issue: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def _add_comment(self, **kwargs) -> Dict[str, Any]:
        """Add a comment to an issue"""
        try:
            issue_key = kwargs.get("issue_key")
            if not issue_key:
                return {"error": "issue_key is required", "success": False}
            
            body = kwargs.get("body", "")
            if not body:
                return {"error": "comment body is required", "success": False}
            
            self.logger.info(f"Adding comment to issue {issue_key}")
            
            comment_data = {
                "body": body,
                "author": kwargs.get("author", "SRE Copilot")
            }
            
            response = requests.post(
                f"{self.base_url}/jira/issues/{issue_key}/comments",
                json=comment_data,
                timeout=30
            )
            response.raise_for_status()
            
            comment = response.json()
            
            self.logger.info(f"Added comment to issue {issue_key}")
            return {
                "success": True,
                "comment": comment,
                "message": f"Successfully added comment to issue {issue_key}"
            }
            
        except Exception as e:
            error_msg = f"Failed to add comment to Jira issue: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg, "success": False}
    
    def _search_issues(self, **kwargs) -> Dict[str, Any]:
        """Search issues using JQL"""
        try:
            jql = kwargs.get("jql", "")
            max_results = kwargs.get("max_results", 50)
            
            self.logger.info(f"Searching Jira issues with JQL: {jql}")
            
            search_data = {
                "jql": jql,
                "maxResults": max_results
            }
            
            response = requests.post(
                f"{self.base_url}/jira/search",
                json=search_data,
                timeout=30
            )
            response.raise_for_status()
            
            search_results = response.json()
            
            # Enhance results with summary
            search_results["summary"] = self._summarize_issues(search_results.get("issues", []))
            
            self.logger.info(f"Found {search_results.get('total', 0)} issues matching JQL query")
            return search_results
            
        except Exception as e:
            error_msg = f"Failed to search Jira issues: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _get_defect_metrics(self, **kwargs) -> Dict[str, Any]:
        """Get defect-related metrics"""
        try:
            self.logger.info(f"Getting Jira defect metrics for: {kwargs}")
            
            params = {
                "project": kwargs.get("project", "all"),
                "time_range": kwargs.get("time_range", "-30d")
            }
            
            response = requests.get(f"{self.base_url}/jira/analytics/defect-metrics", params=params, timeout=30)
            response.raise_for_status()
            
            metrics = response.json()
            
            # Add analysis
            metrics["analysis"] = self._analyze_defect_metrics(metrics.get("metrics", {}))
            
            self.logger.info("Retrieved Jira defect metrics")
            return metrics
            
        except Exception as e:
            error_msg = f"Failed to get Jira defect metrics: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _get_sprint_burndown(self, **kwargs) -> Dict[str, Any]:
        """Get sprint burndown data"""
        try:
            sprint_id = kwargs.get("sprint_id")
            if not sprint_id:
                return {"error": "sprint_id is required"}
            
            self.logger.info(f"Getting burndown data for sprint {sprint_id}")
            
            response = requests.get(f"{self.base_url}/jira/analytics/burndown?sprint_id={sprint_id}", timeout=30)
            response.raise_for_status()
            
            burndown = response.json()
            
            # Add burndown analysis
            burndown["analysis"] = self._analyze_burndown(burndown.get("burndown", []))
            
            self.logger.info(f"Retrieved burndown data for sprint {sprint_id}")
            return burndown
            
        except Exception as e:
            error_msg = f"Failed to get sprint burndown: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _get_velocity_data(self, **kwargs) -> Dict[str, Any]:
        """Get velocity data"""
        try:
            board_id = kwargs.get("board_id")
            if not board_id:
                return {"error": "board_id is required"}
            
            self.logger.info(f"Getting velocity data for board {board_id}")
            
            response = requests.get(f"{self.base_url}/jira/analytics/velocity?board_id={board_id}", timeout=30)
            response.raise_for_status()
            
            velocity = response.json()
            
            # Add velocity analysis
            velocity["analysis"] = self._analyze_velocity(velocity.get("velocity_data", []))
            
            self.logger.info(f"Retrieved velocity data for board {board_id}")
            return velocity
            
        except Exception as e:
            error_msg = f"Failed to get velocity data: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _get_projects(self, **kwargs) -> Dict[str, Any]:
        """Get all Jira projects"""
        try:
            self.logger.info("Getting all Jira projects")
            
            response = requests.get(f"{self.base_url}/jira/projects", timeout=30)
            response.raise_for_status()
            
            projects = response.json()
            
            result = {
                "total_projects": len(projects),
                "projects": projects
            }
            
            self.logger.info(f"Retrieved {len(projects)} projects")
            return result
            
        except Exception as e:
            error_msg = f"Failed to get Jira projects: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def _summarize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize issue data"""
        if not issues:
            return {"message": "No issues found"}
        
        summary = {
            "total_count": len(issues),
            "by_status": {},
            "by_priority": {},
            "by_type": {},
            "by_project": {},
            "bugs_count": 0,
            "critical_issues": 0
        }
        
        for issue in issues:
            # Count by status
            status = issue.get("status", {}).get("name", "Unknown")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count by priority
            priority = issue.get("priority", {}).get("name", "Unknown")
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1
            
            # Count by type
            issue_type = issue.get("issuetype", {}).get("name", "Unknown")
            summary["by_type"][issue_type] = summary["by_type"].get(issue_type, 0) + 1
            
            # Count by project
            project = issue.get("project", {}).get("key", "Unknown")
            summary["by_project"][project] = summary["by_project"].get(project, 0) + 1
            
            # Count bugs
            if issue_type == "Bug":
                summary["bugs_count"] += 1
            
            # Count critical issues
            if priority in ["Blocker", "Critical", "High"]:
                summary["critical_issues"] += 1
        
        return summary
    
    def _analyze_defect_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze defect metrics"""
        analysis = {"status": "Unknown", "recommendations": []}
        
        if not metrics:
            return analysis
        
        total_bugs = metrics.get("total_bugs", 0)
        open_bugs = metrics.get("open_bugs", 0)
        critical_bugs = metrics.get("critical_bugs", 0)
        resolution_time = metrics.get("average_resolution_time", 0)
        
        # Determine overall status
        if critical_bugs == 0 and open_bugs < total_bugs * 0.1:
            analysis["status"] = "Excellent"
        elif critical_bugs <= 2 and open_bugs < total_bugs * 0.2:
            analysis["status"] = "Good"
        elif critical_bugs <= 5 and open_bugs < total_bugs * 0.3:
            analysis["status"] = "Fair"
        else:
            analysis["status"] = "Poor"
        
        # Generate recommendations
        if critical_bugs > 0:
            analysis["recommendations"].append(f"Address {critical_bugs} critical bug(s) immediately")
        
        if resolution_time > 10:
            analysis["recommendations"].append("High average resolution time - optimize defect handling process")
        
        if open_bugs > total_bugs * 0.3:
            analysis["recommendations"].append("High percentage of open bugs - increase resolution capacity")
        
        reopened_bugs = metrics.get("reopened_bugs", 0)
        if reopened_bugs > total_bugs * 0.1:
            analysis["recommendations"].append("High reopened bug rate - improve fix quality")
        
        return analysis
    
    def _analyze_burndown(self, burndown: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze burndown chart"""
        if not burndown:
            return {"message": "No burndown data available"}
        
        last_day = burndown[-1] if burndown else {}
        analysis = {
            "sprint_progress": "Unknown",
            "completion_likelihood": "Unknown",
            "recommendations": []
        }
        
        actual_remaining = last_day.get("actual_remaining", 0)
        ideal_remaining = last_day.get("ideal_remaining", 0)
        
        if actual_remaining <= ideal_remaining * 1.1:
            analysis["sprint_progress"] = "On Track"
            analysis["completion_likelihood"] = "High"
        elif actual_remaining <= ideal_remaining * 1.3:
            analysis["sprint_progress"] = "Slightly Behind"
            analysis["completion_likelihood"] = "Medium"
            analysis["recommendations"].append("Consider removing low-priority items")
        else:
            analysis["sprint_progress"] = "Behind Schedule"
            analysis["completion_likelihood"] = "Low"
            analysis["recommendations"].append("Scope reduction recommended")
            analysis["recommendations"].append("Review team capacity and impediments")
        
        return analysis
    
    def _analyze_velocity(self, velocity_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze velocity data"""
        if not velocity_data:
            return {"message": "No velocity data available"}
        
        recent_velocities = [v.get("velocity", 0) for v in velocity_data[-3:]]  # Last 3 sprints
        avg_velocity = sum(recent_velocities) / len(recent_velocities)
        
        analysis = {
            "trend": "Unknown",
            "consistency": "Unknown",
            "recommendations": []
        }
        
        # Analyze trend
        if len(recent_velocities) >= 2:
            if recent_velocities[-1] > recent_velocities[0]:
                analysis["trend"] = "Improving"
            elif recent_velocities[-1] < recent_velocities[0]:
                analysis["trend"] = "Declining"
                analysis["recommendations"].append("Investigate causes of declining velocity")
            else:
                analysis["trend"] = "Stable"
        
        # Analyze consistency
        if recent_velocities:
            velocity_variance = max(recent_velocities) - min(recent_velocities)
            if velocity_variance <= avg_velocity * 0.2:
                analysis["consistency"] = "High"
            elif velocity_variance <= avg_velocity * 0.4:
                analysis["consistency"] = "Medium"
            else:
                analysis["consistency"] = "Low"
                analysis["recommendations"].append("Work on improving sprint predictability")
        
        return analysis
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities"""
        return {
            "name": self.name,
            "description": "Jira agent for issue tracking and defect management",
            "tools": list(self.tools.keys()),
            "categories": [
                "issue_tracking",
                "defect_management",
                "agile_project_management",
                "analytics",
                "sprint_management"
            ],
            "integrations": ["jira", "agile_tools", "ci_cd"],
            "test_mode": self.test_mode
        }