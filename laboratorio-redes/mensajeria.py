# [-----------------------]
# OBLIGATORIO DE REDES 2026
# mensajeria.py
# CLIENTE
# [-----------------------]

import socket
import sys
import getpass
import hashlib
import threading
from datetime import datetime


BUFFER = 1024
MAX_LARGO_MENSAJE = 255

usuario_actual = None
nombre_usuario = None

buffer_rx = ""

ejecutando = True

socket_receptor = None
socket_broadcast = None


def log(msg):

    print(
        f"[CLIENTE] {msg}"
    )


def conectar(ip, puerto):

    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    s.connect(
        (
            socket.gethostbyname(
                ip
            ),
            puerto
        )
    )

    return s


def enviar(sock, texto):

    sock.sendall(
        texto.encode()
    )


def recibir_linea(sock):

    global buffer_rx

    while "\r\n" not in buffer_rx:

        datos = (
            sock.recv(
                BUFFER
            )
            .decode()
        )

        if not datos:

            return ""

        buffer_rx += datos

    linea, buffer_rx = (
        buffer_rx.split(
            "\r\n",
            1
        )
    )

    return (
        linea.strip()
    )


def md5(texto):

    return hashlib.md5(
        texto.encode()
    ).hexdigest()


def ahora():

    return (
        datetime.now()
        .strftime(
            "%Y.%m.%d %H:%M"
        )
    )


def login(sock):

    global usuario_actual
    global nombre_usuario

    saludo = recibir_linea(
        sock
    )

    usuario = input(
        "Usuario: "
    )

    clave = getpass.getpass(
        "Clave: "
    )

    enviar(
        sock,
        f"{usuario}-{md5(clave)}\r\n"
    )

    if (
        recibir_linea(
            sock
        )
        !=
        "SI"
    ):

        print(
            "Usuario o clave incorrectos"
        )

        return False

    nombre = recibir_linea(
        sock
    )

    usuario_actual = usuario
    nombre_usuario = nombre

    print()
    print(
        f"Bienvenido {nombre}"
    )
    print()

    return True


def imprimir(ip, usuario, mensaje):

    print()

    print(
        f"[{ahora()}] {ip} {usuario} dice: {mensaje}"
    )

    print()


def atender_tcp(
    conn,
    addr
):

    try:

        datos = (
            conn.recv(
                BUFFER
            )
            .decode()
            .strip()
        )

        if not datos:

            return

        usuario, mensaje = (
            datos.split(
                " dice: ",
                1
            )
        )

        imprimir(
            addr[0],
            usuario,
            mensaje
        )

    except:
        pass

    finally:

        cerrar(
            conn
        )


def escuchar_tcp():

    global socket_receptor

    socket_receptor = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    socket_receptor.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    socket_receptor.bind(
        (
            "",
            PORT_LOCAL
        )
    )

    socket_receptor.listen(
        10
    )

    while ejecutando:

        try:

            conn, addr = (
                socket_receptor.accept()
            )

            threading.Thread(
                target=atender_tcp,
                args=(
                    conn,
                    addr
                ),
                daemon=True
            ).start()

        except:
            break


def escuchar_broadcast():

    global socket_broadcast

    socket_broadcast = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    socket_broadcast.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    socket_broadcast.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    socket_broadcast.bind(
        (
            "",
            PORT_LOCAL
        )
    )

    while ejecutando:

        try:

            datos, addr = (
                socket_broadcast.recvfrom(
                    BUFFER
                )
            )

            texto = (
                datos.decode()
            )

            usuario, mensaje = (
                texto.split(
                    " dice: ",
                    1
                )
            )

            imprimir(
                addr[0],
                usuario,
                mensaje
            )

        except:
            break


def enviar_broadcast(
    mensaje
):

    s = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    s.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    s.sendto(
        mensaje.encode(),
        (
            "<broadcast>",
            PORT_LOCAL
        )
    )

    s.close()


def cerrar(sock):

    try:

        if sock:

            sock.close()

    except:
        pass


if len(sys.argv) != 4:

    print(
        "python mensajeria.py port ipAuth portAuth"
    )

    sys.exit()


PORT_LOCAL = int(
    sys.argv[1]
)

IP_AUTH = (
    sys.argv[2]
)

PORT_AUTH = int(
    sys.argv[3]
)

sock = None


try:

    sock = conectar(
        IP_AUTH,
        PORT_AUTH
    )

    if not login(
        sock
    ):

        sys.exit()

    cerrar(
        sock
    )

    threading.Thread(
        target=escuchar_tcp,
        daemon=True
    ).start()

    threading.Thread(
        target=escuchar_broadcast,
        daemon=True
    ).start()

    log(
        f"Escuchando → {PORT_LOCAL}"
    )

    while True:

        entrada = input()

        if entrada.lower() == "salir":

            break

        if entrada.startswith(
            "* "
        ):

            mensaje = (
                entrada[2:]
            )

            enviar_broadcast(
                f"{usuario_actual} dice: {mensaje}"
            )

            continue

        partes = entrada.split()

        if len(
            partes
        ) < 3:

            print(
                "Formato: ip puerto mensaje"
            )

            continue

        destino = partes[0]

        puerto = int(
            partes[1]
        )

        mensaje = " ".join(
            partes[2:]
        )

        if len(
            mensaje
        ) > MAX_LARGO_MENSAJE:

            log(
                "Mensaje demasiado largo"
            )

            continue

        try:

            s = conectar(
                destino,
                puerto
            )

            enviar(
                s,
                f"{usuario_actual} dice: {mensaje}"
            )

            cerrar(
                s
            )

        except Exception as e:

            log(
                f"No enviado → {e}"
            )

except KeyboardInterrupt:

    print()

finally:

    ejecutando = False

    cerrar(
        socket_receptor
    )

    cerrar(
        socket_broadcast
    )

    cerrar(
        sock
    )

    log(
        "Programa finalizado"
    )