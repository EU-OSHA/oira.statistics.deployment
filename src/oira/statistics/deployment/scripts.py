# -*- coding: utf-8 -*-
from .content import AccountsCardFactory
from .content import AssessmentsCardFactory
from .content import QuestionnaireCardFactory
from metabase_api import Metabase_API
from time import sleep
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

        self.set_up_account()
        self.set_up_questionnaire()

        if self.args.countries:
            countries = {
                country.strip(): {} for country in self.args.countries.split(",")
            }

            for country in countries:
                countries[country]["group"] = self.set_up_country_group(country)
                if not self.args.global_statistics:
                    countries[country]["database"] = self.set_up_country_database(
                        country
                    )
                    countries[country]["collection"] = self.set_up_country_collection(
                        country
                    )
                    self.set_up_country_dashboards(
                        country,
                        countries[country]["database"],
                        countries[country]["collection"],
                    )
                    self.set_up_account(
                        country=country,
                        database_id=countries[country]["database"],
                        collection_id=countries[country]["collection"],
                    )
                    self.set_up_questionnaire(
                        country=country,
                        database_id=countries[country]["database"],
                        collection_id=countries[country]["collection"],
                    )

            if not self.args.global_statistics:
                self.set_up_country_permissions(countries, global_group_id)

        if self.args.global_statistics:
            self.set_up_global_permissions(countries, global_group_id)
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
        db_data = {
            "name": db_name,
            "engine": "postgres",
            "details": {
                "dbname": db_name,
                "host": self.args.database_host,
                "port": self.args.database_port,
                "user": self.args.database_user,
                "password": self.args.database_password,
            },
        }
        db_id = self.create("database", db_name, extra_data=db_data)

        self.mb.post("/api/database/{}/sync".format(db_id))

        self._database_mapping = None
        return db_id

    def create(self, obj_type, obj_name, extra_data={}, reuse=True):
        if obj_type == "group":
            url = "/api/permissions/group"
        else:
            url = "/api/{}".format(obj_type)
        obj_data = {"name": obj_name}
        obj_data.update(extra_data)

        obj_exists = obj_name in self.existing_items[obj_type + "s"]
        if obj_exists:
            obj_id = self.existing_items[obj_type + "s"][obj_name]
            if reuse:
                log.info("Keeping existing {} '{}'".format(obj_type, obj_name))
                obj_info = self.mb.put(
                    "{}/{}".format(url, obj_id),
                    json=obj_data,
                ).json()
            else:
                log.info("Deleting existing {} '{}'".format(obj_type, obj_name))
                self.mb.delete("{}/{}".format(url, obj_id))
        if not obj_exists or (obj_exists and not reuse):
            log.info("Adding {} '{}'".format(obj_type, obj_name))
            result = self.mb.post(
                url,
                json=obj_data,
            )
            obj_info = result.json()
            if not result.ok and "duplicate key" in obj_info.get("message", ""):
                # retry, this usually goes away by itself
                log.info('Retrying after "duplicate key" error')
                result = self.mb.post(
                    url,
                    json=obj_data,
                )
                obj_info = result.json()
        obj_id = obj_info["id"]
        return obj_id

    def set_up_global_group(self):
        if "GLOBAL" in self.existing_items["groups"]:
            log.info("Keeping existing global group")
            group_id = self.existing_items["groups"]["GLOBAL"]
        else:
            log.info("Adding global group")
            group_info = self.mb.post(
                "/api/permissions/group",
                json={"name": "global"},
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
                "/api/permissions/group",
                json={"name": country.upper()},
            ).json()
            group_id = group_info["id"]
        return group_id

    def set_up_country_collection(self, country):
        return self.create(
            "collection", country.upper(), extra_data={"color": "#00FF00"}
        )

    def set_up_country_dashboards(self, country, database_id, collection_id):
        log.info("Adding country dashboards")
        dashboard_id_map = {}
        for base_dashboard_id, dashboard_name_tmpl in {
            "1": "Assessments Dashboard ({})",
        }.items():
            dashboard_name = dashboard_name_tmpl.format(country.upper())
            dashboard_data = {
                "collection_id": collection_id,
                "collection_position": int(base_dashboard_id),
            }
            dashboard_id_map[base_dashboard_id] = self.create(
                "dashboard", dashboard_name, extra_data=dashboard_data, reuse=False
            )

        log.info("Adding country dashboard cards")
        for base_dashboard_id in ["1"]:
            country_dashboard_id = dashboard_id_map[base_dashboard_id]
            for dashboard_card in self.mb.get(
                "/api/dashboard/{}".format(base_dashboard_id)
            ).json()["ordered_cards"]:
                card = dashboard_card["card"]
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
                table_id = self.database_mapping[database_id]["tables"][61]
                card_factory = AssessmentsCardFactory(
                    self.database_mapping, database_id, collection_id, table_id
                )
                cards = [
                    (10, 4, card_factory.tools_by_accumulated_assessments),
                    (0, 4, card_factory.tools_by_assessment_completion),
                ]
                for col, row, card in cards:
                    new_card = self.mb.post("/api/card", json=card).json()
                    card_id = new_card["id"]

                    self.mb.post(
                        "/api/dashboard/{}/cards".format(
                            dashboard_id_map[base_dashboard_id]
                        ),
                        json={
                            "cardId": card_id,
                            "col": col,
                            "row": row,
                            "sizeX": 4,
                            "sizeY": 4,
                        },
                    )

    def set_up_global_permissions(self, countries, global_group_id):
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

        permissions["groups"].update(
            {
                country_info["group"]: {"34": {"schemas": "all"}}
                for country_info in countries.values()
            }
        )

        collection_permissions["groups"][str(global_group_id)]["3"] = "read"
        collection_permissions["groups"][str(global_group_id)]["4"] = "read"
        collection_permissions["groups"].setdefault(
            self.existing_items["groups"]["ALL USERS"], {}
        )["3"] = "none"
        collection_permissions["groups"].setdefault(
            self.existing_items["groups"]["ALL USERS"], {}
        )["4"] = "none"

        collection_permissions["groups"].update(
            {
                country_info["group"]: {"3": "read", "4": "read"}
                for country_info in countries.values()
            }
        )

        self.mb.put("/api/permissions/graph", json=permissions)
        self.mb.put("/api/collection/graph", json=collection_permissions)

    def set_up_country_permissions(self, countries, global_group_id):
        log.info("Setting up country permissions")
        permissions = self.mb.get("/api/permissions/graph").json()
        collection_permissions = self.mb.get("/api/collection/graph").json()

        for country_info in countries.values():
            permissions["groups"][str(country_info["group"])] = {
                str(country_info["database"]): {"schemas": "all"}
            }
            permissions["groups"][str(country_info["group"])].update(
                {
                    str(country_other["database"]): {"schemas": "none"}
                    for country_other in countries.values()
                    if country_info["group"] != country_other["group"]
                }
            )

            collection_permissions["groups"][str(country_info["group"])] = {
                str(country_info["collection"]): "read"
            }
            collection_permissions["groups"][str(country_info["group"])].update(
                {
                    str(country_other["collection"]): "none"
                    for country_other in countries.values()
                    if country_info["group"] != country_other["group"]
                }
            )

        permissions["groups"][str(global_group_id)] = {
            str(country_info["database"]): {"schemas": "all"}
            for country_info in countries.values()
        }
        collection_permissions["groups"][str(global_group_id)] = {
            str(country_info["collection"]): "read"
            for country_info in countries.values()
        }

        all_users_id = str(self.existing_items["groups"]["ALL USERS"])
        if all_users_id in permissions["groups"]:
            permissions["groups"][all_users_id].update(
                {
                    str(country_info["database"]): {"schemas": "none"}
                    for country_info in countries.values()
                }
            )
        if all_users_id in collection_permissions["groups"]:
            collection_permissions["groups"][all_users_id].update(
                {
                    country_info["collection"]: "none"
                    for country_info in countries.values()
                }
            )
        self.mb.put("/api/permissions/graph", json=permissions)
        self.mb.put("/api/collection/graph", json=collection_permissions)

    def set_up_account(self, country=None, database_id=34, collection_id=4):
        dashboard_name = "Users Dashboard"
        if country is not None:
            dashboard_name = "{} ({})".format(dashboard_name, country.upper())

        dashboard_data = {
            "collection_id": collection_id,
            "collection_position": 1,
        }
        dashboard_id = self.create(
            "dashboard", dashboard_name, extra_data=dashboard_data, reuse=False
        )

        log.info("Adding accounts cards")
        table_id = self.database_mapping[database_id]["tables"][43]
        card_factory = AccountsCardFactory(
            self.database_mapping, database_id, collection_id, table_id
        )
        cards = [
            card_factory.accumulated_users_per_type,
            card_factory.new_users_per_month,
            card_factory.user_conversions_per_month,
            card_factory.accumulated_registered_users_per_type,
            card_factory.accumulated_number_of_full_users_over_time,
            card_factory.accumulated_number_of_converted_users_over_time,
            card_factory.accumulated_number_of_guest_users_over_time,
        ]
        new_cards = []
        for card in cards:
            new_card = self.mb.post("/api/card", json=card).json()
            card_id = new_card["id"]
            new_cards.append(card_id)

        for idx, card_id in enumerate(new_cards[:4]):
            self.mb.post(
                "/api/dashboard/{}/cards".format(dashboard_id),
                json={
                    "cardId": card_id,
                    "col": idx * 4 % 12,
                    "row": idx // 3 * 4,
                    "sizeX": 4,
                    "sizeY": 4,
                },
            )
        self.mb.post(
            "/api/dashboard/{}/cards".format(dashboard_id),
            json={
                "cardId": new_cards[4],
                "col": 4,
                "row": 4,
                "sizeX": 4,
                "sizeY": 4,
                "series": [
                    {
                        "id": new_cards[5],
                    },
                    {
                        "id": new_cards[6],
                    },
                ],
                "visualization_settings": {
                    "graph.dimensions": ["creation_date"],
                    "graph.metrics": ["count"],
                    "series_settings": {
                        "count": {"color": "#A989C5", "title": "full"},
                        "Accumulated Number Of Converted Users Over Time": {
                            "color": "#98D9D9",
                            "title": "converted",
                        },
                        "Accumulated Number Of Guest Users Over Time": {
                            "color": "#F9D45C",
                            "title": "guest",
                        },
                    },
                    "card.title": "Accumulated Number Of Users Over Time",
                },
            },
        )

    def set_up_questionnaire(self, country=None, database_id=34, collection_id=None):
        if collection_id is None:
            collection_name = "Questionnaire"
            collection_id = self.create(
                "collection",
                collection_name,
                extra_data={
                    "color": "#509EE3",
                },
            )

        dashboard_name = "Questionnaire Dashboard"
        if country is not None:
            dashboard_name = "{} ({})".format(dashboard_name, country.upper())

        dashboard_data = {
            "collection_id": collection_id,
            "collection_position": 3,
        }
        dashboard_id = self.create(
            "dashboard", dashboard_name, extra_data=dashboard_data, reuse=False
        )

        log.info("Adding questionnaire cards")
        table_id = self.database_mapping[database_id]["tables"][44]
        card_factory = QuestionnaireCardFactory(
            self.database_mapping, database_id, collection_id, table_id
        )
        cards = [
            card_factory.number_of_survey_responses,
            card_factory.employees,
            card_factory.conductor,
            card_factory.referer,
            card_factory.workers_participated,
            card_factory.needs_met,
            card_factory.recommend_tool,
        ]
        for idx, card in enumerate(cards):
            new_card = self.mb.post("/api/card", json=card).json()
            card_id = new_card["id"]

            self.mb.post(
                "/api/dashboard/{}/cards".format(dashboard_id),
                json={
                    "cardId": card_id,
                    "col": idx * 4 % 16,
                    "row": idx // 4 * 4,
                    "sizeX": 4,
                    "sizeY": 4,
                },
            )

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
                "ldap-group-base": ("ou=OiRA_CMS,ou=Sites,dc=osha,dc=europa,dc=eu"),
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
            self.mb.post("/api/database/34/sync_schema")
            # XXX check for "sync.util :: FINISHED: Analyze data" in /api/util/logs
            sleep(2)
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
