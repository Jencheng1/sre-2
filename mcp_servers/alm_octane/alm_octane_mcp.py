"""
ALM Octane MCP Server for defect management and quality assurance
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import threading

class ALMOctaneMCPServer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Mock data for test mode
        self.mock_defects = []
        self.mock_test_runs = []
        self.mock_requirements = []
        if test_mode:
            self._initialize_mock_data()
        
    def setup_routes(self):
        @self.app.route('/octane/defects', methods=['GET'])
        def get_defects():
            filters = {
                'status': request.args.get('status', 'all'),
                'severity': request.args.get('severity', 'all'),
                'assigned_to': request.args.get('assigned_to', 'all'),
                'project': request.args.get('project', 'all'),
                'limit': int(request.args.get('limit', 50))
            }
            
            defects = self.get_defects(filters)
            return jsonify(defects)
            
        @self.app.route('/octane/defects', methods=['POST'])
        def create_defect():
            defect_data = request.json
            result = self.create_defect(defect_data)
            return jsonify(result), 201
            
        @self.app.route('/octane/defects/<defect_id>', methods=['PUT'])
        def update_defect(defect_id):
            update_data = request.json
            result = self.update_defect(defect_id, update_data)
            return jsonify(result)
            
        @self.app.route('/octane/defects/<defect_id>/comments', methods=['POST'])
        def add_defect_comment(defect_id):
            comment_data = request.json
            result = self.add_comment(defect_id, comment_data)
            return jsonify(result)
            
        @self.app.route('/octane/test-runs', methods=['GET'])
        def get_test_runs():
            filters = {
                'release': request.args.get('release', 'all'),
                'status': request.args.get('status', 'all'),
                'suite': request.args.get('suite', 'all'),
                'limit': int(request.args.get('limit', 50))
            }
            
            test_runs = self.get_test_runs(filters)
            return jsonify(test_runs)
            
        @self.app.route('/octane/test-runs', methods=['POST'])
        def create_test_run():
            test_run_data = request.json
            result = self.create_test_run(test_run_data)
            return jsonify(result), 201
            
        @self.app.route('/octane/requirements/<requirement_id>/coverage', methods=['GET'])
        def get_requirement_coverage(requirement_id):
            coverage = self.get_requirement_coverage(requirement_id)
            return jsonify(coverage)
            
        @self.app.route('/octane/analytics/defect-trends', methods=['GET'])
        def get_defect_trends():
            time_range = request.args.get('time_range', '-30d')
            project = request.args.get('project', 'all')
            
            trends = self.get_defect_trends(time_range, project)
            return jsonify(trends)
            
        @self.app.route('/octane/analytics/quality-metrics', methods=['GET'])
        def get_quality_metrics():
            project = request.args.get('project', 'all')
            release = request.args.get('release', 'all')
            
            metrics = self.get_quality_metrics(project, release)
            return jsonify(metrics)
    
    def get_defects(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get defects based on filters"""
        if self.test_mode:
            defects = self.mock_defects.copy()
            
            # Apply filters
            if filters['status'] != 'all':
                defects = [d for d in defects if d['status'].lower() == filters['status'].lower()]
            if filters['severity'] != 'all':
                defects = [d for d in defects if d['severity'].lower() == filters['severity'].lower()]
            if filters['assigned_to'] != 'all':
                defects = [d for d in defects if d['assigned_to'].lower() == filters['assigned_to'].lower()]
            if filters['project'] != 'all':
                defects = [d for d in defects if d['project'].lower() == filters['project'].lower()]
            
            return defects[:filters['limit']]
        else:
            # Real ALM Octane API call would go here
            pass
    
    def create_defect(self, defect_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new defect"""
        if self.test_mode:
            defect = {
                'id': str(uuid.uuid4()),
                'name': defect_data.get('name', 'New Defect'),
                'description': defect_data.get('description', ''),
                'severity': defect_data.get('severity', 'Medium'),
                'priority': defect_data.get('priority', 'Medium'),
                'status': 'New',
                'assigned_to': defect_data.get('assigned_to', 'Unassigned'),
                'project': defect_data.get('project', 'Default Project'),
                'component': defect_data.get('component', 'General'),
                'created_date': datetime.now().isoformat(),
                'updated_date': datetime.now().isoformat(),
                'created_by': defect_data.get('created_by', 'System'),
                'environment': defect_data.get('environment', 'Production'),
                'build_version': defect_data.get('build_version', '1.0.0'),
                'steps_to_reproduce': defect_data.get('steps_to_reproduce', ''),
                'expected_result': defect_data.get('expected_result', ''),
                'actual_result': defect_data.get('actual_result', ''),
                'comments': []
            }
            
            self.mock_defects.append(defect)
            return defect
        else:
            # Real ALM Octane API call would go here
            pass
    
    def update_defect(self, defect_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing defect"""
        if self.test_mode:
            for defect in self.mock_defects:
                if defect['id'] == defect_id:
                    defect.update(update_data)
                    defect['updated_date'] = datetime.now().isoformat()
                    return defect
            return {'error': 'Defect not found'}
        else:
            # Real ALM Octane API call would go here
            pass
    
    def add_comment(self, defect_id: str, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a comment to a defect"""
        if self.test_mode:
            for defect in self.mock_defects:
                if defect['id'] == defect_id:
                    comment = {
                        'id': str(uuid.uuid4()),
                        'text': comment_data.get('text', ''),
                        'author': comment_data.get('author', 'System'),
                        'created_date': datetime.now().isoformat()
                    }
                    defect['comments'].append(comment)
                    defect['updated_date'] = datetime.now().isoformat()
                    return comment
            return {'error': 'Defect not found'}
        else:
            # Real ALM Octane API call would go here
            pass
    
    def get_test_runs(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get test runs based on filters"""
        if self.test_mode:
            test_runs = self.mock_test_runs.copy()
            
            # Apply filters
            if filters['status'] != 'all':
                test_runs = [tr for tr in test_runs if tr['status'].lower() == filters['status'].lower()]
            if filters['release'] != 'all':
                test_runs = [tr for tr in test_runs if tr['release'].lower() == filters['release'].lower()]
            if filters['suite'] != 'all':
                test_runs = [tr for tr in test_runs if tr['suite'].lower() == filters['suite'].lower()]
            
            return test_runs[:filters['limit']]
        else:
            # Real ALM Octane API call would go here
            pass
    
    def create_test_run(self, test_run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test run"""
        if self.test_mode:
            test_run = {
                'id': str(uuid.uuid4()),
                'name': test_run_data.get('name', 'New Test Run'),
                'suite': test_run_data.get('suite', 'Regression Suite'),
                'release': test_run_data.get('release', 'Release 1.0'),
                'status': 'Planned',
                'environment': test_run_data.get('environment', 'QA'),
                'assigned_to': test_run_data.get('assigned_to', 'QA Team'),
                'planned_start': test_run_data.get('planned_start', datetime.now().isoformat()),
                'planned_end': test_run_data.get('planned_end', (datetime.now() + timedelta(days=1)).isoformat()),
                'created_date': datetime.now().isoformat(),
                'test_count': test_run_data.get('test_count', 0),
                'passed_count': 0,
                'failed_count': 0,
                'blocked_count': 0
            }
            
            self.mock_test_runs.append(test_run)
            return test_run
        else:
            # Real ALM Octane API call would go here
            pass
    
    def get_requirement_coverage(self, requirement_id: str) -> Dict[str, Any]:
        """Get test coverage for a requirement"""
        if self.test_mode:
            return {
                'requirement_id': requirement_id,
                'requirement_name': f'Requirement {requirement_id}',
                'total_tests': random.randint(5, 25),
                'passed_tests': random.randint(3, 20),
                'failed_tests': random.randint(0, 5),
                'blocked_tests': random.randint(0, 2),
                'coverage_percentage': random.randint(60, 100),
                'last_executed': (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat()
            }
        else:
            # Real ALM Octane API call would go here
            pass
    
    def get_defect_trends(self, time_range: str, project: str) -> Dict[str, Any]:
        """Get defect trends analytics"""
        if self.test_mode:
            days = 30 if time_range == '-30d' else 7
            trends = []
            
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                trends.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'new_defects': random.randint(0, 10),
                    'resolved_defects': random.randint(0, 8),
                    'open_defects': random.randint(5, 50),
                    'critical_defects': random.randint(0, 3),
                    'high_defects': random.randint(1, 10),
                    'medium_defects': random.randint(2, 15),
                    'low_defects': random.randint(0, 8)
                })
            
            return {
                'time_range': time_range,
                'project': project,
                'trends': sorted(trends, key=lambda x: x['date'])
            }
        else:
            # Real ALM Octane API call would go here
            pass
    
    def get_quality_metrics(self, project: str, release: str) -> Dict[str, Any]:
        """Get quality metrics"""
        if self.test_mode:
            return {
                'project': project,
                'release': release,
                'metrics': {
                    'defect_density': round(random.uniform(0.1, 2.5), 2),
                    'defect_removal_efficiency': round(random.uniform(85, 98), 1),
                    'test_coverage': round(random.uniform(75, 95), 1),
                    'defect_escape_rate': round(random.uniform(1, 8), 1),
                    'mean_time_to_resolution': round(random.uniform(2, 15), 1),
                    'critical_defects_open': random.randint(0, 5),
                    'high_defects_open': random.randint(2, 15),
                    'total_defects_open': random.randint(10, 50),
                    'defects_fixed_this_week': random.randint(5, 25),
                    'test_pass_rate': round(random.uniform(88, 97), 1)
                },
                'last_updated': datetime.now().isoformat()
            }
        else:
            # Real ALM Octane API call would go here
            pass
    
    def _initialize_mock_data(self):
        """Initialize mock data for test mode"""
        # Mock defects
        severities = ['Critical', 'High', 'Medium', 'Low']
        statuses = ['New', 'In Progress', 'Fixed', 'Closed', 'Rejected', 'Deferred']
        projects = ['Web Portal', 'Mobile App', 'API Gateway', 'Database Engine', 'Analytics Platform']
        components = ['Frontend', 'Backend', 'Database', 'API', 'UI/UX', 'Security', 'Performance']
        environments = ['Production', 'Staging', 'QA', 'Development']
        
        for i in range(50):
            defect = {
                'id': str(uuid.uuid4()),
                'name': f'Defect-{i:04d}: {random.choice(["Login failure", "Data inconsistency", "Performance issue", "UI rendering error", "API timeout", "Memory leak", "Security vulnerability", "Integration failure"])}',
                'description': f'Detailed description for defect {i:04d}',
                'severity': random.choice(severities),
                'priority': random.choice(severities),
                'status': random.choice(statuses),
                'assigned_to': random.choice(['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Wilson', 'Unassigned']),
                'project': random.choice(projects),
                'component': random.choice(components),
                'created_date': (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
                'updated_date': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'created_by': random.choice(['QA Team', 'Developer', 'Customer', 'Support Team']),
                'environment': random.choice(environments),
                'build_version': f'{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 99)}',
                'steps_to_reproduce': f'Step 1: Navigate to module\nStep 2: Perform action\nStep 3: Observe error',
                'expected_result': 'System should work correctly',
                'actual_result': 'System shows error or unexpected behavior',
                'comments': [
                    {
                        'id': str(uuid.uuid4()),
                        'text': 'Initial analysis completed',
                        'author': 'QA Team',
                        'created_date': (datetime.now() - timedelta(days=random.randint(0, 10))).isoformat()
                    }
                ]
            }
            self.mock_defects.append(defect)
        
        # Mock test runs
        suites = ['Smoke Tests', 'Regression Suite', 'Integration Tests', 'Performance Tests', 'Security Tests']
        releases = ['Release 1.0', 'Release 1.1', 'Release 2.0', 'Hotfix 1.0.1']
        test_statuses = ['Planned', 'In Progress', 'Completed', 'Failed', 'Blocked']
        
        for i in range(20):
            test_run = {
                'id': str(uuid.uuid4()),
                'name': f'Test Run {i:03d}',
                'suite': random.choice(suites),
                'release': random.choice(releases),
                'status': random.choice(test_statuses),
                'environment': random.choice(environments),
                'assigned_to': random.choice(['QA Team', 'Automation Team', 'Manual Testers']),
                'planned_start': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'planned_end': (datetime.now() + timedelta(days=random.randint(1, 7))).isoformat(),
                'created_date': (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat(),
                'test_count': random.randint(10, 100),
                'passed_count': random.randint(5, 80),
                'failed_count': random.randint(0, 15),
                'blocked_count': random.randint(0, 5)
            }
            self.mock_test_runs.append(test_run)
    
    def start_server(self, port=9085):
        """Start the MCP server"""
        self.app.run(host='0.0.0.0', port=port, debug=False)


def start_alm_octane_mcp_server(port=9085, test_mode=True):
    """Start ALM Octane MCP server in a separate thread"""
    server = ALMOctaneMCPServer(test_mode=test_mode)
    thread = threading.Thread(target=server.start_server, args=(port,))
    thread.daemon = True
    thread.start()
    return server