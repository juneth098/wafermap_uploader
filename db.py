# db.py
import sqlalchemy
from sqlalchemy import Table, MetaData, select, update, insert, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from configs import DB_URI, DB_UPLOAD_TABLE, DB_FACT_REPORT_TABLE

# ============================================================
# Engine (shared, safe pool settings)
# ============================================================
engine = sqlalchemy.create_engine(
    DB_URI,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
)

SessionFactory = sessionmaker(bind=engine)

# ============================================================
# Metadata
# ============================================================
metadata = MetaData()

# ============================================================
# Upload Status Table (WRITE)
# ============================================================
if "." in DB_UPLOAD_TABLE:
    UPLOAD_SCHEMA, UPLOAD_TABLE = DB_UPLOAD_TABLE.split(".")
else:
    UPLOAD_SCHEMA, UPLOAD_TABLE = None, DB_UPLOAD_TABLE

upload_table = Table(
    UPLOAD_TABLE,
    metadata,
    schema=UPLOAD_SCHEMA,
    autoload_with=engine,
)

# ============================================================
# Factory Report Table (READ ONLY)
# ============================================================
FACT_SCHEMA, FACT_TABLE = DB_FACT_REPORT_TABLE.split(".")

factory_table = Table(
    FACT_TABLE,
    metadata,
    schema=FACT_SCHEMA,
    autoload_with=engine,
)

# ============================================================
# Session helper
# ============================================================
def create_upload_session():
    """Session for upload status table (read/write)."""
    return SessionFactory()

def create_factory_session():
    """Session for factory report table (read-only)."""
    return SessionFactory()

# ============================================================
# Factory Report Lookup (READ ONLY)
# ============================================================
def get_factory_info(session, lot, wafer, product):
    """
    Returns machine / program / operator info from factory report DB.
    """
    lot_prefix = lot.split(".")[0]
    product_wildcard = product.split("-")[0]

    row = session.query(factory_table).filter(
        factory_table.c.Lot_No.like(f"{lot_prefix}%"),
        factory_table.c.ID == wafer,
        factory_table.c.Product.like(f"{product_wildcard}%")
    ).one_or_none()

    if row:
       machine = getattr(row, "Machine", "")
       program = getattr(row, "Program", "")
       operator = getattr(row, "Operator", "")
       operator_class = getattr(row, "Class", "")
       operator_id = f"{operator_class}-{operator}"
    else:
       machine = ""
       program = ""
       operator_id = ""

    return {
        "machine": machine,
        "program": program,
        "operator": operator,
        "operator_id": operator_id,
    }

# ============================================================
# REAL UPSERT for upload status table
# ============================================================
def upsert_upload(session, upload_table, product, lot, wafer, stage,
                  status="uploaded", agent="gtk_to_umc"):
    """
    Insert or update upload status.
    Works even if created_at / updated_at columns do NOT exist.
    """
    lot_prefix = lot.split(".")[0]
    now = datetime.now()

    # Get actual column names from DB
    cols = upload_table.c.keys()

    insert_values = {
        "Product": product,
        "Lot_Number": lot_prefix,
        "Wafer_Id": int(wafer),
        "stage": stage,
        "status": status,
        "upload_agent": agent,
        "created_at" : now,
    }

    update_values = {
        "status": status,
        "upload_agent": agent,
        "created_at": now,
    }


    try:
        existing = session.execute(
            select(upload_table.c.id).where(
                and_(
                    upload_table.c.Product == product,
                    upload_table.c.Lot_Number == lot_prefix,
                    upload_table.c.Wafer_Id == int(wafer),
                    upload_table.c.stage == stage
                )
            )
        ).first()

        if existing:
            session.execute(
                update(upload_table)
                .where(upload_table.c.id == existing.id)
                .values(**update_values)
            )
            print(f"[DB] Updated: Lot={lot_prefix}, Wafer={wafer}, Stage={stage}")
        else:
            session.execute(
                insert(upload_table).values(**insert_values)
            )
            print(f"[DB] Inserted: Lot={lot_prefix}, Wafer={wafer}, Stage={stage}")

        session.commit()
        return True

    except Exception as e:
        session.rollback()
        print(
            f"[DB] ERROR: UPSERT failed for Lot={lot_prefix}, "
            f"Wafer={wafer}, Stage={stage}: {e}"
        )
        return False
