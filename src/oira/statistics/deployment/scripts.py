# -*- coding: utf-8 -*-
from .initializer import MetabaseInitializer
import argparse
import json
import logging
import requests
import sys

log = logging.getLogger(__name__)


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
        help=("Name of the postgresql statistics database"),
    )
    parser.add_argument(
        "--database-pattern-statistics",
        type=str,
        default="statistics_{country}",
        help=(
            "Pattern for constructing the name of the postgresql statistics databases. "
            "{country} will be replaced by the two-letter country code. Default: "
            "statisticts_{country}"
        ),
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
        "--countries",
        type=str,
        help=(
            "Comma separated list of country codes for which database, collection, "
            "dashboards and cards will be set up."
        ),
    )
    parser.add_argument(
        "--ldap-host",
        type=str,
        help=("LDAP host name or IP-address"),
    )
    parser.add_argument(
        "--ldap-port",
        type=str,
        help=("LDAP port"),
    )
    parser.add_argument(
        "--ldap-bind-dn",
        type=str,
        help=("LDAP bind DN"),
    )
    parser.add_argument(
        "--ldap-password",
        type=str,
        help=("LDAP password"),
    )
    parser.add_argument(
        "--ldap-user-base",
        type=str,
        help=("LDAP user base DN"),
    )
    parser.add_argument(
        "--ldap-user-filter",
        type=str,
        help=("LDAP user filter"),
    )
    parser.add_argument(
        "--ldap-attribute-firstname",
        type=str,
        default="givenName",
        help=("LDAP attribute to use as first name"),
    )
    return parser.parse_args()


def bootstrap_metabase_instance(args):
    api_url = "http://{args.metabase_host}:{args.metabase_port}".format(args=args)
    probe = requests.post(
        "{api_url}/api/session".format(api_url=api_url),
        json={
            "username": args.metabase_user,
            "password": args.metabase_password,
        },
    )
    if probe.ok:
        log.info("Metabase user already set up")
        return
    log.info("Setting up metabase user")
    result = requests.get(api_url)
    token = json.loads(
        next((line for line in result.text.split("\n") if "setup-token" in line))
    )["setup-token"]
    bootstrap = {
        "token": token,
        "prefs": {
            "site_name": "Syslab.com",
            "site_locale": "en",
            "allow_tracking": "false",
        },
        "database": None,
        "user": {
            "first_name": "Admin",
            "last_name": "Syslab",
            "email": args.metabase_user,
            "password": args.metabase_password,
            "site_name": "Syslab.com",
        },
    }
    result = requests.post(api_url + "/api/setup", json=bootstrap)
    if not result.ok:
        log.warn("Bootstrap returned %r: %r!", result.status_code, result.text)


def init_metabase_instance():
    logging.basicConfig(stream=sys.stderr, level=20)
    args = get_metabase_args()

    log.info("Initializing metabase instance")
    bootstrap_metabase_instance(args)
    initializer = MetabaseInitializer(args)
    initializer()
