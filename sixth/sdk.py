from flask import Flask
from sixth import schemas
import requests
from pydantic.error_wrappers import ValidationError
from sixth.utils.time_utils import get_time_now
import re
from sixth.middlewares.sixth_encryption_middleware import EncryptionMiddleware
from sixth.middlewares.sixth_rate_limiter_middleware import SixRateLimiterMiddleware
from sixth.utils.flask_http_middleware.base import BaseHTTPMiddleware
from sixth.utils.flask_http_middleware.manager import MiddlewareManager

class Sixth():
    def __init__(self, apikey: str, app: Flask):
        self._apikey = apikey
        self._app: Flask = app 
        self._all_routes =  [str(rule) for rule in self._app.url_map.iter_rules()]
        

    def init(self):
        _base_url = "https://backend.withsix.co"
        _project_config_resp = requests.get(_base_url+"/project-config/config/"+self._apikey)
        # get the user's project config
        self._app.wsgi_app = MiddlewareManager(self._app)
        #self._app.wsgi_app.add_middleware(EncryptionMiddleware, app=self._app.wsgi_app, apikey=self._apikey, all_routes=self._all_routes)
        try:
            if _project_config_resp.status_code == 200:
                _config: schemas.ProjectConfig = schemas.ProjectConfig.parse_obj(dict(_project_config_resp.json()))
                self._sync_project_route(_config)
            else:
                _config = self._sync_project_route()
        except ValidationError as e:
            #self._app.wsgi_app = EncryptionMiddleware(self._app.wsgi_ap, self._apikey)
            _config = self._sync_project_route()

        self._app.wsgi_app.add_middleware(SixRateLimiterMiddleware, apikey= self._apikey, app= self._app, project_config=_config, all_routes=self._all_routes)
        return self._app

    def _sync_project_route(self, config: schemas.ProjectConfig = None)-> schemas.ProjectConfig:
        #sync the config with db
        _rl_configs = {}
        all_routes = [str(rule) for rule in self._app.url_map.iter_rules()]
        for route in all_routes:
            edited_route = re.sub(r'\W+', '~', route)
            if config and edited_route in config.rate_limiter.keys():
                    #default config has been set earlier on so skip
                    _rl_configs[edited_route] = config.rate_limiter[edited_route]
                    continue
                #set the default values
            _rl_config = schemas.RateLimiter(id = edited_route, route=edited_route, interval=60, rate_limit=10, last_updated=get_time_now(), created_at=get_time_now(), unique_id="host", is_active=False)
            _rl_configs[edited_route] = _rl_config

        _config = schemas.ProjectConfig(
            user_id = self._apikey, 
            rate_limiter = _rl_configs, 
            encryption = schemas.Encryption(public_key="dummy",private_key="dummy", use_count=0, last_updated=0,created_at=0, is_active=False), 
            base_url = "project",
            last_updated=get_time_now(), 
            created_at=get_time_now(), 
            encryption_enabled=config.encryption_enabled if config != None else False, 
            rate_limiter_enabled=config.rate_limiter_enabled if config != None else True
        )
        _base_url = "https://backend.withsix.co"
        _project_config_resp = requests.post(_base_url+"/project-config/config/sync-user-config", json=_config.dict())
        if _project_config_resp.status_code == 200:
            return _config
        else: 
            return _config