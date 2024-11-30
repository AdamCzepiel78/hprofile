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
    # Download SQL file from S3

    schema_path = f"./{sql_filepath}"
    if not os.path.exists(schema_path):
        error_message = f"File {sql_filepath} not found."
        print(error_message)  # For debugging purposes, you can log it as well
        return {
            'statusCode': 400,
            'body': json.dumps({"error": error_message})
        }
    connection = connect_to_rds()

    with connection.cursor() as cursor:
        # Read the downloaded SQL file
        with open(schema_path, 'r') as schema_file:
            schema_sql = schema_file.read()

            # Split the SQL file by the semicolon (;) to get individual statements
            # This assumes each SQL statement ends with a semicolon and may have multiple lines.
            # Use re.split to handle multiple semicolons, ignoring semicolons within comments or strings.
            statements = re.split(r';\s*', schema_sql.strip())

            # Execute each SQL statement individually
            for statement in statements:
                if statement.strip():  # Make sure the statement is not empty
                    cursor.execute(statement)

            # Commit the changes
            connection.commit()

    connection.close()

    return {
        'statusCode': 200,
        'body': json.dumps("Schema executed successfully.")
    }
