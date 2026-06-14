# [-----------------------]
# OBLIGATORIO DE REDES 2026
# [-----------------------]

# [------]
# EJECUTAR
# [------]
# python mensajeria.py puerto ti.esi.edu.uy 33
# IP LOCAL 192.168.56.1
# PUERTOS ARRIBA DE 5000


import getpass
import hashlib
import socket
import sys
import threading
import random

# [----------------]
# VARIABLES GLOBALES
# [----------------]
MAX_LARGO_MENSAJE = 255

trueVar = True

# [-------]
# FUNCIONES 
# [-------]

# [-----]
# RECPTOR 
# [-----]
def createConectRecvSocket(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crea socket
    serverSocket.bind(('', port)) # Bindea el socket, sin el doble parentesis no funciona
    return serverSocket

# [----]
# EMISOR 
# [----]
def createConectClientSocket(ipDest, destPort):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crea socket
    clientSocket.connect((ipDest, destPort)) # Se conecta al socket destino
    return clientSocket


def rcv(conn):
    while True:
        data = conn.recv(1024)
        if not data:
            print("Conexión cerrada por el otro lado")
            break
        print("RECIBIDO:", data.decode("utf-8"))

def snd(conn):
    while True:
        msg = input()
        if msg.lower() == "salir":
            break
        conn.sendall(msg.encode("utf-8"))
    conn.close()

# [--]
# MAIN 
# [--]

# Chequea lo que entra por la terminal, verifica que sea la inofrmación necesaria
if len(sys.argv) < 3:
    print(" Error: faltan argumentos. Uso: mensajeria.py ip puerto ti.esi.edu.uy 33")
    sys.exit(1)
elif (len(sys.argv) > 4):
    print(" Error: sobran argumentos. Uso: mensajeria.py ip puerto ti.esi.edu.uy 33")
    sys.exit(1)

terminalPort = int(sys.argv[1]) #Toma el puerto desde la terminal

usuario = input("Usuario: ")
clave = input("Clave: ")
print("Bienvenido ", usuario)

mainSocket = createConectRecvSocket(terminalPort)
mainSocket.listen(9)
print(f"Escuchando en el puerto {terminalPort}...")
conn, addr = mainSocket.accept()
print("Conectado desde", addr)


while (trueVar == True):
    rcvThread = threading.Thread(target=snd, args=(conn,), daemon=True)
    sndThread = threading.Thread(target=rcv, args=(conn,), daemon=True)

    rcvThread.start()
    sndThread.start()

    if not conn.recv(1024):
        trueVar = False



sndThread.join()
print("Cerrando conexión.")
mainSocket.close()