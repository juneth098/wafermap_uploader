# db.py
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from configs import DB_URI, DB_UPLOAD_TABLE

# -------------------------
# Shared engine
# -------------------------
_engine = sqlalchemy.create_engine(DB_URI, pool_pre_ping=True)

_SessionFactory = sessionmaker(bind=_engine)


def create_session():
    """
    Returns a new SQLAlchemy session.
    Engine and session factory are shared globally.
    """
    return _SessionFactory()


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

def upsert_upload(session, upload_table, product, lot, wafer, stage, status="uploaded", agent="gtk_to_umc"):
    """
    Insert or update a row in the upload_table.
    Uses PC-local timestamp for created_at if inserting.
    """
    lot_prefix = lot.split(".")[0]

    try:
        session.execute(
            upload_table.insert().values(
                Product=product,
                Lot_Number=lot_prefix,
                Wafer_Id=int(wafer),
                stage=stage,
                status="uploaded",
                upload_agent="gtk_to_umc",
                created_at=datetime.now()
            )
        )
        print(f"[DB] Inserted: Lot={lot_prefix}, Wafer={wafer}, Stage={stage}")

        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(f"[DB] ERROR: DB UPSERT failed for Lot={lot}, Wafer={wafer}, Stage={stage}: {e}")
        return False