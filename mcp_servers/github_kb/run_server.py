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
