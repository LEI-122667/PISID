import paho.mqtt.client as mqtt
import mysql.connector
import json

#Configurações do MySql
#TODO Testar código
db_config = {
    'host': 'localhost',    
    'user': 'root',
    'password': 'root',     
    'database': 'db_pisid'
}

#TODO Configurações do MQTT
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPICS = []

#TODO Função para guardar os dados no MySql

#TODO Função de callback para o MQTT

#Configuração do cliente MQTT e loop de escuta
#TODO Testar código
client = mqtt.Client()
client.on_message = on_message

print("Conectando ao broker...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe(MQTT_TOPICS)

print("Escutando o tópico {MQTT_TOPICS}...")
client.loop_forever()