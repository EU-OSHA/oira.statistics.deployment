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
        default="givenName",
        help=("LDAP attribute to use as first name"),
    )
    return parser.parse_args()


class MetabaseInitializer(object):
    def __init__(self, args):
        self.args = args
        api_url = "http://{args.metabase_host}:{args.metabase_port}".format(args=args)
        self.mb = OiraMetabase_API(api_url, args.metabase_user, args.metabase_password)
        self._database_mapping = None
        self._existing_items = None

    def __call__(self):
        countries = {}

        global_group_id = self.set_up_global_group()
        if self.args.countries:
            countries = {
                country.strip(): {} for country in self.args.countries.split(",")
            }

            for country in countries:
                countries[country]["database"] = self.set_up_country_database(country)
                countries[country]["group"] = self.set_up_country_group(country)
                countries[country]["collection"] = self.set_up_country_collection(
                    country
                )
                self.set_up_country_dashboards(
                    country,
                    countries[country]["database"],
                    countries[country]["collection"],
                )

            self.set_up_country_permissions(countries, global_group_id)

        if self.args.global_statistics:
            self.set_up_global_permissions(global_group_id)
            log.info("Adding global dashboard cards")
            self.mb.post(
                "/api/dashboard/1/cards",
                json={"cardId": 15, "col": 0, "row": 4, "sizeX": 4, "sizeY": 4},
            )

        if self.args.ldap_host:
            self.set_up_ldap(countries, global_group_id)

        if self.args.statistics_user:
            users = self.mb.get("/api/user").json()
            user_emails = [user["email"] for user in users]
            for email, password, first_name, last_name in (
                self.args.statistics_user or []
            ):
                if email not in user_emails:
                    log.info("Creating user {}".format(email))
                    self.mb.post(
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
                    user_id = [user["id"] for user in users if user["email"] == email][
                        0
                    ]
                    self.mb.put(
                        "/api/user/{}".format(user_id),
                        json={
                            "first_name": first_name,
                            "last_name": last_name,
                            "email": email,
                            "password": password,
                            "group_ids": [1, 4],
                        },
                    )

        if self.args.database_name_statistics:
            log.info(
                "Setting up database {}".format(self.args.database_name_statistics)
            )
            self.mb.put(
                "/api/database/34",
                json={
                    "name": self.args.database_name_statistics,
                    "engine": "postgres",
                    "details": {
                        "dbname": self.args.database_name_statistics,
                        "host": self.args.database_host,
                        "port": self.args.database_port,
                        "user": self.args.database_user,
                        "password": self.args.database_password,
                    },
                },
            )
            self.mb.post("/api/database/34/sync")
        else:
            permissions = self.mb.get("/api/permissions/graph").json()
            if "1" in permissions["groups"]:
                permissions["groups"]["1"]["34"] = {"schemas": "none"}

        log.info("Done initializing metabase instance")

    def set_up_country_database(self, country):
        db_name = self.args.database_pattern_statistics.format(country=country.lower())
        if db_name in self.existing_items["databases"]:
            log.info("Keeping existing database {}".format(db_name))
            db_id = self.existing_items["databases"][db_name]
            db_info = self.mb.put(
                "/api/database/{}".format(db_id),
                json={
                    "name": db_name,
                    "engine": "postgres",
                    "details": {
                        "dbname": db_name,
                        "host": self.args.database_host,
                        "port": self.args.database_port,
                        "user": self.args.database_user,
                        "password": self.args.database_password,
                    },
                },
            ).json()
            db_id = db_info["id"]
        else:
            log.info("Setting up database {}".format(db_name))
            db_info = self.mb.post(
                "/api/database/",
                json={
                    "name": db_name,
                    "engine": "postgres",
                    "details": {
                        "dbname": db_name,
                        "host": self.args.database_host,
                        "port": self.args.database_port,
                        "user": self.args.database_user,
                        "password": self.args.database_password,
                    },
                },
            ).json()
            db_id = db_info["id"]

        self.mb.post("/api/database/{}/sync".format(db_id))

        self._database_mapping = None
        return db_id

    def set_up_global_group(self):
        if "GLOBAL" in self.existing_items["groups"]:
            log.info("Keeping existing global group")
            group_id = self.existing_items["groups"]["GLOBAL"]
        else:
            log.info("Adding global group")
            group_info = self.mb.post(
                "/api/permissions/group", json={"name": "global"},
            ).json()
            group_id = group_info["id"]
        return group_id

    def set_up_country_group(self, country):
        if country.upper() in self.existing_items["groups"]:
            log.info("Keeping existing country group {}".format(country))
            group_id = self.existing_items["groups"][country.upper()]
        else:
            log.info("Adding country group {}".format(country))
            group_info = self.mb.post(
                "/api/permissions/group", json={"name": country.upper()},
            ).json()
            group_id = group_info["id"]
        return group_id

    def set_up_country_collection(self, country):
        if country.upper() in self.existing_items["collections"]:
            log.info("Reusing existing country collection")
            collection_id = self.existing_items["collections"][country.upper()]
        else:
            log.info("Adding country collection")
            collection_id = self.mb.post(
                "/api/collection", json={"name": country.upper(), "color": "#00FF00"}
            ).json()["id"]
        return collection_id

    def set_up_country_dashboards(self, country, database_id, collection_id):
        log.info("Adding country dashboards")
        dashboard_id_map = {}
        for base_dashboard_id, dashboard_name_tmpl in {
            "1": "Assessments Dashboard ({})",
            "2": "Users Dashboard ({})",
        }.items():
            dashboard_name = dashboard_name_tmpl.format(country.upper())
            if dashboard_name in self.existing_items["dashboards"]:
                dashboard_id_map[base_dashboard_id] = self.existing_items["dashboards"][
                    dashboard_name
                ]
            else:
                dashboard_data = {
                    "name": dashboard_name,
                    "collection_id": collection_id,
                    "collection_position": int(base_dashboard_id),
                }
                result = self.mb.post("/api/dashboard", json=dashboard_data,)
                if not result.ok and "duplicate key" in result.json()["message"]:
                    # retry, this usually goes away by itself
                    log.info('Retrying after "duplicate key" error')
                    result = self.mb.post("/api/dashboard", json=dashboard_data,)
                dashboard_id_map[base_dashboard_id] = result.json()["id"]

        log.info("Adding country dashboard cards")
        for base_dashboard_id in ["1", "2"]:
            country_dashboard_id = dashboard_id_map[base_dashboard_id]
            existing_cards = {
                card["card"]["name"]: card["id"]
                for card in self.mb.get(
                    "/api/dashboard/{}".format(country_dashboard_id)
                ).json()["ordered_cards"]
            }
            for dashboard_card in self.mb.get(
                "/api/dashboard/{}".format(base_dashboard_id)
            ).json()["ordered_cards"]:
                card = dashboard_card["card"]
                if card["name"] not in existing_cards:
                    del card["id"]
                    card["collection_id"] = collection_id
                    if "query" in card["dataset_query"]:
                        old_database_id = card["dataset_query"]["database"]
                        card["dataset_query"]["query"] = self.transform_query(
                            card["dataset_query"]["query"], old_database_id, database_id
                        )
                    card["dataset_query"]["database"] = database_id
                    card["database_id"] = database_id
                    new_card = self.mb.post("/api/card", json=card).json()
                    new_card_id = new_card["id"]
                else:
                    new_card_id = existing_cards[card["name"]]
                self.mb.post(
                    "/api/dashboard/{}/cards".format(country_dashboard_id),
                    json={
                        "cardId": new_card_id,
                        "col": dashboard_card["col"],
                        "row": dashboard_card["row"],
                        "sizeX": dashboard_card["sizeX"],
                        "sizeY": dashboard_card["sizeY"],
                    },
                )
            if base_dashboard_id == "1":
                card = self.mb.get("/api/card/17").json()
                if card["name"] not in existing_cards:
                    del card["id"]
                    card["collection_id"] = collection_id
                    card["database_id"] = database_id
                    card["dataset_query"]["database"] = database_id
                    new_card = self.mb.post("/api/card", json=card).json()
                    new_card_id = new_card["id"]
                else:
                    new_card_id = existing_cards[card["name"]]
                self.mb.post(
                    "/api/dashboard/{}/cards".format(
                        dashboard_id_map[base_dashboard_id]
                    ),
                    json={
                        "cardId": new_card_id,
                        "col": 10,
                        "row": 4,
                        "sizeX": 4,
                        "sizeY": 4,
                    },
                )

    def set_up_global_permissions(self, global_group_id):
        log.info("Setting up global permissions")
        permissions = self.mb.get("/api/permissions/graph").json()
        collection_permissions = self.mb.get("/api/collection/graph").json()
        if str(self.existing_items["groups"]["ALL USERS"]) in permissions["groups"]:
            permissions["groups"][str(self.existing_items["groups"]["ALL USERS"])][
                "34"
            ] = {"schemas": "none"}
        global_group_permissions = permissions["groups"].setdefault(
            str(global_group_id), {}
        )
        global_group_permissions["34"] = {"schemas": "all"}
        permissions["groups"][str(global_group_id)] = global_group_permissions

        collection_permissions["groups"][str(global_group_id)]["3"] = "read"
        collection_permissions["groups"][str(global_group_id)]["4"] = "read"
        collection_permissions["groups"].setdefault(
            self.existing_items["groups"]["ALL USERS"], {}
        )["3"] = "none"
        collection_permissions["groups"].setdefault(
            self.existing_items["groups"]["ALL USERS"], {}
        )["4"] = "none"

        self.mb.put("/api/permissions/graph", json=permissions)
        self.mb.put("/api/collection/graph", json=collection_permissions)

    def set_up_country_permissions(self, countries, global_group_id):
        log.info("Setting up country permissions")
        permissions = self.mb.get("/api/permissions/graph").json()
        collection_permissions = self.mb.get("/api/collection/graph").json()
        for country_info in countries.values():
            if str(self.existing_items["groups"]["ALL USERS"]) in permissions["groups"]:
                permissions["groups"][str(self.existing_items["groups"]["ALL USERS"])][
                    str(country_info["database"])
                ] = {"schemas": "none"}
            group_permissions = permissions["groups"].setdefault(
                str(country_info["group"]), {}
            )
            group_permissions = {db: {"schemas": "none"} for db in group_permissions}
            group_permissions[str(country_info["database"])] = {"schemas": "all"}
            permissions["groups"][str(country_info["group"])] = group_permissions

            global_group_permissions = permissions["groups"].setdefault(
                str(global_group_id), {}
            )
            global_group_permissions[str(country_info["database"])] = {"schemas": "all"}
            permissions["groups"][str(global_group_id)] = global_group_permissions

            collection_permissions["groups"][str(country_info["group"])][
                country_info["collection"]
            ] = "read"
            collection_permissions["groups"][str(global_group_id)][
                country_info["collection"]
            ] = "read"
            collection_permissions["groups"].setdefault(
                self.existing_items["groups"]["ALL USERS"], {}
            )[country_info["collection"]] = "none"
        self.mb.put("/api/permissions/graph", json=permissions)
        self.mb.put("/api/collection/graph", json=collection_permissions)

    def set_up_ldap(self, countries, global_group_id):
        log.info("Setting up LDAP")
        group_mappings = {
            "cn={},ou=Countries,ou=OiRA_CMS,ou=Sites,dc=osha,dc=europa,dc=eu".format(
                country
            ): [info["group"]]
            for country, info in countries.items()
        }
        group_mappings["cn=ADMIN,ou=OiRA_CMS,ou=Sites,dc=osha,dc=europa,dc=eu"] = [
            global_group_id
        ]
        self.mb.put(
            "/api/ldap/settings",
            json={
                "ldap-enabled": True,
                "ldap-host": self.args.ldap_host,
                "ldap-port": self.args.ldap_port or "389",
                "ldap-bind-dn": self.args.ldap_bind_dn,
                "ldap-password": self.args.ldap_password,
                "ldap-user-base": self.args.ldap_user_base,
                "ldap-user-filter": self.args.ldap_user_filter,
                "ldap-attribute-firstname": self.args.ldap_attribute_firstname,
                "ldap-group-sync": True,
                "ldap-group-base": (
                    "ou=Countries,ou=OiRA_CMS,ou=Sites,dc=osha,dc=europa,dc=eu"
                ),
            },
        )
        self.mb.put("/api/setting/ldap-group-mappings", json={"value": group_mappings})

    @property
    def existing_items(self):
        if not self._existing_items:
            self._existing_items = {}
            self._existing_items["groups"] = {
                group["name"].upper(): group["id"]
                for group in self.mb.get("/api/permissions/group").json()
            }
            self._existing_items["databases"] = {
                db["details"]["dbname"]: db["id"]
                for db in self.mb.get("/api/database").json()
            }
            self._existing_items["collections"] = {
                collection["name"]: collection["id"]
                for collection in self.mb.get("/api/collection").json()
            }
            self._existing_items["dashboards"] = {
                dashboard["name"]: dashboard["id"]
                for dashboard in self.mb.get("/api/dashboard").json()
            }

        return self._existing_items

    def transform_query(self, query, old_database_id, database_id):
        old_table_id = query["source-table"]
        if "breakout" in query:
            for item in query["breakout"]:
                if item[0] == "field-id":
                    item[1] = self.database_mapping[database_id]["fields"][item[1]]
                elif item[1][0] == "field-id":
                    item[1][1] = self.database_mapping[database_id]["fields"][
                        item[1][1]
                    ]
        if "filter" in query:
            if query["filter"][1][0] == "field-id":
                query["filter"][1][1] = self.database_mapping[database_id]["fields"][
                    query["filter"][1][1]
                ]
        query["source-table"] = self.database_mapping[database_id]["tables"][
            old_table_id
        ]
        return query

    @property
    def database_mapping(self):
        if not self._database_mapping:
            self._database_mapping = {}
            base_database = self.mb.get("/api/database/34?include=tables.fields").json()
            for database in self.mb.get("/api/database?include=tables").json():
                if database["id"] != "34":
                    tables = {
                        table["name"]: table["id"] for table in database["tables"]
                    }
                    fields = {
                        table["name"]: {
                            field["name"]: field["id"] for field in table["fields"]
                        }
                        for table in self.mb.get(
                            "/api/database/{}?include=tables.fields".format(
                                database["id"]
                            )
                        ).json()["tables"]
                    }
                    self._database_mapping[database["id"]] = {
                        "tables": {},
                        "fields": {},
                    }
                    for base_table in base_database["tables"]:
                        self._database_mapping[database["id"]]["tables"][
                            base_table["id"]
                        ] = tables[base_table["name"]]
                        for base_field in base_table["fields"]:
                            self._database_mapping[database["id"]]["fields"][
                                base_field["id"]
                            ] = fields[base_table["name"]][base_field["name"]]
        return self._database_mapping


def init_metabase_instance():
    logging.basicConfig(stream=sys.stderr, level=20)
    args = get_metabase_args()

    log.info("Initializing metabase instance")
    initializer = MetabaseInitializer(args)
    initializer()
