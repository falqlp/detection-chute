from flask_socketio import SocketIO, emit
from flask import Flask, render_template
import serial
import threading
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

port = 'COM5'
baud_rate = 115200

# Configuration de MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Chute']
collection = db['falling']


def read_from_port(ser):
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)

            try:
                msg_type, card_id = line.split(';')

                if msg_type.lower() == 'chute':
                    # Insertion dans MongoDB
                    date = datetime.now()
                    data = {'date': date, 'card_id': card_id}
                    collection.insert_one(data)
                    print(f"Inséré dans MongoDB: {data}")

                    # Récupérer les 20 derniers messages triés par date décroissante
                    last_messages = collection.find().sort('date', -1).limit(20)
                    messages = [{'date': msg['date'].strftime('%Y-%m-%d %H:%M:%S'), 'card_id': msg['card_id']} for msg in last_messages]
                    # Émettre les messages au client connecté
                    socketio.emit('last_messages', messages)

            except ValueError:
                print("Erreur de format du message")


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    # Récupérer les 20 derniers messages triés par date décroissante
    last_messages = collection.find().sort('date', -1).limit(20)
    messages = [{'date': msg['date'], 'card_id': msg['card_id']} for msg in last_messages]
    # Convertir les dates en chaînes de caractères
    for message in messages:
        message['date'] = message['date'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(message['date'], datetime) else \
        message['date']
    # Émettre les messages au client connecté
    emit('last_messages', messages)


if __name__ == '__main__':
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
    except serial.SerialException as e:
        print(f"Erreur lors de la connexion au port série : {e}")
        exit()

    t = threading.Thread(target=read_from_port, args=(ser,))
    t.start()

    socketio.run(app, allow_unsafe_werkzeug=True)
