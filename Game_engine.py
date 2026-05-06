"""
Game_engine.py ─ Oyun Motoru (Güncellenmiş)
════════════════════════════════════════════

AI_CHESS.py entegrasyonu için eklenenler (AI Developer – Optimization):
  • Oyun başlangıcında zorluk seçim ekranı (Easy / Medium / Hard)
  • AI siyah tarafı oynar (threading ile; UI donmaz)
  • Seçilen taş için yasal hamle vurgulaması (AI_CHESS.legal_moves)
  • Mat / Pat tespiti ve oyun sonu ekranı
  • AI "düşünüyor" göstergesi
"""

import pygame
import threading

# ── AI modülünü içe aktar ───────────────────────────────────────────────────
from AI_CHESS import (
    ai_make_move,
    legal_moves_for_piece,
    is_checkmate,
    is_stalemate,
)

# ══════════════════════════════════════════════════════════════════════════════
# PYGAME BAŞLANGIÇ
# ══════════════════════════════════════════════════════════════════════════════

pygame.init()

WIDTH, HEIGHT = 640, 760
ROWS, COLS    = 8, 8
SQUARE_SIZE   = WIDTH // COLS

# Renkler
LIGHT_SQUARE   = (240, 217, 181)
DARK_SQUARE    = (181, 136,  99)
HIGHLIGHT_MOVE = ( 20, 160,  20, 160)   # yeşil ─ yasal hamle
HIGHLIGHT_SEL  = (255, 255,   0, 140)   # sarı  ─ seçili kare
PANEL_COLOR    = ( 30,  30,  30)
BUTTON_COLOR   = ( 65,  65,  65)
BUTTON_HOVER   = ( 95,  95,  95)
BUTTON_ACCENT  = ( 50, 120, 200)
WHITE          = (255, 255, 255)
BLACK          = ( 10,  10,  10)
RED            = (210,  50,  50)
GREEN          = ( 50, 180,  80)
GOLD           = (212, 175,  55)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("AI Chess")

piece_font  = pygame.font.SysFont("segoeuisymbol", 68)
ui_font     = pygame.font.SysFont("arial", 22, bold=True)
small_font  = pygame.font.SysFont("arial", 16)
large_font  = pygame.font.SysFont("arial", 32, bold=True)
title_font  = pygame.font.SysFont("arial", 42, bold=True)

piece_symbols = {
    "r": "♜", "n": "♞", "b": "♝", "q": "♛", "k": "♚", "p": "♟",
    "R": "♖", "N": "♘", "B": "♗", "Q": "♕", "K": "♔", "P": "♙",
}

# ══════════════════════════════════════════════════════════════════════════════
# OYUN DURUMU
# ══════════════════════════════════════════════════════════════════════════════

def get_initial_board():
    return [
        ["r","n","b","q","k","b","n","r"],
        ["p","p","p","p","p","p","p","p"],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["","","","","","","",""],
        ["P","P","P","P","P","P","P","P"],
        ["R","N","B","Q","K","B","N","R"],
    ]

board          = get_initial_board()
selected_piece = None
selected_pos   = None
valid_targets  = []        # seçili taşın yasal hedef kareleri
turn           = "white"
move_history   = []

# AI durumu
ai_thinking    = False     # AI hesaplama yapıyor mu?
ai_move_ready  = None      # AI'ın ürettiği hamle (thread → ana döngü)
current_diff   = "medium"  # zorluk seviyesi (difficulty ekranından gelir)

# Oyun sonu
game_over      = False
game_result    = ""        # "white_wins" | "black_wins" | "stalemate"

# UI butonları (alt panel)
PANEL_Y        = HEIGHT - 100
undo_btn       = pygame.Rect( 20, PANEL_Y + 30, 110, 40)
restart_btn    = pygame.Rect(145, PANEL_Y + 30, 130, 40)
bench_btn      = pygame.Rect(290, PANEL_Y + 30, 160, 40)

# ══════════════════════════════════════════════════════════════════════════════
# ZORLUK SEÇİM EKRANI
# ══════════════════════════════════════════════════════════════════════════════

DIFF_LABELS = [
    ("easy",   "Easy",   "(Depth 2 — 1s)",  GREEN),
    ("medium", "Medium", "(Depth 4 — 2s)",  GOLD),
    ("hard",   "Hard",   "(Depth 6 — 4s)",  RED),
]

