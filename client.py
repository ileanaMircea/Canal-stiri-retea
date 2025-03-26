import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

# Thread pentru a primi notificări de la server în fundal
def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024).decode()
            if data:
                print("\n" + data + "> ", end="")
        except:
            break

def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        
        # Afișează mesajul de întâmpinare de la server
        welcome = s.recv(1024).decode()
        print(welcome)

        # Pornim un thread care ascultă constant notificări de la server
        threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

        while True:
            msg = input("> ")
            s.sendall(msg.encode())
            if msg.upper() == "EXIT":
                break

if __name__ == "__main__":
    start_client()
