import psycopg2
import config

def setup_database(force_recreate=False):
    """
    Connects to the PostgreSQL database and creates the score table
    if it doesn't exist.
    """
    connection = None
    try:
        connection = psycopg2.connect(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            port=config.DB_PORT
        )
        cursor = connection.cursor()

        if force_recreate:
            print(f"WARNING: Dropping table {config.DB_TABLE_NAME} if it exists...")
            cursor.execute(f'DROP TABLE IF EXISTS {config.DB_TABLE_NAME}')
            print(f"Table {config.DB_TABLE_NAME} dropped (if existed).")

        create_table_query = f'''
            CREATE TABLE IF NOT EXISTS {config.DB_TABLE_NAME} (
                user_name TEXT PRIMARY KEY NOT NULL,
                level INT,
                score INT,
                snake_body_coords TEXT
            )
        '''

        cursor.execute(create_table_query)
        connection.commit()
        print(f"Table '{config.DB_TABLE_NAME}' checked/created successfully.")

    except psycopg2.Error as error:
        print('Database Error:', error)
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    print("Setting up the database...")
    setup_database()