def run_difficulty_screen():
    """Oyun başlamadan önce zorluk seçimi ekranını gösterir."""
    btn_w, btn_h = 300, 60
    btn_x        = WIDTH  // 2 - btn_w // 2
    base_y       = HEIGHT // 2 - 60

    buttons = []
    for i, (key, label, sub, color) in enumerate(DIFF_LABELS):
        rect = pygame.Rect(btn_x, base_y + i * (btn_h + 18), btn_w, btn_h)
        buttons.append((rect, key, label, sub, color))

    clock = pygame.time.Clock()

    while True:
        mx, my = pygame.mouse.get_pos()
        screen.fill((20, 20, 30))

        # Başlık
        t1 = title_font.render("AI CHESS", True, GOLD)
        t2 = ui_font.render("Zorluk Seviyesi Seçin", True, (200, 200, 200))
        screen.blit(t1, t1.get_rect(centerx=WIDTH // 2, y=100))
        screen.blit(t2, t2.get_rect(centerx=WIDTH // 2, y=165))

        # Bilgi satırı
        info = small_font.render("Beyaz: Sen    │    Siyah: AI", True, (140, 140, 140))
        screen.blit(info, info.get_rect(centerx=WIDTH // 2, y=210))

        for rect, key, label, sub, color in buttons:
            hover   = rect.collidepoint(mx, my)
            bg      = tuple(min(c + 40, 255) for c in color[:3]) if hover else (45, 45, 55)
            border  = color

            pygame.draw.rect(screen, bg,     rect, border_radius=12)
            pygame.draw.rect(screen, border, rect, 2, border_radius=12)

            lbl  = ui_font.render(label, True, color)
            slbl = small_font.render(sub, True, (180, 180, 180))
            screen.blit(lbl,  lbl.get_rect(centerx=rect.centerx, y=rect.y + 8))
            screen.blit(slbl, slbl.get_rect(centerx=rect.centerx, y=rect.y + 34))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.MOUSEBUTTONDOWN:
                for rect, key, *_ in buttons:
                    if rect.collidepoint(event.pos):
                        return key      # seçilen zorluk anahtarını döndür


# ══════════════════════════════════════════════════════════════════════════════
# ÇIZIM FONKSİYONLARI
# ══════════════════════════════════════════════════════════════════════════════

def draw_board():
    for row in range(ROWS):
        for col in range(COLS):
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(screen, color,
                             (col * SQUARE_SIZE, row * SQUARE_SIZE,
                              SQUARE_SIZE, SQUARE_SIZE))

    # Koordinat etiketleri
    files = "abcdefgh"
    for i in range(8):
        lbl = small_font.render(files[i], True, (120, 80, 50))
        screen.blit(lbl, (i * SQUARE_SIZE + 3, HEIGHT - 110))
        lbl = small_font.render(str(8 - i), True, (120, 80, 50))
        screen.blit(lbl, (2, i * SQUARE_SIZE + 3))


def draw_highlights():
    """Seçili kare ve yasal hedef kareleri vurgular."""
    surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)

    # Seçili kare — sarı çerçeve
    if selected_pos:
        r, c = selected_pos
        pygame.draw.rect(screen, (240, 200, 0),
                         (c * SQUARE_SIZE, r * SQUARE_SIZE,
                          SQUARE_SIZE, SQUARE_SIZE), 4)

    # Yasal hedef kareler — yeşil nokta
    for (tr, tc) in valid_targets:
        surf.fill((0, 0, 0, 0))
        cx = SQUARE_SIZE // 2
        cy = SQUARE_SIZE // 2
        if board[tr][tc] != "":    # yeme hamlesi → halka
            pygame.draw.circle(surf, (20, 160, 20, 160), (cx, cy),
                               SQUARE_SIZE // 2 - 4, 5)
        else:                      # boş kare → dolu nokta
            pygame.draw.circle(surf, (20, 160, 20, 160), (cx, cy),
                               SQUARE_SIZE // 6)
        screen.blit(surf, (tc * SQUARE_SIZE, tr * SQUARE_SIZE))


def draw_pieces():
    for row in range(ROWS):
        for col in range(COLS):
            piece = board[row][col]
            if piece == "": continue
            symbol = piece_symbols[piece]
            x = col * SQUARE_SIZE + 4
            y = row * SQUARE_SIZE + 1
            if piece.isupper():                 # beyaz taşlar — kalın
                t = piece_font.render(symbol, True, WHITE)
                for dx, dy in ((0,0),(1,0),(0,1),(1,1)):
                    screen.blit(t, (x + dx, y + dy))
            else:                               # siyah taşlar
                t = piece_font.render(symbol, True, (15, 15, 15))
                screen.blit(t, (x, y))


def draw_button(rect, text, accent=False):
    mx, my = pygame.mouse.get_pos()
    hover  = rect.collidepoint(mx, my)
    bg     = BUTTON_ACCENT if accent else (BUTTON_HOVER if hover else BUTTON_COLOR)
    border = (100, 160, 255) if accent else (160, 160, 160)
    pygame.draw.rect(screen, bg,     rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, 2, border_radius=10)
    lbl = small_font.render(text, True, WHITE)
    screen.blit(lbl, lbl.get_rect(center=rect.center))


DIFF_COLOR = {"easy": GREEN, "medium": GOLD, "hard": RED}

def draw_ui():
    """Alt paneli çizer."""
    pygame.draw.rect(screen, PANEL_COLOR, (0, PANEL_Y, WIDTH, HEIGHT - PANEL_Y))
    pygame.draw.line(screen, (60, 60, 60), (0, PANEL_Y), (WIDTH, PANEL_Y), 2)

    if ai_thinking:
        # AI düşünüyor göstergesi (nabız efekti)
        t = pygame.time.get_ticks()
        alpha_val = int(128 + 127 * abs((t % 1000) / 500.0 - 1))
        lbl = ui_font.render("🤖 AI düşünüyor…", True,
                             (alpha_val, alpha_val, 255))
        screen.blit(lbl, lbl.get_rect(centerx=WIDTH // 2, y=PANEL_Y + 8))
    else:
        # Sıra göstergesi
        col  = WHITE if turn == "white" else (180, 180, 180)
        txt  = "⬜ BEYAZ SIRASI" if turn == "white" else "⬛ SİYAH SIRASI (AI)"
        lbl  = ui_font.render(txt, True, col)
        screen.blit(lbl, lbl.get_rect(centerx=WIDTH // 2, y=PANEL_Y + 8))

    # Zorluk etiketi
    diff_col  = DIFF_COLOR.get(current_diff, WHITE)
    diff_lbl  = small_font.render(f"Zorluk: {current_diff.upper()}", True, diff_col)
    screen.blit(diff_lbl, (WIDTH - 120, PANEL_Y + 10))

    draw_button(undo_btn,    "↩ GERİ AL")
    draw_button(restart_btn, "↺ YENİDEN")
    draw_button(bench_btn,   "📊 BENCHMARK", accent=True)


def draw_game_over():
    """Oyun sonu overlay'i çizer."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    if game_result == "white_wins":
        msg  = "⬜ BEYAZ KAZANDI!"
        col  = WHITE
    elif game_result == "black_wins":
        msg  = "⬛ SİYAH (AI) KAZANDI!"
        col  = (150, 150, 255)
    else:
        msg  = "PAT! Beraberlik."
        col  = GOLD

    t1 = large_font.render(msg, True, col)
    t2 = small_font.render("Yeniden oynamak için RESTART'a bas", True, (200, 200, 200))
    screen.blit(t1, t1.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 - 20))
    screen.blit(t2, t2.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2 + 30))


# ══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════

def change_turn():
    global turn
    turn = "black" if turn == "white" else "white"


def reset_selection():
    global selected_piece, selected_pos, valid_targets
    selected_piece = None
    selected_pos   = None
    valid_targets  = []


def full_reset():
    global board, move_history, turn, game_over, game_result, ai_move_ready
    board         = get_initial_board()
    move_history  = []
    turn          = "white"
    game_over     = False
    game_result   = ""
    ai_move_ready = None
    reset_selection()


def check_game_over():
    """Mat veya pat kontrolü yapar; sonucu ayarlar."""
    global game_over, game_result
    if is_checkmate(board, turn):
        game_over   = True
        game_result = "black_wins" if turn == "white" else "white_wins"
    elif is_stalemate(board, turn):
        game_over   = True
        game_result = "stalemate"


# ══════════════════════════════════════════════════════════════════════════════
# AI THREAD
# ══════════════════════════════════════════════════════════════════════════════

def _ai_worker():
    """Arka planda AI hamlesini hesaplar; sonucu global değişkene yazar."""
    global ai_move_ready
    ai_make_move(board, ai_color="black", difficulty=current_diff)
    # ai_make_move board'u yerinde değiştirir; sadece sinyali güncelleriz.
    ai_move_ready = True


def start_ai_turn():
    """AI hesaplamasını ayrı bir thread'de başlatır."""
    global ai_thinking, ai_move_ready
    ai_thinking   = True
    ai_move_ready = None
    t = threading.Thread(target=_ai_worker, daemon=True)
    t.start()


# ══════════════════════════════════════════════════════════════════════════════
# BENCHMARK EKRANI
# ══════════════════════════════════════════════════════════════════════════════

def run_benchmark_screen():
    """Anlık board durumunda benchmark sonuçlarını hesaplar ve gösterir."""
    from AI_CHESS import benchmark as run_bench

    # Hesaplama (ekran kararır, sonra sonuçlar gösterilir)
    screen.fill((20, 20, 30))
    msg = ui_font.render("Benchmark hesaplanıyor, lütfen bekleyin…", True, GOLD)
    screen.blit(msg, msg.get_rect(centerx=WIDTH // 2, centery=HEIGHT // 2))
    pygame.display.flip()

    results = run_bench(board, "black", depth=3)

    # Sonuç ekranı
    clock = pygame.time.Clock()
    running = True
    while running:
        screen.fill((20, 20, 30))
        lines = [
            ("BENCHMARK SONUÇLARI (Derinlik 3)", GOLD,    title_font),
            ("",                                  WHITE,   small_font),
            (f"Saf Minimax   → {results['minimax_nodes']:,} düğüm, {results['minimax_time']:.4f}s",
             WHITE, ui_font),
            (f"Alpha-Beta    → {results['alphabeta_nodes']:,} düğüm, {results['alphabeta_time']:.4f}s",
             GREEN, ui_font),
            (f"Budanan dal   → {results['pruned_nodes']:,} (%{results['pruning_pct']})",
             (150, 200, 255), ui_font),
            (f"Hız çarpanı   → {results['speedup']}x daha hızlı",
             GOLD,  large_font),
            ("",                                  WHITE, small_font),
            ("[Devam etmek için bir tuşa bas]",   (150,150,150), small_font),
        ]
        y = 80
        for text, color, font in lines:
            lbl = font.render(text, True, color)
            screen.blit(lbl, lbl.get_rect(centerx=WIDTH // 2, y=y))
            y += font.get_height() + 8
        pygame.display.flip()
        clock.tick(60)
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False


# ══════════════════════════════════════════════════════════════════════════════
# ANA DÖNGÜ
# ══════════════════════════════════════════════════════════════════════════════

# Zorluk seçim ekranını göster
current_diff = run_difficulty_screen()

clock = pygame.time.Clock()
running = True

while running:
    clock.tick(60)
    screen.fill((0, 0, 0))

    draw_board()
    draw_highlights()
    draw_pieces()
    draw_ui()

    if game_over:
        draw_game_over()

    # ── AI sırası kontrolü ────────────────────────────────────────────────────
    if not game_over and turn == "black" and not ai_thinking:
        start_ai_turn()

    if ai_thinking and ai_move_ready is True:
        ai_thinking   = False
        ai_move_ready = None
        change_turn()
        check_game_over()

    # ── Olaylar ───────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()

            # ── Buton alanı ─────────────────────────────────────────────────
            if undo_btn.collidepoint(x, y):
                if move_history and not ai_thinking:
                    board = move_history.pop()
                    if move_history:   # AI hamlesini de geri al
                        board = move_history.pop()
                    game_over = False
                    game_result = ""
                    turn = "white"
                reset_selection()

            elif restart_btn.collidepoint(x, y):
                full_reset()
                current_diff = run_difficulty_screen()

            elif bench_btn.collidepoint(x, y):
                if not ai_thinking:
                    run_benchmark_screen()

            # ── Tahta alanı ─────────────────────────────────────────────────
            elif y < PANEL_Y and not game_over and turn == "white" and not ai_thinking:
                row = y // SQUARE_SIZE
                col = x // SQUARE_SIZE

                if selected_piece is None:
                    # Taş seç
                    clicked = board[row][col]
                    if clicked != "" and clicked.isupper():   # beyaz taş
                        selected_piece = clicked
                        selected_pos   = (row, col)
                        valid_targets  = legal_moves_for_piece(
                            board, "white", row, col)

                else:
                    # Hamle yap veya seçimi değiştir
                    old_r, old_c = selected_pos

                    if (row, col) == (old_r, old_c):
                        # Aynı kare → seçimi kaldır
                        reset_selection()

                    elif (row, col) in valid_targets:
                        # Yasal hamle
                        move_history.append([r[:] for r in board])
                        board[row][col]   = selected_piece
                        board[old_r][old_c] = ""

                        # Piyon terfisi
                        if selected_piece == "P" and row == 0:
                            board[row][col] = "Q"

                        reset_selection()
                        change_turn()
                        check_game_over()

                    elif board[row][col] != "" and board[row][col].isupper():
                        # Başka bir beyaz taşa geç
                        selected_piece = board[row][col]
                        selected_pos   = (row, col)
                        valid_targets  = legal_moves_for_piece(
                            board, "white", row, col)
                    else:
                        # Geçersiz kare → seçimi kaldır
                        reset_selection()

    pygame.display.update()

pygame.quit()
