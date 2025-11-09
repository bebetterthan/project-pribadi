#!/usr/bin/env python3
"""
Migration script to add progress tracking columns to scans table
Run this if database already exists: python migrate_add_progress.py
"""
import sqlite3
import os

DB_PATH = "pentest.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"✅ Database {DB_PATH} doesn't exist yet - will be created with new schema")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(scans)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'progress_message' not in columns:
            print("Adding 'progress_message' column...")
            cursor.execute("ALTER TABLE scans ADD COLUMN progress_message TEXT")
            print("✅ Added progress_message")
        else:
            print("✅ progress_message already exists")

        if 'progress_metadata' not in columns:
            print("Adding 'progress_metadata' column...")
            cursor.execute("ALTER TABLE scans ADD COLUMN progress_metadata TEXT")  # SQLite stores JSON as TEXT
            print("✅ Added progress_metadata")
        else:
            print("✅ progress_metadata already exists")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  DATABASE MIGRATION: Add Progress Tracking")
    print("=" * 60)
    print()
    migrate()
    print()
    print("You can now start the backend server!")
    print("=" * 60)

