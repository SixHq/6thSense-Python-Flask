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
from sixth import schemas
import requests




class SixRateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, apikey: str, project_config: schemas.ProjectConfig,  all_routes: List[str]):
        super().__init__()
        self._config = project_config
        self._log_dict = {}
        self._app = app
        self._apikey = apikey
        self._route_last_updated = {}
        self._rate_limit_logs_sent = {}
        
        for route in all_routes:
            edited_route = re.sub(r'\W+', '~', route)
            self._log_dict[str(edited_route)] = {}
            self._route_last_updated[str(edited_route)] = time.time()
            self._rate_limit_logs_sent[str(edited_route)] = 0                
        
    def _is_rate_limit_reached(self, uid, route):
        rate_limit = self._config.rate_limiter[route].rate_limit
        interval = self._config.rate_limiter[route].interval
        body = {
            "route": route, 
            "interval": interval, 
            "rate_limit": rate_limit, 
            "unique_id": uid.replace(".","~"), 
            "user_id": self._apikey,
            "is_active":True
        }
        resp = requests.post("https://backend.withsix.co/rate-limit/enquire-has-reached-rate_limit", json=body)
        if resp.status_code == 200:
            body =  resp.json()
            return body["response"]
        else:
            return False
        
    def _send_logs(self, route: str, header, body, query)-> None:
        timestamp = time.time()
        last_log_sent = self._rate_limit_logs_sent[route]
        if timestamp - last_log_sent > 10:
            requests.post("https://backend.withsix.co/slack/send_message_to_slack_user", json=schemas.SlackMessageSchema(
                header=header, 
                user_id=self._apikey, 
                body=str(body), 
                query_args=str(query), 
                timestamp=timestamp, 
                attack_type="No Rate Limit Attack", 
                cwe_link="https://cwe.mitre.org/data/definitions/770.html", 
                status="MITIGATED", 
                learn_more_link="https://en.wikipedia.org/wiki/Rate_limiting", 
                route=route
            ).dict())
            self._rate_limit_logs_sent[route]=timestamp

    def _extract_query_params(self, query_string:str)-> dict:
        final = {}
        query_list= query_string.decode("utf-8").split('&')
        for i in query_list:
            temp = i.split("=")
            final[temp[0]] = temp[1]

        return final


        
    def dispatch(self,request: Request,call_next) -> None:
        #get client ip address first 
        host = request.host
        route =request.path
        route = re.sub(r'\W+', '~', route)
        headers = request.headers
        query_params = request.query_string
        query_params = self._extract_query_params(query_params)
        rate_limit_resp = None
        status_code = 200
       
        
        
        #fail safe if there is an internal server error our servers are currenly in maintnance
        try:
            update_time = time.time()
            if update_time - self._route_last_updated[route] >60:
                #update rate limit details every 60 seconds
                rate_limit_resp = requests.get("https://backend.withsix.co/project-config/config/get-route-rate-limit/"+self._apikey+"/"+route)
                self._route_last_updated[route] = update_time
                status_code = rate_limit_resp.status_code
            body = None

            try:
                body = request.get_json()
            except:
                pass
            if status_code == 200: 
                try:
                    rate_limit = schemas.RateLimiter.model_validate(rate_limit_resp.json()) if rate_limit_resp != None else self._config.rate_limiter[route]
                    if rate_limit.is_active:
                        self._config.rate_limiter[route] = rate_limit
                        preferred_id = self._config.rate_limiter[route].unique_id
                    
                        if preferred_id == "" or preferred_id=="host":
                            preferred_id = host
                            
                        else:
                            if rate_limit.rate_limit_type == "body":
                                if body != None:
                                    preferred_id = body[preferred_id]
                                else:
                                    _response = call_next(request)
                                    return _response
                            elif rate_limit.rate_limit_type == "header":
                                preferred_id = headers[preferred_id]
                            elif rate_limit.rate_limit_type == "args":
                                preferred_id = query_params[preferred_id]
                            else:
                                preferred_id = host
                        

                        if not self._is_rate_limit_reached(preferred_id, route): 
                            _response = call_next(request)
                            return _response
                        else:    
                            self._send_logs(route=route, header=dict(headers.items()), body=body, query=query_params)
                            temp_payload = rate_limit.error_payload.values()
                            final = {}
                            for c in temp_payload:
                                for keys in c:
                                    if keys != "uid":
                                        final[keys] = c[keys]
                            output= final
                            _response = jsonify(output)
                            _response.headers = {"content-length": str(len(str(output).encode())), 'content-type': 'application/json'}
                            _response.status_code=420
                            return _response
                    else:
                        _response = call_next(request)
                        return _response
                except Exception as e:
                    _response = call_next(request)
                    return _response
            else:
                #fail safe if there is an internal server error our servers are currenly in maintnance
                _response = call_next(request)
                return _response
        except Exception as e:
            _response = call_next(request)
            return _response