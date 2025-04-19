import psycopg2
import config
from game_objects import Point

def _get_db_connection():
    try:
        connection = psycopg2.connect(
            host=config.DB_HOST,
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            port=config.DB_PORT
        )
        return connection
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def points_to_text(points):
    return ";".join(f"{point.x}:{point.y}" for point in points)

def text_to_points(text):
    points = []
    if not text:
        return points
    try:
        pairs = text.split(';')
        for pair in pairs:
            if ':' in pair:
                x_str, y_str = pair.split(':')
                points.append(Point(int(x_str), int(y_str)))
    except (ValueError, IndexError) as e:
        print(f"Error parsing points text '{text}': {e}")
        return []
    return points

def find_user(user_name):
    connection = _get_db_connection()
    if not connection:
        return None

    find_query = f'''
        SELECT user_name, level, score, snake_body_coords
        FROM {config.DB_TABLE_NAME}
        WHERE user_name = %s
    '''
    user_data = None
    try:
        with connection.cursor() as cursor:
            cursor.execute(find_query, (user_name,))
            result = cursor.fetchone()
            if result:
                user_data = result
    except psycopg2.Error as error:
        print("DB Error (find_user):", error)
    finally:
        if connection:
            connection.close()
    return user_data

def create_new_user(user_name):
    connection = _get_db_connection()
    if not connection:
        return False

    insert_query = f'''
        INSERT INTO {config.DB_TABLE_NAME} (user_name, level, score, snake_body_coords)
        VALUES (%s, %s, %s, %s)
    '''
    success = False
    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_query, (user_name, 1, 0, ''))
            connection.commit()
        print(f"User '{user_name}' created successfully.")
        success = True
    except psycopg2.Error as error:
        print("DB Error (create_new_user):", error)
        connection.rollback()
    finally:
        if connection:
            connection.close()
    return success

def update_user_progress(user_name, level, score, snake_points):
    connection = _get_db_connection()
    if not connection:
        return False

    update_query = f'''
        UPDATE {config.DB_TABLE_NAME}
        SET level = %s, score = %s, snake_body_coords = %s
        WHERE user_name = %s
    '''
    success = False
    snake_coords_text = points_to_text(snake_points)
    try:
        with connection.cursor() as cursor:
            cursor.execute(update_query, (level, score, snake_coords_text, user_name))
            connection.commit()
        success = True
    except psycopg2.Error as error:
        print("DB Error (update_user_progress):", error)
        connection.rollback()
    finally:
        if connection:
            connection.close()
    return success