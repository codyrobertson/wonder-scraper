"""
Migration: Add Polar subscription fields to User table
           and create Watchlist + EmailPreferences tables
"""
from sqlmodel import Session, text
from app.db import engine


def add_column_if_not_exists(session: Session, table: str, column: str, col_type: str, default=None):
    """Helper to add column if it doesn't exist"""
    try:
        session.exec(text(f"SELECT {column} FROM {table} LIMIT 1"))
        print(f"  Column '{column}' already exists in '{table}'")
    except Exception:
        session.rollback()
        default_clause = f" DEFAULT {default}" if default is not None else ""
        try:
            session.exec(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}{default_clause}"))
            session.commit()
            print(f"  Added column '{column}' to '{table}'")
        except Exception as e:
            print(f"  Failed to add '{column}': {e}")
            session.rollback()


def create_table_if_not_exists(session: Session, table: str, create_sql: str):
    """Helper to create table if it doesn't exist"""
    try:
        session.exec(text(f"SELECT 1 FROM {table} LIMIT 1"))
        print(f"  Table '{table}' already exists")
    except Exception:
        session.rollback()
        try:
            session.exec(text(create_sql))
            session.commit()
            print(f"  Created table '{table}'")
        except Exception as e:
            print(f"  Failed to create '{table}': {e}")
            session.rollback()


def migrate():
    with Session(engine) as session:
        # ==================== USER TABLE - Subscription Fields ====================
        print("\n=== Adding subscription fields to User table ===")

        add_column_if_not_exists(session, '"user"', 'subscription_tier',
                                  "VARCHAR(20)", "'free'")
        add_column_if_not_exists(session, '"user"', 'subscription_status',
                                  "VARCHAR(20)", "NULL")
        add_column_if_not_exists(session, '"user"', 'subscription_id',
                                  "VARCHAR(255)", "NULL")
        add_column_if_not_exists(session, '"user"', 'polar_customer_id',
                                  "VARCHAR(255)", "NULL")
        add_column_if_not_exists(session, '"user"', 'subscription_current_period_end',
                                  "TIMESTAMP", "NULL")

        # Add indexes for subscription fields
        try:
            session.exec(text('CREATE INDEX IF NOT EXISTS ix_user_subscription_id ON "user" (subscription_id)'))
            session.exec(text('CREATE INDEX IF NOT EXISTS ix_user_polar_customer_id ON "user" (polar_customer_id)'))
            session.commit()
            print("  Added indexes for subscription fields")
        except Exception as e:
            print(f"  Indexes may already exist: {e}")
            session.rollback()

        # ==================== WATCHLIST TABLE ====================
        print("\n=== Creating Watchlist table ===")

        watchlist_sql = """
        CREATE TABLE IF NOT EXISTS watchlist (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
            card_id INTEGER NOT NULL REFERENCES card(id) ON DELETE CASCADE,
            alert_enabled BOOLEAN DEFAULT TRUE,
            alert_type VARCHAR(20) DEFAULT 'below',
            target_price FLOAT,
            treatment VARCHAR(50),
            notify_email BOOLEAN DEFAULT TRUE,
            notes TEXT,
            last_alerted_at TIMESTAMP,
            last_alerted_price FLOAT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(user_id, card_id)
        )
        """
        create_table_if_not_exists(session, 'watchlist', watchlist_sql)

        # Add indexes for watchlist
        try:
            session.exec(text('CREATE INDEX IF NOT EXISTS ix_watchlist_user_id ON watchlist (user_id)'))
            session.exec(text('CREATE INDEX IF NOT EXISTS ix_watchlist_card_id ON watchlist (card_id)'))
            session.commit()
            print("  Added indexes for watchlist")
        except Exception as e:
            print(f"  Watchlist indexes may already exist: {e}")
            session.rollback()

        # ==================== EMAIL PREFERENCES TABLE ====================
        print("\n=== Creating EmailPreferences table ===")

        email_prefs_sql = """
        CREATE TABLE IF NOT EXISTS emailpreferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
            daily_digest BOOLEAN DEFAULT FALSE,
            weekly_report BOOLEAN DEFAULT TRUE,
            portfolio_summary BOOLEAN DEFAULT TRUE,
            price_alerts BOOLEAN DEFAULT TRUE,
            new_listings BOOLEAN DEFAULT FALSE,
            digest_hour INTEGER DEFAULT 9,
            digest_day INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
        create_table_if_not_exists(session, 'emailpreferences', email_prefs_sql)

        # Add index for emailpreferences
        try:
            session.exec(text('CREATE INDEX IF NOT EXISTS ix_emailpreferences_user_id ON emailpreferences (user_id)'))
            session.commit()
            print("  Added index for emailpreferences")
        except Exception as e:
            print(f"  EmailPreferences index may already exist: {e}")
            session.rollback()

        print("\n=== Migration complete! ===")


if __name__ == "__main__":
    migrate()
