"""
Purpose:
Safely migrate news_articles records from local PostgreSQL
to Neon PostgreSQL while preserving existing article IDs and data.
"""

import sys
from getpass import getpass
from pathlib import Path

from sqlalchemy import URL, MetaData, Table, create_engine, select, text

# Add project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database.connection import engine as neon_engine

TABLE_NAME = "news_articles"
BATCH_SIZE = 100


def main():
    # Connect to local PostgreSQL.
    local_password = getpass("Enter local PostgreSQL password: ")

    local_url = URL.create(
        drivername="postgresql+psycopg",
        username="postgres",
        password=local_password,
        host="localhost",
        port=5432,
        database="ai_news_intelligence",
    )

    local_engine = create_engine(local_url, pool_pre_ping=True)

    try:
        # Reflect the existing table structures.
        local_metadata = MetaData()
        neon_metadata = MetaData()

        local_table = Table(TABLE_NAME, local_metadata, autoload_with=local_engine)
        neon_table = Table(TABLE_NAME, neon_metadata, autoload_with=neon_engine)

        local_columns = set(local_table.columns.keys())
        neon_columns = set(neon_table.columns.keys())

        if local_columns != neon_columns:
            raise RuntimeError(
                "Local and Neon table columns do not match.\n"
                f"Local only: {local_columns - neon_columns}\n"
                f"Neon only: {neon_columns - local_columns}"
            )

        # Read local records.
        with local_engine.connect() as source:
            records = source.execute(select(local_table)).mappings().all()

        print(f"Local articles found: {len(records)}")

        # Stop if Neon already contains records.
        with neon_engine.connect() as destination:
            existing_count = destination.execute(
                select(text("COUNT(*)")).select_from(neon_table)
            ).scalar_one()

        if existing_count != 0:
            raise RuntimeError(
                f"Neon already contains {existing_count} records. "
                "Migration stopped to prevent duplicate data."
            )

        if not records:
            print("No local records found. Nothing to migrate.")
            return

        # Insert records into Neon in batches.
        with neon_engine.begin() as destination:
            for start in range(0, len(records), BATCH_SIZE):
                batch = [dict(record) for record in records[start : start + BATCH_SIZE]]
                destination.execute(neon_table.insert(), batch)

        # Verify migrated record count.
        with neon_engine.connect() as destination:
            migrated_count = destination.execute(
                select(text("COUNT(*)")).select_from(neon_table)
            ).scalar_one()

        print(f"Migration completed. Neon articles: {migrated_count}")

        if migrated_count != len(records):
            raise RuntimeError("Migration count verification failed.")

        # Reset the PostgreSQL sequence if the primary key uses one.
        primary_keys = list(local_table.primary_key.columns)

        if len(primary_keys) == 1:
            pk_name = primary_keys[0].name

            with neon_engine.begin() as destination:
                sequence = destination.execute(
                    text(
                        "SELECT pg_get_serial_sequence("
                        "'public.news_articles', :column_name)"
                    ),
                    {"column_name": pk_name},
                ).scalar_one_or_none()

                if sequence:
                    max_id = max(record[pk_name] for record in records)
                    destination.execute(
                        text(
                            "SELECT setval("
                            "CAST(:sequence_name AS regclass), "
                            ":max_id, true)"
                        ),
                        {
                            "sequence_name": sequence,
                            "max_id": max_id,
                        },
                    )
                    print("PostgreSQL ID sequence synchronized.")

        print("Local database was not modified.")

    finally:
        local_engine.dispose()


if __name__ == "__main__":
    main()
