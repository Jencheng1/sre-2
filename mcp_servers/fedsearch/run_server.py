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
