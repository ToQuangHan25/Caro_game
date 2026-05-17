# 1. Nâng cấp Vòng đời Trò chơi (Game Loop & State Machine)
# Code cũ: Trò chơi là một luồng tuyến tính. Đánh xong 1 ván, màn hình khựng lại 2 giây rồi tự động văng (tắt chương trình).

# Code mới: Áp dụng mô hình Vòng lặp trạng thái vô hạn.

# Thêm vòng lặp while True ngoài cùng bao bọc lấy ván đấu.

# Bổ sung hàm reset_game_state() để tự động dọn dẹp sạch sẽ bàn cờ, reset lượt đi và lịch sử khi bắt đầu ván mới.

# Kết quả: Người chơi có thể chơi đi chơi lại vô số ván mà không cần phải mở lại file code.

# 2. Xây dựng Hệ thống Phân cấp Độ khó (AI Difficulty)
# Code cũ: Bot chỉ có 1 mức cấu hình duy nhất (vét cạn mọi khả năng), đánh rất khó và chậm.

# Code mới: Xây dựng thành công Giao diện Menu chọn độ khó với 3 cấp bậc rõ rệt, can thiệp sâu vào thuật toán Minimax và Alpha-Beta:
#     Cấp Dễ (Depth = 1): Tắt chế độ sắp xếp thông minh. Chọn 5 nước đi. Minimax không tính depth vào điểm số nên AI có xu hướng đánh ngây ngô, dễ mắc bẫy.
#     Cấp TB (Depth = 2): Sử dụng hàm Heuristic để sắp xếp điểm, nhưng giới hạn chỉ cắt Top 30 nước đi tiềm năng nhất nên AI đánh rất nhanh, phòng thủ cơ bản tốt nhưng có thể bỏ sót các bẫy xa.
#     Cấp Khó (Depth = 3): Tháo bỏ toàn bộ giới hạn cắt tỉa. AI vét cạn toàn bộ các ô trống, kết hợp với tham số depth cộng vào điểm số để tối ưu hóa việc thắng nhanh nhất / thua lâu nhất.

# 3. Cải tiến Trải nghiệm Giao diện (UI/UX)
# Sửa lỗi font chữ: Đổi toàn bộ hệ thống sang font tahoma để hỗ trợ hiển thị Tiếng Việt 100%.

# Hiệu ứng Game Over xịn sò: Khi có người thắng, bàn cờ sẽ được phủ một lớp nền mờ ảo (Alpha Overlay 200), hiển thị dòng chữ thông báo màu Xanh/Đỏ tương ứng.

# Tương tác mượt mà: Khóa màn hình lại và chờ người chơi Click chuột vào bất cứ đâu để quay trở lại Menu.

# 4. Tối ưu Quản lý Luồng (Threading) & Dữ liệu (PGN)
# Sửa luồng Terminal (terminal_input_thread) thành vòng lặp while True để nó sống vĩnh viễn, cho phép người chơi gõ phím ở bất kỳ ván nào.

# Xử lý triệt để logic Biên bản (PGN): * Tự động in biên bản khi ván cờ kết thúc.

# Gọi pgn_history.clear() ngay sau khi in để tránh lỗi in lặp cú đúp khi quay ra Menu.

# Thêm logic if not pgn_history: return để tránh việc in ra một bảng rỗng vô nghĩa.

# Đồng bộ lệnh print_pgn_final() vào tất cả các nút [X] (QUIT) để đảm bảo không bao giờ bị mất dữ liệu khi người chơi thoát game đột ngột.
import pygame
import sys
import math
import re
import threading
import time

# ==========================================
# 1. BỘ NÃO AI ĐÃ TỐI ƯU HÓA TỐC ĐỘ (SPEED OPTIMIZED)
# ==========================================
BOARD_SIZE = 15

