import pymysql

# Replace with the user's DB credentials
db_user = "root"
db_password = "Ksksuriya1826"
db_host = "localhost"
db_name = "fitguard"

try:
    # Connect to MySQL server (without specifying a database)
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password
    )
    
    with connection.cursor() as cursor:
        # Create the database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
        print(f"Successfully checked/created database: {db_name}")
        
    connection.commit()
except Exception as e:
    print(f"Error creating database: {e}")
finally:
    if 'connection' in locals() and connection.open:
        connection.close()
