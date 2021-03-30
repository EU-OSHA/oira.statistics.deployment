from . import config
import logging

log = logging.getLogger(__name__)


class CardFactory(object):
    table_name = None
    extra_filter = None
    _raw_cards = {}

    def __init__(self, mb, database_id, collection_id, country=None):
        self.database_id = database_id
        self.collection_id = collection_id
        self.country = country
        database = mb.get(
            "/api/database/{}?include=tables.fields".format(database_id)
        ).json()
        for table in database["tables"]:
            if table["name"] == self.table_name:
                self.table_id = table["id"]
                self.fields = {field["name"]: field["id"] for field in table["fields"]}

    def __getattr__(self, name):
        card = self.get_base_properties()
        card_data = self._raw_cards[name]
        card.update(card_data)
        card["name"] = self.transform_name(card["name"])
        if self.extra_filter:
            query_type = card["query_type"]
            if query_type == "query":
                if "filter" in card["dataset_query"][query_type]:
                    log.warning(
                        "Overwriting existing filter ({})".format(
                            card["dataset_query"][query_type]["filter"]
                        )
                    )
                card["dataset_query"][query_type]["filter"] = self.extra_filter[
                    query_type
                ]
            elif query_type == "native":
                query = card["dataset_query"][query_type]["query"]
                if self.extra_filter[query_type] not in query:
                    log.warning(
                        "Filter not found in query: {}".format(
                            self.extra_filter[query_type]
                        )
                    )
            else:
                log.warning("Unknown query type {}".format(query_type))
        return card

    def get_base_properties(self):
        base = {
            "collection_id": self.collection_id,
            "database_id": self.database_id,
        }
        return base

    def transform_name(self, name):
        if self.country:
            return "{} ({})".format(name, self.country.upper())
        else:
            return name


class AccountsCardFactory(CardFactory):
    table_name = "account"

    @property
    def _raw_cards(self):
        return {
            "accumulated_users_per_type": {
                "name": "Accumulated Users per Type",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["account_type"],
                            ]
                        ],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Account Type",
                        "name": "account_type",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.show_legend": True,
                    "pie.show_legend_perecent": True,
                    "pie.colors": {
                        "converted": "#98D9D9",
                        "full": "#7172AD",
                        "guest": "#F9D45C",
                    },
                },
            },
            "accumulated_registered_users_per_type": {
                "name": "Accumulated Registered Users per Type",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["account_type"],
                            ]
                        ],
                        "filter": [
                            "!=",
                            [
                                "field-id",
                                self.fields["account_type"],
                            ],
                            "guest",
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Account Type",
                        "name": "account_type",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.show_legend": True,
                    "pie.show_legend_perecent": True,
                    "pie.colors": {
                        "converted": "#98D9D9",
                        "full": "#7172AD",
                        "guest": "#F9D45C",
                    },
                },
            },
            "new_users_per_month": {
                "name": "New Users per Month",
                "display": "bar",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.fields["creation_date"],
                                ],
                                "month",
                            ],
                            [
                                "field-id",
                                self.fields["account_type"],
                            ],
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/DateTime",
                        "display_name": "Creation Date",
                        "name": "creation_date",
                        "unit": "month",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/Text",
                        "display_name": "Account Type",
                        "name": "account_type",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.show_goal": False,
                    "graph.show_trendline": True,
                    "graph.y_axis.title_text": "Number of New Users",
                    "graph.show_values": True,
                    "stackable.stack_display": "bar",
                    "graph.x_axis.title_text": "Creation Date",
                    "graph.y_axis.auto_split": False,
                    "graph.metrics": ["count"],
                    "graph.label_value_formatting": "auto",
                    "series_settings": {"guest": {"color": "#F9D45C"}},
                    "graph.dimensions": ["creation_date", "account_type"],
                    "stackable.stack_type": None,
                },
            },
            "user_conversions_per_month": {
                "name": "User Conversions per Month",
                "display": "line",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "filter": [
                            "=",
                            [
                                "field-id",
                                self.fields["account_type"],
                            ],
                            "converted",
                        ],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.fields["creation_date"],
                                ],
                                "month",
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/DateTime",
                        "display_name": "Creation Date",
                        "name": "creation_date",
                        "unit": "month",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.x_axis.title_text": "Date",
                    "graph.dimensions": ["creation_date"],
                    "graph.metrics": ["count"],
                    "graph.show_values": True,
                    "series_settings": {
                        "count": {
                            "title": "Number of User Accounts Converted",
                            "color": "#98D9D9",
                        }
                    },
                },
            },
            "accumulated_registered_users_over_time": {
                "name": "Accumulated Registered Users Over Time",
                "display": "line",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "filter": [
                            "=",
                            [
                                "field-id",
                                self.fields["account_type"],
                            ],
                            "full",
                            "converted",
                        ],
                        "aggregation": [["cum-count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.fields["creation_date"],
                                ],
                                "month",
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/DateTime",
                        "display_name": "Creation Date",
                        "name": "creation_date",
                        "unit": "month",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.dimensions": ["creation_date"],
                    "graph.metrics": ["count"],
                    "series_settings": {"count": {"color": "#A989C5"}},
                },
            },
        }


