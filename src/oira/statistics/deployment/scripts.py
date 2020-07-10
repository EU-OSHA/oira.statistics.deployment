# -*- coding: utf-8 -*-
from metabase_api import Metabase_API
import argparse
import json
import logging
import requests
import sys

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


def get_metabase_args():
    parser = argparse.ArgumentParser(
        description=(
            "Initialize a metabase instance that has been freshly restored from a SQL "
            "dump by adapting settings to the given parameters."
        )
    )
    parser.add_argument(
        "--metabase-host",
        type=str,
        required=False,
        default="localhost",
        help=("Host that the metabase instance is running on"),
    )
    parser.add_argument(
        "--metabase-port",
        type=str,
        required=False,
        default=3000,
        help=("Port that the metabase instance is running on"),
    )
    parser.add_argument(
        "--metabase-user",
        type=str,
        required=True,
        help=("User name for connecting to the metabase instance"),
    )
    parser.add_argument(
        "--metabase-password",
        type=str,
        required=True,
        help=("Password for connecting to the metabase instance"),
    )
    parser.add_argument(
        "--database-name", type=str, help=("Name of the internal metabase database")
    )
    parser.add_argument(
        "--database-host",
        type=str,
        required=False,
        default="localhost",
        help=("Host that the postgresql server is running on"),
    )
    parser.add_argument(
        "--database-port",
        type=str,
        required=False,
        default=5432,
        help=("Port that the postgresql server is running on"),
    )
    parser.add_argument(
        "--database-user",
        type=str,
        required=True,
        help=("User name for connecting to the postgresql server"),
    )
    parser.add_argument(
        "--database-password",
        type=str,
        required=True,
        help=("Password for connecting to the postgresql server"),
    )
    parser.add_argument(
        "--database-name-statistics",
        type=str,
        required=True,
        help=("Name of the postgresql statistics database"),
    )
    parser.add_argument(
        "--statistics-user",
        type=str,
        action="append",
        nargs=4,
        metavar="USER_INFO",
        help=(
            "Email address, password, first and last name, separated by whitespace, "
            "for a non-superuser account to create for viewing the statistics"
        ),
    )
    parser.add_argument(
        "--global-statistics",
        action="store_true",
        help=("If passed, global-only dashboard cards will be added."),
    )
    parser.add_argument(
        "--country-statistics",
        action="store_true",
        help=("If passed, country-only dashboard cards will be added."),
    )
    parser.add_argument(
        "--ldap-host", type=str, help=("LDAP host name or IP-address"),
    )
    parser.add_argument(
        "--ldap-port", type=str, help=("LDAP port"),
    )
    parser.add_argument(
        "--ldap-bind-dn", type=str, help=("LDAP bind DN"),
    )
    parser.add_argument(
        "--ldap-password", type=str, help=("LDAP password"),
    )
    parser.add_argument(
        "--ldap-user-base", type=str, help=("LDAP user base DN"),
    )
    parser.add_argument(
        "--ldap-user-filter", type=str, help=("LDAP user filter"),
    )
    parser.add_argument(
        "--ldap-attribute-firstname",
        type=str,
        help=("LDAP attribute to use as first name"),
    )
    return parser.parse_args()


def init_metabase_instance():
    logging.basicConfig(stream=sys.stderr, level=20)
    args = get_metabase_args()

    log.info("Initializing metabase instance")
    api_url = "http://{args.metabase_host}:{args.metabase_port}".format(args=args)
    mb = OiraMetabase_API(api_url, args.metabase_user, args.metabase_password)

    log.info("Setting up database {}".format(args.database_name_statistics))
    mb.put(
        "/api/database/34",
        json={
            "name": args.database_name_statistics,
            "engine": "postgres",
            "details": {
                "dbname": args.database_name_statistics,
                "host": args.database_host,
                "port": args.database_port,
                "user": args.database_user,
                "password": args.database_password,
            },
        },
    )

    users = mb.get("/api/user").json()
    user_emails = [user["email"] for user in users]
    for email, password, first_name, last_name in args.statistics_user or []:
        if email not in user_emails:
            log.info("Creating user {}".format(email))
            mb.post(
                "/api/user",
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "password": password,
                    "group_ids": [1, 4],
                },
            )
        else:
            log.info("Modifying user {}".format(email))
            user_id = [user["id"] for user in users if user["email"] == email][0]
            mb.put(
                "/api/user/{}".format(user_id),
                json={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "password": password,
                    "group_ids": [1, 4],
                },
            )

    if args.global_statistics:
        log.info("Adding global dashboard cards")
        mb.post(
            "/api/dashboard/1/cards",
            json={"cardId": 15, "col": 0, "row": 4, "sizeX": 4, "sizeY": 4},
        )
    if args.country_statistics:
        log.info("Adding country dashboard cards")
        mb.post(
            "/api/dashboard/1/cards",
            json={"cardId": 17, "col": 10, "row": 4, "sizeX": 4, "sizeY": 4},
        )

    if args.ldap_host:
        log.info("Setting up LDAP")
        mb.put(
            "/api/ldap/settings",
            json={
                "ldap-enabled": True,
                "ldap-host": args.ldap_host,
                "ldap-port": args.ldap_port or "389",
                "ldap-bind-dn": args.ldap_bind_dn,
                "ldap-password": args.ldap_password,
                "ldap-user-base": args.ldap_user_base,
                "ldap-user-filter": args.ldap_user_filter,
                "ldap-attribute-firstname": args.ldap_attribute_firstname,
            },
        )

    log.info("Done initializing metabase instance")
