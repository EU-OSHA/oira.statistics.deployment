class CardFactory(object):
    def __init__(self, database_mapping, database_id, collection_id, table_id):
        self.database_mapping = database_mapping
        self.database_id = database_id
        self.collection_id = collection_id
        self.table_id = table_id


class AssessmentsCardFactory(CardFactory):
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
                            self.database_mapping[self.database_id]["fields"][302],
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


class QuestionnaireCardFactory(CardFactory):
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
                            self.database_mapping[self.database_id]["fields"][179],
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
                            self.database_mapping[self.database_id]["fields"][182],
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
                            self.database_mapping[self.database_id]["fields"][176],
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
                            self.database_mapping[self.database_id]["fields"][178],
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
                            self.database_mapping[self.database_id]["fields"][184],
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
                            self.database_mapping[self.database_id]["fields"][183],
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
