import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

channels = {}  # nume_canal -> {descriere, autor, subscribers}
banned_words = {"spam", "fake"}
active_clients = {}  # client_name -> conn

def handle_client(conn, addr):
    client_name = f"{addr[0]}:{addr[1]}"
    active_clients[client_name] = conn
    print(f"[SERVER] Conectat la {client_name}")
    conn.sendall(b"Bine ai venit la serverul de stiri! Scrie 'EXIT' pentru a iesi.\n")

    try:
        while True:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            if data.upper() == 'EXIT':
                conn.sendall(b"Conexiune inchisa.\n")
                break

            response = process_command(data, client_name)
            conn.sendall(response.encode())
    except:
        pass
    finally:
        print(f"[SERVER] Deconectat de la {client_name}")
        conn.close()
        del active_clients[client_name]

def process_command(command, client_name):
    tokens = command.strip().split()
    if not tokens:
        return "Comanda invalida.\n"

    cmd = tokens[0].upper()

    if cmd == "LIST":
        if not channels:
            return "Nu exista canale disponibile.\n"
        resp = "Canale disponibile:\n"
        for name, info in channels.items():
            resp += f" - {name}: {info['descriere']}\n"
        return resp

    elif cmd == "CREATE" and len(tokens) >= 3:
        name = tokens[1]
        descriere = ' '.join(tokens[2:])
        if name in channels:
            return f"Canalul '{name}' exista deja.\n"
        channels[name] = {
            "descriere": descriere,
            "autor": client_name,
            "subscribers": set()
        }

        # notifica toti ceilalti clienti
        for other, sock in active_clients.items():
            if other != client_name:
                try:
                    sock.sendall(
                        f"[SERVER] Canal nou creat: {name} - {descriere}\n".encode()
                    )
                except:
                    pass

        return f"Canalul '{name}' a fost creat.\n"


    elif cmd == "DELETE" and len(tokens) == 2:
        name = tokens[1]
        if name not in channels:
            return f"Canalul '{name}' nu exista.\n"
        if channels[name]["autor"] != client_name:
            return "Nu poti sterge un canal pe care nu l-ai creat.\n"
        del channels[name]

        #notifica toti clientii
        for other, sock in active_clients.items():
            if other != client_name:
                try:
                    sock.sendall(
                        f"[SERVER] Canalul '{name}' a fost sters.\n".encode()
                    )
                except:
                    pass

        return f"Canalul '{name}' a fost sters.\n"


    elif cmd == "SUBSCRIBE" and len(tokens) == 2:
        name = tokens[1]
        if name not in channels:
            return f"Canalul '{name}' nu exista.\n"
        channels[name]["subscribers"].add(client_name)
        return f"Te-ai abonat la canalul '{name}'.\n"

    elif cmd == "UNSUBSCRIBE" and len(tokens) == 2:
        name = tokens[1]
        if name not in channels:
            return f"Canalul '{name}' nu exista.\n"
        channels[name]["subscribers"].discard(client_name)
        return f"Te-ai dezabonat de la canalul '{name}'.\n"

    elif cmd == "SEND" and len(tokens) >= 3:
        name = tokens[1]
        if name not in channels:
            return f"Canalul '{name}' nu exista.\n"
        if channels[name]["autor"] != client_name:
            return "Nu poti trimite stiri pe un canal pe care nu l-ai creat.\n"
        mesaj = ' '.join(tokens[2:])

        if any(word.lower() in mesaj.lower() for word in banned_words):
            return "Mesajul contine cuvinte interzise si nu a fost trimis.\n"

        subs = channels[name]["subscribers"]
        if not subs:
            return f"Nu exista abonati la canalul '{name}'.\n"

        numar_trimisi = 0
        for sub in subs:
            if sub == client_name:
                continue
            if sub in active_clients:
                try:
                    active_clients[sub].sendall(
                        f"[NOTIFICARE {name}] {mesaj}\n".encode()
                    )
                    numar_trimisi += 1
                except:
                    pass

        return f"Stirea a fost trimisa catre {numar_trimisi} abonati ai canalului '{name}'.\n"

    return "Comanda necunoscuta.\n"

def start_server():
    print("[SERVER] Porneste...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVER] Asculta pe {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
