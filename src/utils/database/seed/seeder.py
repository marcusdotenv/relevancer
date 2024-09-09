import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def read_dump_and_insert(file_name, db):
    try:
        cursor = db.cursor()
        with open(file_name, 'r') as file:
            all_terms = list(set([file_line.strip().lower() for file_line in file]))
            values = ", ".join(["(%s)"] * len(all_terms))
            insert_query = f"INSERT INTO terms (term) VALUES {values};"
            cursor.execute(insert_query, all_terms)
        db.commit()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")

file_name = 'words.txt'  

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)

db = psycopg2.connect(
    dbname=os.getenv("DATABASE_NAME"),
    user=os.getenv("DATABASE_USER"),
    password=os.getenv("DATABASE_PASSWD"),
    host=os.getenv("DATABASE_HOST")
)

read_dump_and_insert(path, db)


db.close()
