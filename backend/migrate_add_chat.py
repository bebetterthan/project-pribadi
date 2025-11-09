#!/usr/bin/env python3
"""
Migration: Add chat_messages table for SSE history
Run: python migrate_add_chat.py
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
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
        if cursor.fetchone():
            print("✅ chat_messages table already exists")
            conn.close()
            return

        print("Creating chat_messages table...")
        cursor.execute("""
            CREATE TABLE chat_messages (
                id TEXT PRIMARY KEY,
                scan_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                metadata_json TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
            )
        """)
        
        print("Creating indexes...")
        cursor.execute("CREATE INDEX ix_chat_messages_scan_id ON chat_messages(scan_id)")
        cursor.execute("CREATE INDEX ix_chat_messages_message_type ON chat_messages(message_type)")
        cursor.execute("CREATE INDEX ix_chat_messages_created_at ON chat_messages(created_at)")
        cursor.execute("CREATE INDEX ix_chat_scan_sequence ON chat_messages(scan_id, sequence)")
        cursor.execute("CREATE INDEX ix_chat_scan_created ON chat_messages(scan_id, created_at)")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("   - chat_messages table created")
        print("   - 5 indexes created for performance")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  DATABASE MIGRATION: Add Chat History")
    print("=" * 60)
    print()
    migrate()
    print()
    print("=" * 60)

