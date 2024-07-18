from sqlalchemy import create_engine, Column, Integer, text
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column
from database import Base

# # Create the engine and session
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# Session = sessionmaker(bind=engine)
# session = Session()

# # Add the new column to the table
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE player ADD COLUMN keys INTEGER DEFAULT 5'))

# # Initialize the values for the existing records
# session.execute(text('UPDATE player SET keys = 5 WHERE keys IS NULL'))
# session.commit()


# # Créer le moteur et la session
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# Session = sessionmaker(bind=engine)
# session = Session()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE bully ADD COLUMN in_reserve BOOLEAN DEFAULT 0'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE bully SET in_reserve = 0 WHERE in_reserve IS NULL'))
# session.commit()

# Créer le moteur et la session
engine = create_engine('sqlite:///PBE_db.sqlite3')
Session = sessionmaker(bind=engine)
session = Session()

# Modifier le schéma pour ajouter la colonne in_reserve
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE bully ADD COLUMN in_reserve BOOLEAN DEFAULT False'))

# Initialiser les valeurs pour les enregistrements existants
session.execute(text('UPDATE bully SET in_reserve = False WHERE in_reserve IS NULL'))
session.commit()
