from flask_socketio import SocketIO
from flask import Flask, render_template
import serial
import threading

app = Flask(__name__)
socketio = SocketIO(app)

port = 'COM5'
baud_rate = 115200


def read_from_port(ser):
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            socketio.emit('new_message', {'message': line})


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
    except serial.SerialException as e:
        print(f"Erreur lors de la connexion au port série : {e}")
        exit()

    t = threading.Thread(target=read_from_port, args=(ser,))
    t.start()

    socketio.run(app, allow_unsafe_werkzeug=True)
