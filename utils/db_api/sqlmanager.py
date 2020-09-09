import pyodbc

# Specifying the ODBC driver, server name, database, etc. directly
cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                      'SERVER=mysql.9260099463.myjino.ru;'
                      'DATABASE=9260099463_jobs;'
                      'UID=045937292_jobs;'
                      'PWD=DimaPass')
# Using a DSN, but providing a password as well
# Create a cursor from the connection
cursor = cnxn.cursor()

cursor.execute("select * from jobs")
row = cursor.fetchone()



# Адрес для внешних подключений mysql.9260099463.myjino.ru
# Сокет /var/lib/mysql/mysql.sock
# Имя бд 9260099463_jobs
# User 045937292_jobs
# Pass: DimaPass