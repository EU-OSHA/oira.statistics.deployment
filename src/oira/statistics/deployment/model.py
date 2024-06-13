from sqlalchemy import schema
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import functions


Base = declarative_base()


# Enum copied from euphorie.client.model so we do not have to pull it in as a dependency
class Enum(types.TypeDecorator):
    impl = types.Unicode

    def __init__(self, values, empty_to_none=False, strict=False):
        """Emulate an Enum type.

        values:
           A list of valid values for this column
        empty_to_none:
           Optional, treat the empty string '' as None
        strict:
           Also insist that columns read from the database are in the
           list of valid values.  Note that, with strict=True, you won't
           be able to clean out bad data from the database through your
           code.
        """

        if values is None or len(values) == 0:
            raise TypeError("Enum requires a list of values")
        self.empty_to_none = empty_to_none
        self.strict = strict
        self.values = values[:]

        # The length of the string/unicode column should be the longest string
        # in values
        size = max([len(v) for v in values if v is not None])
        super().__init__(size)

    def process_bind_param(self, value, dialect):
        if self.empty_to_none and value == "":
            value = None
        if value not in self.values:
            raise ValueError('"%s" not in Enum.values' % value)
        if value is None:
            return None
        else:
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if self.strict and value not in self.values:
            raise ValueError('"%s" not in Enum.values' % value)
        return value


class AccountStatistics(Base):
    """Statistically relevant data concerning an account."""

    __tablename__ = "account"

    id = schema.Column(types.Integer(), primary_key=True, autoincrement=True)
    account_type = schema.Column(
        Enum(["guest", "converted", "full"]), default="full", nullable=True
    )
    creation_date = schema.Column(
        types.DateTime, nullable=True, default=functions.now()
    )


class SurveyStatistics(Base):
    """Statistically relevant data concerning a survey (tool)."""

    __tablename__ = "tool"

    tool_path = schema.Column(types.String(512), primary_key=True)
    published_date = schema.Column(types.DateTime, nullable=True)
    years_online = schema.Column(types.Integer(), nullable=True)
    num_users = schema.Column(types.Integer(), nullable=True)
    num_assessments = schema.Column(types.Integer(), nullable=True)


class SurveySessionStatistics(Base):
    """Statistically relevant data concerning a session."""

    __tablename__ = "assessment"

    tool_path = schema.Column(types.String(512), nullable=False)
    completion_percentage = schema.Column(types.Integer, nullable=True, default=0)
    account_type = schema.Column(
        Enum(["guest", "converted", "full"]), default="full", nullable=True
    )
    start_date = schema.Column(types.DateTime, nullable=False, default=functions.now())
    modified = schema.Column(types.DateTime, nullable=True)
    country = schema.Column(types.String(512), nullable=False)
    id = schema.Column(types.Integer(), primary_key=True, autoincrement=True)
    account_id = schema.Column(types.Integer(), nullable=True)


class NewsletterStatistics(Base):
    """Statistics on the newsletter subscriptions."""

    __tablename__ = "newsletter"
    zodb_path = schema.Column(types.String(512), primary_key=True, nullable=False)
    count = schema.Column(types.Integer(), default=0)


class CompanyStatistics(Base):
    """Statistically relevant data concerning a company."""

    __tablename__ = "company"

    id = schema.Column(types.Integer(), primary_key=True, autoincrement=True)
    country = schema.Column(types.String(3))
    employees = schema.Column(Enum(["no answer", "1-9", "10-49", "50-249", "250+"]))
    conductor = schema.Column(Enum(["no answer", "staff", "third-party", "both"]))
    referer = schema.Column(
        Enum(
            [
                "no answer",
                "employers-organisation",
                "trade-union",
                "national-public-institution",
                "eu-institution",
                "health-safety-experts",
                "other",
            ]
        )
    )
    workers_participated = schema.Column(Enum(["no answer", "yes", "no"]))
    needs_met = schema.Column(Enum(["no answer", "yes", "no"]))
    recommend_tool = schema.Column(Enum(["no answer", "yes", "no"]))
    date = schema.Column(types.DateTime(), nullable=True)
    tool_path = schema.Column(types.String(512), nullable=False)
