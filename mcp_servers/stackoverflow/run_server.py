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
