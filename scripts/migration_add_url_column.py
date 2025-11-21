from sqlmodel import Session, text
from app.db import engine

def migrate():
    with Session(engine) as session:
        print("Checking for 'url' column in 'marketprice' table...")
        try:
            # Attempt to query the column to see if it exists
            session.exec(text("SELECT url FROM marketprice LIMIT 1"))
            print("Column 'url' already exists.")
        except Exception:
            print("Column 'url' missing. Adding it now...")
            session.rollback() # Reset transaction after error
            try:
                session.exec(text("ALTER TABLE marketprice ADD COLUMN url VARCHAR DEFAULT NULL"))
                session.commit()
                print("Successfully added 'url' column.")
            except Exception as e:
                print(f"Failed to add column: {e}")

if __name__ == "__main__":
    migrate()

