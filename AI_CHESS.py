"""
AI_CHESS.py  ─  AI Developer: Optimization  (Rol #5)
══════════════════════════════════════════════════════════════════════════════

Bu modül, Rol #4 (AI Developer – Minimax) tarafından yazılan temel minimax'ı
aşağıdaki optimizasyon teknikleriyle güçlendirir:

  Optimizasyon #1 ─ Alpha-Beta Pruning
      Minimax ağacının sonucu değiştiremeyen dallarını keser.
      En iyi durumda O(b^d) → O(b^(d/2)) karmaşıklığa düşürür.

  Optimizasyon #2 ─ Move Ordering (MVV-LVA + Killer + History)
      En iyi hamleleri önce arayarak alpha-beta'nın kesim oranını artırır.

  Optimizasyon #3 ─ Transposition Table (Zobrist Hashing)
      Daha önce görülen pozisyonları önbellekler; yeniden hesaplamayı önler.

  Optimizasyon #4 ─ Iterative Deepening
      Zaman sınırı içinde mümkün olan maksimum derinliği bulur.

  Optimizasyon #5 ─ Quiescence Search
      Yatay etki (horizon effect) sorununu önlemek için ele geçirme
      hamlelerinde aramayı derinleştirir.

  Optimizasyon #6 ─ Null Move Pruning
      Sırayı rakibe vererek zayıf pozisyonları hızla reddeder.

  Optimizasyon #7 ─ Late Move Reductions (LMR)
      Geç sıradaki sessiz hamleleri düşürülmüş derinlikte arar.

  Zorluk Seviyeleri ─ Easy / Medium / Hard
      Derinlik ve zaman sınırını ayarlayan üç ön ayar.

Performans karşılaştırması için benchmark() fonksiyonu mevcuttur.

Bağımlılıklar:
  - advanced_evaluation.py  (evaluate_for_ai)
  - "" boş kare gösterimi (Game_engine.py ile uyumlu)

Kullanım (Game_engine.py'den):
  from AI_CHESS import ai_make_move, legal_moves, is_in_check, benchmark
  move = ai_make_move(board, ai_color="black", difficulty="medium")
"""

import time
import random as _rng
from advanced_evaluation import evaluate_for_ai
from Logic import get_all_legal_moves, is_in_check

# ══════════════════════════════════════════════════════════════════════════════
# SABİTLER
# ══════════════════════════════════════════════════════════════════════════════

INF = 10_000_000

# Zorluk ön ayarları  {derinlik, saniye, etiket}
DIFFICULTY_SETTINGS = {
    "easy":   {"depth": 2, "time": 1.0, "label": "Easy   (Depth 2)"},
    "medium": {"depth": 4, "time": 2.0, "label": "Medium (Depth 4)"},
    "hard":   {"depth": 6, "time": 4.0, "label": "Hard   (Depth 6)"},
}

PIECE_VALUES = {
    "P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000,
    "p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 20000,
}

# Quiescence arama derinliği
QSEARCH_DEPTH = 4

# Null Move Pruning azaltma miktarı
NULL_REDUCTION = 2

# ══════════════════════════════════════════════════════════════════════════════
# HAMLE ÜRETICI  (boş kare → ""; Game_engine.py ile uyumlu)
# ══════════════════════════════════════════════════════════════════════════════

def _in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _is_white(p):    return p != "" and p.isupper()
def _is_black(p):    return p != "" and p.islower()

def _is_enemy(p, color):
    return _is_black(p) if color == "white" else _is_white(p)

def _is_friendly(p, color):
    return _is_white(p) if color == "white" else _is_black(p)


