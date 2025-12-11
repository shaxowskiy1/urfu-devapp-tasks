from sqlalchemy import create_engine

engine = create_engine(
    "sqlite:///app.db",
    echo=True  # Логирование SQL-запросов
)