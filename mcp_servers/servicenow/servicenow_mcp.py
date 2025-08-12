"""
ServiceNow MCP Server for incident and change management
"""

import json
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask, request, jsonify
import threading

class ServiceNowMCPServer:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.app = Flask(__name__)
        self.incidents = []  # In-memory storage for test mode
        self.changes = []
        self.problems = []  # Add problems storage
        self.cmdb_items = []
        self.setup_routes()
        self.init_test_data()
        
    def init_test_data(self):
        """Initialize test data"""
        if self.test_mode:
            # Create sample incidents
            for i in range(10):
                self.incidents.append({
                    "sys_id": str(uuid.uuid4()),
                    "number": f"INC00{i:05d}",
                    "short_description": f"Test incident {i}",
                    "description": f"Detailed description for incident {i}",
                    "state": random.choice(["New", "In Progress", "Resolved", "Closed"]),
                    "priority": random.choice(["1", "2", "3", "4"]),
                    "category": random.choice(["Network", "Hardware", "Software", "Database"]),
                    "assignment_group": "SRE Team",
                    "created_on": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    "updated_on": datetime.now().isoformat()
                })
            
            # Create sample change requests
            for i in range(5):
                self.changes.append({
                    "sys_id": str(uuid.uuid4()),
                    "number": f"CHG00{i:05d}",
                    "short_description": f"Change request {i}",
                    "type": random.choice(["Standard", "Normal", "Emergency"]),
                    "state": random.choice(["New", "Assess", "Scheduled", "Implement", "Review", "Closed"]),
                    "risk": random.choice(["Low", "Medium", "High"]),
                    "start_date": (datetime.now() + timedelta(days=random.randint(1, 7))).isoformat(),
                    "end_date": (datetime.now() + timedelta(days=random.randint(8, 14))).isoformat()
                })
            
            # Create CMDB items
            for i in range(20):
                self.cmdb_items.append({
                    "sys_id": str(uuid.uuid4()),
                    "name": f"server-{i:03d}",
                    "class": random.choice(["Server", "Application", "Database", "Network"]),
                    "status": random.choice(["Operational", "Maintenance", "Retired"]),
                    "location": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
                    "relationships": []
                })
        
    def setup_routes(self):
        @self.app.route('/servicenow/incidents', methods=['GET', 'POST'])
        def incidents_endpoint():
            if request.method == 'GET':
                filters = request.args.to_dict()
                return jsonify(self.get_incidents(filters))
            else:
                data = request.json
                return jsonify(self.create_incident(data))
                
        @self.app.route('/servicenow/changes', methods=['GET'])
        def changes_endpoint():
            filters = request.args.to_dict()
            return jsonify(self.get_changes(filters))
            
        @self.app.route('/servicenow/cmdb', methods=['GET'])
        def cmdb_endpoint():
            ci_name = request.args.get('name', '')
            ci_class = request.args.get('class', '')
            
            return jsonify(self.get_cmdb_items(ci_name, ci_class))
        
        @self.app.route('/servicenow/problems', methods=['GET', 'POST'])
        def problems_endpoint():
            if request.method == 'GET':
                filters = request.args.to_dict()
                return jsonify(self.get_problems(filters))
            else:
                data = request.json
                return jsonify(self.create_problem(data))
        
        @self.app.route('/servicenow/problems/<problem_id>', methods=['PUT'])
        def update_problem_endpoint(problem_id):
            data = request.json
            return jsonify(self.update_problem(problem_id, data))
        
        @self.app.route('/servicenow/problems/by-incident/<incident_id>', methods=['GET'])
        def problems_by_incident_endpoint(incident_id):
            return jsonify(self.get_problems_by_incident(incident_id))
    
    def get_incidents(self, filters: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get incidents based on filters"""
        if self.test_mode:
            results = self.incidents.copy()
            
            # Apply filters - be more lenient with matching
            if filters.get('state'):
                if filters['state'].lower() == 'active':
                    # Map 'active' to actual states
                    results = [i for i in results if i['state'] in ['New', 'In Progress']]
                else:
                    results = [i for i in results if i['state'].lower() == filters['state'].lower()]
            if filters.get('priority'):
                results = [i for i in results if i['priority'] == filters['priority']]
            if filters.get('category'):
                results = [i for i in results if i['category'].lower() == filters['category'].lower()]
                
            return results
    
    def create_incident(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new incident"""
        if self.test_mode:
            incident = {
                "sys_id": str(uuid.uuid4()),
                "number": f"INC00{len(self.incidents) + 1:05d}",
                "short_description": data.get("short_description", ""),
                "description": data.get("description", ""),
                "state": "New",
                "priority": data.get("priority", "3"),
                "category": data.get("category", "Software"),
                "assignment_group": data.get("assignment_group", "SRE Team"),
                "created_on": datetime.now().isoformat(),
                "updated_on": datetime.now().isoformat(),
                "created_by": "MCP Integration"
            }
            
            self.incidents.append(incident)
            return incident
    
    def get_changes(self, filters: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get change requests"""
        if self.test_mode:
            results = self.changes.copy()
            
            # Apply filters
            if filters.get('state'):
                results = [c for c in results if c['state'].lower() == filters['state'].lower()]
            if filters.get('risk'):
                results = [c for c in results if c['risk'].lower() == filters['risk'].lower()]
                
            return results
    
    def get_cmdb_items(self, name: str, ci_class: str) -> List[Dict[str, Any]]:
        """Get CMDB configuration items"""
        if self.test_mode:
            results = self.cmdb_items.copy()
            
            if name:
                results = [ci for ci in results if name.lower() in ci['name'].lower()]
            if ci_class:
                results = [ci for ci in results if ci['class'].lower() == ci_class.lower()]
                
            return results
    
    def get_problems(self, filters: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get problems based on filters"""
        if self.test_mode:
            results = self.problems.copy()
            
            # Apply filters
            if filters.get('state'):
                results = [p for p in results if p['state'].lower() == filters['state'].lower()]
            if filters.get('priority'):
                results = [p for p in results if p['priority'] == filters['priority']]
            if filters.get('category'):
                results = [p for p in results if p['category'].lower() == filters['category'].lower()]
                
            return results
    
    def create_problem(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new problem"""
        if self.test_mode:
            problem_id = f"PRB{len(self.problems) + 1:07d}"
            problem = {
                "problem_id": problem_id,
                "sys_id": str(uuid.uuid4()),
                "number": problem_id,
                "short_description": data.get("short_description", ""),
                "description": data.get("description", ""),
                "state": data.get("state", "New"),
                "impact": data.get("impact", "3 - Low"),
                "urgency": data.get("urgency", "3 - Low"),
                "priority": data.get("priority", "4 - Low"),
                "category": data.get("category", "Software"),
                "subcategory": data.get("subcategory", "Application"),
                "assignment_group": data.get("assignment_group", "SRE Team"),
                "assigned_to": data.get("assigned_to", ""),
                "source_incident_id": data.get("source_incident_id", ""),
                "problem_statement": data.get("problem_statement", ""),
                "workaround": data.get("workaround", ""),
                "known_error": data.get("known_error", False),
                "root_cause_analysis": data.get("root_cause_analysis", "In Progress"),
                "resolution_notes": data.get("resolution_notes", ""),
                "created_by": data.get("created_by", "MCP Integration"),
                "opened_at": data.get("opened_at", datetime.now().isoformat()),
                "created_on": datetime.now().isoformat(),
                "updated_on": datetime.now().isoformat(),
                "url": f"https://company.service-now.com/nav_to.do?uri=problem.do?sys_id={problem_id}"
            }
            
            self.problems.append(problem)
            return problem
    
    def update_problem(self, problem_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing problem"""
        if self.test_mode:
            # Find the problem
            problem = None
            for p in self.problems:
                if p['problem_id'] == problem_id or p['sys_id'] == problem_id:
                    problem = p
                    break
            
            if problem:
                # Update fields
                for key, value in data.items():
                    if key in problem:
                        problem[key] = value
                problem['updated_on'] = datetime.now().isoformat()
                return problem
            else:
                return {"error": f"Problem {problem_id} not found"}
    
    def get_problems_by_incident(self, incident_id: str) -> List[Dict[str, Any]]:
        """Get all problems associated with an incident"""
        if self.test_mode:
            return [p for p in self.problems if p.get('source_incident_id') == incident_id]
    
    def start_server(self, port=8082):
        """Start the MCP server"""
        self.app.run(host='0.0.0.0', port=port, debug=False)


def start_servicenow_mcp_server(port=8082, test_mode=True):
    """Start ServiceNow MCP server in a separate thread"""
    server = ServiceNowMCPServer(test_mode=test_mode)
    thread = threading.Thread(target=server.start_server, args=(port,))
    thread.daemon = True
    thread.start()
    return server