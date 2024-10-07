import mysql.connector
from mysql.connector import Error
from app.config import Config


def execute_sql_file(connection, sql_file):
    try:
        with open(sql_file, 'r') as file:
            sql_script = file.read()

        cursor = connection.cursor()

        # Split the SQL script into individual statements
        statements = sql_script.split(';')

        for statement in statements:
            if statement.strip():
                cursor.execute(statement)

        connection.commit()
        print("SQL script executed successfully")
    except Error as e:
        print(f"Error executing SQL script: {e}")
    finally:
        if cursor:
            cursor.close()


def main():
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME
        )

        if connection.is_connected():
            print("Connected to MySQL database")
            execute_sql_file(connection, 'schema.sql')
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("MySQL connection closed")


if __name__ == "__main__":
    main()