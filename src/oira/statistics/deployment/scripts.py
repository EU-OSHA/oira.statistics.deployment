# -*- coding: utf-8 -*-
from metabase_api import Metabase_API
import argparse
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
        res = requests.get(self.domain + endpoint, headers=self.header, **kwargs)
        return res

    def post(self, endpoint, **kwargs):
        self.validate_session()
        res = requests.post(self.domain + endpoint, headers=self.header, **kwargs)
        return res

    def put(self, endpoint, **kwargs):
        self.validate_session()
        res = requests.put(self.domain + endpoint, headers=self.header, **kwargs)
        return res

    def delete(self, endpoint, **kwargs):
        self.validate_session()
        res = requests.delete(self.domain + endpoint, headers=self.header, **kwargs)
        return res


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
    return parser.parse_args()


def init_metabase_instance():
    logging.basicConfig(stream=sys.stderr, level=20)
    args = get_metabase_args()

    log.info("Initializing metabase instance")
    api_url = "http://{args.metabase_host}:{args.metabase_port}".format(args=args)
    mb = OiraMetabase_API(api_url, args.metabase_user, args.metabase_password)

    result = mb.put(
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
    if not result.ok:
        log.error(
            "Could not update database connection! ({status_code}: {errors})".format(
                status_code=result.status_code, errors=result.json().get("errors")
            )
        )
    else:
        log.info("Set up database {}".format(args.database_name_statistics))

    for email, password, first_name, last_name in args.statistics_user or []:
        result = mb.post(
            "/api/user",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password,
                "group_ids": [1],
            },
        )
        if not result.ok:
            log.error(
                "Could not create user! ({status_code}: {errors})".format(
                    status_code=result.status_code, errors=result.json().get("errors")
                )
            )
        else:
            log.info("Created user {}".format(email))

    if args.global_statistics:
        result = mb.post(
            "/api/dashboard/1/cards",
            json={"cardId": 15, "col": 0, "row": 4, "sizeX": 4, "sizeY": 4},
        )
        if not result.ok:
            log.error(
                "Could not add dashboard card! ({status_code}: {errors})".format(
                    status_code=result.status_code, errors=result.json().get("errors")
                )
            )
        else:
            log.info("Added dashboard card 15")
    if args.country_statistics:
        result = mb.post(
            "/api/dashboard/1/cards",
            json={"cardId": 17, "col": 10, "row": 4, "sizeX": 4, "sizeY": 4},
        )
        if not result.ok:
            log.error(
                "Could not add dashboard card! ({status_code}: {errors})".format(
                    status_code=result.status_code, errors=result.json().get("errors")
                )
            )
        else:
            log.info("Added dashboard card 17")

    log.info("Done initializing metabase instance")
