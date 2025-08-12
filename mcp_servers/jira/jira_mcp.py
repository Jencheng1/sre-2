"""
Jira MCP Server for defect management and issue tracking
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import threading

class JiraMCPServer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Mock data for test mode
        self.mock_issues = []
        self.mock_projects = []
        self.mock_sprints = []
        if test_mode:
            self._initialize_mock_data()
        
    def setup_routes(self):
        @self.app.route('/jira/issues', methods=['GET'])
        def get_issues():
            filters = {
                'project': request.args.get('project', 'all'),
                'status': request.args.get('status', 'all'),
                'priority': request.args.get('priority', 'all'),
                'assignee': request.args.get('assignee', 'all'),
                'issue_type': request.args.get('issue_type', 'all'),
                'limit': int(request.args.get('limit', 50)),
                'jql': request.args.get('jql', '')
            }
            
            issues = self.get_issues(filters)
            return jsonify(issues)
            
        @self.app.route('/jira/issues', methods=['POST'])
        def create_issue():
            issue_data = request.json
            result = self.create_issue(issue_data)
            return jsonify(result), 201
            
        @self.app.route('/jira/issues/<issue_key>', methods=['PUT'])
        def update_issue(issue_key):
            update_data = request.json
            result = self.update_issue(issue_key, update_data)
            return jsonify(result)
            
        @self.app.route('/jira/issues/<issue_key>/transitions', methods=['POST'])
        def transition_issue(issue_key):
            transition_data = request.json
            result = self.transition_issue(issue_key, transition_data)
            return jsonify(result)
            
        @self.app.route('/jira/issues/<issue_key>/comments', methods=['POST'])
        def add_comment(issue_key):
            comment_data = request.json
            result = self.add_comment(issue_key, comment_data)
            return jsonify(result)
            
        @self.app.route('/jira/issues/<issue_key>/comments', methods=['GET'])
        def get_comments(issue_key):
            comments = self.get_comments(issue_key)
            return jsonify(comments)
            
        @self.app.route('/jira/projects', methods=['GET'])
        def get_projects():
            projects = self.get_projects()
            return jsonify(projects)
            
        @self.app.route('/jira/projects/<project_key>/versions', methods=['GET'])
        def get_project_versions(project_key):
            versions = self.get_project_versions(project_key)
            return jsonify(versions)
            
        @self.app.route('/jira/sprints', methods=['GET'])
        def get_sprints():
            board_id = request.args.get('board_id', 'all')
            state = request.args.get('state', 'all')
            
            sprints = self.get_sprints(board_id, state)
            return jsonify(sprints)
            
        @self.app.route('/jira/search', methods=['POST'])
        def search_issues():
            search_data = request.json
            jql = search_data.get('jql', '')
            max_results = search_data.get('maxResults', 50)
            
            results = self.search_issues(jql, max_results)
            return jsonify(results)
            
        @self.app.route('/jira/analytics/burndown', methods=['GET'])
        def get_burndown():
            sprint_id = request.args.get('sprint_id')
            burndown = self.get_burndown_data(sprint_id)
            return jsonify(burndown)
            
        @self.app.route('/jira/analytics/velocity', methods=['GET'])
        def get_velocity():
            board_id = request.args.get('board_id')
            velocity = self.get_velocity_data(board_id)
            return jsonify(velocity)
            
        @self.app.route('/jira/analytics/defect-metrics', methods=['GET'])
        def get_defect_metrics():
            project = request.args.get('project', 'all')
            time_range = request.args.get('time_range', '-30d')
            
            metrics = self.get_defect_metrics(project, time_range)
            return jsonify(metrics)
    
    def get_issues(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get issues based on filters"""
        if self.test_mode:
            issues = self.mock_issues.copy()
            
            # Apply filters
            if filters['project'] != 'all':
                issues = [i for i in issues if i['project']['key'].lower() == filters['project'].lower()]
            if filters['status'] != 'all':
                issues = [i for i in issues if i['status']['name'].lower() == filters['status'].lower()]
            if filters['priority'] != 'all':
                issues = [i for i in issues if i['priority']['name'].lower() == filters['priority'].lower()]
            if filters['assignee'] != 'all':
                issues = [i for i in issues if i['assignee'] and i['assignee']['displayName'].lower() == filters['assignee'].lower()]
            if filters['issue_type'] != 'all':
                issues = [i for i in issues if i['issuetype']['name'].lower() == filters['issue_type'].lower()]
            
            return issues[:filters['limit']]
        else:
            # Real Jira API call would go here
            pass
    
    def create_issue(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue"""
        if self.test_mode:
            issue_key = f"{issue_data.get('project', 'PROJ')}-{len(self.mock_issues) + 1001}"
            
            issue = {
                'id': str(uuid.uuid4()),
                'key': issue_key,
                'self': f"https://company.atlassian.net/rest/api/2/issue/{issue_key}",
                'fields': {
                    'summary': issue_data.get('summary', 'New Issue'),
                    'description': issue_data.get('description', ''),
                    'issuetype': {
                        'id': str(random.randint(1, 10)),
                        'name': issue_data.get('issue_type', 'Bug'),
                        'iconUrl': 'https://company.atlassian.net/images/icons/bug.png'
                    },
                    'project': {
                        'id': str(random.randint(10000, 99999)),
                        'key': issue_data.get('project', 'PROJ'),
                        'name': f"Project {issue_data.get('project', 'PROJ')}"
                    },
                    'priority': {
                        'id': str(random.randint(1, 5)),
                        'name': issue_data.get('priority', 'Medium'),
                        'iconUrl': 'https://company.atlassian.net/images/icons/priority_medium.png'
                    },
                    'status': {
                        'id': '1',
                        'name': 'Open',
                        'iconUrl': 'https://company.atlassian.net/images/icons/status_open.png'
                    },
                    'assignee': {
                        'displayName': issue_data.get('assignee', 'Unassigned'),
                        'emailAddress': f"{issue_data.get('assignee', 'unassigned')}@company.com"
                    } if issue_data.get('assignee') != 'Unassigned' else None,
                    'reporter': {
                        'displayName': issue_data.get('reporter', 'System'),
                        'emailAddress': f"{issue_data.get('reporter', 'system')}@company.com"
                    },
                    'created': datetime.now().isoformat(),
                    'updated': datetime.now().isoformat(),
                    'resolution': None,
                    'environment': issue_data.get('environment', ''),
                    'components': issue_data.get('components', []),
                    'labels': issue_data.get('labels', []),
                    'fixVersions': issue_data.get('fix_versions', [])
                }
            }
            
            # Simplified structure for easier access
            simplified_issue = {
                'id': issue['id'],
                'key': issue['key'],
                'summary': issue['fields']['summary'],
                'description': issue['fields']['description'],
                'issuetype': issue['fields']['issuetype'],
                'project': issue['fields']['project'],
                'priority': issue['fields']['priority'],
                'status': issue['fields']['status'],
                'assignee': issue['fields']['assignee'],
                'reporter': issue['fields']['reporter'],
                'created': issue['fields']['created'],
                'updated': issue['fields']['updated'],
                'resolution': issue['fields']['resolution'],
                'comments': []
            }
            
            self.mock_issues.append(simplified_issue)
            return simplified_issue
        else:
            # Real Jira API call would go here
            pass
    
    def update_issue(self, issue_key: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing issue"""
        if self.test_mode:
            for issue in self.mock_issues:
                if issue['key'] == issue_key:
                    if 'summary' in update_data:
                        issue['summary'] = update_data['summary']
                    if 'description' in update_data:
                        issue['description'] = update_data['description']
                    if 'priority' in update_data:
                        issue['priority']['name'] = update_data['priority']
                    if 'assignee' in update_data:
                        issue['assignee'] = {
                            'displayName': update_data['assignee'],
                            'emailAddress': f"{update_data['assignee']}@company.com"
                        }
                    
                    issue['updated'] = datetime.now().isoformat()
                    return issue
            return {'error': 'Issue not found'}
        else:
            # Real Jira API call would go here
            pass
    
    def transition_issue(self, issue_key: str, transition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transition an issue to a new status"""
        if self.test_mode:
            for issue in self.mock_issues:
                if issue['key'] == issue_key:
                    new_status = transition_data.get('transition', {}).get('name', 'In Progress')
                    issue['status']['name'] = new_status
                    
                    if new_status in ['Done', 'Resolved', 'Closed']:
                        issue['resolution'] = {
                            'id': '1',
                            'name': transition_data.get('resolution', 'Fixed')
                        }
                    
                    issue['updated'] = datetime.now().isoformat()
                    return issue
            return {'error': 'Issue not found'}
        else:
            # Real Jira API call would go here
            pass
    
    def add_comment(self, issue_key: str, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a comment to an issue"""
        if self.test_mode:
            for issue in self.mock_issues:
                if issue['key'] == issue_key:
                    comment = {
                        'id': str(uuid.uuid4()),
                        'body': comment_data.get('body', ''),
                        'author': {
                            'displayName': comment_data.get('author', 'System'),
                            'emailAddress': f"{comment_data.get('author', 'system')}@company.com"
                        },
                        'created': datetime.now().isoformat(),
                        'updated': datetime.now().isoformat()
                    }
                    issue['comments'].append(comment)
                    issue['updated'] = datetime.now().isoformat()
                    return comment
            return {'error': 'Issue not found'}
        else:
            # Real Jira API call would go here
            pass
    
    def get_comments(self, issue_key: str) -> List[Dict[str, Any]]:
        """Get comments for an issue"""
        if self.test_mode:
            for issue in self.mock_issues:
                if issue['key'] == issue_key:
                    return issue['comments']
            return []
        else:
            # Real Jira API call would go here
            pass
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        if self.test_mode:
            return self.mock_projects
        else:
            # Real Jira API call would go here
            pass
    
    def get_project_versions(self, project_key: str) -> List[Dict[str, Any]]:
        """Get versions for a project"""
        if self.test_mode:
            return [
                {
                    'id': str(i),
                    'name': f'Version {i}.0',
                    'description': f'Release version {i}.0',
                    'released': i <= 2,
                    'releaseDate': (datetime.now() + timedelta(days=30*i)).strftime('%Y-%m-%d')
                }
                for i in range(1, 6)
            ]
        else:
            # Real Jira API call would go here
            pass
    
    def get_sprints(self, board_id: str, state: str) -> List[Dict[str, Any]]:
        """Get sprints"""
        if self.test_mode:
            sprints = self.mock_sprints.copy()
            if state != 'all':
                sprints = [s for s in sprints if s['state'].lower() == state.lower()]
            return sprints
        else:
            # Real Jira API call would go here
            pass
    
    def search_issues(self, jql: str, max_results: int) -> Dict[str, Any]:
        """Search issues using JQL"""
        if self.test_mode:
            # Simple JQL simulation
            issues = self.mock_issues[:max_results]
            return {
                'jql': jql,
                'maxResults': max_results,
                'total': len(self.mock_issues),
                'issues': issues
            }
        else:
            # Real Jira API call would go here
            pass
    
    def get_burndown_data(self, sprint_id: str) -> Dict[str, Any]:
        """Get burndown chart data"""
        if self.test_mode:
            days = 14  # 2-week sprint
            burndown_data = []
            remaining_points = 100
            
            for day in range(days + 1):
                date = datetime.now() - timedelta(days=days - day)
                if day == 0:
                    remaining_points = 100
                else:
                    # Simulate burndown with some variance
                    ideal_remaining = 100 - (100 * day / days)
                    actual_decrease = random.uniform(4, 10)
                    remaining_points = max(0, remaining_points - actual_decrease)
                
                burndown_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'ideal_remaining': round(100 - (100 * day / days), 1),
                    'actual_remaining': round(remaining_points, 1),
                    'completed': round(100 - remaining_points, 1)
                })
            
            return {
                'sprint_id': sprint_id,
                'burndown': burndown_data,
                'total_story_points': 100
            }
        else:
            # Real Jira API call would go here
            pass
    
    def get_velocity_data(self, board_id: str) -> Dict[str, Any]:
        """Get velocity chart data"""
        if self.test_mode:
            velocity_data = []
            
            for i in range(6):  # Last 6 sprints
                sprint_name = f'Sprint {20 + i}'
                committed = random.randint(40, 80)
                completed = random.randint(30, committed)
                
                velocity_data.append({
                    'sprint_name': sprint_name,
                    'committed_points': committed,
                    'completed_points': completed,
                    'velocity': completed
                })
            
            avg_velocity = sum(v['velocity'] for v in velocity_data) / len(velocity_data)
            
            return {
                'board_id': board_id,
                'velocity_data': velocity_data,
                'average_velocity': round(avg_velocity, 1)
            }
        else:
            # Real Jira API call would go here
            pass
    
    def get_defect_metrics(self, project: str, time_range: str) -> Dict[str, Any]:
        """Get defect-related metrics"""
        if self.test_mode:
            days = 30 if time_range == '-30d' else 7
            
            return {
                'project': project,
                'time_range': time_range,
                'metrics': {
                    'total_bugs': random.randint(50, 200),
                    'open_bugs': random.randint(10, 50),
                    'resolved_bugs': random.randint(40, 150),
                    'critical_bugs': random.randint(0, 5),
                    'high_priority_bugs': random.randint(5, 25),
                    'average_resolution_time': round(random.uniform(2, 15), 1),
                    'bug_creation_rate': round(random.uniform(1, 8), 1),
                    'bug_resolution_rate': round(random.uniform(2, 10), 1),
                    'reopened_bugs': random.randint(0, 10),
                    'escaped_bugs': random.randint(0, 5)
                },
                'last_updated': datetime.now().isoformat()
            }
        else:
            # Real Jira API call would go here
            pass
    
    def _initialize_mock_data(self):
        """Initialize mock data for test mode"""
        # Mock projects
        projects = ['WEBAPP', 'MOBILE', 'API', 'DB', 'ANALYTICS']
        for proj in projects:
            self.mock_projects.append({
                'id': str(random.randint(10000, 99999)),
                'key': proj,
                'name': f'{proj} Project',
                'projectTypeKey': 'software',
                'lead': {
                    'displayName': f'{proj} Lead',
                    'emailAddress': f'{proj.lower()}-lead@company.com'
                }
            })
        
        # Mock issues
        issue_types = ['Bug', 'Task', 'Story', 'Epic', 'Improvement']
        priorities = ['Blocker', 'Critical', 'High', 'Medium', 'Low']
        statuses = ['Open', 'In Progress', 'Code Review', 'Testing', 'Done', 'Closed']
        assignees = ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Wilson', 'Charlie Brown', None]
        
        for i in range(100):
            project = random.choice(projects)
            issue_type = random.choice(issue_types)
            
            # Bug-specific logic
            if issue_type == 'Bug':
                summary_templates = [
                    'Application crashes when user clicks submit button',
                    'Data validation error on user registration form',
                    'Memory leak in background service',
                    'API returns incorrect status code',
                    'UI elements not displaying correctly on mobile',
                    'Database connection timeout error',
                    'Authentication failure after password reset',
                    'Performance degradation during peak hours'
                ]
                summary = random.choice(summary_templates)
            else:
                summary = f'{issue_type}: Implement feature #{i:03d}'
            
            assignee_info = None
            if random.choice(assignees):
                assignee_name = random.choice([a for a in assignees if a])
                assignee_info = {
                    'displayName': assignee_name,
                    'emailAddress': f'{assignee_name.lower().replace(" ", ".")}@company.com'
                }
            
            issue = {
                'id': str(uuid.uuid4()),
                'key': f'{project}-{i + 1001}',
                'summary': summary,
                'description': f'Detailed description for {summary[:50]}...',
                'issuetype': {
                    'id': str(random.randint(1, 10)),
                    'name': issue_type,
                    'iconUrl': f'https://company.atlassian.net/images/icons/{issue_type.lower()}.png'
                },
                'project': {
                    'id': str(random.randint(10000, 99999)),
                    'key': project,
                    'name': f'{project} Project'
                },
                'priority': {
                    'id': str(random.randint(1, 5)),
                    'name': random.choice(priorities),
                    'iconUrl': f'https://company.atlassian.net/images/icons/priority_{random.choice(priorities).lower()}.png'
                },
                'status': {
                    'id': str(random.randint(1, 10)),
                    'name': random.choice(statuses),
                    'iconUrl': f'https://company.atlassian.net/images/icons/status_{random.choice(statuses).lower().replace(" ", "_")}.png'
                },
                'assignee': assignee_info,
                'reporter': {
                    'displayName': random.choice(['QA Team', 'Customer', 'Developer', 'Support']),
                    'emailAddress': 'reporter@company.com'
                },
                'created': (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
                'updated': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'resolution': None,
                'comments': []
            }
            
            # Add some comments
            for j in range(random.randint(0, 3)):
                comment = {
                    'id': str(uuid.uuid4()),
                    'body': f'Comment {j + 1} on issue {issue["key"]}',
                    'author': {
                        'displayName': random.choice(['Developer', 'QA', 'Manager']),
                        'emailAddress': 'commenter@company.com'
                    },
                    'created': (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat(),
                    'updated': (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat()
                }
                issue['comments'].append(comment)
            
            self.mock_issues.append(issue)
        
        # Mock sprints
        sprint_states = ['closed', 'active', 'future']
        for i in range(10):
            state = random.choice(sprint_states)
            start_date = datetime.now() - timedelta(days=14 * (10 - i))
            end_date = start_date + timedelta(days=14)
            
            sprint = {
                'id': i + 1,
                'name': f'Sprint {i + 1}',
                'state': state,
                'startDate': start_date.isoformat(),
                'endDate': end_date.isoformat(),
                'goal': f'Sprint {i + 1} goal: Deliver key features'
            }
            self.mock_sprints.append(sprint)
    
    def start_server(self, port=9086):
        """Start the MCP server"""
        self.app.run(host='0.0.0.0', port=port, debug=False)


def start_jira_mcp_server(port=9086, test_mode=True):
    """Start Jira MCP server in a separate thread"""
    server = JiraMCPServer(test_mode=test_mode)
    thread = threading.Thread(target=server.start_server, args=(port,))
    thread.daemon = True
    thread.start()
    return server