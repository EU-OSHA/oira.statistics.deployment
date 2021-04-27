from . import config
from .content import AccountsCardFactory
from .content import AssessmentsCardFactory
from .content import QuestionnaireCardFactory
from .content import SectorAssessmentsCardFactory
from .content import ToolsCardFactory
from .metabase import OiraMetabase_API
from pkg_resources import resource_string
from time import sleep
import logging

log = logging.getLogger(__name__)


class MetabaseInitializer(object):

    _total_cols = 16

    def __init__(self, args):
        self.args = args
        api_url = "http://{args.metabase_host}:{args.metabase_port}".format(args=args)
        self.mb = OiraMetabase_API(api_url, args.metabase_user, args.metabase_password)
        self._existing_items = None

    def __call__(self):
        self.mb.put("/api/setting/show-homepage-xrays", json={"value": False})
        self.mb.put("/api/setting/show-homepage-data", json={"value": False})
        for database in self.mb.get("/api/database").json():
            if database["name"] == "Sample Dataset":
                self.mb.delete("/api/database/{}".format(database["id"]))

        self.set_up_start_here_dashboard()

        global_group_id = self.set_up_global_group()

        if self.args.global_statistics:
            global_database_id = self.set_up_database()
            global_collection_id = self.set_up_global_collection()
            self.set_up_account(
                database_id=global_database_id, collection_id=global_collection_id
            )
            self.set_up_assessment(
                database_id=global_database_id, collection_id=global_collection_id
            )
            self.set_up_tool(
                database_id=global_database_id, collection_id=global_collection_id
            )
            self.set_up_questionnaire(
                database_id=global_database_id, collection_id=global_collection_id
            )

        # `countries` has this format:
        # countries = {
        #     "de": {
        #         "group": 23,
        #         "database": 42,
        #         "collection": 69,
        #     },
        #     ...
        # }
        countries = {}
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
                    self.set_up_tool(
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
            else:
                self.set_up_countries_overview(global_database_id, global_collection_id)

        # `sectors` has this format:
        # sectors = {
        #     "Cleaning": {
        #         "collection": 69,
        #         "cards": {
        #             "accumulated_assessments": {
        #                 "id": 42,
        #                 ...
        #             },
        #             ...
        #         },
        #     },
        #     ...
        # }
        sectors = {}
        if self.args.global_statistics:
            sectors = self.set_up_sectors(global_database_id, global_collection_id)
            self.set_up_global_permissions(
                global_database_id,
                countries,
                sectors,
                global_group_id,
                global_collection_id,
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
        while not [
            entry["msg"]
            for entry in self.mb.get("/api/util/logs").json()
            if "FINISHED: Sync postgres Database {} '{}'".format(db_id, db_name)
            in entry["msg"]
        ]:
            log.info("Waiting for database sync to finish...")
            sleep(1)

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

    def set_up_start_here_dashboard(self):
        intro_text = resource_string(__package__, "resources/intro_text.md").decode(
            "utf-8"
        )
        dashboard_data = {
            "description": "Introduction to the statistics",
            "collection_position": 1,
            "collection_id": None,
        }
        dashboard_id = self.create(
            "dashboard", "-> Start here", extra_data=dashboard_data, reuse=False
        )

        intro_card = {
            "card_id": None,
            "parameter_mappings": [],
            "series": [],
            "visualization_settings": {
                "virtual_card": {
                    "name": None,
                    "display": "text",
                },
                "text": intro_text,
            },
            "dashboard_id": 3,
            "sizeX": 8,
            "sizeY": 9,
            "col": 0,
            "row": 0,
        }
        self.mb.post(
            "/api/dashboard/{}/cards".format(dashboard_id),
            json=intro_card,
        )

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
        self,
        global_database_id,
        countries,
        sectors,
        global_group_id,
        global_collection_id,
    ):
        log.info("Setting up global permissions")
        all_users_id = str(self.existing_items["groups"]["All Users"])

        # Database permissions
        permissions = self.mb.get("/api/permissions/graph").json()
        permissions["groups"].update(
            dict(
                {
                    str(all_users_id): {
                        str(global_database_id): {"schemas": "none"},
                    },
                    str(global_group_id): {
                        str(global_database_id): {"schemas": "all"},
                    },
                },
                **{
                    str(country_info["group"]): {
                        str(global_database_id): {"schemas": "all"},
                    }
                    for country_info in countries.values()
                }
            )
        )

        self.mb.put("/api/permissions/graph", json=permissions)

        # Collection permissions
        collection_permissions = self.mb.get("/api/collection/graph").json()
        collection_permissions["groups"].update(
            dict(
                {
                    str(all_users_id): dict(
                        {
                            str(global_collection_id): "none",
                        },
                        **{
                            str(sector["collection"]): "none"
                            for sector in sectors.values()
                        }
                    ),
                    str(global_group_id): dict(
                        {
                            str(global_collection_id): "read",
                        },
                        **{
                            str(sector["collection"]): "read"
                            for sector in sectors.values()
                        }
                    ),
                },
                **{
                    str(country_info["group"]): dict(
                        {
                            str(global_collection_id): "read",
                        },
                        **(
                            {
                                str(sector["collection"]): "read"
                                for sector in sectors.values()
                            }
                            if country_id == "eu"
                            else {}
                        )
                    )
                    for country_id, country_info in countries.items()
                }
            )
        )

        self.mb.put("/api/collection/graph", json=collection_permissions)

    def set_up_country_permissions(self, countries, global_group_id):
        log.info("Setting up country permissions")
        all_users_id = str(self.existing_items["groups"]["All Users"])

        # Database permissions
        permissions = self.mb.get("/api/permissions/graph").json()
        permissions["groups"].update(
            dict(
                {
                    str(all_users_id): {
                        str(country_info["database"]): {"schemas": "none"}
                        for country_info in countries.values()
                    },
                    str(global_group_id): {
                        str(country_info["database"]): {"schemas": "all"}
                        for country_info in countries.values()
                    },
                },
                **{
                    str(country_info["group"]): dict(
                        {
                            str(country_info["database"]): {"schemas": "all"},
                        },
                        **{
                            str(country_other["database"]): {"schemas": "none"}
                            for country_other in countries.values()
                            if country_info["group"] != country_other["group"]
                        }
                    )
                    for country_info in countries.values()
                }
            )
        )
        self.mb.put("/api/permissions/graph", json=permissions)

        # Collection permissions
        collection_permissions = self.mb.get("/api/collection/graph").json()
        collection_permissions["groups"].update(
            dict(
                {
                    str(all_users_id): {
                        str(country_info["collection"]): "none"
                        for country_info in countries.values()
                    },
                    str(global_group_id): {
                        str(country_info["collection"]): "read"
                        for country_info in countries.values()
                    },
                },
                **{
                    str(country_info["group"]): dict(
                        {
                            str(country_info["collection"]): "read",
                        },
                        **{
                            str(country_other["collection"]): "none"
                            for country_other in countries.values()
                            if country_info["group"] != country_other["group"]
                        }
                    )
                    for country_info in countries.values()
                }
            )
        )

        self.mb.put("/api/collection/graph", json=collection_permissions)

    def set_up_dashboard(
        self,
        dashboard_name=None,
        cards=[],
        country=None,
        database_id=None,
        collection_id=None,
        collection_position=None,
    ):
        if country is not None:
            dashboard_name = "{} ({})".format(dashboard_name, country.upper())

        dashboard_data = {
            "collection_id": collection_id,
            "collection_position": collection_position or 1,
        }
        dashboard_id = self.create(
            "dashboard", dashboard_name, extra_data=dashboard_data, reuse=False
        )

        log.info("Adding {} cards".format(dashboard_name))

        col = 0
        row = 0
        row_height = 4
        for card in cards:
            if "id" in card:
                card_id = card["id"]
            else:
                card_id = self.create("card", card["name"], extra_data=card)
            width = min(card.get("width", 4), self._total_cols)
            height = card.get("height", 4)
            if width + col > self._total_cols:
                col = 0
                row += row_height
                row_height = height
            else:
                row_height = max(height, row_height)
            self.mb.post(
                "/api/dashboard/{}/cards".format(dashboard_id),
                json={
                    "cardId": card_id,
                    "col": col,
                    "row": row,
                    "sizeX": width,
                    "sizeY": height,
                },
            )

            col += width
        return dashboard_id

    def set_up_account(self, country=None, database_id=34, collection_id=4):
        card_factory = AccountsCardFactory(
            self.mb, database_id, collection_id, country=country
        )
        cards = [
            card_factory.accumulated_users_per_type,
            card_factory.new_users_per_month,
            card_factory.user_conversions_per_month,
            card_factory.accumulated_registered_users_per_type,
            card_factory.accumulated_registered_users_over_time,
        ]
        self.set_up_dashboard(
            dashboard_name="Users Dashboard",
            cards=cards,
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=1,
        )

    def set_up_assessment(self, country=None, database_id=34, collection_id=3):
        assessments_card_factory = AssessmentsCardFactory(
            self.mb, database_id, collection_id, country=country
        )
        cards = [
            assessments_card_factory.accumulated_assessments,
            assessments_card_factory.new_assessments_per_month,
            assessments_card_factory.completion_of_assessments,
            assessments_card_factory.accumulated_assessments_over_time,
            assessments_card_factory.top_ten_tools_by_number_of_assessments,
        ]
        if country is not None:
            cards.extend(
                [
                    assessments_card_factory.tools_by_accumulated_assessments,
                    assessments_card_factory.tools_by_assessment_completion,
                ]
            )
        else:
            cards.extend(
                [
                    assessments_card_factory.accumulated_assessments_per_country,
                ]
            )
        self.set_up_dashboard(
            dashboard_name="Assessments Dashboard",
            cards=cards,
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=2,
        )

    def set_up_tool(self, country=None, database_id=34, collection_id=None):
        tools_card_factory = ToolsCardFactory(
            self.mb, database_id, collection_id, country=country
        )
        cards = [
            tools_card_factory.top_tools_by_number_of_users,
        ]
        self.set_up_dashboard(
            dashboard_name="Tools Dashboard",
            cards=cards,
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=3,
        )

    def set_up_questionnaire(self, country=None, database_id=34, collection_id=None):
        card_factory = QuestionnaireCardFactory(
            self.mb, database_id, collection_id, country=country
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
        self.set_up_dashboard(
            dashboard_name="Questionnaire Dashboard",
            cards=cards,
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=4,
        )

    def set_up_sectors(self, global_database_id, global_collection_id):
        sectors = {}
        for sector_name in config.sectors:
            log.info("Adding sector {}".format(sector_name))
            sectors[sector_name] = {}
            collection_id = self.create(
                "collection",
                "Sector: {}".format(sector_name),
                extra_data={
                    "color": "#509EE3",
                },
            )
            sectors[sector_name]["collection"] = collection_id
            card_factory = SectorAssessmentsCardFactory(
                sector_name, self.mb, global_database_id, collection_id
            )
            cards = {
                "accumulated_assessments": card_factory.accumulated_assessments,
                "new_assessments_per_month": card_factory.new_assessments_per_month,
                "completion_of_assessments": card_factory.completion_of_assessments,
                "accumulated_assessments_over_time": card_factory.accumulated_assessments_over_time,
                "top_ten_tools_by_number_of_assessments": card_factory.top_ten_tools_by_number_of_assessments,
            }
            for card_token, card in cards.items():
                cards[card_token]["id"] = self.create(
                    "card", card["name"], extra_data=card
                )

            sectors[sector_name]["cards"] = cards
            self.set_up_dashboard(
                dashboard_name="Assessments ({})".format(sector_name),
                cards=cards.values(),
                database_id=global_database_id,
                collection_id=collection_id,
                collection_position=1,
            )

        overview_dashboard_id = self.set_up_dashboard(
            dashboard_name="Sectors Overview Dashboard",
            database_id=global_database_id,
            collection_id=global_collection_id,
            collection_position=5,
        )
        overview_cards = [
            {
                "token": "accumulated_assessments_over_time",
                "base_title": "Accumulated Assessments Over Time",
                "graph.dimensions": ["start_date"],
            },
            {
                "token": "completion_of_assessments",
                "base_title": "Completion of Assessments",
                "graph.dimensions": ["completion", "count"],
            },
        ]
        for idx, card_info in enumerate(overview_cards):
            combined_card = None
            for sector_name, sector_info in sectors.items():
                next_card = sector_info["cards"][card_info["token"]]
                if combined_card is None:
                    combined_card = {
                        "cardId": next_card["id"],
                        "col": 0,
                        "row": idx * 8,
                        "sizeX": self._total_cols,
                        "sizeY": 8,
                        "series": [],
                        "visualization_settings": {
                            "graph.dimensions": card_info["graph.dimensions"],
                            "graph.metrics": ["count"],
                            "series_settings": {
                                "count": {"color": "#A989C5", "title": sector_name},
                            },
                            "card.title": "{} Per Sector".format(
                                card_info["base_title"]
                            ),
                        },
                    }
                else:
                    combined_card["series"].append(
                        {
                            "id": next_card["id"],
                        }
                    )
                    combined_card["visualization_settings"]["series_settings"][
                        "{} ({})".format(card_info["base_title"], sector_name)
                    ] = {
                        "title": sector_name,
                    }
            self.mb.post(
                "/api/dashboard/{}/cards".format(overview_dashboard_id),
                json=combined_card,
            )
        return sectors

    def set_up_countries_overview(self, global_database_id, global_collection_id):
        overview_dashboard_countryid = self.set_up_dashboard(
            dashboard_name="Countries Overview Dashboard",
            database_id=global_database_id,
            collection_id=global_collection_id,
            collection_position=6,
        )

        card_factory = AssessmentsCardFactory(
            self.mb, global_database_id, global_collection_id
        )
        card = card_factory.top_assessments_by_country
        card_id = self.create("card", card["name"], extra_data=card)
        self.mb.post(
            "/api/dashboard/{}/cards".format(overview_dashboard_countryid),
            json={
                "cardId": card_id,
                "col": 0,
                "row": 0,
                "sizeX": 18,
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
            self._existing_items["cards"] = {
                card["name"]: card["id"] for card in self.mb.get("/api/card").json()
            }

        return self._existing_items
