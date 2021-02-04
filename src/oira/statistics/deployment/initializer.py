from .content import AccountsCardFactory
from .content import AssessmentsCardFactory
from .content import QuestionnaireCardFactory
from .metabase import OiraMetabase_API
import logging

log = logging.getLogger(__name__)


class MetabaseInitializer(object):
    def __init__(self, args):
        self.args = args
        api_url = "http://{args.metabase_host}:{args.metabase_port}".format(args=args)
        self.mb = OiraMetabase_API(api_url, args.metabase_user, args.metabase_password)
        self._existing_items = None

    def __call__(self):
        countries = {}

        self.mb.put("/api/setting/show-homepage-xrays", json={"value": False})
        self.mb.put("/api/setting/show-homepage-data", json={"value": False})

        global_group_id = self.set_up_global_group()

        global_database_id = self.set_up_database()
        global_collection_id = self.set_up_global_collection()
        self.set_up_account(
            database_id=global_database_id, collection_id=global_collection_id
        )
        self.set_up_assessment(
            database_id=global_database_id, collection_id=global_collection_id
        )
        self.set_up_questionnaire(
            database_id=global_database_id, collection_id=global_collection_id
        )

        if self.args.countries:
            countries = {
                country.strip(): {} for country in self.args.countries.split(",")
            }

            for country in countries:
                countries[country]["group"] = self.set_up_country_group(country)
                if not self.args.global_statistics:
                    countries[country]["database"] = self.set_up_database(
                        country=country
                    )
                    countries[country]["collection"] = self.set_up_country_collection(
                        country
                    )
                    self.set_up_account(
                        country=country,
                        database_id=countries[country]["database"],
                        collection_id=countries[country]["collection"],
                    )
                    self.set_up_assessment(
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
            self.set_up_global_permissions(
                global_database_id, countries, global_group_id, global_collection_id
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

        log.info("Done initializing metabase instance")

    def set_up_database(self, country=None):
        if country is None:
            db_name = "statistics_global"
            for database in self.mb.get("/api/database").json():
                if database["name"] == "Sample Dataset":
                    self.mb.delete("/api/database/{}".format(database["id"]))
        else:
            db_name = self.args.database_pattern_statistics.format(
                country=country.lower()
            )
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
                if extra_data:
                    obj_info = self.mb.put(
                        "{}/{}".format(url, obj_id),
                        json=obj_data,
                    ).json()
                else:
                    obj_info = self.mb.get("{}/{}".format(url, obj_id)).json()
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
        return self.create("group", "global")

    def set_up_country_group(self, country):
        return self.create("group", country.upper())

    def set_up_global_collection(self):
        return self.create("collection", "-Global-", extra_data={"color": "#0000FF"})

    def set_up_country_collection(self, country):
        return self.create(
            "collection", country.upper(), extra_data={"color": "#00FF00"}
        )

    def set_up_global_permissions(
        self, global_database_id, countries, global_group_id, global_collection_id
    ):
        log.info("Setting up global permissions")
        permissions = self.mb.get("/api/permissions/graph").json()
        collection_permissions = self.mb.get("/api/collection/graph").json()
        all_users_id = str(self.existing_items["groups"]["All Users"])
        if str(all_users_id) in permissions["groups"]:
            permissions["groups"][str(all_users_id)][str(global_database_id)] = {
                "schemas": "none"
            }
        global_group_permissions = permissions["groups"].setdefault(
            str(global_group_id), {}
        )
        global_group_permissions[str(global_database_id)] = {"schemas": "all"}
        permissions["groups"][str(global_group_id)] = global_group_permissions

        permissions["groups"].update(
            {
                country_info["group"]: {str(global_database_id): {"schemas": "all"}}
                for country_info in countries.values()
            }
        )

        collection_permissions["groups"][str(global_group_id)][
            str(global_collection_id)
        ] = "read"
        collection_permissions["groups"].setdefault(all_users_id, {})[
            str(global_collection_id)
        ] = "none"

        collection_permissions["groups"].update(
            {
                country_info["group"]: {str(global_collection_id): "read"}
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

        all_users_id = str(self.existing_items["groups"]["All Users"])
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
                    str(country_info["collection"]): "none"
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
        card_factory = AccountsCardFactory(self.mb, database_id, collection_id)
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

    def set_up_assessment(self, country=None, database_id=34, collection_id=3):
        dashboard_name = "Assessments Dashboard"
        if country is not None:
            dashboard_name = "{} ({})".format(dashboard_name, country.upper())

        dashboard_data = {
            "collection_id": collection_id,
            "collection_position": 2,
        }
        dashboard_id = self.create(
            "dashboard", dashboard_name, extra_data=dashboard_data, reuse=False
        )

        log.info("Adding assessments cards")
        card_factory = AssessmentsCardFactory(self.mb, database_id, collection_id)
        cards = [
            card_factory.accumulated_assessments,
            card_factory.new_assessments_per_month,
            card_factory.completion_of_assessments,
            card_factory.accumulated_assessments_over_time,
        ]
        if country is not None:
            cards.extend(
                [
                    card_factory.tools_by_accumulated_assessments,
                    card_factory.tools_by_assessment_completion,
                ]
            )
        else:
            cards.extend(
                [
                    card_factory.accumulated_assessments_per_country,
                ]
            )
        new_cards = []
        for card in cards:
            new_card = self.mb.post("/api/card", json=card).json()
            card_id = new_card["id"]
            new_cards.append(card_id)

        for idx, card_id in enumerate(new_cards):
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
        card_factory = QuestionnaireCardFactory(self.mb, database_id, collection_id)
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
                group["name"]: group["id"]
                for group in self.mb.get("/api/permissions/group").json()
            }
            self._existing_items["databases"] = {
                db["name"]: db["id"] for db in self.mb.get("/api/database").json()
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
