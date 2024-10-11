import openpyxl
import psycopg2

# Database connection setup
def connect_db():
    try:
        connection = psycopg2.connect(
            dbname="readrack3",
            user="postgres",  # Replace with your PostgreSQL username
            password="root",  # Replace with your PostgreSQL password
            host="localhost",  # Replace if your PostgreSQL runs on a different host
            port="5432"  # Default port for PostgreSQL
        )
        return connection
    except Exception as error:
        print(f"Error connecting to database: {error}")
        return None

# Insert author names into the database
def insert_author_name(connection, author_name):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO authors (author_name) VALUES (%s);"
        cursor.execute(query, (author_name,))
        connection.commit()
        print(f"Inserted: {author_name}")
    except Exception as error:
        print(f"Error inserting {author_name}: {error}")
        connection.rollback()

# Read author names from Excel file (column B)
def read_authors_from_excel(file_path):
    try:
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        authors = []
        for row in sheet.iter_rows(min_row=2, min_col=2, max_col=2, values_only=True):  # Assuming author names are in column B
            author_name = row[0]
            if author_name:
                authors.append(author_name.strip())
        return authors
    except Exception as error:
        print(f"Error reading Excel file: {error}")
        return []

def main():
    file_path = "readrack_authors.xlsx"  # Replace with the path to your Excel file
    authors = read_authors_from_excel(file_path)
    
    if not authors:
        print("No authors found to insert.")
        return
    
    connection = connect_db()
    
    if connection is None:
        print("Database connection failed.")
        return

    try:
        for author_name in authors:
            insert_author_name(connection, author_name)
    finally:
        connection.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()
