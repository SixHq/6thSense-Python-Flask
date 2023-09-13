import re
from flask import Flask, request, Response, jsonify
import time
import requests


class EncryptionMiddleware():
    def __init__(self, app, apikey: str):
        self._app = app
        self._apikey = apikey
        self._logs_sent = {}
        self._last_updated = 0
        self._encryption_enabled = False
        self._update_encryption_details()
        all_routes = [str(rule) for rule in self._app.url_map.iter_rules()]
        
        for route in all_routes:
            edited_route = re.sub(r'\W+', '~', route)
            self._logs_sent[str(edited_route)] = 0 

    def __call__(self, environ, start_response):
        # Code to run before handling the request
       # print("Before request processing")

        # Call the next middleware or route handler
        return self._app(environ, start_response)

        # Code to run after handling the request
        print("After request processing")

        # Modify the response body (if it's a string)
        if isinstance(response, str):
            modified_response = "Modified: " + response
            response = Response(modified_response)

        if response.is_json:
            data = response.get_json()

            # Modify the JSON data as needed
            if 'message' in data:
                data['message'] = 'Modified: ' + data['message']

            # Create a new response with the modified JSON data
            modified_response = Response(response=jsonify(data), status=response.status, content_type=response.content_type)
            return modified_response

        return response(environ, start_response)
    
    def _update_encryption_details(self):
        timestamp = time.time()
        if timestamp - self._last_updated <10:
            return 
        response = requests.get(f"https://backend.withsix.co/encryption-service/get-encryption-setting-for-user?user_id={self._apikey}")
        if response.status_code == 200:
            self._encryption_enabled = response.json()["enabled"]
            self._last_updated=timestamp
        else:
            self._encryption_enabled=False