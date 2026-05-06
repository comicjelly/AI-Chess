# logic.py

WHITE = "white"
BLACK = "black"


def inside_board(row, col):
    return 0 <= row < 8 and 0 <= col < 8


def get_color(piece):
    if piece == ".":
        return None
    return WHITE if piece.isupper() else BLACK


def enemy(color):
    return BLACK if color == WHITE else WHITE


def is_clear_path(board, start, end):
    sr, sc = start
    er, ec = end

    dr = er - sr
    dc = ec - sc

    step_r = 0 if dr == 0 else dr // abs(dr)
    step_c = 0 if dc == 0 else dc // abs(dc)

    r = sr + step_r
    c = sc + step_c

    while (r, c) != (er, ec):
        if board[r][c] != ".":
            return False
        r += step_r
        c += step_c

    return True


def find_king(board, color):
    king = "K" if color == WHITE else "k"

    for r in range(8):
        for c in range(8):
            if board[r][c] == king:
                return r, c

    return None


def is_basic_move_valid(board, start, end):
    sr, sc = start
    er, ec = end

    if not inside_board(sr, sc) or not inside_board(er, ec):
        return False

    piece = board[sr][sc]

    if piece == ".":
        return False

    target = board[er][ec]
    color = get_color(piece)

    if target != "." and get_color(target) == color:
        return False

    piece_type = piece.upper()

    dr = er - sr
    dc = ec - sc

    # Pawn
    if piece_type == "P":
        direction = -1 if color == WHITE else 1
        start_row = 6 if color == WHITE else 1

        # one square forward
        if dc == 0 and dr == direction and target == ".":
            return True

        # two squares forward from start
        if (
            dc == 0
            and sr == start_row
            and dr == 2 * direction
            and target == "."
            and board[sr + direction][sc] == "."
        ):
            return True

        # diagonal capture
        if abs(dc) == 1 and dr == direction and target != ".":
            return get_color(target) == enemy(color)

        return False

    # Knight
    if piece_type == "N":
        return (abs(dr), abs(dc)) in [(2, 1), (1, 2)]

    # Bishop
    if piece_type == "B":
        return abs(dr) == abs(dc) and is_clear_path(board, start, end)

    # Rook
    if piece_type == "R":
        return (dr == 0 or dc == 0) and is_clear_path(board, start, end)

    # Queen
    if piece_type == "Q":
        diagonal = abs(dr) == abs(dc)
        straight = dr == 0 or dc == 0
        return (diagonal or straight) and is_clear_path(board, start, end)

    # King
    if piece_type == "K":
        return abs(dr) <= 1 and abs(dc) <= 1

    return False


def make_temp_move(board, start, end):
    new_board = [row[:] for row in board]

    sr, sc = start
    er, ec = end

    new_board[er][ec] = new_board[sr][sc]
    new_board[sr][sc] = "."

    return new_board


def is_square_attacked(board, square, by_color):
    for r in range(8):
        for c in range(8):
            piece = board[r][c]

            if piece != "." and get_color(piece) == by_color:
                if is_basic_move_valid(board, (r, c), square):
                    return True

    return False


def is_in_check(board, color):
    king_pos = find_king(board, color)

    if king_pos is None:
        return True

    return is_square_attacked(board, king_pos, enemy(color))


def is_legal_move(board, start, end):
    sr, sc = start

    if not inside_board(sr, sc):
        return False

    piece = board[sr][sc]

    if piece == ".":
        return False

    color = get_color(piece)

    if not is_basic_move_valid(board, start, end):
        return False

    temp_board = make_temp_move(board, start, end)

    # A move is illegal if it leaves your own king in check
    if is_in_check(temp_board, color):
        return False

    return True


def get_all_legal_moves(board, color):
    legal_moves = []

    for sr in range(8):
        for sc in range(8):
            piece = board[sr][sc]

            if piece != "." and get_color(piece) == color:
                for er in range(8):
                    for ec in range(8):
                        if is_legal_move(board, (sr, sc), (er, ec)):
                            legal_moves.append(((sr, sc), (er, ec)))

    return legal_moves


def is_checkmate(board, color):
    if not is_in_check(board, color):
        return False

    return len(get_all_legal_moves(board, color)) == 0


def is_stalemate(board, color):
    if is_in_check(board, color):
        return False

    return len(get_all_legal_moves(board, color)) == 0


def move_piece(board, start, end):
    if not is_legal_move(board, start, end):
        return False

    sr, sc = start
    er, ec = end

    board[er][ec] = board[sr][sc]
    board[sr][sc] = "."

    return True