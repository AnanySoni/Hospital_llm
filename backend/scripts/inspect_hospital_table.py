from backend.core.database import engine
from sqlalchemy import inspect

if __name__ == "__main__":
    inspector = inspect(engine)
    columns = inspector.get_columns('hospitals')
    print("--- hospitals table schema ---")
    for col in columns:
        print(f"{col['name']}: {col['type']}, nullable={col['nullable']}") 