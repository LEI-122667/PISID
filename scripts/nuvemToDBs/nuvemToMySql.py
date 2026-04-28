import pymysql
from mysql.connector import Error
import mysql.connector as mariadb

usermysql="root"
passmysql="root"
hostmysql="localhost"
database="pisid_db"

nuvemuser="aluno"
nuvempass="aluno"
nuvemhost="194.210.86.10"
nuvemDb="maze"

try:
    connection = mariadb.connect(host=hostmysql, user=usermysql,
    passwd=passmysql, db=database,connect_timeout=1000,autocommit=True)
    print("Connected to MySQL pisid_db")
except Error as e:
    print("Error while connecting to MySQL pisid_db", e)

try:
    connection_nuvem = mariadb.connect(host=nuvemhost, user=nuvemuser,
    passwd=nuvempass, db=nuvemDb,connect_timeout=1000,autocommit=True)
    print("Connected to MySQL maze")
except Error as e:
    print("Error while connecting to MySQL maze", e)


sql_select_Query = "select * from SetupMaze"
cursor_nuvem = connection_nuvem.cursor(dictionary=True)
cursor_nuvem.execute(sql_select_Query)
records = cursor_nuvem.fetchall()

### Como é ordenado os dados na DB ###
'''
ID = 1
numbermarsamis = 30
numberrooms = 10
numberplayers = 40
normalnoise = 10.00
noisevartoleration = 17.00
normaltemperature = 15
temperaturevarhightoleration = 10
temperaturevarlowtoleration = 10
'''

for row in records:
    for coluna, valor in row.items():
        print(f"{coluna} = {valor}")
    print("-" * 20) # Separador entre linhas


for row in records:
    numbermarsamis = row['numbermarsamis']
    numberrooms = row['numberrooms']
    numberplayers = row['numberplayers']
    normalnoise = row['normalnoise']
    noisevartoleration = row['noisevartoleration']
    normaltemperature = row['normaltemperature']
    temperaturevarhightoleration = row['temperaturevarhightoleration']
    temperaturevarlowtoleration = row['temperaturevarlowtoleration']

    sql_insert_query = """INSERT INTO SetupMaze (NumberRooms, NumberMarsamis, NumberPlayers, NormalTemperature, TemperatureVarHighToleration, TemperatureVarLowToleration, NormalNoise, NoiseVarToleration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    record_tuple = (numberrooms, numbermarsamis, numberplayers, normaltemperature, temperaturevarhightoleration, temperaturevarlowtoleration, normalnoise, noisevartoleration)
    
    cursor_mysql = connection.cursor()
    cursor_mysql.execute(sql_insert_query, record_tuple)
    connection.commit()
    print("Record inserted successfully into SetupMaze table")

