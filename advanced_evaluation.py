# advanced_evaluation.py

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 20000
}

# Piece-square tables: White perspective
PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50]
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20]
]

ROOK_TABLE = [
    [0, 0, 0, 5, 5, 0, 0, 0],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0]
]

QUEEN_TABLE = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20]
]

KING_TABLE = [
    [20, 30, 10, 0, 0, 10, 30, 20],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30]
]

TABLES = {
    "P": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE,
    "K": KING_TABLE
}

PIECE = "."

def get_color(piece):
    if piece == PIECE:
        return None
    return "white" if piece.isupper() else "black"


def get_piece_square_value(piece, row, col):
    piece_type = piece.upper()
    table = TABLES.get(piece_type)

    if table is None:
        return 0

    if piece.isupper():
        return table[row][col]
    else:
        return table[7 - row][col]


def material_and_position_score(board):
    score = 0

    for r in range(8):
        for c in range(8):
            piece = board[r][c]

            if piece == PIECE:
                continue

            piece_type = piece.upper()
            base_value = PIECE_VALUES[piece_type]
            position_value = get_piece_square_value(piece, r, c)

            total = base_value + position_value

            if piece.isupper():
                score += total
            else:
                score -= total

    return score


def center_control_score(board):
    center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
    score = 0

    for r, c in center_squares:
        piece = board[r][c]

        if piece == PIECE:
            continue

        if piece.isupper():
            score += 30
        else:
            score -= 30

    return score


def pawn_structure_score(board):
    score = 0

    for color in ["white", "black"]:
        pawn_columns = []

        for r in range(8):
            for c in range(8):
                piece = board[r][c]

                if color == "white" and piece == "P":
                    pawn_columns.append(c)
                elif color == "black" and piece == "p":
                    pawn_columns.append(c)

        penalty = 0

        for col in set(pawn_columns):
            count = pawn_columns.count(col)

            if count > 1:
                penalty += (count - 1) * 20

        if color == "white":
            score -= penalty
        else:
            score += penalty

    return score


def find_king(board, color):
    target = "K" if color == "white" else "k"

    for r in range(8):
        for c in range(8):
            if board[r][c] == target:
                return r, c

    return None


def king_safety_score(board):
    score = 0

    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    for color in ["white", "black"]:
        king_pos = find_king(board, color)

        if king_pos is None:
            continue

        r, c = king_pos
        friendly_count = 0
        enemy_count = 0

        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if 0 <= nr < 8 and 0 <= nc < 8:
                neighbor = board[nr][nc]

                if neighbor == ".":
                    continue

                if get_color(neighbor) == color:
                    friendly_count += 1
                else:
                    enemy_count += 1

        safety = friendly_count * 15 - enemy_count * 25

        if color == "white":
            score += safety
        else:
            score -= safety

    return score


def mobility_score(board, move_generator=None):
    """
    Eğer ekipteki Game/Logic Developer legal move generator yazarsa,
    onu buraya verebilirsiniz.

    move_generator(board, color) -> legal moves listesi döndürmeli.

    Örnek:
    white_moves = move_generator(board, "white")
    black_moves = move_generator(board, "black")
    """

    if move_generator is None:
        return 0

    white_moves = len(move_generator(board, "white"))
    black_moves = len(move_generator(board, "black"))

    return (white_moves - black_moves) * 5


def evaluate_board(board, move_generator=None):
    """
    Final evaluation function.

    Pozitif skor: White avantajlı
    Negatif skor: Black avantajlı
    """

    material_position = material_and_position_score(board)
    center = center_control_score(board)
    pawn_structure = pawn_structure_score(board)
    king_safety = king_safety_score(board)
    mobility = mobility_score(board, move_generator)

    final_score = (
        1.00 * material_position +
        0.30 * center +
        0.40 * pawn_structure +
        0.70 * king_safety +
        0.50 * mobility
    )

    return round(final_score, 2)


def evaluate_for_ai(board, ai_color, move_generator=None):
    """
    Minimax için kullanımı daha kolay fonksiyon.

    AI white ise pozitif skor iyi.
    AI black ise skor ters çevrilir.
    """

    score = evaluate_board(board, move_generator)

    if ai_color == "white":
        return score
    elif ai_color == "black":
        return -score
    else:
        raise ValueError("ai_color must be 'white' or 'black'")