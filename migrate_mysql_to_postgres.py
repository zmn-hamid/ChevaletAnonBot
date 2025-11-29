#!/usr/bin/env python3
"""
MySQL to Postgres Migration Script
Migrates all tables from radioatu_mydatabase.csv to Postgres database
Tables: users, blocks, cids, reports
"""

import csv

from modules.Global.database import db_base
from modules.Global.log import logger


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

                # Determine which table based on the columns
                if (
                    "blocker_uid" in current_headers
                    and "blocked_uid" in current_headers
                ):
                    current_table = "blocks"
                elif "reported_id" in current_headers:
                    current_table = "reports"
                elif "uid" in current_headers and "cid" in current_headers:
                    current_table = "cids"
                elif "uid" in current_headers and "name" in current_headers:
                    current_table = "users"
                else:
                    current_table = None

                logger.info(f"Found {current_table} table header: {current_headers}")
                continue

            # Add data row to current table
            if current_table and current_headers:
                row_dict = dict(zip(current_headers, row))
                tables_data[current_table].append(row_dict)

    return tables_data


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

    # Connect to database
    conn = None
    try:
        conn = db_base.get_connection()
        cur = conn.cursor()

        stats = {}

        # # Ensure unique constraint exists on blocks table
        # logger.info("Ensuring unique constraint on blocks table...")
        # try:
        #     cur.execute("""
        #         ALTER TABLE blocks
        #         ADD CONSTRAINT unique_pair UNIQUE (blocker_uid, blocked_uid)
        #     """)
        #     conn.commit()
        # except:
        #     conn.rollback()

        # # Ensure unique constraint exists on cids table
        # logger.info("Ensuring unique constraint on cids table...")
        # try:
        #     cur.execute("""
        #         ALTER TABLE cids
        #         ADD CONSTRAINT cids_cid_key UNIQUE (cid)
        #     """)
        #     conn.commit()
        # except:
        #     conn.rollback()

        # Migrate blocks table
        if tables_data["blocks"]:
            logger.info(f"Migrating {len(tables_data['blocks'])} blocks...")
            blocks_data = [
                (row["blocker_uid"], row["blocked_uid"])
                for row in tables_data["blocks"]
            ]

            cur.executemany(
                """
                INSERT INTO blocks (blocker_uid, blocked_uid)
                VALUES (%s, %s)
                ON CONFLICT (blocker_uid, blocked_uid) DO NOTHING
            """,
                blocks_data,
            )

            stats["blocks"] = {"total": len(blocks_data), "inserted": cur.rowcount}
            conn.commit()
            logger.info(
                f"Blocks: {cur.rowcount} inserted, {len(blocks_data) - cur.rowcount} skipped"
            )

        # Migrate cids table
        if tables_data["cids"]:
            logger.info(f"Migrating {len(tables_data['cids'])} cids...")
            cids_data = [(row["uid"], row["cid"]) for row in tables_data["cids"]]

            cur.executemany(
                """
                INSERT INTO cids (uid, cid)
                VALUES (%s, %s)
                ON CONFLICT (cid) DO NOTHING
            """,
                cids_data,
            )

            stats["cids"] = {"total": len(cids_data), "inserted": cur.rowcount}
            conn.commit()
            logger.info(
                f"CIDs: {cur.rowcount} inserted, {len(cids_data) - cur.rowcount} skipped"
            )

        # Migrate users table
        if tables_data["users"]:
            logger.info(f"Migrating {len(tables_data['users'])} users...")
            users_data = []

            for row in tables_data["users"]:
                users_data.append(
                    (
                        row["uid"],
                        row["name"],
                        row.get("is_banned", "FALSE").upper() in ("TRUE", "1", "t"),
                        row.get("warning", "TRUE").upper() in ("TRUE", "1", "t"),
                        row.get("seen_option", "FALSE").upper() in ("TRUE", "1", "t"),
                        row.get("wpp", "TRUE").upper() in ("TRUE", "1", "t"),
                        int(row.get("cid_limit", 2)),
                        row.get("custom_tag") if row.get("custom_tag") else None,
                        row.get("audio_tag", "[ناشناس]"),
                        row.get("chevaletid") if row.get("chevaletid") else None,
                    )
                )

            cur.executemany(
                """
                INSERT INTO users (uid, name, is_banned, warning, seen_option, wpp,
                                  cid_limit, custom_tag, audio_tag, chevaletid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (uid) DO NOTHING
            """,
                users_data,
            )

            stats["users"] = {"total": len(users_data), "inserted": cur.rowcount}
            conn.commit()
            logger.info(
                f"Users: {cur.rowcount} inserted, {len(users_data) - cur.rowcount} skipped"
            )

        # Migrate reports table
        if tables_data["reports"]:
            logger.info(f"Migrating {len(tables_data['reports'])} reports...")
            reports_data = [(row["reported_id"],) for row in tables_data["reports"]]

            cur.executemany(
                """
                INSERT INTO reports (reported_id)
                VALUES (%s)
            """,
                reports_data,
            )

            stats["reports"] = {"total": len(reports_data), "inserted": cur.rowcount}
            conn.commit()
            logger.info(f"Reports: {cur.rowcount} inserted")

        # # Print summary
        # print("\n" + "="*60)
        # print("MIGRATION SUMMARY")
        # print("="*60)

        # for table_name in ['users', 'blocks', 'cids', 'reports']:
        #     if table_name in stats:
        #         s = stats[table_name]
        #         skipped = s['total'] - s['inserted']
        #         print(f"{table_name.upper():10} - Total: {s['total']:6,} | "
        #               f"Inserted: {s['inserted']:6,} | Skipped: {skipped:6,}")

        # print("="*60 + "\n")

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
