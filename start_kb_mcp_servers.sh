#!/bin/bash
# Start Knowledge Management MCP Servers

echo "Starting Knowledge Management MCP Servers..."

# Create runner scripts for KB servers
cat > mcp_servers/fed_lpp/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')

# Simple mock server for demo
from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/lpp/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
    return jsonify({
        "results": [
            {"title": f"Federal Best Practice: {query}", "relevance": 0.95},
            {"title": f"Lessons Learned: {query} Implementation", "relevance": 0.89}
        ]
    })

if __name__ == "__main__":
    print("Starting Federal LPP KB server on port 9087...")
    app.run(host='0.0.0.0', port=9087, debug=False)
EOF

cat > mcp_servers/fedsearch/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')

from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/fedsearch/query', methods=['POST'])
def query():
    search_query = request.json.get('query', '')
    return jsonify({
        "results": [
            {"title": f"Federal System: {search_query}", "system": "GSA", "relevance": 0.92},
            {"title": f"Policy Document: {search_query}", "system": "OMB", "relevance": 0.87}
        ]
    })

if __name__ == "__main__":
    print("Starting FedSearch server on port 9088...")
    app.run(host='0.0.0.0', port=9088, debug=False)
EOF

cat > mcp_servers/stackoverflow/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')

from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/stackoverflow/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
    return jsonify({
        "results": [
            {"title": f"How to fix {query}", "votes": 156, "accepted": True},
            {"title": f"Best approach for {query}", "votes": 89, "accepted": False}
        ]
    })

if __name__ == "__main__":
    print("Starting StackOverflow KB server on port 9089...")
    app.run(host='0.0.0.0', port=9089, debug=False)
EOF

cat > mcp_servers/github_kb/run_server.py << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ec2-user/sre/sre_mcp')

from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/github/search', methods=['POST'])
def search():
    query = request.json.get('query', '')
    return jsonify({
        "results": [
            {"title": f"Issue: {query} in production", "repo": "sre-tools", "state": "closed"},
            {"title": f"PR: Fix for {query}", "repo": "infrastructure", "state": "merged"}
        ]
    })

if __name__ == "__main__":
    print("Starting GitHub KB server on port 9090...")
    app.run(host='0.0.0.0', port=9090, debug=False)
EOF

# Kill any existing processes on these ports
echo "Stopping any existing KB servers..."
fuser -k 9087/tcp 9088/tcp 9089/tcp 9090/tcp 2>/dev/null || true
sleep 2

# Start all KB servers
echo "Starting KB MCP servers..."

nohup python3 mcp_servers/fed_lpp/run_server.py > mcp_servers/fed_lpp/server.log 2>&1 &
echo "Fed LPP PID: $! (port 9087)"

nohup python3 mcp_servers/fedsearch/run_server.py > mcp_servers/fedsearch/server.log 2>&1 &
echo "FedSearch PID: $! (port 9088)"

nohup python3 mcp_servers/stackoverflow/run_server.py > mcp_servers/stackoverflow/server.log 2>&1 &
echo "StackOverflow KB PID: $! (port 9089)"

nohup python3 mcp_servers/github_kb/run_server.py > mcp_servers/github_kb/server.log 2>&1 &
echo "GitHub KB PID: $! (port 9090)"

echo ""
echo "✅ Knowledge Management MCP servers started!"
echo ""
echo "Available KB Sources:"
echo "- Federal LPP: http://localhost:9087"
echo "- FedSearch: http://localhost:9088"  
echo "- StackOverflow KB: http://localhost:9089"
echo "- GitHub KB: http://localhost:9090"
echo "- Confluence: http://localhost:9083 (already running)"
echo "- ServiceNow: http://localhost:9082 (already running)"
echo ""
echo "Access the Knowledge Base External Sources in Streamlit:"
echo "1. Go to http://localhost:8501"
echo "2. Navigate to Knowledge Base tab"
echo "3. Click on 'External Sources' sub-tab"