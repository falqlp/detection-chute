import serial
import time

port = 'COM6'
baud_rate = 115200

try:
    ser = serial.Serial(port, baud_rate, timeout=1)
    time.sleep(2)

    print("Démarrage de la lecture des données du port série...")

    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').rstrip()
            print(f"Message reçu : {line}")
except serial.SerialException as e:
    print(f"Erreur lors de la connexion au port série : {e}")
except KeyboardInterrupt:
    print("\nArrêté par l'utilisateur")
finally:
    ser.close()
    print("Connexion série fermée.")
