from . import config

import logging


log = logging.getLogger(__name__)


class CardFactory(object):
    extra_filter = None
    _raw_cards = {}

    def __init__(self, mb, database_id, collection_id, country=None):
        self.database_id = database_id
        self.collection_id = collection_id
        self.country = country
        database = mb.get(
            "/api/database/{}?include=tables.fields".format(database_id)
        ).json()
        self.tables = {}
        for table in database["tables"]:
            self.tables[table["name"]] = {
                "id": table["id"],
                "fields": {field["name"]: field["id"] for field in table["fields"]},
            }

    def __getattr__(self, name):
        if name not in self._raw_cards:
            return
        card = self.get_base_properties()
        card_data = self._raw_cards[name]
        card.update(card_data)
        card["name"] = self.transform_name(card["name"])
        if self.extra_filter:
            query_type = card["query_type"]
            if query_type == "query":
                if "source-query" in card["dataset_query"][query_type]:
                    orig_query = card["dataset_query"][query_type]["source-query"]
                else:
                    orig_query = card["dataset_query"][query_type]
                if "filter" in orig_query:
                    orig_filter = orig_query["filter"]
                    new_filter = [
                        "and",
                        orig_filter,
                        self.extra_filter[query_type],
                    ]
                else:
                    new_filter = self.extra_filter[query_type]
                orig_query["filter"] = new_filter

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
                        "source-table": self.tables["account"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["account"]["fields"]["account_type"],
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
                        "source-table": self.tables["account"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["account"]["fields"]["account_type"],
                            ]
                        ],
                        "filter": [
                            "!=",
                            [
                                "field-id",
                                self.tables["account"]["fields"]["account_type"],
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
                        "source-table": self.tables["account"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.tables["account"]["fields"]["creation_date"],
                                ],
                                "month",
                            ],
                            [
                                "field-id",
                                self.tables["account"]["fields"]["account_type"],
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
                        "source-table": self.tables["account"]["id"],
                        "filter": [
                            "=",
                            [
                                "field-id",
                                self.tables["account"]["fields"]["account_type"],
                            ],
                            "converted",
                        ],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.tables["account"]["fields"]["creation_date"],
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
                        "source-table": self.tables["account"]["id"],
                        "filter": [
                            "=",
                            [
                                "field-id",
                                self.tables["account"]["fields"]["account_type"],
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
                                    self.tables["account"]["fields"]["creation_date"],
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
            "newsletter_subscriptions": {
                "name": "Newsletter Subscriptions",
                "display": "table",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {"source-table": self.tables["newsletter"]["id"]},
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "description": None,
                        "semantic_type": "type/PK",
                        "coercion_strategy": None,
                        "name": "zodb_path",
                        "settings": None,
                        "field_ref": ["field", 120, None],
                        "effective_type": "type/Text",
                        "id": 120,
                        "visibility_type": "normal",
                        "display_name": "Path",
                        "fingerprint": None,
                        "base_type": "type/Text",
                    },
                    {
                        "description": None,
                        "semantic_type": "type/Quantity",
                        "coercion_strategy": None,
                        "name": "count",
                        "settings": None,
                        "field_ref": ["field", 121, None],
                        "effective_type": "type/Integer",
                        "id": 121,
                        "visibility_type": "normal",
                        "display_name": "Count",
                        "base_type": "type/Integer",
                    },
                ],
                "visualization_settings": {
                    "table.pivot_column": "count",
                    "table.cell_column": "zodb_path",
                    "column_settings": {
                        '["ref",["field",120,null]]': {"column_title": "Path"}
                    },
                },
                "height": 8,
                "width": 6,
            },
            "top_tools_by_number_of_users": {
                "name": "Top Tools by Number of Users / By yearly average",
                "display": "row",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.tables["tool"]["id"],
                        "expressions": {
                            "Users per Year": [
                                "/",
                                [
                                    "field-id",
                                    self.tables["tool"]["fields"]["num_users"],
                                ],
                                [
                                    "+",
                                    [
                                        "field-id",
                                        self.tables["tool"]["fields"]["years_online"],
                                    ],
                                    1,
                                ],
                            ]
                        },
                        "order-by": [["desc", ["expression", "Users per Year"]]],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Tool Path",
                        "name": "Tool_path",
                        "special_type": "type/PK",
                    },
                    {
                        "base_type": "type/DateTime",
                        "display_name": "Published Date",
                        "name": "published_date",
                        "unit": "default",
                        "special_type": None,
                    },
                    {
                        "base_type": "type/Integer",
                        "display_name": "Years Online",
                        "name": "years_online",
                        "special_type": "type/Category",
                    },
                    {
                        "base_type": "type/Integer",
                        "display_name": "Num Users",
                        "name": "num_users",
                        "special_type": "type/Quantity",
                    },
                    {
                        "base_type": "type/Float",
                        "display_name": "Users per Year",
                        "name": "Users per Year",
                        "special_type": None,
                    },
                ],
                "visualization_settings": {
                    "graph.dimensions": ["tool_path"],
                    "graph.metrics": ["Users per Year"],
                },
                "height": 8,
                "width": 6,
            },
            "number_of_users_and_assessments_by_tool": {
                "name": "Number Of Users And Assessments By Tool / Since publication",
                "display": "table",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.tables["tool"]["id"],
                        "expressions": {
                            "Users per Year": [
                                "/",
                                [
                                    "field-id",
                                    self.tables["tool"]["fields"]["num_users"],
                                ],
                                [
                                    "+",
                                    [
                                        "field-id",
                                        self.tables["tool"]["fields"]["years_online"],
                                    ],
                                    1,
                                ],
                            ]
                        },
                        "fields": [
                            ["field-id", self.tables["tool"]["fields"]["tool_path"]],
                            ["field-id", self.tables["tool"]["fields"]["num_users"]],
                            [
                                "field-id",
                                self.tables["tool"]["fields"]["num_assessments"],
                            ],
                        ],
                        "order-by": [
                            [
                                "desc",
                                [
                                    "field-id",
                                    self.tables["tool"]["fields"]["num_assessments"],
                                ],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Tool Path",
                        "name": "tool_path",
                        "special_type": "type/PK",
                    },
                    {
                        "base_type": "type/Integer",
                        "display_name": "Num Users",
                        "name": "num_users",
                        "special_type": "type/Quantity",
                    },
                    {
                        "base_type": "type/Integer",
                        "display_name": "Num Assessments",
                        "name": "num_assessments",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "table.pivot": False,
                    "table.pivot_column": "num_users",
                    "table.cell_column": "num_assessments",
                },
                "height": 8,
                "width": 6,
            },
            "accumulated_assessments": {
                "name": "Accumulated Assessments",
                "display": "scalar",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.tables["assessment"]["id"],
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
                        "source-table": self.tables["assessment"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.tables["assessment"]["fields"]["start_date"],
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
                        "source-table": self.tables["assessment"]["id"],
                        "aggregation": [["cum-count"]],
                        "breakout": [
                            [
                                "datetime-field",
                                [
                                    "field-id",
                                    self.tables["assessment"]["fields"]["start_date"],
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
                        "source-table": self.tables["assessment"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["assessment"]["fields"]["tool_path"],
                            ]
                        ],
                        "order-by": [["desc", ["aggregation", 0]]],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Tool Path",
                        "name": "tool_path",
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
                    "graph.dimensions": ["tool_path"],
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
                            "select tool_path,\n"
                            "    count(case when completion_percentage > 70 then 'top' end) as top_assessments,\n"
                            "    count(case when completion_percentage >= 10 and completion_percentage <= 70 then 'avg' end) as avg_assessments,\n"
                            "    count(case when completion_percentage < 10 then 'low' end) as low_assessments\n"
                            "from assessment\n"
                            "where tool_path not like '%/preview'\n"
                            "group by tool_path\n"
                            "order by top_assessments desc, avg_assessments desc, low_assessments desc;"
                        ),
                        "template-tags": {},
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Tool Path",
                        "name": "tool_path",
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
                "display": "bar",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.tables["assessment"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["assessment"]["fields"].get("country", ""),
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
                    "graph.dimensions": ["country"],
                    "graph.metrics": ["count"],
                },
            },
            "registered_users_per_country": {
                "name": "Registered Users per Country",
                "display": "bar",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-table": self.tables["assessment"]["id"],
                        "aggregation": [
                            [
                                "distinct",
                                [
                                    "field-id",
                                    self.tables["assessment"]["fields"].get(
                                        "account_id", ""
                                    ),
                                ],
                            ]
                        ],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["assessment"]["fields"].get("country", ""),
                            ]
                        ],
                        "filter": [
                            "=",
                            [
                                "field-id",
                                self.tables["assessment"]["fields"].get(
                                    "account_type", ""
                                ),
                            ],
                            "converted",
                            "full",
                        ],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "description": None,
                        "semantic_type": "type/Country",
                        "coercion_strategy": None,
                        "name": "country",
                        "settings": None,
                        "field_ref": ["field", 41, None],
                        "effective_type": "type/Text",
                        "id": 41,
                        "display_name": "Country",
                        "base_type": "type/Text",
                    },
                    {
                        "display_name": "Distinct values of Account ID",
                        "semantic_type": "type/Quantity",
                        "settings": None,
                        "field_ref": ["aggregation", 0],
                        "name": "count",
                        "base_type": "type/BigInteger",
                        "effective_type": "type/BigInteger",
                    },
                ],
                "visualization_settings": {
                    "graph.y_axis.title_text": "Registered Users",
                    "graph.dimensions": ["country"],
                    "series_settings": {
                        "count": {"title": "Number of Registered Users"}
                    },
                    "graph.metrics": ["count"],
                },
            },
            "top_tools_by_number_of_assessments": {
                "name": "Top Tools by Number of Assessments",
                "display": "row",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.tables["assessment"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["assessment"]["fields"]["tool_path"],
                            ]
                        ],
                        "order-by": [["desc", ["aggregation", 0]]],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Tool Path",
                        "name": "tool_path",
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
                    "graph.dimensions": ["tool_path"],
                    "stackable.stack_type": None,
                },
            },
            "top_assessments_by_country": {
                "name": "Top Assessments By Country",
                "display": "bar",
                "query_type": "query",
                "dataset_query": {
                    "query": {
                        "source-table": self.tables["assessment"]["id"],
                        "aggregation": [
                            [
                                "aggregation-options",
                                [
                                    "/",
                                    [
                                        "count-where",
                                        [
                                            ">",
                                            [
                                                "field-id",
                                                self.tables["assessment"]["fields"][
                                                    "completion_percentage"
                                                ],
                                            ],
                                            70,
                                        ],
                                    ],
                                    ["count"],
                                ],
                                {"display-name": "Top Assessments"},
                            ]
                        ],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["assessment"]["fields"].get("country", ""),
                            ]
                        ],
                    },
                    "type": "query",
                    "database": self.database_id,
                },
                "visualization_settings": {
                    "table.pivot": False,
                    "graph.dimensions": ["country"],
                    "graph.metrics": ["expression"],
                    "column_settings": {
                        '["name","expression"]': {"number_style": "percent"}
                    },
                },
            },
            "accumulated_number_of_users": {
                "name": "Accumulated Users Over Time",
                "display": "line",
                "query_type": "query",
                "dataset_query": {
                    "database": self.database_id,
                    "query": {
                        "source-query": {
                            "source-table": self.tables["assessment"]["id"],
                            "aggregation": [
                                [
                                    "distinct",
                                    [
                                        "field-id",
                                        self.tables["assessment"]["fields"][
                                            "account_id"
                                        ],
                                    ],
                                ]
                            ],
                            "breakout": [
                                [
                                    "datetime-field",
                                    [
                                        "field-id",
                                        self.tables["assessment"]["fields"][
                                            "start_date"
                                        ],
                                    ],
                                    "month",
                                ]
                            ],
                        },
                        "aggregation": [
                            [
                                "cum-sum",
                                ["field", "count", {"base-type": "type/Integer"}],
                            ]
                        ],
                        "breakout": [["field-literal", "start_date", "type/DateTime"]],
                    },
                    "type": "query",
                },
                "result_metadata": [
                    {
                        "base_type": "type/Date",
                        "display_name": "Start Date",
                        "name": "start_date",
                        "special_type": "type/CreationTimestamp",
                        "unit": "day",
                    },
                    {
                        "base_type": "type/BigInteger",
                        "display_name": "Count",
                        "name": "count",
                        "special_type": "type/Quantity",
                    },
                ],
                "visualization_settings": {
                    "graph.dimensions": ["start_date"],
                    "graph.metrics": ["count"],
                    "series_settings": {
                        "sum": {"title": "Accumulated Number of Users"}
                    },
                },
            },
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
                        "source-table": self.tables["company"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["company"]["fields"]["employees"],
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
                        "source-table": self.tables["company"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["company"]["fields"]["conductor"],
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
                        "source-table": self.tables["company"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["company"]["fields"]["referer"],
                            ]
                        ],
                    },
                    "database": self.database_id,
                },
                "result_metadata": [
                    {
                        "base_type": "type/Text",
                        "display_name": "Referer",
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
            "referer_france": {
                "name": "Learned about OiRA",
                "display": "pie",
                "query_type": "query",
                "dataset_query": {
                    "type": "query",
                    "query": {
                        "source-table": self.tables["company"]["id"],
                        "aggregation": [["count"]],
                        "expressions": {
                            "France referer": [
                                "replace",
                                [
                                    "field",
                                    self.tables["company"]["fields"]["referer"],
                                    None,
                                ],
                                "trade-union",
                                "social-security",
                            ]
                        },
                        "breakout": [["expression", "France referer", None]],
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
                        "display_name": "Referer",
                        "field_ref": ["expression", "France referer"],
                        "name": "France referer",
                        "base_type": "type/Text",
                        "effective_type": "type/Text",
                        "semantic_type": None,
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
                        "source-table": self.tables["company"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["company"]["fields"][
                                    "workers_participated"
                                ],
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
                        "source-table": self.tables["company"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["company"]["fields"]["needs_met"],
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
                        "source-table": self.tables["company"]["id"],
                        "aggregation": [["count"]],
                        "breakout": [
                            [
                                "field-id",
                                self.tables["company"]["fields"]["recommend_tool"],
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
            "oiras_poissonerie_sessions_cumulees": self._get_inrs_card("poissonerie"),
            "oiras_boulangerie_sessions_cumulees": self._get_inrs_card("boulangerie"),
            "oiras_boucherie_charcuterie_sessions_cumulees": self._get_inrs_card(
                "boucherie-charcuterie"
            ),
            "oiras_commerce_alimentaire_de_proximite_sessions_cumulees": self._get_inrs_card(
                "commerce-alimentaire-de-proximite"
            ),
        }

    def _get_inrs_card(self, tool):
        return {
            "name": "OiRA {} - Sessions cumulées".format(tool),
            "display": "line",
            "query_type": "query",
            "dataset_query": {
                "type": "query",
                "query": {
                    "source-table": self.tables["assessment"]["id"],
                    "filter": [
                        "ends-with",
                        [
                            "field",
                            self.tables["assessment"]["fields"]["tool_path"],
                            None,
                        ],
                        tool,
                        {"case-sensitive": False},
                    ],
                    "aggregation": [["cum-count"]],
                    "breakout": [
                        [
                            "field",
                            self.tables["assessment"]["fields"]["start_date"],
                            {"temporal-unit": "month"},
                        ],
                    ],
                },
                "database": self.database_id,
            },
            "result_metadata": [
                {
                    "semantic_type": "type/CreationTimestamp",
                    "coercion_strategy": None,
                    "unit": "month",
                    "name": "start_date",
                    "display_name": "Start Date",
                    "base_type": "type/DateTime",
                },
                {
                    "name": "count",
                    "display_name": "Count",
                    "base_type": "type/BigInteger",
                    "semantic_type": "type/Quantity",
                },
            ],
            "visualization_settings": {
                "graph.dimensions": ["start_date"],
                "graph.metrics": ["count"],
            },
        }


class SectorCardFactory(CardFactory):
    def __init__(self, sector_name, *args):
        self.sector_name = sector_name
        super(SectorCardFactory, self).__init__(*args)

    @property
    def extra_filter(self):
        return {
            "query": [
                "=",
                [
                    "field-id",
                    self.tables["assessment"]["fields"]["tool_path"],
                ],
            ]
            + config.sectors[self.sector_name],
            "native": " AND ({}) ".format(
                " OR ".join(
                    (
                        "tool_path = '{}'".format(path)
                        for path in config.sectors[self.sector_name]
                    )
                )
            ),
        }

    def transform_name(self, name):
        return "{} ({})".format(name, self.sector_name)