def _piece_moves(board, r, c, color):
    """Bir taşın sahte-yasal (pseudo-legal) hamlelerini üretir."""
    piece = board[r][c].upper()
    moves = []

    if piece == "P":
        d  = -1 if color == "white" else 1
        sr =  6 if color == "white" else 1
        nr = r + d

        # Bir kare ileri
        if _in_bounds(nr, c) and board[nr][c] == "":
            moves.append((r, c, nr, c))
            # İki kare ileri (başlangıç sırasından)
            if r == sr and board[r + 2*d][c] == "":
                moves.append((r, c, r + 2*d, c))

        # Çapraz yeme
        for dc in (-1, 1):
            nc = c + dc
            if _in_bounds(nr, nc) and _is_enemy(board[nr][nc], color):
                moves.append((r, c, nr, nc))

    elif piece == "N":
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),
                       ( 1,-2),( 1,2),( 2,-1),( 2,1)]:
            nr, nc = r + dr, c + dc
            if _in_bounds(nr, nc) and not _is_friendly(board[nr][nc], color):
                moves.append((r, c, nr, nc))

    elif piece in ("B", "R", "Q"):
        dirs = []
        if piece in ("B", "Q"): dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
        if piece in ("R", "Q"): dirs += [(-1, 0),(1, 0),(0,-1),(0, 1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while _in_bounds(nr, nc):
                if board[nr][nc] == "":
                    moves.append((r, c, nr, nc))
                elif _is_enemy(board[nr][nc], color):
                    moves.append((r, c, nr, nc))
                    break
                else:
                    break
                nr += dr; nc += dc

    elif piece == "K":
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0: continue
                nr, nc = r + dr, c + dc
                if _in_bounds(nr, nc) and not _is_friendly(board[nr][nc], color):
                    moves.append((r, c, nr, nc))

    return moves


def _all_pseudo_moves(board, color):
    """Bir renk için tüm sahte-yasal hamleleri döndürür."""
    moves = []
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == "": continue
            if color == "white" and p.isupper():
                moves.extend(_piece_moves(board, r, c, color))
            elif color == "black" and p.islower():
                moves.extend(_piece_moves(board, r, c, color))
    return moves


def apply_move(board, fr, fc, tr, tc):
    """Hamleyi uygular ve yeni tahtayı döndürür. Piyon terfisini işler."""
    b = [row[:] for row in board]
    piece = b[fr][fc]
    b[tr][tc] = piece
    b[fr][fc] = ""
    # Piyon terfisi → Vezir
    if piece == "P" and tr == 0: b[tr][tc] = "Q"
    if piece == "p" and tr == 7: b[tr][tc] = "q"
    return b


def find_king(board, color):
    """Verilen rengin şah konumunu bulur."""
    k = "K" if color == "white" else "k"
    for r in range(8):
        for c in range(8):
            if board[r][c] == k:
                return (r, c)
    return None


def is_in_check(board, color):
    """Verilen rengin şahı tehdit altında mı?"""
    pos = find_king(board, color)
    if pos is None: return True     # şah yenilmiş → yasadışı
    kr, kc = pos
    opp = "black" if color == "white" else "white"
    for fr, fc, tr, tc in _all_pseudo_moves(board, opp):
        if tr == kr and tc == kc:
            return True
    return False


def legal_moves(board, color):
    """Şahı tehlike altında bırakmayan tüm yasal hamleleri döndürür."""
    result = []
    for move in _all_pseudo_moves(board, color):
        nb = apply_move(board, *move)
        if not is_in_check(nb, color):
            result.append(move)
    return result


def legal_moves_for_piece(board, color, pr, pc):
    """Belirli bir taşın yasal hamlelerini döndürür (UI vurgulama için)."""
    return [(tr, tc)
            for (fr, fc, tr, tc) in legal_moves(board, color)
            if fr == pr and fc == pc]


def is_checkmate(board, color):
    return is_in_check(board, color) and len(legal_moves(board, color)) == 0

def is_stalemate(board, color):
    return (not is_in_check(board, color)) and len(legal_moves(board, color)) == 0


# ══════════════════════════════════════════════════════════════════════════════
# BOARD ADAPTÖRLERI
# ══════════════════════════════════════════════════════════════════════════════
#
# Bizim tahtamız boş kare için "" kullanır (Game_engine.py ile uyumlu).
# advanced_evaluation.py ise "." bekler.  İki yönde dönüşüm yapan adaptörler:

def _to_dot_board(board):
    """'""' → '"."' dönüşümü; Math_of_AI çağrıları için."""
    return [["." if cell == "" else cell for cell in row] for row in board]

def _from_dot_board(board):
    """'"."' → '""' dönüşümü (gerekirse)."""
    return [["" if cell == "." else cell for cell in row] for row in board]


def _move_gen_dot(dot_board, color):
    """Math_of_AI.mobility_score için adaptör (dot-board alır, dot-board verir)."""
    # dot_board → "" board → legal_moves → sayı
    real_board = _from_dot_board(dot_board)
    return legal_moves(real_board, color)


# ══════════════════════════════════════════════════════════════════════════════
# DEĞERLENDİRME
# ══════════════════════════════════════════════════════════════════════════════

def _evaluate(board, color):
    """
    Math_of_AI değerlendirme fonksiyonunu çağırır.
    Board "" → "." dönüşümü yapılır.
    """
    dot_board = _to_dot_board(board)
    return evaluate_for_ai(dot_board, color, _move_gen_dot)


# Math_of_AI dışı kullanım için (AI_CHESS içi çağrılar)
def _move_gen(board, color):
    return legal_moves(board, color)


# ══════════════════════════════════════════════════════════════════════════════
# TEMEL MİNİMAX  (Rol #4'ün katkısı — performans karşılaştırması için tutuldu)
# ══════════════════════════════════════════════════════════════════════════════

_minimax_node_count = 0   # benchmark sayacı

def minimax(board, color, depth):
    """
    Herhangi bir optimizasyon içermeyen saf Minimax.
    Tek amacı: alpha-beta ile karşılaştırmak için referans sağlamak.
    """
    global _minimax_node_count
    _minimax_node_count += 1

    opp   = "black" if color == "white" else "white"
    moves = legal_moves(board, color)

    # Terminal kontrol
    if not moves:
        return (-INF, None) if is_in_check(board, color) else (0, None)
    if depth == 0:
        return _evaluate(board, color), None

    best_score = -INF
    best_move  = moves[0]

    for fr, fc, tr, tc in moves:
        nb = apply_move(board, fr, fc, tr, tc)
        score, _ = minimax(nb, opp, depth - 1)
        score = -score                        # Negamax çerçevesi
        if score > best_score:
            best_score = score
            best_move  = (fr, fc, tr, tc)

    return best_score, best_move


# ══════════════════════════════════════════════════════════════════════════════
# OPTİMİZASYON #2 ─ HAMLE SIRALAMA
# ══════════════════════════════════════════════════════════════════════════════
#
# Alpha-Beta'nın verimliliği, ağaçtaki hamlelerin sıralamasına bağlıdır.
# En iyi hamle ilk aranırsa daha fazla kesim (pruning) gerçekleşir.
# Sıralama kriterleri (öncelik sırasıyla):
#   1. MVV-LVA  : En değerli kurbanı, en ucuz saldırganla ye
#   2. Killer   : Bu derinlikte beta kesimi yapan sessiz hamleler
#   3. History  : Geçmişte beta kesimi yapan hamlelerin ağırlığı

def _move_priority(board, move, killers, history, ply):
    fr, fc, tr, tc = move
    victim   = board[tr][tc]
    attacker = board[fr][fc]

    # 1) Yeme hamlesi — MVV-LVA skoru
    if victim != "":
        return 10_000 \
               + PIECE_VALUES.get(victim.upper(),   0) \
               - PIECE_VALUES.get(attacker.upper(), 0) // 10

    # 2) Killer hamle
    if move in killers.get(ply, []):
        return 9_000

    # 3) History heuristic
    return history.get((attacker, tr, tc), 0)


def _order_moves(board, moves, killers, history, ply):
    return sorted(moves,
                  key=lambda m: _move_priority(board, m, killers, history, ply),
                  reverse=True)


# ══════════════════════════════════════════════════════════════════════════════
# OPTİMİZASYON #3 ─ TRANSPOSISYON TABLOSU (Zobrist Hashing)
# ══════════════════════════════════════════════════════════════════════════════
#
# Bir tahta pozisyonu birden fazla hamle yoluyla ulaşılabilir (transpozisyon).
# Zobrist hashing ile her pozisyona benzersiz 64-bit anahtar atanır.
# Daha önce hesaplanan pozisyonlar tablodan okunur → yeniden arama yapılmaz.

_rng.seed(42)
_PIECE_IDX = {
    "P":0,"N":1,"B":2,"R":3,"Q":4,"K":5,
    "p":6,"n":7,"b":8,"r":9,"q":10,"k":11,
}
_ZOBRIST      = [[_rng.getrandbits(64) for _ in range(12)] for _ in range(64)]
_ZOBRIST_TURN = _rng.getrandbits(64)


def _hash_board(board, white_to_move: bool) -> int:
    """Tahta için deterministik 64-bit Zobrist hash üretir."""
    h = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p:
                h ^= _ZOBRIST[r * 8 + c][_PIECE_IDX[p]]
    if white_to_move:
        h ^= _ZOBRIST_TURN
    return h


# Transposisyon Tablosu giriş bayrakları
EXACT = 0   # kesin değer
LOWER = 1   # alt sınır (alpha'dan yükseltildi)
UPPER = 2   # üst sınır (beta'ya kesildi)


class TranspositionTable:
    """
    Tahta pozisyonlarını ve en iyi hamleleri önbellekleyen hash tablosu.
    Yaklaşık ~1 milyon giriş tutar (bellek ≈ 50-80 MB).
    """
    def __init__(self, size: int = 1 << 20):
        self.size  = size
        self._data: dict = {}

    def store(self, key: int, depth: int, score: int,
              flag: int, move) -> None:
        """(key, depth, score, flag, best_move) dörtlüsünü kaydeder."""
        slot = key % self.size
        # Aynı slotta daha derin veya aynı derinlik varsa üstüne yaz
        existing = self._data.get(slot)
        if existing is None or existing[1] <= depth:
            self._data[slot] = (key, depth, score, flag, move)

    def probe(self, key: int):
        """Hash eşleşirse kaydı döndürür, eşleşmezse None."""
        entry = self._data.get(key % self.size)
        return entry if (entry and entry[0] == key) else None

    def clear(self) -> None:
        self._data.clear()


# ══════════════════════════════════════════════════════════════════════════════
# OPTİMİZASYON #5 ─ QUIESCENCE SEARCH
# ══════════════════════════════════════════════════════════════════════════════
#
# Sabit derinlikte durmak "ufuk etkisi" yaratır: AI bir taşı yeme pozisyonunda
# durabilir ve tehlikeyi göremez. Quiescence, yalnızca yeme hamlelerini
# araştırarak taktiksel açıdan "sakin" bir pozisyona ulaşana dek devam eder.

_ab_node_count = 0   # benchmark sayacı


def _quiescence(board, color, alpha, beta, depth):
    """Yeme hamlelerini araştıran quiescence search."""
    stand_pat = _evaluate(board, color)

    if stand_pat >= beta:  return beta    # beta kesimi
    if stand_pat > alpha:  alpha = stand_pat
    if depth == 0:         return alpha   # quiescence derinlik sınırı

    opp      = "black" if color == "white" else "white"
    captures = [m for m in _all_pseudo_moves(board, color)
                if board[m[2]][m[3]] != ""]

    for fr, fc, tr, tc in captures:
        nb = apply_move(board, fr, fc, tr, tc)
        if is_in_check(nb, color): continue    # yasadışı hamle
        score = -_quiescence(nb, opp, -beta, -alpha, depth - 1)
        if score >= beta:   return beta
        if score >  alpha:  alpha = score

    return alpha


# ══════════════════════════════════════════════════════════════════════════════
# OPTİMİZASYON #1 ─ NEGAMAX + ALPHA-BETA PRUNING  (Ana Optimizasyon)
# ══════════════════════════════════════════════════════════════════════════════
#
# Alpha-Beta Pruning prensibi:
#   • alpha = mevcut oyuncunun garantilenmiş en iyi skoru (alt sınır)
#   • beta  = rakibin garantilenmiş en iyi skoru (üst sınır)
#   • score >= beta ise rakip bu hamleye izin vermez → dal kesilir (beta cutoff)
#   • score <= alpha ise bu dal zaten daha iyisinin altında → zaman kaybı
#
# Negamax çerçevesi: her derinlikte skor negated edilir, böylece her
# oyuncu kendi bakış açısından maximize eder.

def _alphabeta(board, color, depth, alpha, beta,
               tt, killers, history, null_ok=True, ply=0):
    """
    Alpha-Beta pruning ile Negamax araması.
    Tüm optimizasyonları (#1-#7) içerir.
    """
    global _ab_node_count
    _ab_node_count += 1

    opp       = "black" if color == "white" else "white"
    white_now = (color == "white")
    orig_alpha = alpha

    # ── Transposisyon Tablosu (Optimizasyon #3) ──────────────────────────────
    key   = _hash_board(board, white_now)
    entry = tt.probe(key)
    if entry:
        _, e_depth, e_score, e_flag, e_move = entry
        if e_depth >= depth:
            if   e_flag == EXACT: return e_score, e_move
            elif e_flag == LOWER: alpha = max(alpha, e_score)
            elif e_flag == UPPER: beta  = min(beta,  e_score)
            if alpha >= beta:     return e_score, e_move

    # ── Terminal Kontrol ─────────────────────────────────────────────────────
    moves = legal_moves(board, color)
    if not moves:
        # mat → derinliğe göre cezalandır (erken mat daha iyi)
        return (-INF + ply, None) if is_in_check(board, color) else (0, None)

    # ── Yaprak Düğüm → Quiescence Search (Optimizasyon #5) ──────────────────
    if depth == 0:
        score = _quiescence(board, color, alpha, beta, QSEARCH_DEPTH)
        return score, None

    # ── Null Move Pruning (Optimizasyon #6) ──────────────────────────────────
    # Sırayı rakibe verip arama yapıyoruz; eğer yine de beta'yı geçerse
    # bu pozisyon zaten rakibimiz için iyidir → dal kesilir.
    if null_ok and depth >= 3 and not is_in_check(board, color):
        ns, _ = _alphabeta(board, opp, depth - 1 - NULL_REDUCTION,
                           -beta, -beta + 1, tt, killers, history,
                           null_ok=False, ply=ply + 1)
        if -ns >= beta:
            return beta, None

    # ── Hamle Sıralama (Optimizasyon #2) ────────────────────────────────────
    ordered    = _order_moves(board, moves, killers, history, ply)
    best_score = -INF
    best_move  = ordered[0]

    for i, (fr, fc, tr, tc) in enumerate(ordered):
        nb = apply_move(board, fr, fc, tr, tc)

        # ── Late Move Reductions (Optimizasyon #7) ───────────────────────────
        # Sıralamada geriye kalan sessiz hamleler büyük olasılıkla kötüdür;
        # azaltılmış derinlikte ara, yalnızca alpha'yı geçerse tam derinlikte
        # yeniden ara.
        reduction = 0
        if i >= 4 and depth >= 3 and board[tr][tc] == "" \
                and not is_in_check(nb, color):
            reduction = 1

        score, _ = _alphabeta(nb, opp, depth - 1 - reduction,
                              -beta, -alpha, tt, killers, history,
                              null_ok=True, ply=ply + 1)
        score = -score

        # LMR alpha'yı geçtiyse tam derinlikte yeniden ara
        if reduction and score > alpha:
            score, _ = _alphabeta(nb, opp, depth - 1,
                                  -beta, -alpha, tt, killers, history,
                                  null_ok=True, ply=ply + 1)
            score = -score

        if score > best_score:
            best_score = score
            best_move  = (fr, fc, tr, tc)

        alpha = max(alpha, score)

        # ── BETA KESİMİ (Alpha-Beta'nın özü) ─────────────────────────────────
        if alpha >= beta:
            # Bu hamle rakibimizin zaten reddedeceği kadar iyi;
            # geri kalan hamleleri aramaya gerek yok.
            if board[tr][tc] == "":    # yalnızca sessiz hamleler
                killers.setdefault(ply, [])
                if (fr, fc, tr, tc) not in killers[ply] and len(killers[ply]) < 2:
                    killers[ply].append((fr, fc, tr, tc))
                key_h = (board[fr][fc], tr, tc)
                history[key_h] = history.get(key_h, 0) + depth * depth
            break

    # ── Transposisyon Tablosuna Kaydet ───────────────────────────────────────
    if   best_score <= orig_alpha: flag = UPPER
    elif best_score >= beta:       flag = LOWER
    else:                          flag = EXACT
    tt.store(key, depth, best_score, flag, best_move)

    return best_score, best_move


# ══════════════════════════════════════════════════════════════════════════════
# OPTİMİZASYON #4 ─ ITERATİF DERİNLEŞTİRME  +  ZORLUK SEVİYELERİ
# ══════════════════════════════════════════════════════════════════════════════
#
# Sabit derinlik yerine derinliği 1'den başlatıp zaman dolana kadar artırır.
# Avantajlar:
#   • Zaman sınırı içinde mümkün olan en iyi hamle garantilenir.
#   • Her derinliğin sonucu bir sonraki derinlik için iyi başlangıç noktasıdır.

def get_best_move(board, ai_color, difficulty="medium", verbose=True):
    """
    Oyun motoru için ana giriş noktası.

    Parametreler:
        board      : 8×8 liste (boş kare = "")
        ai_color   : "white" veya "black"
        difficulty : "easy" | "medium" | "hard"
        verbose    : Her derinlikte konsola çıktı yaz

    Döndürür:
        (fr, fc, tr, tc) demeti veya hamle yoksa None
    """
    cfg       = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS["medium"])
    max_depth = cfg["depth"]
    time_lim  = cfg["time"]

    moves = legal_moves(board, ai_color)
    if not moves:    return None
    if len(moves) == 1: return moves[0]   # zorlanmış hamle → arama gerekmez

    tt      = TranspositionTable()
    killers = {}
    history = {}
    start   = time.time()

    best_move  = moves[0]
    best_score = -INF

    if verbose:
        print(f"\n{'─'*55}")
        print(f"  AI [{cfg['label']}] düşünüyor …")
        print(f"{'─'*55}")

    for depth in range(1, max_depth + 1):
        if time.time() - start >= time_lim:
            break

        score, move = _alphabeta(board, ai_color, depth, -INF, INF,
                                 tt, killers, history)
        if move:
            best_move  = move
            best_score = score

        elapsed = time.time() - start
        if verbose:
            print(f"  Derinlik {depth:2d} │ Skor {best_score:+9.2f} │ "
                  f"Hamle {_fmt(best_move):6s} │ {elapsed:.3f}s")

        if abs(best_score) > INF // 2:
            break   # mat bulundu; daha derin aramaya gerek yok

    if verbose:
        print(f"{'─'*55}")
        print(f"  ✓ En iyi hamle: {_fmt(best_move)} "
              f"({time.time() - start:.2f}s)\n")

    return best_move


def _fmt(m):
    """Hamleyi satranç notasyonuna çevirir: e2e4"""
    if m is None: return "─"
    fr, fc, tr, tc = m
    files = "abcdefgh"
    return f"{files[fc]}{8 - fr}{files[tc]}{8 - tr}"


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANS KARŞILAŞTIRMASI  ─  Minimax vs Alpha-Beta
# ══════════════════════════════════════════════════════════════════════════════

def benchmark(board, ai_color, depth=3):
    """
    Aynı derinlikte saf minimax ve alpha-beta'yı çalıştırır;
    düğüm sayısı ve süreyi karşılaştırır.

    Döndürür: dict (raporlama ve grafik için kullanılabilir)

    Örnek kullanım:
        results = benchmark(board, "black", depth=3)
        # Raporlama/Testing rolü bu sonuçları grafik haline getirebilir
    """
    global _minimax_node_count, _ab_node_count

    print(f"\n{'═'*60}")
    print(f"  PERFORMANS KARŞILAŞTIRMASI  ─  Derinlik {depth}")
    print(f"{'═'*60}")

    # ── Saf Minimax ──────────────────────────────────────────────────────────
    _minimax_node_count = 0
    t0 = time.time()
    minimax(board, ai_color, depth)
    mm_time  = time.time() - t0
    mm_nodes = _minimax_node_count

    # ── Alpha-Beta ───────────────────────────────────────────────────────────
    _ab_node_count = 0
    t0 = time.time()
    _alphabeta(board, ai_color, depth, -INF, INF,
               TranspositionTable(), {}, {})
    ab_time  = time.time() - t0
    ab_nodes = _ab_node_count

    # ── Sonuçlar ─────────────────────────────────────────────────────────────
    pruned  = max(mm_nodes - ab_nodes, 0)
    pct     = (pruned / mm_nodes * 100) if mm_nodes else 0
    speedup = (mm_time  / ab_time)       if ab_time  else float("inf")

    print(f"  {'Metrik':<28} {'Minimax':>10}   {'Alpha-Beta':>12}")
    print(f"  {'─'*54}")
    print(f"  {'Ziyaret edilen düğüm':<28} {mm_nodes:>10,}   {ab_nodes:>12,}")
    print(f"  {'Süre (saniye)':<28} {mm_time:>10.4f}   {ab_time:>12.4f}")
    print(f"  {'Kesilen dal':<28} {'─':>10}   {pruned:>12,}")
    print(f"  {'Budama oranı':<28} {'─':>10}   {pct:>11.1f}%")
    print(f"  {'Hız çarpanı':<28} {'─':>10}   {speedup:>11.1f}x")
    print(f"{'═'*60}\n")

    return {
        "depth":           depth,
        "minimax_nodes":   mm_nodes,
        "minimax_time":    round(mm_time,  4),
        "alphabeta_nodes": ab_nodes,
        "alphabeta_time":  round(ab_time,  4),
        "pruned_nodes":    pruned,
        "pruning_pct":     round(pct,      2),
        "speedup":         round(speedup,  2),
    }


# ══════════════════════════════════════════════════════════════════════════════
# KOLAYLIK FONKSİYONU ─ Game_engine.py tarafından çağrılır
# ══════════════════════════════════════════════════════════════════════════════

def ai_make_move(board, ai_color="black", difficulty="medium"):
    """
    AI'ın hamlesini hesaplar ve tahtaya yerinde uygular.

    Game_engine.py örnek kullanımı:
        from AI_CHESS import ai_make_move
        move = ai_make_move(board, ai_color="black", difficulty=current_difficulty)
        if move:
            change_turn()

    Döndürür: (fr, fc, tr, tc) veya None
    """
    move = get_best_move(board, ai_color, difficulty)
    if move:
        fr, fc, tr, tc = move
        piece = board[fr][fc]
        board[tr][tc] = piece
        board[fr][fc] = ""
        # Piyon terfisi
        if piece == "P" and tr == 0: board[tr][tc] = "Q"
        if piece == "p" and tr == 7: board[tr][tc] = "q"
    return move
