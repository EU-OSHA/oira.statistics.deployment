from metabase_api import Metabase_API

import json
import logging
import requests


log = logging.getLogger(__name__)


class OiraMetabase_API(Metabase_API):
    def authenticate(self):
        """Get a Session ID"""
        conn_header = {"username": self.email, "password": self.password}

        try:
            res = requests.post(
                self.domain + "/api/session", json=conn_header, timeout=15
            )
        except requests.exceptions.Timeout:
            log.warn("Authentication timed out, retrying")
            res = requests.post(
                self.domain + "/api/session", json=conn_header, timeout=30
            )
        if not res.ok:
            raise Exception(res)

        self.session_id = res.json()["id"]
        self.header = {"X-Metabase-Session": self.session_id}

    def get(self, endpoint, **kwargs):
        self.validate_session()
        result = requests.get(self.domain + endpoint, headers=self.header, **kwargs)
        self.check_error(result)
        return result

    def post(self, endpoint, **kwargs):
        self.validate_session()
        result = requests.post(self.domain + endpoint, headers=self.header, **kwargs)
        self.check_error(result)
        return result

    def put(self, endpoint, **kwargs):
        self.validate_session()
        result = requests.put(self.domain + endpoint, headers=self.header, **kwargs)
        self.check_error(result)
        return result

    def delete(self, endpoint, **kwargs):
        self.validate_session()
        result = requests.delete(self.domain + endpoint, headers=self.header, **kwargs)
        self.check_error(result)
        return result

    def check_error(self, result):
        if not result.ok:
            if result.status_code not in [404]:
                try:
                    errors = result.json().get("errors") or result.json().get("message")
                except json.decoder.JSONDecodeError:
                    errors = result.text
            else:
                errors = result.reason
            log.error(
                "Error {status_code} during {method} request to {url}! ({errors})"
                "".format(
                    method=result.request.method,
                    url=result.url,
                    status_code=result.status_code,
                    errors=errors,
                )
            )