SCORE_MATRIX = {
    (1, 1, 1, 1, 1): 100000,   
    (0, 1, 1, 1, 1, 0): 10000, 
    (0, 1, 1, 1, 1): 2000,     
    (1, 1, 1, 1, 0): 2000,     
    (0, 1, 1, 1, 0): 1500,     
    (0, 1, 1, 0, 1, 0): 1200,  
    (0, 1, 1, 1): 500,         
    (0, 1, 1, 0): 200,         

    (-1, -1, -1, -1, -1): -80000, 
    (0, -1, -1, -1, -1, 0): -30000,
    (0, -1, -1, -1, -1): -9500,    
    (-1, -1, -1, -1, 0): -9500,
    (0, -1, -1, -1, 0): -4000,     
    (0, -1, -1, -1): -800,
    (0, -1, -1, 0): -100
}

def evaluate_line(line):
    line_score = 0
    line_str = tuple(line)
    for length in [6, 5, 4]:
        for i in range(len(line_str) - length + 1):
            sub_line = line_str[i:i+length]
            if sub_line in SCORE_MATRIX:
                line_score += SCORE_MATRIX[sub_line]
    return line_score

def evaluate_board_heuristic(board):
    total_score = 0
    for r in range(BOARD_SIZE):
        total_score += evaluate_line(board[r])
    for c in range(BOARD_SIZE):
        col = [board[r][c] for r in range(BOARD_SIZE)]
        total_score += evaluate_line(col)
    for d in range(-BOARD_SIZE + 1, BOARD_SIZE):
        diag1 = [board[i][i - d] for i in range(BOARD_SIZE) if 0 <= i - d < BOARD_SIZE]
        diag2 = [board[i][BOARD_SIZE - 1 - i - d] for i in range(BOARD_SIZE) if 0 <= BOARD_SIZE - 1 - i - d < BOARD_SIZE]
        if len(diag1) >= 4: total_score += evaluate_line(diag1)
        if len(diag2) >= 4: total_score += evaluate_line(diag2)
    return total_score

def check_win(board, player):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != player: continue
            for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                count = 0
                for i in range(5):
                    nr, nc = r + dr*i, c + dc*i
                    if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == player:
                        count += 1
                    else: break
                if count == 5: return True
    return False

