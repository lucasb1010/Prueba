# =========================================================
# Redes - Laboratorio 1
# Mensajería P2P con sockets
# =========================================================

import socket
import threading
import sys
import os
import signal
import hashlib
from datetime import datetime

MAX_LARGO_MENSAJE = 255
BUFFER_SIZE = 65535
BROADCAST_ADDR = "255.255.255.255"
MAX_UDP_CHUNK = 1400

running = True
archivos_en_espera = {}

# =========================================================
# VARIABLES GLOBALES
# =========================================================

usuario = ""
nombre_completo = ""
mi_ip = socket.gethostbyname(socket.gethostname())

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def fecha_hora():
    return datetime.now().strftime("%Y.%m.%d %H:%M")


def imprimir_mensaje(ip, user, mensaje):
    print(f"[{fecha_hora()}] {ip} {user} dice: {mensaje}")


def imprimir_archivo(ip, user, archivo):
    print(f"[{fecha_hora()}] {ip} <Recibido {archivo} de {user}>")


def imprimir_error_archivo(ip, user):
    print(f"[{fecha_hora()}] {ip} <Error Recibiendo Archivo de {user}>")


# =========================================================
# AUTENTICACIÓN
# =========================================================

def autenticar(ipAuth, portAuth):

    global usuario
    global nombre_completo

    usuario = input("Usuario: ")
    clave = input("Clave: ")

    md5 = hashlib.md5(clave.encode()).hexdigest()

    mensaje = f"{usuario}-{md5}\r\n"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ipAuth, int(portAuth)))

        bienvenida = sock.recv(1024).decode()
        print(bienvenida.strip())

        sock.sendall(mensaje.encode())

        respuesta = sock.recv(1024).decode().strip()

        if respuesta == "SI":
            nombre_completo = sock.recv(1024).decode().strip()
            print(f"Bienvenido {nombre_completo}")
            return True
        else:
            print("Autenticación incorrecta")
            return False
    finally:
        sock.close()


# =========================================================
# RECEPCIÓN
# =========================================================

def receptor(port):

    global running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(("", int(port)))

    while running:

        try:

            data, addr = sock.recvfrom(BUFFER_SIZE)

            ip_emisor = addr[0]

            # encabezado tipo|usuario|...
            partes = data.split(b"|", 6)

            if len(partes) < 3:
                continue

            tipo = partes[0].decode()
            user = partes[1].decode()

            if tipo == "MSG":

                mensaje = partes[2].decode(errors="replace")
                imprimir_mensaje(ip_emisor, user, mensaje)

            elif tipo == "FILE":

                if len(partes) < 4:
                    imprimir_error_archivo(ip_emisor, user)
                    continue

                nombre_archivo = partes[2].decode(errors="replace")
                modo = partes[3].decode(errors="replace") if len(partes) > 3 else ""

                try:
                    if modo == "CHUNK" and len(partes) >= 7:
                        indice = int(partes[4].decode(errors="replace"))
                        total = int(partes[5].decode(errors="replace"))
                        contenido = partes[6]

                        clave = (ip_emisor, user, nombre_archivo)
                        estado = archivos_en_espera.setdefault(clave, {"total": total, "chunks": {}})
                        estado["chunks"][indice] = contenido

                        if len(estado["chunks"]) == total:
                            contenido_final = b"".join(estado["chunks"][i] for i in range(total) if i in estado["chunks"])
                            with open(nombre_archivo, "wb") as f:
                                f.write(contenido_final)
                            imprimir_archivo(ip_emisor, user, nombre_archivo)
                            archivos_en_espera.pop(clave, None)
                    else:
                        contenido = partes[3] if modo == "" else partes[4] if modo == "RAW" and len(partes) >= 5 else b""
                        if not contenido:
                            imprimir_error_archivo(ip_emisor, user)
                            continue

                        with open(nombre_archivo, "wb") as f:
                            f.write(contenido)
                        imprimir_archivo(ip_emisor, user, nombre_archivo)
                except Exception:
                    imprimir_error_archivo(ip_emisor, user)

        except Exception:
            break

    sock.close()


