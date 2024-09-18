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

# # Créer le moteur et la session
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# Session = sessionmaker(bind=engine)
# session = Session()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE bully ADD COLUMN in_reserve BOOLEAN DEFAULT False'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE bully SET in_reserve = False WHERE in_reserve IS NULL'))
# session.commit()

# # Créer le moteur et la session
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# Session = sessionmaker(bind=engine)
# session = Session()

# ##############################################################################################
# # CREER la table consommable
# # Créer le moteur et la session
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# Session = sessionmaker(bind=engine)
# session = Session()
# # Créer la table consommable
# with engine.connect() as conn:
#     conn.execute(text('''
#     CREATE TABLE consommable (
#         id INTEGER PRIMARY KEY,
#         name TEXT NOT NULL,
#         type TEXT NOT NULL,
#         player_id INTEGER,
#         FOREIGN KEY (player_id) REFERENCES player(id)
#     )
#     '''))
# # Fermer la session lorsque vous avez fini
# session.close()

# ###############################################################################################
# # AJOUTER les colonnes dans la table consommable OLD VERSION
# # Créer le moteur et la session
# engine = create_engine('sqlite:///db.sqlite3')
# Session = sessionmaker(bind=engine)
# session = Session()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE consommable ADD COLUMN stat_buff FLOAT DEFAULT ""'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE consommable SET stat_buff = "" WHERE stat_buff IS NULL'))
# session.commit()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE consommable ADD COLUMN stat_debuff FLOAT DEFAULT ""'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE consommable SET stat_debuff = "" WHERE stat_debuff IS NULL'))
# session.commit()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE consommable ADD COLUMN value FLOAT DEFAULT 0'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE consommable SET value = 0 WHERE value IS NULL'))
# session.commit()
# # ______________________________________________________________________________________________________________________________________________________
# # #################################################### # #################################################### # ###################################################
# # Supprimer la table ITEM de la bdd ___________________________________________________________________________
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# with engine.connect() as connection:
#     # Envoi de la commande SQL pour supprimer la table
#     connection.execute(text("DROP TABLE IF EXISTS item"))
#     connection.commit()
# # ______________________________________________________________________________________________________________________________________________________
# # #################################################### # #################################################### # ###########################################
# # Supprimer la table CONSOMMABLE de la bdd ___________________________________________________________________________
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# with engine.connect() as connection:
#     # Envoi de la commande SQL pour supprimer la table
#     connection.execute(text("DROP TABLE IF EXISTS consommable"))
#     connection.commit()
# #______________________________________________________________________________________________________________________________________________________

# # Vider la table CONSOMMABLE de la bdd ___________________________________________________________________________
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# with engine.connect() as connection:
#     # Envoi de la commande SQL pour vider la table
#     connection.execute(text("DELETE FROM consommable"))
#     connection.commit()
# #______________________________________________________________________________________________________________________________________________________

# # ###############################################################################################
# # AJOUTER les colonnes de la table consommable NEW VERSION
# # Créer le moteur et la session
# engine = create_engine('sqlite:///db.sqlite3')
# Session = sessionmaker(bind=engine)
# session = Session()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE consommable ADD COLUMN stat_buff FLOAT DEFAULT ""'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE consommable SET stat_buff = "" WHERE stat_buff IS NULL'))
# session.commit()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE consommable ADD COLUMN stat_debuff FLOAT DEFAULT ""'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE consommable SET stat_debuff = "" WHERE stat_debuff IS NULL'))
# session.commit()

# # Modifier le schéma pour ajouter la colonne in_reserve
# with engine.connect() as conn:
#     conn.execute(text('ALTER TABLE consommable ADD COLUMN value FLOAT DEFAULT 0'))

# # Initialiser les valeurs pour les enregistrements existants
# session.execute(text('UPDATE consommable SET value = 0 WHERE value IS NULL'))
# session.commit()
# # ______________________________________________________________________________________________________________________________________________________


# #########################################################################################################################################
# import consommable
# engine = create_engine('sqlite:///PBE_db.sqlite3')
# # Créer toutes les tables
# Base.metadata.create_all(engine, tables=[consommable.Consommable.__tablename__])
# # ______________________________________________________________________________________________________________________________________________________
