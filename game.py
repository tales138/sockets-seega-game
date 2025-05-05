
class SeegaGame:
    """
    Classe que implementa a lógica do jogo Seega.

    O jogo Seega é jogado em um tabuleiro 5x5, com duas fases:
    - Fase de colocação: cada jogador coloca 12 peças (exceto na célula central bloqueada).
    - Fase de movimentação: os jogadores alternam movimentos de suas peças, capturando peças adversárias.

    A classe gerencia o estado do jogo, verifica regras de colocação, movimentação e captura,
    controla o turno dos jogadores e permite verificar o vencedor ou desistência.

    Atributos:
        board (list[list[str]]): Representa o tabuleiro 5x5.
        players (list[str]): Lista dos identificadores dos jogadores ('A' e 'B').
        turn (int): Índice do jogador da vez (0 ou 1).
        placement_phase (bool): Indica se ainda estamos na fase de colocação.
        placement_count (list[int]): Contagem de peças colocadas por cada jogador.
        captured_pieces (list[int]): Contagem de peças capturadas por cada jogador.
        broadcast (callable): Função para notificar eventos externos (como remoções).

    Métodos:
        __init__(broadcast_fn): Inicializa o jogo com a função de broadcast.
        reset_game(): Reinicia o estado do jogo.
        get_board_string(): Retorna uma representação textual do tabuleiro (útil para debug).
        valid_coords(x, y): Verifica se as coordenadas são válidas para jogadas.
        place_piece(x, y): Realiza uma jogada de colocação de peça no tabuleiro.
        move_piece(x1, y1, x2, y2): Move uma peça de (x1, y1) para (x2, y2), se permitido.
        check_capture(x, y): Verifica e executa capturas ao redor da peça recém-movida.
        check_winner(): Verifica se algum jogador venceu (sem peças no tabuleiro).
        surrender(): Finaliza o jogo com desistência do jogador atual.
    """
    def __init__(self,broadcast_fn):
        self.reset_game()
        self.broadcast = broadcast_fn
    def reset_game(self):
        self.board = [[' ' for _ in range(5)] for _ in range(5)]
        self.board[2][2] = 'X'            # centro bloqueado
        self.players = ['A', 'B']
        self.turn = 0                     # 0 → A, 1 → B
        self.placement_phase = True
        self.placement_count = [0, 0]
        self.captured_pieces = [0, 0]
    
    
   
    def get_board_string(self):
        # apenas para debug / restart
        return '\n'.join(''.join(row) for row in self.board)

    def valid_coords(self, x, y):
        return 0 <= x < 5 and 0 <= y < 5 and not (x == 2 and y == 2)

    def valid_coords(self, x, y):
        # Verifica se está dentro do tabuleiro
        if not (0 <= x < 5 and 0 <= y < 5):
            return False

        # Bloqueia o centro apenas durante a fase de colocação
        if self.placement_phase and (x == 2 and y == 2):
            return False

        return True

    
    def place_piece(self, x, y):
       
       

        # Verifica centro bloqueado
        if not self.valid_coords(x, y):
            return False, "Coordenadas inválidas ou centro bloqueado."
        
        if self.placement_count[self.turn] >= 12:
            return False, "Você já colocou 12 peças."
        
        # ** e verifica ocupação usando strip()**
        cell = self.board[y][x]
        if cell.strip() != '':
            return False, "Espaço ocupado."

        # Verifica limite de peças
        if self.placement_count[self.turn] >= 12:
            return False, "Você já colocou 12 peças."

        # Coloca a peça
        player = self.players[self.turn]
        self.board[y][x] = player
        self.placement_count[self.turn] += 1

        # Se terminou colocação, muda de fase
        if sum(self.placement_count) == 24:
            self.placement_phase = False
        if sum(self.placement_count) == 24:
            self.placement_phase = False
            self.board[2][2] = ' '  # Desbloqueia o centro para movimentaçõess
        self.turn = 1 - self.turn
        return True, "Peça colocada."

    def move_piece(self, x1, y1, x2, y2):

        if self.placement_phase:
            return False, "Ainda na fase de colocação."
        
        if not (self.valid_coords(x1, y1) and self.valid_coords(x2, y2)):
            return False, "Coordenadas inválidas."

        player = self.players[self.turn]
        # Só pode mover suas próprias peças
        if self.board[y1][x1] != player:
            return False, "Só pode mover suas próprias peças."

        # **normalize destino também**
        dest = self.board[y2][x2]
        if dest.strip() != '':
            return False, "Destino ocupado."

        if max(abs(x1 - x2), abs(y1 - y2)) != 1:
            return False, "Movimento inválido."

        # Executa movimento
        self.board[y1][x1] = ' '
        self.board[y2][x2] = player

        # Captura e troca de turno
        self.check_capture(x2, y2)
        self.turn = 1 - self.turn
        return True, "Peça movida."


    def check_capture(self, x, y):
        player = self.board[y][x]
        opponent = 'A' if player == 'B' else 'B'
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            ax, ay = x + dx, y + dy
            bx, by = x + 2*dx, y + 2*dy
            if (0 <= ax < 5 and 0 <= ay < 5 and 0 <= bx < 5 and 0 <= by < 5
                and self.board[ay][ax] == opponent
                and self.board[by][bx] == player):
                self.board[ay][ax] = ' '
                mover = self.players.index(player)
                self.captured_pieces[mover] += 1
                self.broadcast(f"REMOVE {ax} {ay}")

    def check_winner(self):
        a = sum(row.count('A') for row in self.board)
        b = sum(row.count('B') for row in self.board)
        if a==0: return "Jogador B venceu!"
        if b==0: return "Jogador A venceu!"
        return None

    def surrender(self):
        loser = self.players[self.turn]
        winner = self.players[1-self.turn]
        return f"Jogador {loser} desistiu. {winner} venceu!"
