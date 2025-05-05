
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

HOST = 'localhost'
PORT = 12345

class SeegaClient:
    def __init__(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar: {e}")
            return
        self.root = tk.Tk()
        self.root.title("Seega Cliente")
        self.player_name = self.ask_player_name()  # Pergunta ao jogador o nome
        self.turn = 0  # O turno começa com o Jogador 1
        self.board = [[' ']*5 for _ in range(5)]  # Tabuleiro 5x5
        self.placement_count = [0, 0]  # Conta o número de peças colocadas
        self.capture_count = [0, 0]  # Conta o número de peças retiradas

       

        # Definindo o fundo da janela como cinza escuro
        self.root.configure(bg='gray30')

        # Painel de informações (dados das jogadas)
        self.info_frame = tk.Frame(self.root, bg='gray30')
        self.info_frame.pack(padx=5, pady=5, fill=tk.X)

        # Labels para mostrar as informações
        self.label_player_name = tk.Label(self.info_frame, text="Jogador: ", bg='gray30', fg='white')
        self.label_player_name.pack()

        # Painel de chat
        self.chat_frame = tk.Frame(self.root, bg='gray30')
        self.chat_frame.pack(padx=5, pady=5, fill=tk.X)

        self.chat_box = tk.Text(self.chat_frame, state='disabled', height=10, bg='gray20', fg='white')
        self.chat_box.pack(fill=tk.X, padx=5, pady=5)

        self.entry = tk.Entry(self.chat_frame, bg='gray20', fg='white')
        self.entry.pack(fill=tk.X, padx=5)
        self.entry.bind("<Return>", self.send_chat)

        # Painel de mensagens do jogo
        self.game_frame = tk.Frame(self.root, bg='gray30')
        self.game_frame.pack(padx=5, pady=5, fill=tk.X)

        self.game_box = tk.Text(self.game_frame, state='disabled', height=10, bg='gray20', fg='white')
        self.game_box.pack(fill=tk.X, padx=5, pady=5)

        # Frame para o tabuleiro
        frame = tk.Frame(self.root, bg='gray30')
        frame.pack(padx=5, pady=5)
        self.cells = [[None]*5 for _ in range(5)]
        self.selected = None

        for y in range(5):
            for x in range(5):
                btn = tk.Button(frame, text='', width=4, height=2,
                                font=('Helvetica', 16),
                                command=lambda x=x, y=y: self.on_click(x, y), bg='gray30', fg='white')
                btn.grid(row=y, column=x, padx=1, pady=1)
                self.cells[y][x] = btn

        tk.Button(self.root, text="🔁 Reiniciar", command=lambda: self.send("RESTART"), bg='gray40', fg='white').pack(pady=(0,10))

        threading.Thread(target=self.receive_loop, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()

    def ask_player_name(self):
        """Solicita o nome do jogador ao iniciar a aplicação"""
        return simpledialog.askstring("Nome do Jogador", "Qual é o seu nome?", parent=self.root)

    def on_click(self, x, y):
        text = self.cells[y][x]['text']

        if text in ('●', '⛔'):
            # seleção de peça para mover
            if self.selected == (x, y):
                self.selected = None
                self.highlight(None)
            else:
                self.selected = (x, y)
                self.highlight((x, y))

        else:
            # célula vazia: PLACE ou MOVE
            if self.selected:
                x1, y1 = self.selected
                self.send(f"MOVE {x1} {y1} {x} {y}")
                self.selected = None
                self.highlight(None)
            else:
                self.send(f"PLACE {x} {y}")

    def highlight(self, pos):
        # limpa todos
        for row in self.cells:
            for b in row:
                b.config(bg='gray30')
        if pos:
            x, y = pos
            self.cells[y][x].config(bg='yellow')

    def send(self, msg):
        try:
            self.sock.sendall((msg + "\n").encode())
        except:
            messagebox.showerror("Erro", "Conexão perdida.")
            self.close()

    def send_chat(self, event=None):
        m = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if m:
            self.send("CHAT " + m)

    def receive_loop(self):
        buffer = ""
        try:
            while True:
                data = self.sock.recv(1024).decode()
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self.process_line(line.strip())
        except:
            pass
        messagebox.showwarning("Aviso", "Servidor desconectado.")
        self.close()

    def process_line(self, line):
        if not line:
            return
        parts = line.split()
        cmd = parts[0]

        if cmd == "TURN" and len(parts) == 2:
            self.turn = int(parts[1])  # Atualiza o turno
            self.update_info()  # Atualiza as informações de turno

        if cmd == "PLACE" and len(parts) == 4:
            _, xs, ys, p = parts
            x, y = int(xs), int(ys)
            self.draw_cell(x, y, p)
            self.update_info()  # Atualiza as informações de peças
            self.show_game_message(f"Jogador {self.player_name} colocou uma peça em ({x},{y})")

        elif cmd == "MOVE" and len(parts) == 6:
            _, x1s, y1s, x2s, y2s, p = parts
            x1, y1, x2, y2 = map(int, (x1s, y1s, x2s, y2s))
            self.draw_cell(x1, y1, ' ')
            self.draw_cell(x2, y2, p)
            self.update_info()  # Atualiza as informações de peças
            self.show_game_message(f"Jogador {self.player_name} moveu de ({x1},{y1}) para ({x2},{y2})")

        elif cmd == "CHAT":
            text = line[5:]
            self.chat_box.config(state='normal')
            self.chat_box.insert(tk.END, text + "\n")
            self.chat_box.config(state='disabled')
            self.chat_box.see(tk.END)

        elif cmd == "RESTART":
            # limpa o tabuleiro local
            for yy in range(5):
                for xx in range(5):
                    self.draw_cell(xx, yy, ' ')
            self.update_info()  # Atualiza após reiniciar o jogo

        elif cmd == "REMOVE" and len(parts) == 3:
            _, xs, ys = parts
            x, y = int(xs), int(ys)
            self.draw_cell(x, y, ' ')
            self.update_info()  # Atualiza as informações após remoção de peça

    def draw_cell(self, x, y, ch):
        btn = self.cells[y][x]
        btn.config(bg='gray30')
        if ch == 'A':
            btn.config(text='●', fg='red', state='normal')
        elif ch == 'B':
            btn.config(text='●', fg='blue', state='normal')
        elif ch == 'X':
            btn.config(text='X', fg='black', state='disabled')
        else:
            btn.config(text='', fg='black', state='normal')

    def update_info(self):
        """Atualiza as informações de nome, peças restantes e capturadas"""
        if self.player_name:
            self.label_player_name.config(text=f"Jogador: {self.player_name}")

    def show_game_message(self, message):
        """Exibe uma mensagem do jogo no painel de mensagens"""
        game_message = f"Jogada: {message}"
        self.game_box.config(state='normal')
        self.game_box.insert(tk.END, game_message + "\n")
        self.game_box.config(state='disabled')
        self.game_box.see(tk.END)

    def count_total_pieces(self):
        """Conta o número total de peças no tabuleiro"""
        return sum(1 for row in self.board for cell in row if cell in ('A', 'B'))

    def close(self):
        self.sock.close()
        self.root.quit()

if __name__ == "__main__":
    SeegaClient()