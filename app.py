from flask_socketio import SocketIO, emit
from flask import Flask, render_template, jsonify
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

                if msg_type.lower().strip() == 'chute':
                    # Insertion dans MongoDB
                    date = datetime.now()
                    data = {'date': date, 'card_id': card_id}
                    collection.insert_one(data)
                    print(f"Inséré dans MongoDB: {data}")
                    get_last_messages()
                if msg_type.lower().strip() == 'countrequest':
                    send_message("count "+collection.count_documents({'card_id': card_id.strip()}).__str__())
                if msg_type.lower().strip() == 'delete':
                    collection.delete_many({'card_id': card_id.strip()})
                    get_last_messages()

            except ValueError:
                print("Erreur de format du message")


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    get_last_messages()


def send_message(message):
    if message:
        ser.write(message.encode('utf-8'))


def get_last_messages():
    # Récupérer les 20 derniers messages triés par date décroissante
    last_messages = collection.find().sort('date', -1).limit(20)
    messages = [{'date': msg['date'].strftime('%Y-%m-%d %H:%M:%S'), 'card_id': msg['card_id'].strip()}
                for msg in last_messages]
    # Émettre les messages au client connecté
    socketio.emit('last_messages', messages)


if __name__ == '__main__':
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
    except serial.SerialException as e:
        print(f"Erreur lors de la connexion au port série : {e}")
        exit()

    t = threading.Thread(target=read_from_port, args=(ser,))
    t.start()

    socketio.run(app, allow_unsafe_werkzeug=True)
