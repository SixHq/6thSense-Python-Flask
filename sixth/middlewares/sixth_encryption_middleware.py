import re
import time
import requests
from typing import List
from flask import Flask, Response, jsonify, Request
from flask import request as rqs
import flask
import io
import json
from sixth.utils.flask_http_middleware.base import BaseHTTPMiddleware
from sixth.utils.flask_http_middleware.manager import MiddlewareManager
from sixth.utils import encryption_utils
from starlette.datastructures import MutableHeaders


class EncryptionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, apikey: str, all_routes: List[str]):
        super().__init__()
        self._app = app
        self._apikey = apikey
        self._logs_sent = {}
        self._last_updated = 0
        self._encryption_enabled = False
        self._update_encryption_details()
        
        for route in all_routes:
            edited_route = re.sub(r'\W+', '~', route)
            self._logs_sent[str(edited_route)] = 0 

    def dispatch(self, request, call_next):
        self._update_encryption_details()
        url = request.url

        if True:
            route = re.sub(r'\W+', '~', url)
            req_body = request.get_json()["data"]
            headers = dict(request.headers)
            output = encryption_utils.post_order_decrypt(req_body)
            print("output is ", output)
            headers["content-length"]= str(len(json.dumps(output).encode()))
            '''except Exception as e:
                #self._send_logs(route=route, header=headers, body=req_body, query="")
                print("error that occured is ", e)
                output= {
                    "data": "UnAuthorized"
                }
                headers = MutableHeaders(headers={"content-length": str(len(str(output).encode())), 'content-type': 'application/json'})
                return Response(jsonify(output), headers={"content-length": str(len(str(output).encode())), 'content-type': 'application/json'})'''
            new_environ = request.environ
            new_environ["wsgi.input"] = jsonify(output).data
            request.stream = io.BytesIO(jsonify(output).data)
            request._cached_json =  jsonify(output).data 
            
            print("request going to endpoint is ", jsonify(output).data)
            response = call_next(request)
            print("output json is", response.json)

            # Get the response body content from the custom property
            response_body = response.json
            #try:
            output = {
                "data": encryption_utils.post_order_encrypt(str(response_body))
            }
            response = jsonify(output)
            response.headers["content-length"]= str(len(json.dumps(output).encode()))
            return response
            
            '''except Exception as e:
                print("new eror is ", e)
                output= {
                    "data": "UnAuthorized"
                }
                headers = MutableHeaders(headers={"content-length": str(len(str(output).encode())), 'content-type': 'application/json'})
                return Response(jsonify(output), headers={"content-length": str(len(str(output).encode()))})'''
        else:
            _response = call_next(request)
            return _response
        print("url is ", request.get_json())
        
        response = call_next(request)
        response.headers.add("x-url", url)
        return response

    '''def __call__(self, environ, start_response):
        # Code to run before handling the request
        print("Before request processing")
        

        request = Request(environ)
       
        environ['wsgi.input'] = io.BytesIO(json.dumps({
            "ope":"this is very good"
        }).encode('utf-8'))

        request_body = request.json
        print("request body is", request_body)
        

        # Call the next middleware or route handler
        response = self._app(environ, start_response)
        
        
        response = Response(response)
        body = response.json

        # Code to run after handling the request
        print("After request processing ", (body))

        # Modify the response body (if it's a string)
        if isinstance(response, str):
            modified_response = "Modified: " + response
            response = Response(modified_response)

        if True:
            # Create a new response with the modified JSON data
            #modified_response = Response(response=jsonify(body), status=response.status, content_type=response.content_type)
            return body.encode('utf-8')

        return response
    '''

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