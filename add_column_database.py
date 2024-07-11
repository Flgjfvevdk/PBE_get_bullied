from sqlalchemy import create_engine, Column, Integer, text
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

# Create the engine and session
engine = create_engine('sqlite:///PBE_db.sqlite3')
Session = sessionmaker(bind=engine)
session = Session()

# Add the new column to the table
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE player ADD COLUMN keys INTEGER DEFAULT 5'))

# Initialize the values for the existing records
session.execute(text('UPDATE player SET keys = 5 WHERE keys IS NULL'))
session.commit()