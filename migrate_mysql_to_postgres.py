#!/usr/bin/env python3
"""
MySQL to Postgres Migration Script
Migrates all tables from radioatu_mydatabase.csv to Postgres database
Tables: users, blocks, cids, reports
"""

import csv

from modules.Global.database import db_base
from modules.Global.log import logger


# === Utility Functions ===


def is_valid_value(value):
    """Check if a value is valid (not None, empty, or 'NULL' string)"""
    return value and value != "NULL"


def get_value_or_none(row, key):
    """Get value from row or return None if invalid"""
    val = row.get(key)
    return val if is_valid_value(val) else None


def to_boolean(value, default=False):
    """Convert string value to boolean"""
    if not value:
        return default
    return value.upper() in ("TRUE", "1", "t")


def identify_table(headers):
    """Determine table type based on column headers"""
    if "blocker_uid" in headers and "blocked_uid" in headers:
        return "blocks"
    elif "reported_id" in headers:
        return "reports"
    elif "uid" in headers and "cid" in headers:
        return "cids"
    elif "uid" in headers and "name" in headers:
        return "users"
    return None


# === CSV Parsing ===


def parse_multi_table_csv(csv_file):
    """
    Parse CSV file containing multiple tables with headers
    Returns dict with table names as keys and list of rows as values
    """
    tables_data = {"users": [], "blocks": [], "cids": [], "reports": []}
    current_table = None
    current_headers = None

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)

        for row in reader:
            if not row:
                continue

            # Check if this is a header row
            if row[0] == "id":
                current_headers = row
                current_table = identify_table(current_headers)
                logger.info(f"Found {current_table} table header: {current_headers}")
                continue

            # Add data row to current table
            if current_table and current_headers:
                row_dict = dict(zip(current_headers, row))
                tables_data[current_table].append(row_dict)

    return tables_data


# === Data Preparation ===


def prepare_blocks_data(rows):
    """Prepare blocks table data for insertion"""
    return [
        (row["blocker_uid"], row["blocked_uid"])
        for row in rows
        if is_valid_value(row.get("blocker_uid"))
        and is_valid_value(row.get("blocked_uid"))
    ]


def prepare_cids_data(rows):
    """Prepare cids table data for insertion"""
    return [
        (row["uid"], row["cid"])
        for row in rows
        if is_valid_value(row.get("uid")) and is_valid_value(row.get("cid"))
    ]


def prepare_users_data(rows):
    """Prepare users table data for insertion"""
    users_data = []

    for row in rows:
        # Skip rows with missing required fields
        if not is_valid_value(row.get("uid")) or not is_valid_value(row.get("name")):
            continue

        # Get cid_limit with default value
        cid_limit = row.get("cid_limit", "2")
        cid_limit = 2 if not is_valid_value(cid_limit) else int(cid_limit)

        # Get audio_tag with default value
        audio_tag = row.get("audio_tag")
        audio_tag = "[ناشناس]" if not is_valid_value(audio_tag) else audio_tag

        users_data.append(
            (
                row["uid"],
                row["name"],
                to_boolean(row.get("is_banned"), default=False),
                to_boolean(row.get("warning"), default=True),
                to_boolean(row.get("seen_option"), default=False),
                to_boolean(row.get("wpp"), default=True),
                cid_limit,
                get_value_or_none(row, "custom_tag"),
                audio_tag,
                get_value_or_none(row, "chevaletid"),
            )
        )

    return users_data


def prepare_reports_data(rows):
    """Prepare reports table data for insertion"""
    return [
        (row["reported_id"],)
        for row in rows
        if is_valid_value(row.get("reported_id"))
    ]


# === Table Migration ===


def migrate_blocks(cursor, conn, rows):
    """Migrate blocks table"""
    if not rows:
        return

    logger.info(f"Migrating {len(rows)} blocks...")
    data = prepare_blocks_data(rows)

    cursor.executemany(
        """
        INSERT INTO blocks (blocker_uid, blocked_uid)
        VALUES (%s, %s)
        ON CONFLICT (blocker_uid, blocked_uid) DO NOTHING
        """,
        data,
    )

    conn.commit()
    logger.info(f"Blocks: {cursor.rowcount} inserted, {len(data) - cursor.rowcount} skipped")


def migrate_cids(cursor, conn, rows):
    """Migrate cids table"""
    if not rows:
        return

    logger.info(f"Migrating {len(rows)} cids...")
    data = prepare_cids_data(rows)

    cursor.executemany(
        """
        INSERT INTO cids (uid, cid)
        VALUES (%s, %s)
        ON CONFLICT (cid) DO NOTHING
        """,
        data,
    )

    conn.commit()
    logger.info(f"CIDs: {cursor.rowcount} inserted, {len(data) - cursor.rowcount} skipped")


def migrate_users(cursor, conn, rows):
    """Migrate users table"""
    if not rows:
        return

    logger.info(f"Migrating {len(rows)} users...")
    data = prepare_users_data(rows)

    cursor.executemany(
        """
        INSERT INTO users (uid, name, is_banned, warning, seen_option, wpp,
                          cid_limit, custom_tag, audio_tag, chevaletid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (uid) DO NOTHING
        """,
        data,
    )

    conn.commit()
    logger.info(f"Users: {cursor.rowcount} inserted, {len(data) - cursor.rowcount} skipped")


def migrate_reports(cursor, conn, rows):
    """Migrate reports table"""
    if not rows:
        return

    logger.info(f"Migrating {len(rows)} reports...")
    data = prepare_reports_data(rows)

    cursor.executemany(
        """
        INSERT INTO reports (reported_id)
        VALUES (%s)
        """,
        data,
    )

    conn.commit()
    logger.info(f"Reports: {cursor.rowcount} inserted")


# === Main Migration ===


def migrate_all_tables():
    """Migrate all tables from CSV to Postgres"""
    csv_file = "radioatu_mydatabase.csv"

    # Parse CSV file
    logger.info(f"Parsing {csv_file}...")
    try:
        tables_data = parse_multi_table_csv(csv_file)
        for table_name, data in tables_data.items():
            logger.info(f"Found {len(data)} records for {table_name} table")
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
        return
    except Exception as e:
        logger.error(f"Error parsing CSV file: {e}")
        raise

    # Connect to database and migrate
    conn = None
    try:
        conn = db_base.get_connection()
        cursor = conn.cursor()

        # Recreate database tables
        db_base.make_tables()

        # Migrate each table
        migrate_blocks(cursor, conn, tables_data["blocks"])
        migrate_cids(cursor, conn, tables_data["cids"])
        migrate_users(cursor, conn, tables_data["users"])
        migrate_reports(cursor, conn, tables_data["reports"])

        logger.info("Migration completed successfully!")

    except Exception as e:
        logger.error(f"Error during migration: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            db_base.put_connection(conn)


if __name__ == "__main__":
    logger.info("Starting MySQL to Postgres migration...")
    migrate_all_tables()
    logger.info("Migration process finished")