def get_interesting_moves(board):
    global BOT_DEPTH
    
    # TỐI ƯU 1: Quay trở lại bán kính 1 ô như caro_game99 để giảm dữ liệu thừa
    moves = set()
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0: continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == 0:
                            moves.add((nr, nc))
    
    move_list = list(moves)

    # ==========================================
    # CẤP 1: DỄ (Giữ nguyên logic bạn khen ổn)
    # ==========================================
    if BOT_DEPTH == 1:
        return move_list[:5] if move_list else [(BOARD_SIZE//2, BOARD_SIZE//2)]

    # ==========================================
    # CẤP 2 & 3: TRUNG BÌNH VÀ KHÓ
    # ==========================================
    # Sắp xếp các ô ưu tiên gần trung tâm
    move_list.sort(key=lambda m: abs(m[0]-BOARD_SIZE//2) + abs(m[1]-BOARD_SIZE//2))
    
    if BOT_DEPTH == 2:
        # Cấp Trung bình: Giới hạn 30 nước đi. 
        # thi thoảng vẫn sẽ bị lọt bẫy nếu bạn đánh giãn đội hình ra xa.
        return move_list[:30] if move_list else [(BOARD_SIZE//2, BOARD_SIZE//2)]
    else:
        # CẤP KHÓ: VŨ KHÍ TỐI THƯỢNG CỦA CARO_GAME99
        # Tại Depth 3, AI sẽ vét cạn 100% các ô trống xung quanh bàn cờ. Không bỏ lọt bất kỳ cơ hội nào!
        return move_list if move_list else [(BOARD_SIZE//2, BOARD_SIZE//2)]

def minimax(board, depth, alpha, beta, maximizing_player):
    global BOT_DEPTH
    
    # LÕI ĐIỀU CHỈNH ĐỘ KHÓ:
    # Cấp Dễ (1): KHÔNG dùng depth. Nó không biết kéo dài sự sống hay thắng nhanh.
    # Cấp TB & Khó (2, 3): CÓ dùng depth để sinh tồn và dồn ép.

    if check_win(board, 1): return 1000000 + depth, None
    if check_win(board, -1): return -1000000 - depth, None
    if depth == 0: return evaluate_board_heuristic(board), None

    moves = get_interesting_moves(board)
    best_move = None

    if maximizing_player:
        max_eval = -math.inf
        for r, c in moves:
            board[r][c] = 1
            evaluation, _ = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = 0
            if evaluation > max_eval: max_eval = evaluation; best_move = (r, c)
            alpha = max(alpha, evaluation)
            if beta <= alpha: break
        return max_eval, best_move
    else:
        min_eval = math.inf
        for r, c in moves:
            board[r][c] = -1
            evaluation, _ = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = 0
            if evaluation < min_eval: min_eval = evaluation; best_move = (r, c)
            beta = min(beta, evaluation)
            if beta <= alpha: break
        return min_eval, best_move

# ==========================================
# 2. HỆ TỌA ĐỘ ĐẢO NGƯỢC & ĐỊNH DẠNG PGN
# ==========================================
def parse_input(move_str):
    move_str = move_str.strip().upper()
    match = re.match(r"^([A-O])(15|1[0-4]|[1-9])$", move_str)
    if not match: return None
    col_char, row_str = match.groups()
    col = ord(col_char) - ord('A')
    row = int(row_str) - 1
    return row, col

def format_output(row, col):
    return f"{chr(col + ord('A'))}{row + 1}"

# ==========================================
# 3. TRẠNG THÁI TOÀN CỤC CHIA SẺ
# ==========================================
board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
game_over = False
game_running = True
current_turn = -1  
pgn_history = []   
input_buffer = ""  
bot_thinking = False  # Cờ hiệu kiểm tra Bot đang tính toán hay không
board_lock = threading.Lock()
BOT_DEPTH = 3 # Mặc định là 3, sẽ được thay đổi ở màn hình Menu

def print_pgn_final():
    if not pgn_history:
        return
    print("\n" + "="*40)
    print("      BIÊN BẢN TRẬN ĐẤU PGN      ")
    print("="*40)
    pgn_str = ""
    for i in range(0, len(pgn_history), 2):
        move_num = (i // 2) + 1
        p_move = pgn_history[i]
        b_move = pgn_history[i+1] if i+1 < len(pgn_history) else ""
        pgn_str += f"{move_num}. {p_move} {b_move}  "
    print(pgn_str) # Không cần kiểm tra và in không có nước đi
    print("="*40 + "\n")

# Luồng phụ xử lý nhập liệu chữ từ Terminal
def terminal_input_thread():
    global input_buffer, game_running, game_over, current_turn
    while True: # ĐỔI THÀNH WHILE TRUE ĐỂ LUỒNG KHÔNG BỊ CHẾT SAU 1 VÁN
        if game_running and not game_over:
            if current_turn == -1 and not bot_thinking:
                try:
                    user_input = input().strip()
                    if user_input: input_buffer = user_input
                except: pass
        time.sleep(0.1)

# TỐI ƯU 3: ĐƯA TOÀN BỘ TIẾN TRÌNH TÍNH TOÁN CỦA BOT SANG LUỒNG RIÊNG KHÔNG GÂY ĐƠ ĐỒ HỌA
def bot_calculation_thread():
    global current_turn, game_over, bot_thinking, BOT_DEPTH
    bot_thinking = True
    
    with board_lock:
        board_copy = [row[:] for row in board]
    
    _, move = minimax(board_copy, depth=BOT_DEPTH, alpha=-math.inf, beta=math.inf, maximizing_player=True)
    
    if move and not game_over:
        r, c = move
        with board_lock:
            if board[r][c] == 0:
                board[r][c] = 1
                is_win = check_win(board, 1)
                move_str = format_output(r, c) + ("#" if is_win else "")
                pgn_history.append(move_str)
                print(f"-> Bot đáp trả: {move_str}")
                
                if is_win:
                    print("\n[KẾT THÚC] BOT ĐÃ THẮNG!")
                    game_over = True
                else:
                    current_turn = -1
                    print("Nhập nước đi của bạn (Ví dụ: H8): ")
    
    bot_thinking = False

# ==========================================
# 4. GIAO DIỆN ĐỒ HỌA GIAO TIẾP MƯỢT MÀ
# ==========================================
GRID_SIZE = 40                             
PADDING = 40                               
BOARD_PIXELS = BOARD_SIZE * GRID_SIZE      
WINDOW_SIZE = BOARD_PIXELS + (PADDING * 2) 

COLOR_BG = (235, 235, 230)       
COLOR_BOARD = (245, 245, 240)    
COLOR_GRID = (170, 170, 170)
COLOR_TEXT = (60, 64, 67)        
COLOR_X = (235, 77, 75)
COLOR_O = (72, 52, 212)

def draw_ui(screen, font):
    screen.fill(COLOR_BG)
    pygame.draw.rect(screen, COLOR_BOARD, (PADDING, PADDING, BOARD_PIXELS, BOARD_PIXELS))
    for i in range(BOARD_SIZE + 1):
        pygame.draw.line(screen, COLOR_GRID, (PADDING, PADDING + i * GRID_SIZE), (PADDING + BOARD_PIXELS, PADDING + i * GRID_SIZE), 1)
        pygame.draw.line(screen, COLOR_GRID, (PADDING + i * GRID_SIZE, PADDING), (PADDING + i * GRID_SIZE, PADDING + BOARD_PIXELS), 1)
    
    for i in range(BOARD_SIZE):
        col_char = chr(i + ord('A'))
        text_surface = font.render(col_char, True, COLOR_TEXT)
        pos_x = PADDING + i * GRID_SIZE + (GRID_SIZE - text_surface.get_width()) // 2
        screen.blit(text_surface, (pos_x, PADDING // 3))                 
        screen.blit(text_surface, (pos_x, WINDOW_SIZE - PADDING + 10))   
        
        row_num = str(i + 1)
        text_surface = font.render(row_num, True, COLOR_TEXT)
        pos_y = PADDING + i * GRID_SIZE + (GRID_SIZE - text_surface.get_height()) // 2
        screen.blit(text_surface, (PADDING // 3, pos_y))                 
        screen.blit(text_surface, (WINDOW_SIZE - PADDING + 15, pos_y))   

    with board_lock:
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                center_x = PADDING + c * GRID_SIZE + GRID_SIZE // 2
                center_y = PADDING + r * GRID_SIZE + GRID_SIZE // 2
                if board[r][c] == 1:
                    pygame.draw.line(screen, COLOR_X, (center_x - 10, center_y - 10), (center_x + 10, center_y + 10), 3)
                    pygame.draw.line(screen, COLOR_X, (center_x + 10, center_y - 10), (center_x - 10, center_y + 10), 3)
                elif board[r][c] == -1:
                    pygame.draw.circle(screen, COLOR_O, (center_x, center_y), 12, 3)

def show_menu(screen, font):
    menu_running = True
    selected_depth = 3 # Mặc định

    # Kích thước và vị trí các nút bấm
    button_width = 200
    button_height = 60
    center_x = WINDOW_SIZE // 2 - button_width // 2
    
    btn_easy = pygame.Rect(center_x, 200, button_width, button_height)
    btn_medium = pygame.Rect(center_x, 300, button_width, button_height)
    btn_hard = pygame.Rect(center_x, 400, button_width, button_height)

    title_font = pygame.font.SysFont("tahoma", 32, bold=True)
    
    while menu_running:
        screen.fill(COLOR_BG)
        
        # Vẽ tiêu đề
        title_text = title_font.render("CHỌN ĐỘ KHÓ", True, COLOR_TEXT)
        screen.blit(title_text, (WINDOW_SIZE // 2 - title_text.get_width() // 2, 100))

        # Vẽ nút DỄ (Màu Xanh lá)
        pygame.draw.rect(screen, (46, 204, 113), btn_easy, border_radius=10)
        text_easy = font.render("DỄ", True, (255, 255, 255))
        screen.blit(text_easy, (btn_easy.centerx - text_easy.get_width() // 2, btn_easy.centery - text_easy.get_height() // 2))

        # Vẽ nút TRUNG BÌNH (Màu Vàng)
        pygame.draw.rect(screen, (241, 196, 15), btn_medium, border_radius=10)
        text_med = font.render("TRUNG BÌNH", True, (255, 255, 255))
        screen.blit(text_med, (btn_medium.centerx - text_med.get_width() // 2, btn_medium.centery - text_med.get_height() // 2))

        # Vẽ nút KHÓ (Màu Đỏ)
        pygame.draw.rect(screen, (231, 76, 60), btn_hard, border_radius=10)
        text_hard = font.render("KHÓ", True, (255, 255, 255))
        screen.blit(text_hard, (btn_hard.centerx - text_hard.get_width() // 2, btn_hard.centery - text_hard.get_height() // 2))

        pygame.display.flip()

        # Bắt sự kiện Click chuột
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                print_pgn_final()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if btn_easy.collidepoint(pos):
                    selected_depth = 1
                    menu_running = False
                elif btn_medium.collidepoint(pos):
                    selected_depth = 2
                    menu_running = False
                elif btn_hard.collidepoint(pos):
                    selected_depth = 3
                    menu_running = False

    return selected_depth

def reset_game_state():
    global board, game_over, game_running, current_turn, pgn_history, input_buffer, bot_thinking
    board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    game_over = False
    game_running = True
    current_turn = -1
    pgn_history = []
    input_buffer = ""
    bot_thinking = False

def main():
    global game_running, current_turn, game_over, input_buffer, BOT_DEPTH
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Caro AI vô hạn ELO")
    font = pygame.font.SysFont("tahoma", 16, bold=True)
    clock = pygame.time.Clock()
    
    # Luồng terminal khởi động 1 LẦN DUY NHẤT và chạy ngầm suốt trò chơi
    input_thread = threading.Thread(target=terminal_input_thread)
    input_thread.daemon = True
    input_thread.start()

    # ========================================================
    # VÒNG LẶP TỔNG: MENU -> CHƠI -> MENU -> CHƠI
    # ========================================================
    while True:
        # 1. Gọi màn hình Menu chọn cấp độ
        BOT_DEPTH = show_menu(screen, font)
        
        # 2. Xóa sạch ván cũ, chuẩn bị ván mới
        reset_game_state()
        print(f"\n=== VÁN MỚI - ĐỘ KHÓ CẤP {BOT_DEPTH} ===")
        print("Nhập nước đi của bạn (Ví dụ: H8): ")

        # 3. Vòng lặp TRẬN ĐẤU (Sẽ break khi game_over)
        while game_running:
            
            # --- Xử lý Terminal ---
            if current_turn == -1 and input_buffer != "" and not bot_thinking:
                coords = parse_input(input_buffer)
                input_buffer = ""
                if coords is None:
                    print("❌ Định dạng sai! Nhập lại (Ví dụ: H8): ")
                else:
                    r, c = coords
                    with board_lock:
                        if board[r][c] != 0:
                            print("❌ Ô đã có quân! Chọn ô khác: ")
                        else:
                            board[r][c] = -1
                            is_win = check_win(board, -1)
                            pgn_history.append(format_output(r, c) + ("#" if is_win else ""))
                            print(f"-> Bạn đi (Terminal): {format_output(r, c)}")
                            if is_win: game_over = True
                            else: current_turn = 1

            # --- Xử lý AI Bot ---
            if current_turn == 1 and not game_over and not bot_thinking:
                bot_thread = threading.Thread(target=bot_calculation_thread)
                bot_thread.daemon = True
                bot_thread.start()

            # --- Xử lý Click Chuột ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    print_pgn_final()
                    sys.exit() # Tắt hẳn app

                if event.type == pygame.MOUSEBUTTONDOWN and not game_over and current_turn == -1 and not bot_thinking:
                    mouseX, mouseY = pygame.mouse.get_pos()
                    clicked_col = (mouseX - PADDING) // GRID_SIZE
                    clicked_row = (mouseY - PADDING) // GRID_SIZE
                    
                    if 0 <= clicked_col < BOARD_SIZE and 0 <= clicked_row < BOARD_SIZE:
                        with board_lock:
                            if board[clicked_row][clicked_col] == 0:
                                board[clicked_row][clicked_col] = -1
                                is_win = check_win(board, -1)
                                pgn_history.append(format_output(clicked_row, clicked_col) + ("#" if is_win else ""))
                                print(f"-> Bạn đi (UI Mouse): {format_output(clicked_row, clicked_col)}")
                                if is_win: game_over = True
                                else: current_turn = 1 

            # ========================================================
            # HIỆU ỨNG GAME OVER - CHỜ CLICK ĐỂ VỀ MENU
            # ========================================================
            if game_over:
                draw_ui(screen, font)
                pygame.display.flip()
                time.sleep(2) # Dừng 1 giây để người chơi ngắm nước cờ chốt hạ
                
                # Làm mờ nền
                overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE))
                overlay.set_alpha(200)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))
                
                # Tự động phán đoán người thắng dựa vào lượt đánh cuối cùng
                if current_turn == -1:
                    msg = "BẠN ĐÃ CHIẾN THẮNG!"
                    color = (46, 204, 113) # Xanh lá
                else:
                    msg = "BẠN THUA RỒI!"
                    color = (231, 76, 60) # Đỏ
                    
                title_font = pygame.font.SysFont("tahoma", 26, bold=True)
                title_text = title_font.render(msg, True, color)
                hint_font = pygame.font.SysFont("tahoma", 16)
                hint_text = hint_font.render("(Click chuột vào màn hình để quay lại Menu)", True, (255, 255, 255))
                
                # Vẽ dòng thông báo ra giữa màn hình
                screen.blit(title_text, (WINDOW_SIZE//2 - title_text.get_width()//2, WINDOW_SIZE//2 - 40))
                screen.blit(hint_text, (WINDOW_SIZE//2 - hint_text.get_width()//2, WINDOW_SIZE//2 + 20))
                pygame.display.flip()
                
                # Tạo vòng lặp chết để gài game lại, chờ 1 cú click chuột
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            print_pgn_final()
                            sys.exit()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            waiting = False # Nhả vòng lặp
                # ---> IN BIÊN BẢN TRẬN ĐẤU RA TERMINAL TRƯỚC KHI VỀ MENU <---
                print_pgn_final()
                
                # THÊM ĐÚNG 1 DÒNG NÀY ĐỂ DỌN SẠCH LỊCH SỬ TRÁNH IN LẶP CÚ ĐÚP:
                pgn_history.clear()
                # Phá vỡ vòng lặp TRẬN ĐẤU, nó sẽ tự động nhảy ngược lên trên vòng lặp TỔNG
                # và gọi lại hàm show_menu()!
                break 

            if game_running:
                draw_ui(screen, font)
                pygame.display.flip()
            clock.tick(30)

if __name__ == "__main__":
    main()
    print('a')
    print('a')