# =========================================================
# ENVÍO DE MENSAJES
# =========================================================

def enviar_mensaje(sock, destino, mensaje, puerto):

    try:

        if destino == BROADCAST_ADDR:
            ip_destino = destino
        else:
            ip_destino = socket.gethostbyname(destino)

        paquete = f"MSG|{usuario}|{mensaje}".encode()

        sock.sendto(paquete, (ip_destino, int(puerto)))

    except Exception as e:
        print("Error enviando mensaje:", e)


# =========================================================
# ENVÍO DE ARCHIVOS
# =========================================================

def enviar_archivo(sock, destino, path, puerto):

    try:

        if destino == BROADCAST_ADDR:
            ip_destino = destino
        else:
            ip_destino = socket.gethostbyname(destino)

        if not os.path.isfile(path):
            print("Archivo no encontrado:", path)
            return

        nombre_archivo = os.path.basename(path)

        with open(path, "rb") as f:
            contenido = f.read()

        if len(contenido) <= MAX_UDP_CHUNK:
            paquete = f"FILE|{usuario}|{nombre_archivo}|RAW|".encode() + contenido
            sock.sendto(paquete, (ip_destino, int(puerto)))
            return

        total_chunks = (len(contenido) + MAX_UDP_CHUNK - 1) // MAX_UDP_CHUNK

        for indice in range(total_chunks):
            inicio = indice * MAX_UDP_CHUNK
            fin = min(inicio + MAX_UDP_CHUNK, len(contenido))
            chunk = contenido[inicio:fin]
            paquete = (
                f"FILE|{usuario}|{nombre_archivo}|CHUNK|{indice}|{total_chunks}|".encode()
                + chunk
            )
            sock.sendto(paquete, (ip_destino, int(puerto)))

    except Exception as e:
        print("Error enviando archivo:", e)


# =========================================================
# EMISOR
# =========================================================

def emisor(port):

    global running

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while running:

        try:

            entrada = input()

            if not entrada.strip():
                continue

            partes = entrada.split(" ", 2)

            destino = partes[0]

            # -------------------------------------------------
            # ENVÍO DE ARCHIVOS
            # -------------------------------------------------

            if len(partes) >= 3 and partes[1] == "&file":

                path = partes[2]

                # broadcast
                if destino == "*":

                    enviar_archivo(sock, BROADCAST_ADDR, path, port)

                else:

                    enviar_archivo(sock, destino, path, port)

            # -------------------------------------------------
            # MENSAJES
            # -------------------------------------------------

            else:

                mensaje = entrada[len(destino)+1:]

                if len(mensaje.encode("utf-8")) > MAX_LARGO_MENSAJE:

                    print("Mensaje demasiado largo")
                    continue

                # broadcast
                if destino == "*":

                    enviar_mensaje(sock, BROADCAST_ADDR, mensaje, port)

                else:

                    enviar_mensaje(sock, destino, mensaje, port)

        except:
            break

    sock.close()


# =========================================================
# SEÑALES
# =========================================================

def cerrar(signum, frame):

    global running

    running = False

    print("\nCTRL + C Recibido.... Cerrando Sesión")

    sys.exit(0)


signal.signal(signal.SIGINT, cerrar)
signal.signal(signal.SIGTERM, cerrar)

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    if len(sys.argv) != 4:

        print("Uso:")
        print("python main.py port ipAuth portAuth")
        sys.exit(1)

    port = int(sys.argv[1])
    ipAuth = sys.argv[2]
    portAuth = int(sys.argv[3])

    # autenticación
    if not autenticar(ipAuth, portAuth):
        sys.exit(1)

    # hilo receptor
    hilo_receptor = threading.Thread(target=receptor, args=(port,))
    hilo_receptor.daemon = True
    hilo_receptor.start()

    # emisor en hilo principal
    emisor(port)