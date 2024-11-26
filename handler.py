#!/usr/bin/env python
# SPDX-License-Identifier: AGPL-3.0-or-later
"""WebApp"""
from serverless_wsgi import handle_request
from flask import Flask, jsonify, request
import sys
from pathlib import Path

from searx.enginelib import Engine
from searx.preferences import ClientPref, Preferences
from searx.search import SearchWithPlugins
from searx.webadapter import get_search_query_from_webapp

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).parent.resolve()))
import searx

class LambdaRequestAdapter:
    """
    Adapts the AWS Lambda event object to mimic a Flask request.
    """

    def __init__(self, event):
        self.headers = event.get("headers", {})
        self.method = event.get("httpMethod", "GET")
        self.query_string = event.get("queryStringParameters", {}) or {}
        self.body = event.get("body", "")
        self.cookies = self.headers.get("Cookie", "")  # Simulate cookies
        self.form = self._parse_body(event)

    def _parse_body(self, event):
        """
        Parse the body into a dictionary, supporting JSON or form-encoded data.
        """
        import json
        body = event.get("body", "")
        if not body:
            return {}

        try:
            # Try parsing as JSON
            return json.loads(body)
        except json.JSONDecodeError:
            # If not JSON, assume form-encoded
            from urllib.parse import parse_qs
            return {k: v[0] for k, v in parse_qs(body).items()}



app = Flask(__name__)

# Example route for web search
@app.route("/web-search", methods=["GET"])
def web_search():
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400
    return jsonify({"message": f"Searching for: {query}"}), 200

# AWS Lambda handler
def lambda_handler(event, context):
    print("searx.max_request_timeout",searx.max_request_timeout)
    event_adapter = LambdaRequestAdapter(event)
    client_pref = ClientPref.from_http_request(event_adapter)
    # pylint: disable=redefined-outer-name
    preferences = Preferences(
        themes=['light', 'dark'],  # Supporting both light and dark modes
        categories=['general', 'technology', 'science'],  # Popular categories
        engines={
            'google': Engine(),  # Example: Google search engine
            'bing': Engine(),  # Example: Bing search engine
        },
        plugins=[],  # No plugins configured for now
        client=None,
    )
    search_query, raw_text_query, _, _, selected_locale = get_search_query_from_webapp(
        preferences, {"q": "Bizzi", "format": "json"}
    )
    print("searx.search_query",search_query)
    search = SearchWithPlugins(search_query, [], request)  # pylint: disable=redefined-outer-name

    print("HERE")

    result_container = search.search()

    return handle_request(app, event, context)
