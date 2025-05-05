import socket
import threading
from game import SeegaGame


HOST = 'localhost'
PORT = 12345

clients = []
def broadcast(msg, exclude=None):
    for c in clients:
        if c is not exclude:
            try:
                c.sendall((msg + "\n").encode())
            except:
                pass

game = SeegaGame(broadcast)
lock = threading.Lock()
player_names = {}  # Adicione isso no topo, fora da função

def handle_client(conn, addr, pid):
    global game
    player_symbol = game.players[pid]
    
    conn.sendall(f"Você é o Jogador {player_symbol}\n".encode())
    conn.sendall(f"PLAYER {player_symbol}\n".encode())
    conn.sendall(("FULL\n" + game.get_board_string() + "\n\n").encode())

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode().strip()

            with lock:
                # Novo bloco para tratar o comando NAME
                if msg.startswith("NAME "):
                    name = msg[5:].strip()
                    player_names[player_symbol] = name
                    broadcast(f"PLAYER {player_symbol} {name}")
                    continue

                if msg.startswith("PLACE"):
                    if game.turn != pid:
                        conn.sendall("Não é seu turno.\n".encode())
                        continue
                    try:
                        _, xs, ys = msg.split()
                        x, y = int(xs), int(ys)
                    except:
                        conn.sendall("Formato inválido. Use: PLACE x y\n".encode())
                        continue

                    ok, resp = game.place_piece(x, y)
                    conn.sendall((resp + "\n").encode())
                    if ok:
                        broadcast(f"PLACE {x} {y} {player_symbol}")

                elif msg.startswith("MOVE"):
                    if game.turn != pid:
                        conn.sendall("Não é seu turno.\n".encode())
                        continue
                    try:
                        _, x1s, y1s, x2s, y2s = msg.split()
                        x1, y1, x2, y2 = map(int, (x1s, y1s, x2s, y2s))
                    except:
                        conn.sendall("Formato inválido. Use: MOVE x1 y1 x2 y2\n".encode())
                        continue

                    ok, resp = game.move_piece(x1, y1, x2, y2)
                    conn.sendall((resp + "\n").encode())
                    if ok:
                        broadcast(f"MOVE {x1} {y1} {x2} {y2} {player_symbol}")
                    
                    if game.check_winner():
                            broadcast(f"CHAT Jogador {player_symbol} venceu!")
                            game.reset_game()
                            

                elif msg.startswith("CHAT"):
                    texto = msg[5:]
                    nome = player_names.get(player_symbol, f"Jogador {player_symbol}")
                    broadcast(f"CHAT {nome}: {texto}")

                elif msg == "RESTART":
                    game.reset_game()
                    broadcast("RESTART")

                else:
                    conn.sendall("Comando desconhecido.\n".encode())

    finally:
        conn.close()
        if conn in clients:
            clients.remove(conn)
        nome = player_names.get(player_symbol, f"Jogador {player_symbol}")
        broadcast(f"CHAT {nome} saiu.")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor rodando em {HOST}:{PORT}")

        pid = 0  # alterna entre 0 e 1
        while True:
            conn, addr = s.accept()
            if len(clients) >= 2:
                conn.sendall("Servidor cheio. Tente novamente mais tarde.\n".encode())
                conn.close()
                continue

            clients.append(conn)
            threading.Thread(target=handle_client, args=(conn, addr, pid), daemon=True).start()
            pid = 1 - pid

if __name__ == "__main__":
    main()
