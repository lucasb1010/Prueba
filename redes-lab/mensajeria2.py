# [-----------------------]
# OBLIGATORIO DE REDES 2026
# [-----------------------]

# [------]
# EJECUTAR
# [------]
# python mensajeria.py puerto ti.esi.edu.uy 33
# IP LOCAL 192.168.56.1
# PUERTOS ARRIBA DE 5000

import time
import getpass
import hashlib
import socket
import sys
import threading
import random
import ipaddress

# [----------------]
# VARIABLES GLOBALES
# [----------------]
MAX_LARGO_MENSAJE = 255

# [-------]
# FUNCIONES 
# [-------]

# [-----]
# RECPTOR 
# [-----]
def createConectRecvSocket(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crea socket
    serverSocket.bind((ip, port)) # Bindea el socket, sin el doble parentesis no funciona
    return serverSocket

# [----]
# EMISOR 
# [----]
def createConectClientSocket(dest_ip, destPort):
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Crea socket
    clientSocket.connect((dest_ip, destPort)) # Se conecta al socket destino
    return clientSocket


terminalPort = int(sys.argv[1])

dest_ip = "127.0.0.1"

socket = createConectClientSocket(dest_ip, terminalPort)

while True:
    socket.sendall(b"hola")
    time.sleep(1)