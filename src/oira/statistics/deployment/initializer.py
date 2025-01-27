from . import config
from .content import CardFactory
from .content import SectorCardFactory
from .metabase import OiraMetabase_API
from pkg_resources import resource_string
from time import sleep

import logging


log = logging.getLogger(__name__)


class MetabaseInitializer(object):
    _total_cols = 16

    def __init__(self, args):
        self.args = args
        self.engine = args.database_engine
        api_url = "http://{args.metabase_host}:{args.metabase_port}".format(args=args)
        self.mb = OiraMetabase_API(api_url, args.metabase_user, args.metabase_password)
        self._existing_items = None

    def __call__(self):
        self.mb.put("/api/setting/show-homepage-xrays", json={"value": False})
        self.mb.put("/api/setting/show-homepage-data", json={"value": False})
        for database in self.mb.get("/api/database").json()["data"]:
            if database["name"] == "Sample Dataset":
                self.mb.delete("/api/database/{}".format(database["id"]))

        self.set_up_start_here_dashboard()

        global_group_id = self.set_up_global_group()

        if self.args.global_statistics:
            global_database_id = self.set_up_database(engine=self.engine)
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
                        country=country, engine=self.engine
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
                    if country.upper() == "FR":
                        self.set_up_inrs(
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
            users = self.mb.get("/api/user").json()["data"]
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

    def set_up_database(self, country=None, engine="postgres"):
        if country is None:
            db_name = "statistics_global"
        else:
            db_name = self.args.database_pattern_statistics.format(
                country=country.lower()
            )
        details = {
            "dbname": db_name,
        }
        if engine == "sqlite":
            details["db"] = f"/home/oira/statistics/var/{db_name}.sqlite"
        else:
            details.update(
                {
                    "host": self.args.database_host,
                    "port": self.args.database_port,
                    "user": self.args.database_user,
                    "password": self.args.database_password,
                }
            )
        db_data = {
            "name": db_name,
            "engine": engine,
            "details": details,
        }
        db_id = self.create("database", db_name, extra_data=db_data)

        self.mb.post("/api/database/{}/sync".format(db_id))
        while not [
            entry["msg"]
            for entry in self.mb.get("/api/util/logs").json()
            if "FINISHED: Sync {} Database {} '{}'".format(engine, db_id, db_name)
            in entry["msg"]
        ]:
            log.info("Waiting for database sync to finish...")
            sleep(1)

        db_info = self.mb.get(
            "/api/database/{}/metadata?include_hidden=true".format(db_id)
        ).json()
        for table_info in db_info["tables"]:
            self.mb.post(
                "/api/table/{}/rescan_values".format(table_info["id"]),
                json={},
            )
            self.mb.put(
                "/api/table/{}".format(table_info["id"]),
                json={"field_order": "database"},
            )
            for field_info in table_info["fields"]:
                if (
                    table_info["name"] in ["assessment", "company"]
                    and field_info["name"] == "id"
                    or (country is not None and field_info["name"] == "country")
                ):
                    self.mb.put(
                        "/api/field/{}".format(field_info["id"]),
                        json={"visibility_type": "sensitive"},
                    )

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
            "dashboard", "-> Start here", extra_data=dashboard_data
        )

        existing_cards = self.mb.get("/api/dashboard/{}".format(dashboard_id)).json()[
            "ordered_cards"
        ]
        if len(existing_cards) > 0:
            card_id = existing_cards[0]["id"]
        else:
            new_card = self.mb.post(
                "/api/dashboard/{}/cards".format(dashboard_id),
                json={"cardId": None},
            ).json()
            card_id = new_card["id"]

        intro_card = {
            "id": card_id,
            "card_id": None,
            "parameter_mappings": [],
            "series": [],
            "visualization_settings": {
                "virtual_card": {
                    "archived": False,
                    "dataset_query": {},
                    "name": None,
                    "display": "text",
                    "visualization_settings": {},
                },
                "text": intro_text,
            },
            "dashboard_id": dashboard_id,
            "size_x": 8,
            "size_y": 9,
            "col": 0,
            "row": 0,
        }
        self.mb.put(
            "/api/dashboard/{}/cards".format(dashboard_id),
            json={"cards": [intro_card]},
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
                        str(global_database_id): {"data": {"schemas": "none"}},
                    },
                    str(global_group_id): {
                        str(global_database_id): {"data": {"schemas": "all"}},
                    },
                },
                **{
                    str(country_info["group"]): {
                        str(global_database_id): {"data": {"schemas": "all"}},
                    }
                    for country_info in countries.values()
                },
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
                        },
                    ),
                    str(global_group_id): dict(
                        {
                            str(global_collection_id): "read",
                        },
                        **{
                            str(sector["collection"]): "read"
                            for sector in sectors.values()
                        },
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
                        ),
                    )
                    for country_id, country_info in countries.items()
                },
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
                        str(country_info["database"]): {"data": {"schemas": "none"}}
                        for country_info in countries.values()
                    },
                    str(global_group_id): {
                        str(country_info["database"]): {"data": {"schemas": "all"}}
                        for country_info in countries.values()
                    },
                },
                **{
                    str(country_info["group"]): dict(
                        {
                            str(country_info["database"]): {"data": {"schemas": "all"}},
                        },
                        **{
                            str(country_other["database"]): {
                                "data": {"schemas": "none"}
                            }
                            for country_other in countries.values()
                            if country_info["group"] != country_other["group"]
                        },
                    )
                    for country_info in countries.values()
                },
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
                        },
                    )
                    for country_info in countries.values()
                },
            )
        )

        self.mb.put("/api/collection/graph", json=collection_permissions)

    def set_up_dashboard(
        self,
        dashboard_name=None,
        description=None,
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
            "dashboard", dashboard_name, extra_data=dashboard_data
        )

        log.info("Adding {} cards".format(dashboard_name))

        col = 0
        row = 0
        row_height = 4
        ordered_cards = self.mb.get("/api/dashboard/{}".format(dashboard_id)).json()[
            "ordered_cards"
        ]
        cards_is = {card["card_id"]: card["id"] for card in ordered_cards}
        cards_add = []
        cards_update = []
        cards_should = []
        # TODO: delete description if it is None but a card exists
        if description is not None:
            description_card = next(
                (card for card in ordered_cards if card["card_id"] is None), None
            )
            if not description_card:
                description_card = self.mb.post(
                    "/api/dashboard/{}/cards".format(dashboard_id),
                    json={"cardId": None},
                ).json()
            dashcard = {
                "id": description_card["id"],
                "card_id": None,
                "parameter_mappings": [],
                "series": [],
                "visualization_settings": {
                    "virtual_card": {
                        "archived": False,
                        "dataset_query": {},
                        "name": None,
                        "display": "text",
                        "visualization_settings": {},
                    },
                    "text": description,
                },
                "dashboard_id": dashboard_id,
                "size_x": 4,
                "size_y": 4,
                "col": col,
                "row": row,
            }
            col += 4
            row += 4
            cards_should.append(dashcard["card_id"])
            cards_update.append(dashcard)

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
            dashcard = {
                "col": col,
                "row": row,
                "size_x": width,
                "size_y": height,
            }
            cards_should.append(card_id)
            if card_id not in cards_is:
                dashcard["cardId"] = card_id
                cards_add.append(dashcard)
            else:
                dashcard["card_id"] = card_id
                dashcard["id"] = cards_is[card_id]
                cards_update.append(dashcard)

            col += width

        cards_delete = [
            dashcard_id
            for card_id, dashcard_id in cards_is.items()
            if card_id not in cards_should
        ]
        for dashcard_id in cards_delete:
            self.mb.delete(
                "/api/dashboard/{}/cards?dashcardId={}".format(
                    dashboard_id, dashcard_id
                )
            )
        for dashcard in cards_add:
            self.mb.post(
                "/api/dashboard/{}/cards".format(dashboard_id),
                json=dashcard,
            )
        if cards_update:
            self.mb.put(
                "/api/dashboard/{}/cards".format(dashboard_id),
                json={"cards": cards_update},
            )
        return dashboard_id

    def set_up_account(self, country=None, database_id=34, collection_id=4):
        card_factory = CardFactory(self.mb, database_id, collection_id, country=country)
        cards = [
            card_factory.accumulated_users_per_type,
            card_factory.new_users_per_month,
            card_factory.user_conversions_per_month,
            card_factory.accumulated_registered_users_per_type,
            card_factory.accumulated_registered_users_over_time,
            card_factory.newsletter_subscriptions,
        ]
        self.set_up_dashboard(
            dashboard_name="Users Dashboard",
            description=(
                "## About this dashboard\n\n"
                "Shows all data in relation to users (registered users and guest users)"
                "\n\n"
                "Information on guest users before January 2020 is not available."
            ),
            cards=cards,
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=1,
        )

    def set_up_assessment(self, country=None, database_id=34, collection_id=3):
        assessments_card_factory = CardFactory(
            self.mb, database_id, collection_id, country=country
        )
        cards = [
            assessments_card_factory.accumulated_assessments,
            assessments_card_factory.new_assessments_per_month,
            assessments_card_factory.completion_of_assessments,
            assessments_card_factory.accumulated_assessments_over_time,
        ]
        if country is not None:
            cards.extend(
                [
                    assessments_card_factory.tools_by_assessment_completion,
                ]
            )
        description = (
            "## About this dashboard\n\nThis dashboard shows data in relation to the "
            "assessments done with the tools in {}, such as new "
            "assessments per month, accumulated assessments, qualitative indicators "
            "(how many of the questions in a tool have been answered) as well as the "
            "number of assessments by tool. Remember to use the filter options (upper "
            "right hand corner) if you want to have more detailed information about a "
            "tool (e.g. for Accumulated Assessments Over Time you can filter by "
            "tool/sector and by completion percentage).\n\n"
            "In order to see the tools that are accumulated under “others” in the "
            "cards that include tools information, you need to click on the table icon "
            "at the bottom centre of the screen.\n\n"
            "![Switch between table and chart]"
            "(/statistics/images/switch_table_graph.png)".format(
                "the current country" if country is not None else "OiRA"
            )
        )
        self.set_up_dashboard(
            dashboard_name="Assessments Dashboard",
            description=description,
            cards=cards,
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=2,
        )

    def set_up_tool(self, country=None, database_id=34, collection_id=None):
        tools_card_factory = CardFactory(
            self.mb, database_id, collection_id, country=country
        )
        cards = [
            tools_card_factory.top_tools_by_number_of_users,
            tools_card_factory.number_of_users_and_assessments_by_tool,
        ]
        description = (
            "## About this dashboard\n\n"
            "Compares tools in {} to each other using the metrics “started "
            "assessments” and “number of users who have used the tool”. "
            "In order to see the tools that are accumulated under “others” you can "
            "click on the table icon at the bottom centre of the screen.\n\n"
            "![Switch between table and chart]"
            "(/statistics/images/switch_table_graph.png)\n\n"
            "The *number of users by yearly average* is used as a rough measure of how "
            "popular a tool stays over time. Instead of taking the total number of "
            "users, the time a tool has been available is taken into account. "
            "This way a tool that was once popular but has fallen into disuse moves "
            "down in the ranking as time passes. Please note that this can mean that a "
            "tool with more total users can end up lower in the ranking than one with "
            "fewer total users. The reason is that the number of years "
            "is rounded up to the next whole number. E.g. a tool with 12 total "
            "users that has been online for just over a year will be treated as having "
            "run for two years and thus have 6 users per year, while a tool with 10 "
            "total users that has been online for just under a year will have 10 users "
            "per year.".format("the current country" if country is not None else "OiRA")
        )
        self.set_up_dashboard(
            dashboard_name="Tools Dashboard",
            description=description,
            cards=cards,
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=3,
        )

    def set_up_questionnaire(self, country=None, database_id=34, collection_id=None):
        card_factory = CardFactory(self.mb, database_id, collection_id, country=country)
        cards = [
            card_factory.number_of_survey_responses,
            card_factory.employees,
            card_factory.conductor,
            card_factory.referer if country != "fr" else card_factory.referer_france,
            card_factory.workers_participated,
            card_factory.needs_met,
            card_factory.recommend_tool,
        ]
        description = (
            "## About this dashboard\n\n"
            "Gives information about the answers to the voluntary questionnaire in the "
            "OiRA tool. This includes e.g. number of employees in the company, needs "
            "were met by the tool, etc. From April 2021 on this data can be filtered "
            "for certain time periods. Before April 2021 this information is not "
            "available.\n\n"
            "By using the “Tool Path” filter you can also filter the information from "
            "the questionnaire for different tools."
        )
        self.set_up_dashboard(
            dashboard_name="Questionnaire Dashboard",
            description=description,
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
            card_factory = SectorCardFactory(
                sector_name, self.mb, global_database_id, collection_id
            )
            cards = {
                "accumulated_assessments": card_factory.accumulated_assessments,
                "new_assessments_per_month": card_factory.new_assessments_per_month,
                "completion_of_assessments": card_factory.completion_of_assessments,
                "top_tools_by_number_of_assessments": card_factory.top_tools_by_number_of_assessments,
                "accumulated_assessments_over_time": card_factory.accumulated_assessments_over_time,
                "accumulated_number_of_users": card_factory.accumulated_number_of_users,
            }
            for card_token, card in cards.items():
                cards[card_token]["id"] = self.create(
                    "card", card["name"], extra_data=card
                )

            sectors[sector_name]["cards"] = cards
            sector_dashboard_id = self.set_up_dashboard(
                dashboard_name="Assessments ({})".format(sector_name),
                cards=list(cards.values())[:-2],
                database_id=global_database_id,
                collection_id=collection_id,
                collection_position=1,
            )
            self.mb.post(
                "/api/dashboard/{}/cards".format(sector_dashboard_id),
                json={
                    "cardId": cards["accumulated_assessments_over_time"]["id"],
                    "col": 4,
                    "row": 4,
                    "size_x": 8,
                    "size_y": 4,
                    "series": [
                        {
                            "id": cards["accumulated_number_of_users"]["id"],
                            "display": "line",
                        },
                    ],
                    "visualization_settings": {
                        "graph.show_trendline": False,
                        "graph.y_axis.title_text": "Number of Assessments/Users",
                        "graph.show_values": True,
                        "graph.x_axis.title_text": "Date",
                        "card.title": "Accumulated Assessments And Users ({})".format(
                            sector_name
                        ),
                        "series_settings": {
                            "count": {
                                "display": "line",
                                "title": "Accumulated Assessments",
                            },
                            "Accumulated Users Over Time ({})".format(sector_name): {
                                "title": "Accumulated Users"
                            },
                        },
                        "graph.label_value_frequency": "fit",
                        "graph.metrics": ["count"],
                        "graph.y_axis.auto_range": True,
                        "graph.y_axis.auto_split": False,
                        "graph.dimensions": ["start_date"],
                        "stackable.stack_type": None,
                    },
                },
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
                        "size_x": self._total_cols,
                        "size_y": 8,
                        "series": [],
                        "visualization_settings": {
                            "graph.dimensions": card_info["graph.dimensions"],
                            "graph.metrics": ["count"],
                            "series_settings": {
                                "count": {
                                    "color": "#A989C5",
                                    "display": "line",
                                    "title": sector_name,
                                },
                            },
                            "card.title": "{} Per Sector".format(
                                card_info["base_title"]
                            ),
                            "graph.show_trendline": False,
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

    def set_up_inrs(self, country=None, database_id=34, collection_id=3):
        card_factory = CardFactory(self.mb, database_id, collection_id, country=country)
        cards = {
            token: getattr(card_factory, token)
            for token in [
                "oiras_poissonerie_sessions_cumulees",
                "oiras_boulangerie_sessions_cumulees",
                "oiras_boucherie_charcuterie_sessions_cumulees",
                "oiras_commerce_alimentaire_de_proximite_sessions_cumulees",
            ]
        }
        for card_token, card in cards.items():
            cards[card_token]["id"] = self.create("card", card["name"], extra_data=card)

        dashboard_id = self.set_up_dashboard(
            dashboard_name="INRS",
            cards=list(cards.values()),
            country=country,
            database_id=database_id,
            collection_id=collection_id,
            collection_position=5,
        )
        combined_card = None
        for idx, card in enumerate(cards.values()):
            if combined_card is None:
                combined_card = {
                    "cardId": card["id"],
                    "col": 0,
                    "row": 4,
                    "size_x": self._total_cols,
                    "size_y": 8,
                    "series": [],
                    "visualization_settings": {
                        "graph.dimensions": ["start_date"],
                        "graph.metrics": ["count"],
                        "series_settings": {
                            "count": {
                                "color": "#A989C5",
                                "display": "line",
                                "title": card["name"],
                            },
                        },
                        "graph.show_trendline": False,
                    },
                }
            else:
                combined_card["series"].append(
                    {
                        "id": card["id"],
                    }
                )
        self.mb.post(
            "/api/dashboard/{}/cards".format(dashboard_id),
            json=combined_card,
        )

    def set_up_countries_overview(self, global_database_id, global_collection_id):
        overview_dashboard_countryid = self.set_up_dashboard(
            dashboard_name="Countries Overview Dashboard",
            database_id=global_database_id,
            collection_id=global_collection_id,
            collection_position=6,
        )

        card_factory = CardFactory(self.mb, global_database_id, global_collection_id)
        card = card_factory.top_assessments_by_country
        card_id = self.create("card", card["name"], extra_data=card)
        self.mb.post(
            "/api/dashboard/{}/cards".format(overview_dashboard_countryid),
            json={
                "cardId": card_id,
                "col": 0,
                "row": 0,
                "size_x": 18,
                "size_y": 4,
            },
        )
        card = card_factory.accumulated_assessments_per_country
        card_id = self.create("card", card["name"], extra_data=card)
        self.mb.post(
            "/api/dashboard/{}/cards".format(overview_dashboard_countryid),
            json={
                "cardId": card_id,
                "col": 0,
                "row": 4,
                "size_x": 18,
                "size_y": 4,
            },
        )

        card = card_factory.registered_users_per_country
        card_id = self.create("card", card["name"], extra_data=card)
        self.mb.post(
            "/api/dashboard/{}/cards".format(overview_dashboard_countryid),
            json={
                "cardId": card_id,
                "col": 0,
                "row": 8,
                "size_x": 18,
                "size_y": 4,
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
                db["name"]: db["id"]
                for db in self.mb.get("/api/database").json()["data"]
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
