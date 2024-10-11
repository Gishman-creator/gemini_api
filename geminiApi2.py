import psycopg2
import google.generativeai as genai
import time
import signal
import threading

# Configure Google AI API key
genai.configure(api_key="AIzaSyA7XbBQYvt4DLZLzFJAEa979UGEDni6rnA")

# Set up model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=generation_config,
)

progress = 0
total_rows = 0
lock = threading.Lock()
connected_once = False
interrupted = False  # To track if the program is interrupted

def get_nationality(author_name):
    """Query the AI model for the author's nationality."""
    chat_session = model.start_chat(history=[])
    prompt = f"Write down the nationality only of {author_name}, and if English write down 'British' only."
    response = chat_session.send_message(prompt)
    return response.text.strip()

def get_bio(author_name):
    """Query the AI model for the author's bio (up to 60 words)."""
    chat_session = model.start_chat(history=[])
    prompt = f"Write down a small bio about {author_name}, not more than 60 words and start with the full names."
    response = chat_session.send_message(prompt)
    return response.text.strip()

def get_awards(author_name):
    """Query the AI model for the author's awards (up to 5 in a specific format)."""
    chat_session = model.start_chat(history=[])
    prompt = (f"Write down only the awards won by {author_name} and don't add any words. Use this format: "
              "'award_1 (year_received), award_2 (year_received), award_3 (year_received), award_4 (year_received), "
              "award_5 (year_received),...' max of 5. If more, add '...'. If none, write 'None'.")
    response = chat_session.send_message(prompt)
    return response.text.strip()

def connect_db():
    """Establish a connection to the PostgreSQL database."""
    try:
        connection = psycopg2.connect(
            dbname="readrack3",
            user="postgres",  # Replace with your PostgreSQL username
            password="root",  # Replace with your PostgreSQL password
            host="localhost",  # Adjust if needed
            port="5432"  # Default PostgreSQL port
        )
        return connection
    except Exception as error:
        print(f"Error connecting to database: {error}")
        return None

def update_author_in_db(connection, author_id, nationality, bio, awards):
    """Update the author information in the database."""
    try:
        cursor = connection.cursor()
        query = """
        UPDATE authors 
        SET nationality = %s, bio = %s, awards = %s 
        WHERE id = %s;
        """
        cursor.execute(query, (nationality, bio, awards, author_id))
        connection.commit()
        print(f"Updated author ID {author_id}")
    except Exception as error:
        print(f"Error updating author ID {author_id}: {error}")
        connection.rollback()

def fetch_authors_with_missing_data(connection):
    """Fetch authors with missing nationality, bio, or awards."""
    try:
        cursor = connection.cursor()
        query = """
        SELECT id, author_name FROM authors 
        WHERE nationality IS NULL OR bio IS NULL OR awards IS NULL;
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as error:
        print(f"Error fetching authors: {error}")
        return []

def handle_interrupt(signal, frame):
    """Handle program interruptions and set interrupted flag."""
    global interrupted
    interrupted = True
    print("\nProgram interrupted. Saving progress before exiting...")

# Register the signal handler for interruptions (Ctrl+C, etc.)
signal.signal(signal.SIGINT, handle_interrupt)

def main():
    connection = connect_db()
    
    if connection is None:
        print("Database connection failed.")
        return
    
    authors = fetch_authors_with_missing_data(connection)
    global total_rows
    total_rows = len(authors)
    
    if total_rows == 0:
        print("No authors with missing data found.")
        connection.close()
        return
    
    try:
        for author_id, author_name in authors:
            if author_name:
                print(f"Processing author: {author_name}")
                
                # Query AI to fill missing details
                nationality = get_nationality(author_name)
                bio = get_bio(author_name)
                awards = get_awards(author_name)

                # Update the database with the fetched details
                update_author_in_db(connection, author_id, nationality, bio, awards)

                # Update progress
                global progress
                with lock:
                    progress += 1
                    percent_complete = (progress / total_rows) * 100
                    print(f"Progress: {progress}/{total_rows} ({percent_complete:.2f}%)")

                # Add a small delay between requests to avoid rate limits
                time.sleep(0.05)

            # Check if the program was interrupted
            if interrupted:
                break

    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        connection.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()
