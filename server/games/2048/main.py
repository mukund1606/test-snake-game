import pygame
import random
import asyncio


class Game2048:
    def __init__(self):
        # -----------------------------
        # 1) SCALING AND SCREEN SETUP
        # -----------------------------
        # We'll use the Pyodide variables: speed for FPS, canvas for dimensions
        self.speed = pyodide.globals.get("speed")  # user-defined FPS
        canvas = pyodide.globals.get("canvas")
        width, height = canvas.width, canvas.height
        min_val = min(width, height)

        # Use 500 here as the “reference dimension” (per your code).
        self.SCALE = min_val / 500.0

        # Our original game was 400 wide x 500 high
        self.SCREEN_WIDTH = int(400 * self.SCALE)
        self.SCREEN_HEIGHT = int(500 * self.SCALE)

        # Initialize Pygame and create the scaled window
        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("2048")

        # Create the clock
        self.timer = pygame.time.Clock()

        # -----------------------------
        # 2) FONT AND SIZE CONSTANTS
        # -----------------------------
        self.font_size = int(24 * self.SCALE)
        self.font = pygame.font.Font("freesansbold.ttf", self.font_size)

        # Tile sizes and offsets
        self.tile_size = int(75 * self.SCALE)
        self.tile_offset = int(20 * self.SCALE)
        self.tile_gap = self.tile_size + self.tile_offset

        self.score_y1 = int(410 * self.SCALE)

        # Colors
        self.colors = {
            0: (204, 192, 179),
            2: (238, 228, 218),
            4: (237, 224, 200),
            8: (242, 177, 121),
            16: (245, 149, 99),
            32: (246, 124, 95),
            64: (246, 94, 59),
            128: (237, 207, 114),
            256: (237, 204, 97),
            512: (237, 200, 80),
            1024: (237, 197, 63),
            2048: (237, 194, 46),
            "light text": (249, 246, 242),
            "dark text": (119, 110, 101),
            "other": (0, 0, 0),
            "bg": (187, 173, 160),
        }

        # -----------------------------
        # 3) GAME VARIABLES
        # -----------------------------
        self.board_values = [[0 for _ in range(4)] for _ in range(4)]
        self.game_over = False
        self.spawn_new = True
        self.init_count = 0
        self.direction = ""
        self.score = 0

        # -----------------------------
        # 4) MAIN LOOP CONTROL
        # -----------------------------
        self.run_game = True

    # -----------------------------
    # 5) HELPER FUNCTIONS
    # -----------------------------
    def draw_over(self):
        """Draw 'Game Over' plus 'Refresh to play again'."""
        rect_x = int(50 * self.SCALE)
        rect_y = int(50 * self.SCALE)
        rect_w = int(300 * self.SCALE)
        rect_h = int(100 * self.SCALE)

        pygame.draw.rect(self.screen, "black", [rect_x, rect_y, rect_w, rect_h], 0, 10)

        # Notify Pyodide that game ended
        pyodide.globals.get("setIsGameEnded")(True)

        over_txt1 = self.font.render("Game Over!", True, "white")
        over_txt2 = self.font.render("Refresh to play again", True, "white")

        self.screen.blit(
            over_txt1, (rect_x + int(80 * self.SCALE), rect_y + int(15 * self.SCALE))
        )
        self.screen.blit(
            over_txt2, (rect_x + int(30 * self.SCALE), rect_y + int(55 * self.SCALE))
        )

    def take_turn(self, direc, board):
        merged = [[False] * 4 for _ in range(4)]
        s = self.score
        if direc == "UP":
            for i in range(4):
                for j in range(4):
                    shift = 0
                    if i > 0:
                        for q in range(i):
                            if board[q][j] == 0:
                                shift += 1
                        if shift > 0:
                            board[i - shift][j] = board[i][j]
                            board[i][j] = 0
                        if (
                            i - shift - 1 >= 0
                            and board[i - shift - 1][j] == board[i - shift][j] != 0
                            and not merged[i - shift][j]
                            and not merged[i - shift - 1][j]
                        ):
                            board[i - shift - 1][j] *= 2
                            s += board[i - shift - 1][j]
                            board[i - shift][j] = 0
                            merged[i - shift - 1][j] = True

        elif direc == "DOWN":
            for i in range(3):
                for j in range(4):
                    shift = 0
                    for q in range(i + 1):
                        if board[3 - q][j] == 0:
                            shift += 1
                    if shift > 0:
                        board[2 - i + shift][j] = board[2 - i][j]
                        board[2 - i][j] = 0
                    if (
                        3 - i + shift <= 3
                        and board[2 - i + shift][j] == board[3 - i + shift][j] != 0
                        and not merged[3 - i + shift][j]
                        and not merged[2 - i + shift][j]
                    ):
                        board[3 - i + shift][j] *= 2
                        s += board[3 - i + shift][j]
                        board[2 - i + shift][j] = 0
                        merged[3 - i + shift][j] = True

        elif direc == "LEFT":
            for i in range(4):
                for j in range(4):
                    shift = 0
                    for q in range(j):
                        if board[i][q] == 0:
                            shift += 1
                    if shift > 0:
                        board[i][j - shift] = board[i][j]
                        board[i][j] = 0
                    if (
                        j - shift - 1 >= 0
                        and board[i][j - shift] == board[i][j - shift - 1] != 0
                        and not merged[i][j - shift]
                        and not merged[i][j - shift - 1]
                    ):
                        board[i][j - shift - 1] *= 2
                        s += board[i][j - shift - 1]
                        board[i][j - shift] = 0
                        merged[i][j - shift - 1] = True

        elif direc == "RIGHT":
            for i in range(4):
                for j in range(4):
                    shift = 0
                    for q in range(j):
                        if board[i][3 - q] == 0:
                            shift += 1
                    if shift > 0:
                        board[i][3 - j + shift] = board[i][3 - j]
                        board[i][3 - j] = 0
                    if (
                        4 - j + shift <= 3
                        and board[i][4 - j + shift] == board[i][3 - j + shift] != 0
                        and not merged[i][4 - j + shift]
                        and not merged[i][3 - j + shift]
                    ):
                        board[i][4 - j + shift] *= 2
                        s += board[i][4 - j + shift]
                        board[i][3 - j + shift] = 0
                        merged[i][4 - j + shift] = True

        self.score = s
        pyodide.globals.get("setScore")(self.score)
        return board

    def new_pieces(self, board):
        count = 0
        full = False
        while any(0 in row for row in board) and count < 1:
            row = random.randint(0, 3)
            col = random.randint(0, 3)
            if board[row][col] == 0:
                count += 1
                if random.randint(1, 10) == 10:
                    board[row][col] = 4
                else:
                    board[row][col] = 2
        if count < 1:
            full = True
        return board, full

    def draw_board(self):
        pygame.draw.rect(
            self.screen,
            self.colors["bg"],
            [0, 0, self.SCREEN_WIDTH, self.SCREEN_WIDTH],
            0,
            10,
        )
        sc_txt = self.font.render(f"Score: {self.score}", True, "black")
        self.screen.blit(sc_txt, (int(10 * self.SCALE), self.score_y1))

    def draw_pieces(self):
        for i in range(4):
            for j in range(4):
                value = self.board_values[i][j]
                value_color = (
                    self.colors["light text"] if value > 8 else self.colors["dark text"]
                )
                color = (
                    self.colors[value] if value in self.colors else self.colors["other"]
                )

                left_x = j * self.tile_gap + self.tile_offset
                top_y = i * self.tile_gap + self.tile_offset

                pygame.draw.rect(
                    self.screen,
                    color,
                    [left_x, top_y, self.tile_size, self.tile_size],
                    0,
                    5,
                )
                pygame.draw.rect(
                    self.screen,
                    "black",
                    [left_x, top_y, self.tile_size, self.tile_size],
                    2,
                    5,
                )

                if value > 0:
                    val_str = str(value)
                    length = len(val_str)
                    tile_font_size = max(
                        int((48 - 5 * length) * self.SCALE), int(12 * self.SCALE)
                    )
                    tile_font = pygame.font.Font("freesansbold.ttf", tile_font_size)
                    value_text = tile_font.render(val_str, True, value_color)
                    text_rect = value_text.get_rect(
                        center=(
                            left_x + self.tile_size // 2,
                            top_y + self.tile_size // 2,
                        )
                    )
                    self.screen.blit(value_text, text_rect)

    # -----------------------------
    # 6) MAIN LOOP
    # -----------------------------
    async def run(self):
        while self.run_game:
            self.timer.tick(self.speed)
            self.screen.fill("gray")

            # Draw background, scores, pieces
            self.draw_board()
            self.draw_pieces()

            # Possibly spawn new tile
            if self.spawn_new or self.init_count < 2:
                self.board_values, self.game_over = self.new_pieces(self.board_values)
                self.spawn_new = False
                self.init_count += 1

            # If a direction has been chosen, take a turn
            if self.direction != "" and not self.game_over:
                self.board_values = self.take_turn(self.direction, self.board_values)
                self.direction = ""
                self.spawn_new = True

            if self.game_over:
                self.draw_over()

            # -----------------------------
            # IGNORE KEYBOARD IF GAME OVER
            # -----------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run_game = False
                elif event.type == pygame.KEYUP:
                    # Only handle arrows if game is not over
                    if not self.game_over:
                        if event.key == pygame.K_UP:
                            self.direction = "UP"
                        elif event.key == pygame.K_DOWN:
                            self.direction = "DOWN"
                        elif event.key == pygame.K_LEFT:
                            self.direction = "LEFT"
                        elif event.key == pygame.K_RIGHT:
                            self.direction = "RIGHT"

            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()


async def main():
    game = Game2048()
    await game.run()


main()
