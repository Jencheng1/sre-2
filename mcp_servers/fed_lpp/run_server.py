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