class AssessmentsCardFactory(CardFactory):
    table_name = "assessment"

    @property
    def _raw_cards(self):
        return {
            "accumulated_assessments": {
                "name": "Accumulated Assessments",
                "display": "scalar",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    }
                ],
                "visualization_settings": {},
            },
            "new_assessments_per_month": {
                "name": "New Assessments per Month",
                "display": "line",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.fields["start_date"],
                                ],
                                "month",
                            ]
                        ],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/DateTime",
                        "display_name": "Start Date",
                        "name": "start_date",
                        "special_type": "type/CreationTimestamp",
                        "unit": "month",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.show_trendline": True,
                    "graph.y_axis.title_text": "Number of started assessments",
                    "graph.show_values": False,
                    "graph.x_axis.title_text": "Date",
                    "graph.label_value_frequency": "fit",
                    "graph.metrics": ["count"],
                    "series_settings": {"count": {"display": "bar"}},
                    "graph.dimensions": ["start_date"],
                    "stackable.stack_type": None,
                },
            },
            "completion_of_assessments": {
                "name": "Completion of Assessments",
                "display": "bar",
                "query_type": "native",
                "dataset_query": {
                    "database": self.database_id,
                    "native": {
                        "query": "select (\n"
                        "    case when completion_percentage > 70 then "
                        "'top (more than 70% of risks answered)'\n"
                        "         when completion_percentage >= 10 and completion_percentage <= 70 then 'average (more than 10% of risks answered)'\n"
                        "         when completion_percentage < 10 then 'low (less than 10% of risks answered)'\n"
                        "         when completion_percentage is null then 'unknown (no data)'\n"
                        "         else 'unknown (unusable data)'\n"
                        "end) as completion,\n"
                        "count(*) from assessment\n"
                        "where completion_percentage >= 0 "
                        "  {extra_filter} \n"
                        "group by completion "
                        "order by min(completion_percentage) desc;".format(
                            extra_filter=(
                                self.extra_filter["native"] if self.extra_filter else ""
                            )
                        )
                    },
                    "type": "native",
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "completion",
                        "name": "completion",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.y_axis.title_text": "Number of Assessments",
                    "graph.show_values": True,
                    "table.cell_column": "count",
                    "stackable.stack_display": "bar",
                    "graph.x_axis.title_text": "Completion Percentage",
                    "graph.y_axis.scale": "pow",
                    "graph.metrics": ["count"],
                    "graph.label_value_formatting": "auto",
                    "table.pivot_column": "completion",
                    "series_settings": {
                        "2": {"color": "#88BF4D"},
                        "22": {"color": "#F9D45C"},
                        "86": {"color": "#EF8C8C"},
                        "count": {"color": "#98D9D9", "display": "bar"},
                    },
                    "graph.dimensions": ["completion", "count"],
                    "stackable.stack_type": None,
                },
            },
            "accumulated_assessments_over_time": {
                "name": "Accumulated Assessments Over Time",
                "display": "line",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["cum-count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.fields["start_date"],
                                ],
                                "month",
                            ]
                        ],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/DateTime",
                        "display_name": "Start Date",
                        "name": "start_date",
                        "special_type": "type/CreationTimestamp",
                        "unit": "month",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.show_trendline": True,
                    "graph.y_axis.title_text": "Number of Accumulated Assessments",
                    "graph.show_values": False,
                    "graph.x_axis.title_text": "Date",
                    "graph.label_value_frequency": "fit",
                    "graph.metrics": ["count"],
                    "series_settings": {
                        "count": {"display": "bar", "title": "Number of Assessments"}
                    },
                    "graph.dimensions": ["start_date"],
                    "stackable.stack_type": None,
                },
            },
            "tools_by_accumulated_assessments": {
                "name": "Tools by Accumulated Assessments",
                "display": "row",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["tool"],
                            ]
                        ],
                        "order-by": [["desc", ["aggregation", 0]]],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Tool",
                        "name": "tool",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.dimensions": ["tool"],
                    "graph.metrics": ["count"],
                    "series_settings": {"count": {"title": "Number of Assessments"}},
                },
            },
            "tools_by_assessment_completion": {
                "name": "Tools by Assessment Completion",
                "display": "bar",
                "query_type": "native",
                "dataset_query": {
                    "type": "native",
                    "native": {
                        "query": (
                            "select sector || '/' || tool as tool,\n"
                            "    count(case when completion_percentage > 70 then 'top' end) as top_assessments,\n"
                            "    count(case when completion_percentage >= 10 and completion_percentage <= 70 then 'avg' end) as avg_assessments,\n"
                            "    count(case when completion_percentage < 10 then 'low' end) as low_assessments\n"
                            "from assessment\n"
                            "where tool != 'preview'\n"
                            "group by country, sector, tool\n"
                            "order by top_assessments desc, avg_assessments desc, low_assessments desc;"
                        ),
                        "template-tags": {},
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "tool",
                        "name": "tool",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "top_assessments",
                        "name": "top_assessments",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "avg_assessments",
                        "name": "avg_assessments",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "low_assessments",
                        "name": "low_assessments",
                        "special_type": None,
                    },
                ],
                "visualization_settings": {
                    "series_settings": {
                        "top_assessments": {
                            "color": "#88BF4D",
                            "title": "Top Assessments",
                        },
                        "low_assessments": {
                            "color": "#EF8C8C",
                            "title": "Low Assessments",
                        },
                        "avg_assessments": {"title": "Average Assessments"},
                    },
                    "stackable.stack_type": None,
                    "graph.dimensions": ["tool"],
                    "graph.metrics": [
                        "top_assessments",
                        "avg_assessments",
                        "low_assessments",
                    ],
                    "graph.show_values": False,
                    "graph.x_axis.axis_enabled": False,
                    "graph.y_axis.auto_split": False,
                },
            },
            "accumulated_assessments_per_country": {
                "name": "Accumulated Assessments per Country",
                "display": "row",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["country"],
                            ]
                        ],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Country",
                        "name": "country",
                        "special_type": "type/Country",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "map.type": "region",
                    "map.region": "world_countries",
                    "graph.dimensions": ["country"],
                    "graph.metrics": ["count"],
                },
            },
            "top_ten_tools_by_number_of_assessments": {
                "name": "Top Ten Tools by Number of Assessments",
                "display": "row",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [["field-id", self.fields["path"]]],
                        "order-by": [["desc", ["aggregation", 0]]],
                        "limit": 10,
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Path",
                        "name": "path",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.show_trendline": True,
                    "graph.y_axis.title_text": "Number of started assessments",
                    "graph.show_values": False,
                    "graph.x_axis.title_text": "Date",
                    "graph.label_value_frequency": "fit",
                    "graph.metrics": ["count"],
                    "series_settings": {"count": {"display": "bar"}},
                    "graph.dimensions": ["path"],
                    "stackable.stack_type": None,
                },
            },
            "top_ten_tools_by_number_of_users": {
                "name": "Top Ten Tools by Number of Users",
                "display": "row",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [
                            ["distinct", ["field-id", self.fields["account_id"]]]
                        ],
                        "breakout": [["field-id", self.fields["path"]]],
                        "order-by": [["desc", ["aggregation", 0]]],
                        "limit": 10,
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Path",
                        "name": "path",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Distinct values of Account ID",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.dimensions": ["path"],
                    "graph.metrics": ["count"],
                },
            },
        }


