# [---------------------------]
# OBLIGATORIO REDES 2026
# redes-auth.py
# SERVIDOR AUTENTICACION
# [---------------------------]

import socket
import threading
import hashlib
import sys


# [------]
# CONFIG
# [------]

BUFFER = 1024
TIMEOUT_ACCEPT = 1

ARCHIVO_USUARIOS = "usuarios.txt"

clientes = 0
lock = threading.Lock()


# [----]
# LOG
# [----]

def log(msg):

    print(msg)


def bloque(titulo):

    print()

    print("=" * 30)

    print(f" {titulo}")

    print("=" * 30)

    print()


# [---------------]
# CARGAR USUARIOS
# [---------------]

def cargar_usuarios():

    usuarios = {}

    try:

        with open(
            ARCHIVO_USUARIOS,
            "r",
            encoding="utf-8"
        ) as f:

            for linea in f:

                linea = linea.strip()

                if not linea:
                    continue

                partes = linea.split(";")

                if len(partes) < 2:
                    continue

                usuario_hash = partes[0]

                nombre = partes[1]

                usuario, clave = (
                    usuario_hash.split("-")
                )

                usuarios[usuario] = (
                    clave.lower(),
                    nombre
                )

    except FileNotFoundError:

        bloque(
            "ERROR"
        )

        print(
            f"No existe {ARCHIVO_USUARIOS}"
        )

        sys.exit(1)

    return usuarios


USUARIOS = cargar_usuarios()


# [-------------]
# PROTOCOLO CRLF
# [-------------]

def enviar(conn, texto):

    conn.sendall(
        (
            texto +
            "\r\n"
        ).encode()
    )


def recibir(conn):

    return (
        conn.recv(BUFFER)
        .decode()
        .strip()
    )


# [---------------]
# AUTENTICACION
# [---------------]

def autenticar(texto):

    try:

        usuario, md5 = (
            texto.split("-")
        )

    except:

        return (
            False,
            None
        )

    if usuario not in USUARIOS:

        return (
            False,
            None
        )

    hash_real = (
        USUARIOS[usuario][0]
    )

    nombre = (
        USUARIOS[usuario][1]
    )

    return (
        md5.lower() == hash_real,
        nombre
    )


# [----------------]
# CLIENTE
# [----------------]

def atender(conn, addr):

    global clientes

    ip = addr[0]

    with lock:

        clientes += 1

    try:

        bloque(
            f"NUEVA CONEXION {ip}"
        )

        enviar(
            conn,
            "Redes 2026 - Laboratorio - Autenticación de Usuarios"
        )

        recibido = recibir(
            conn
        )

        log(
            f"[LOGIN] {recibido}"
        )

        ok, nombre = autenticar(
            recibido
        )

        if ok:

            enviar(
                conn,
                "SI"
            )

            enviar(
                conn,
                nombre
            )

            log(
                f"[OK] {nombre}"
            )

        else:

            enviar(
                conn,
                "NO"
            )

            log(
                "[ERROR] Login inválido"
            )

    except Exception as e:

        log(
            f"[ERROR] {e}"
        )

    finally:

        try:
            conn.close()
        except:
            pass

        with lock:

            clientes -= 1

        log(
            f"[INFO] Clientes auth activos → {clientes}"
        )


# [----]
# MAIN
# [----]

if len(sys.argv) != 2:

    print()

    print(
        "Uso:"
    )

    print(
        "python redes-auth.py 5000"
    )

    sys.exit(1)


PUERTO = int(
    sys.argv[1]
)


server = socket.socket(
    socket.AF_INET,
    socket.SOCK_STREAM
)

server.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1
)

server.bind(
    (
        "",
        PUERTO
    )
)

server.listen(
    10
)

server.settimeout(
    TIMEOUT_ACCEPT
)


bloque(
    "SERVIDOR AUTH INICIADO"
)

log(
    f"[INFO] Puerto → {PUERTO}"
)

log(
    f"[INFO] Usuarios → {list(USUARIOS.keys())}"
)


try:

    while True:

        try:

            conn, addr = (
                server.accept()
            )

        except socket.timeout:

            continue

        t = threading.Thread(
            target=atender,
            args=(
                conn,
                addr
            ),
            daemon=True
        )

        t.start()


except KeyboardInterrupt:

    print()

    log(
        "[INFO] CTRL+C detectado"
    )


finally:

    try:
        server.close()
    except:
        pass

    log(
        "[INFO] Servidor detenido"
    )