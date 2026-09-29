import logging
import os
import sys

from db.session import get_db
from hindsight.adapter import get_hindsight_adapter
from services.dataset_importer import DatasetImporter

logging.basicConfig(level=logging.INFO)


def run_import(file_path: str):
    with get_db() as db:
        try:
            from db.base import Base
            from db.session import engine

            print("Clearing old seed data...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

            adapter = get_hindsight_adapter()
            if hasattr(adapter, "_conn"):
                adapter._conn.execute("DELETE FROM memories")
                adapter._conn.commit()

            importer = DatasetImporter(session=db, hindsight_adapter=adapter)

            valid, result = importer.validate_workbook(file_path)
            if not valid:
                print("Validation failed:")
                print(result)
                sys.exit(1)

            print("Validation passed. Sizes:", result.get("sizes"))
            print("Importing dataset...")

            counts = importer.import_workbook(file_path)
            print("Import complete!")
            print(counts)
        except Exception as e:
            print(f"Error during import: {e}")
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("file_path", help="Path to Excel dataset")
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"File not found: {args.file_path}")
        sys.exit(1)

    run_import(args.file_path)