class SectorAssessmentsCardFactory(AssessmentsCardFactory):
    table_name = "assessment"

    def __init__(self, sector_name, *args):
        self.sector_name = sector_name
        super(SectorAssessmentsCardFactory, self).__init__(*args)

    @property
    def extra_filter(self):
        return {
            "query": [
                "=",
                [
                    "field-id",
                    self.fields["path"],
                ],
            ]
            + config.sectors[self.sector_name],
            "native": " AND ({}) ".format(
                " OR ".join(
                    (
                        "path = '{}'".format(path)
                        for path in config.sectors[self.sector_name]
                    )
                )
            ),
        }

    def transform_name(self, name):
        return "{} ({})".format(name, self.sector_name)


class QuestionnaireCardFactory(CardFactory):
    table_name = "company"

    @property
    def _raw_cards(self):
        return {
            "number_of_survey_responses": {
                "name": "Number of Survey Responses",
                "display": "scalar",
                "query_type": "native",
                "dataset_query": {
                    "type": "native",
                    "native": {
                        "query": 'SELECT count(*) AS "count"\nFROM "public"."company"\nWHERE needs_met is not NULL or workers_participated is not NULL or referer is not NULL or employees is not NULL or conductor is not NULL or recommend_tool is not NULL',
                        "template-tags": {},
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    }
                ],
                "visualization_settings": {"table.cell_column": "count"},
            },
            "employees": {
                "name": "Number of Employees",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["employees"],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Employees",
                        "name": "employees",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.colors": {
                        "1-9": "#98D9D9",
                        "10-49": "#509EE3",
                        "250+": "#7172AD",
                        "null": "#74838f",
                        "50-249": "#A989C5",
                    },
                    "pie.slice_threshold": 0.1,
                    "column_settings": {
                        '["name","count"]': {"number_style": "decimal"}
                    },
                    "pie.show_legend": True,
                    "pie.show_legend_perecent": True,
                },
            },
            "conductor": {
                "name": "Assessment conducted by",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["conductor"],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Conductor",
                        "name": "conductor",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.colors": {
                        "both": "#EF8C8C",
                        "null": "#74838f",
                        "staff": "#509EE3",
                        "third-party": "#7172AD",
                    },
                    "pie.slice_threshold": 0,
                    "pie.show_legend": True,
                },
            },
            "referer": {
                "name": "Learned about OiRA",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["referer"],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Refer Er",
                        "name": "referer",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.slice_threshold": 0,
                    "pie.colors": {
                        "employers-organisation": "#88BF4D",
                        "eu-institution": "#F2A86F",
                        "null": "#74838f",
                        "other": "#509EE3",
                        "health-safety-experts": "#A989C5",
                        "national-public-institution": "#EF8C8C",
                    },
                    "pie.show_legend": True,
                },
            },
            "workers_participated": {
                "name": "Workers were invited",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["workers_participated"],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Boolean",
                        "display_name": "Workers Participated",
                        "name": "workers_participated",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.show_legend": True,
                    "pie.slice_threshold": 0,
                    "pie.colors": {
                        "null": "#74838f",
                        "true": "#88BF4D",
                        "false": "#F2A86F",
                    },
                },
            },
            "needs_met": {
                "name": "Needs were met",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["needs_met"],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Boolean",
                        "display_name": "Needs Met",
                        "name": "needs_met",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.slice_threshold": 0,
                    "pie.colors": {
                        "null": "#74838f",
                        "true": "#88BF4D",
                        "false": "#F2A86F",
                    },
                    "pie.show_legend": True,
                },
            },
            "recommend_tool": {
                "name": "Would recommend tool",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.table_id,
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.fields["recommend_tool"],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Boolean",
                        "display_name": "Recommend Tool",
                        "name": "recommend_tool",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "pie.show_legend": True,
                    "pie.slice_threshold": 0,
                    "pie.colors": {
                        "null": "#74838f",
                        "true": "#88BF4D",
                        "false": "#F2A86F",
                    },
                },
            },
        }
