from . import config


class CardFactory(object):
    table_name = None

    def __init__(self, mb, database_id, collection_id):
        self.database_id = database_id
        self.collection_id = collection_id
        database = mb.get(
            "/api/database/{}?include=tables.fields".format(database_id)
        ).json()
        for table in database["tables"]:
            if table["name"] == self.table_name:
                self.table_id = table["id"]
                self.fields = {field["name"]: field["id"] for field in table["fields"]}


class AccountsCardFactory(CardFactory):
    table_name = "account"

    @property
    def accumulated_users_per_type(self):
        return {
            "name": "Accumulated Users per Type",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
        }

    @property
    def accumulated_registered_users_per_type(self):
        return {
            "name": "Accumulated Registered Users per Type",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
        }

    @property
    def new_users_per_month(self):
        return {
            "name": "New Users per Month",
            "collection_id": self.collection_id,
            "display": "bar",
            "database_id": self.database_id,
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
        }

    @property
    def user_conversions_per_month(self):
        return {
            "name": "User Conversions per Month",
            "collection_id": self.collection_id,
            "display": "line",
            "database_id": self.database_id,
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
        }

    @property
    def accumulated_number_of_full_users_over_time(self):
        return {
            "name": "Accumulated Number Of Full Users Over Time",
            "collection_id": self.collection_id,
            "display": "line",
            "database_id": self.database_id,
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
        }

    @property
    def accumulated_number_of_converted_users_over_time(self):
        return {
            "name": "Accumulated Number Of Converted Users Over Time",
            "collection_id": self.collection_id,
            "display": "line",
            "database_id": self.database_id,
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
                "series_settings": {"count": {"color": "#98D9D9"}},
            },
        }

    @property
    def accumulated_number_of_guest_users_over_time(self):
        return {
            "name": "Accumulated Number Of Guest Users Over Time",
            "collection_id": self.collection_id,
            "display": "line",
            "database_id": self.database_id,
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
                        "guest",
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
                "series_settings": {"count": {"color": "#F9D45C"}},
            },
        }


class AssessmentsCardFactory(CardFactory):
    table_name = "assessment"

    @property
    def accumulated_assessments(self):
        return {
            "name": "Accumulated Assessments",
            "collection_id": self.collection_id,
            "display": "scalar",
            "database_id": self.database_id,
            "query_type": "query",
            "dataset_query": {
                "database": self.database_id,
                "query": {"source-table": self.table_id, "aggregation": [["count"]]},
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
        }

    @property
    def new_assessments_per_month(self):
        return {
            "name": "New Assessments per Month",
            "collection_id": self.collection_id,
            "display": "line",
            "database_id": self.database_id,
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
        }

    @property
    def completion_of_assessments(self):
        return {
            "name": "Completion of Assessments",
            "collection_id": self.collection_id,
            "display": "bar",
            "database_id": self.database_id,
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
                    "where completion_percentage >= 0 group by completion order by min(completion_percentage) desc;"
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
        }

    @property
    def accumulated_assessments_over_time(self):
        return {
            "name": "Accumulated Assessments Over Time",
            "collection_id": self.collection_id,
            "display": "line",
            "database_id": self.database_id,
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
        }

    @property
    def tools_by_accumulated_assessments(self):
        return {
            "name": "Tools by Accumulated Assessments",
            "collection_id": self.collection_id,
            "display": "row",
            "database_id": self.database_id,
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
        }

    @property
    def tools_by_assessment_completion(self):
        return {
            "name": "Tools by Assessment Completion",
            "collection_id": self.collection_id,
            "display": "bar",
            "database_id": self.database_id,
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
                    "top_assessments": {"color": "#88BF4D", "title": "Top Assessments"},
                    "low_assessments": {"color": "#EF8C8C", "title": "Low Assessments"},
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
        }

    @property
    def accumulated_assessments_per_country(self):
        return {
            "name": "Accumulated Assessments per Country",
            "collection_id": self.collection_id,
            "display": "row",
            "database_id": self.database_id,
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
        }


class SectorAssessmentsCardFactory(CardFactory):
    table_name = "assessment"

    def __init__(self, sector_name, *args):
        super(SectorAssessmentsCardFactory, self).__init__(*args)
        self.sector_name = sector_name

    @property
    def assessments_per_month(self):
        return {
            "name": "Education: Assessments per month",
            "collection_id": self.collection_id,
            "display": "line",
            "database_id": self.database_id,
            "query_type": "query",
            "dataset_query": {
                "database": self.database_id,
                "query": {
                    "source-table": self.table_id,
                    "filter": [
                        "=",
                        [
                            "field-id",
                            self.fields["path"],
                        ],
                    ]
                    + config.sectors[self.sector_name],
                    "aggregation": [["count"]],
                    "breakout": [
                        [
                            "datetime-field",
                            ["field-id", self.fields["start_date"]],
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
                "graph.dimensions": ["start_date"],
                "graph.metrics": ["count"],
            },
        }


class QuestionnaireCardFactory(CardFactory):
    table_name = "company"

    @property
    def number_of_survey_responses(self):
        return {
            "name": "Number of Survey Responses",
            "collection_id": self.collection_id,
            "display": "scalar",
            "database_id": self.database_id,
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
        }

    @property
    def employees(self):
        return {
            "name": "Number of Employees",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
                "column_settings": {'["name","count"]': {"number_style": "decimal"}},
                "pie.show_legend": True,
                "pie.show_legend_perecent": True,
            },
        }

    @property
    def conductor(self):
        return {
            "name": "Assessment conducted by",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
        }

    @property
    def referer(self):
        return {
            "name": "Learned about OiRA",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
        }

    @property
    def workers_participated(self):
        return {
            "name": "Workers were invited",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
        }

    @property
    def needs_met(self):
        return {
            "name": "Needs were met",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
        }

    @property
    def recommend_tool(self):
        return {
            "name": "Would recommend tool",
            "collection_id": self.collection_id,
            "display": "pie",
            "database_id": self.database_id,
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
        }
