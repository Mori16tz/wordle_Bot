from typing import Iterator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from database.models import Base


engine = create_engine("mysql+pymysql://root:@localhost:3306/wordle",
                       pool_pre_ping=True, pool_recycle=3600, pool_size=5, max_overflow=10)

inspector = inspect(engine)
existing_tables = inspector.get_table_names()
Base.metadata.create_all(engine)

# for table_name, table in Base.metadata.tables.items():
#     if table_name in existing_tables:
#         existing_columns = {col['name']
#                             for col in inspector.get_columns(table_name)}
#         model_columns = {col.name for col in table.columns}
#         new_columns = model_columns - existing_columns

#         if new_columns:
#             for col_name in new_columns:
#                 col = table.columns[col_name]
#                 col_type = col.type.compile(engine.dialect)
#                 nullable = "NULL" if col.nullable else "NOT NULL"
#                 default = f"DEFAULT {col.default.arg}" if col.default else ""

#                 sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} {nullable} {default}"
#                 with engine.connect() as conn:
#                     conn.execute(text(sql))
#                     conn.commit()

SESSION = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def open_session() -> Iterator[Session]:
    """
    Context manager for database session.

    """
    session = SESSION()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
