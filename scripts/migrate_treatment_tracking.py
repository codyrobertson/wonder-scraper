"""
Database migration to add treatment column to marketsnapshot table.
This enables Option 2: Treatment-specific price tracking.

Run this script to add the treatment field to existing MarketSnapshot records.
"""
from sqlalchemy import text
from app.db import engine

def migrate():
    """Add treatment column to marketsnapshot table."""
    print("Starting migration: Adding treatment column to marketsnapshot...")

    with engine.begin() as conn:
        # Check if column already exists
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='marketsnapshot' AND column_name='treatment';
        """)
        result = conn.execute(check_query).first()

        if result:
            print("✓ Column 'treatment' already exists. Skipping migration.")
            return

        # Add treatment column with default value
        print("Adding 'treatment' column...")
        add_column_query = text("""
            ALTER TABLE marketsnapshot
            ADD COLUMN treatment VARCHAR NOT NULL DEFAULT 'All';
        """)
        conn.execute(add_column_query)

        # Create index on treatment column for performance
        print("Creating index on 'treatment' column...")
        create_index_query = text("""
            CREATE INDEX ix_marketsnapshot_treatment ON marketsnapshot(treatment);
        """)
        conn.execute(create_index_query)

        print("✓ Migration complete!")
        print("\nNext Steps:")
        print("1. Current snapshots default to 'All' treatments (mixed)")
        print("2. Future: Modify scraper to create separate snapshots per treatment")
        print("3. Future: Query snapshots by card_id + treatment for variant-specific prices")

if __name__ == "__main__":
    migrate()
