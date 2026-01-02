# db.py
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from configs import DB_URI, DB_UPLOAD_TABLE

# -------------------------
# Shared engine
# -------------------------
_engine = sqlalchemy.create_engine(DB_URI, pool_pre_ping=True)

_SessionFactory = sessionmaker(bind=_engine)

def open_upload_session():
    """
    Returns:
        session        - SQLAlchemy session
        upload_table   - reflected wafers_uploaded table
    """
    session = _SessionFactory()

    # Split schema.table if provided
    if "." in DB_UPLOAD_TABLE:
        schema_name, table_name = DB_UPLOAD_TABLE.split(".")
    else:
        schema_name, table_name = None, DB_UPLOAD_TABLE

    metadata = sqlalchemy.MetaData()
    upload_table = sqlalchemy.Table(
        table_name,
        metadata,
        schema=schema_name,
        autoload_with=_engine
    )

    return session, upload_table
