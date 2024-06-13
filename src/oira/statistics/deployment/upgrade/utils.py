from alembic import op
from logging import getLogger
from sqlalchemy import inspect


logger = getLogger(__name__)


def has_table(name):
    """Utility function that can be used in alembic upgrades to check if a
    table exists."""
    return name in inspect(op.get_bind()).get_table_names()


def has_column(table_name, column_name):
    """Utility function that can be used in alembic upgrades to check if a
    column exists."""
    bind = op.get_bind()
    columns = inspect(bind).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)
