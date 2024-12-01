import json
import os
import re
import pymysql

# Database connection info from the environment variables
rds_host = os.environ['RDS_HOST']
rds_port = int(os.environ['RDS_PORT'])
db_user = os.environ['DB_USER']
db_password = os.environ['DB_PASSWORD']
db_name = os.environ['DB_NAME']
sql_filepath = os.environ["SQL_FILEPATH"]

# Establish a connection to the RDS instance
def connect_to_rds():
    connection = pymysql.connect(
        host=rds_host,
        port=rds_port,
        user=db_user,
        password=db_password,
        db=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Lambda function handler
def lambda_handler(event, context):
    schema_path = f"./{sql_filepath}"
    if not os.path.exists(schema_path):
        error_message = f"File {sql_filepath} not found."
        print(error_message)  # For debugging purposes
        return {
            'statusCode': 400,
            'body': json.dumps({"error": error_message})
        }

    connection = connect_to_rds()

    try:
        with connection.cursor() as cursor:
            # Read the downloaded SQL file
            with open(schema_path, 'r') as schema_file:
                schema_sql = schema_file.read()

                # Split the SQL file into individual statements
                statements = re.split(r';\s*', schema_sql.strip())

                # Execute each SQL statement individually
                for statement in statements:
                    if statement.strip():  # Skip empty statements
                        cursor.execute(statement)

            # Commit the changes
            connection.commit()

            # Output the current database name
            cursor.execute("SELECT DATABASE() AS current_db;")
            db_result = cursor.fetchone()
            current_db = db_result['current_db'] if db_result else "Unknown"

            # Show all tables in the current database
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            table_list = [table[f'Tables_in_{current_db}'] for table in tables]

            response = {
                'database': current_db,
                'tables': table_list
            }
            print(f"Database and tables: {response}")

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({"error": error_message})
        }
    finally:
        connection.close()
