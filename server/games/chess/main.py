import pygame
import asyncio


class ChessGame:
    def __init__(self):
        # --------------------------------------------------
        # SCALING LOGIC (like in the Space Invaders example)
        # --------------------------------------------------
        self.speed = pyodide.globals.get("speed")  # FPS from Pyodide
        canvas = pyodide.globals.get("canvas")
        width, height = canvas.width, canvas.height
        min_val = min(width, height)

        # Base reference: 800 wide
        # Our "native" game is 1000×900, so we scale from 800 (to keep aspect ratio).
        self.SCALE = min_val / 1000.0

        # Scale the window
        self.SCREEN_WIDTH = int(1000 * self.SCALE)
        self.SCREEN_HEIGHT = int(900 * self.SCALE)

        # Each square was 100×100 in the original code
        self.SQUARE_SIZE = int(100 * self.SCALE)

        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Two-Player Pygame Chess!")

        # Fonts, Clock
        # We'll also scale fonts so they look correct on smaller/larger screens
        font_size_small = int(20 * self.SCALE)
        font_size_medium = int(40 * self.SCALE)
        font_size_big = int(50 * self.SCALE)
        self.font = pygame.font.Font("freesansbold.ttf", font_size_small)
        self.medium_font = pygame.font.Font("freesansbold.ttf", font_size_medium)
        self.big_font = pygame.font.Font("freesansbold.ttf", font_size_big)

        self.timer = pygame.time.Clock()

        # Board/piece definitions
        self.white_pieces = [
            "rook",
            "knight",
            "bishop",
            "king",
            "queen",
            "bishop",
            "knight",
            "rook",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
        ]
        self.white_locations = [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0),
            (5, 0),
            (6, 0),
            (7, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
        ]
        self.black_pieces = [
            "rook",
            "knight",
            "bishop",
            "king",
            "queen",
            "bishop",
            "knight",
            "rook",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
        ]
        self.black_locations = [
            (0, 7),
            (1, 7),
            (2, 7),
            (3, 7),
            (4, 7),
            (5, 7),
            (6, 7),
            (7, 7),
            (0, 6),
            (1, 6),
            (2, 6),
            (3, 6),
            (4, 6),
            (5, 6),
            (6, 6),
            (7, 6),
        ]
        self.captured_pieces_white = []
        self.captured_pieces_black = []

        # Turn states
        self.turn_step = 0
        self.selection = 100
        self.valid_moves = []

        self.black_options = []
        self.white_options = []
        self.counter = 0
        self.winner = ""
        self.game_over = False

        # Load images
        self.load_images()

        # Pre-compute piece move options
        self.black_options = self.check_options(
            self.black_pieces, self.black_locations, "black"
        )
        self.white_options = self.check_options(
            self.white_pieces, self.white_locations, "white"
        )

    def load_images(self):
        """Load and scale piece images for both sides."""
        # Use the same filenames as your original code, but scale them.
        # We'll define a helper to load & scale each piece:

        def load_and_scale(path, w, h):
            img = pygame.image.load(path).convert_alpha()
            # Scale w×h by self.SCALE
            scaled_w = int(w * self.SCALE)
            scaled_h = int(h * self.SCALE)
            return pygame.transform.scale(img, (scaled_w, scaled_h))

        # black queen: originally (80, 80)
        self.black_queen = load_and_scale("assets/images/black queen.png", 80, 80)
        self.black_queen_small = load_and_scale("assets/images/black queen.png", 45, 45)

        self.black_king = load_and_scale("assets/images/black king.png", 80, 80)
        self.black_king_small = load_and_scale("assets/images/black king.png", 45, 45)

        self.black_rook = load_and_scale("assets/images/black rook.png", 80, 80)
        self.black_rook_small = load_and_scale("assets/images/black rook.png", 45, 45)

        self.black_bishop = load_and_scale("assets/images/black bishop.png", 80, 80)
        self.black_bishop_small = load_and_scale(
            "assets/images/black bishop.png", 45, 45
        )

        self.black_knight = load_and_scale("assets/images/black knight.png", 80, 80)
        self.black_knight_small = load_and_scale(
            "assets/images/black knight.png", 45, 45
        )

        self.black_pawn = load_and_scale("assets/images/black pawn.png", 65, 65)
        self.black_pawn_small = load_and_scale("assets/images/black pawn.png", 45, 45)

        # white versions
        self.white_queen = load_and_scale("assets/images/white queen.png", 80, 80)
        self.white_queen_small = load_and_scale("assets/images/white queen.png", 45, 45)

        self.white_king = load_and_scale("assets/images/white king.png", 80, 80)
        self.white_king_small = load_and_scale("assets/images/white king.png", 45, 45)

        self.white_rook = load_and_scale("assets/images/white rook.png", 80, 80)
        self.white_rook_small = load_and_scale("assets/images/white rook.png", 45, 45)

        self.white_bishop = load_and_scale("assets/images/white bishop.png", 80, 80)
        self.white_bishop_small = load_and_scale(
            "assets/images/white bishop.png", 45, 45
        )

        self.white_knight = load_and_scale("assets/images/white knight.png", 80, 80)
        self.white_knight_small = load_and_scale(
            "assets/images/white knight.png", 45, 45
        )

        self.white_pawn = load_and_scale("assets/images/white pawn.png", 65, 65)
        self.white_pawn_small = load_and_scale("assets/images/white pawn.png", 45, 45)

        self.white_images = [
            self.white_pawn,
            self.white_queen,
            self.white_king,
            self.white_knight,
            self.white_rook,
            self.white_bishop,
        ]
        self.small_white_images = [
            self.white_pawn_small,
            self.white_queen_small,
            self.white_king_small,
            self.white_knight_small,
            self.white_rook_small,
            self.white_bishop_small,
        ]
        self.black_images = [
            self.black_pawn,
            self.black_queen,
            self.black_king,
            self.black_knight,
            self.black_rook,
            self.black_bishop,
        ]
        self.small_black_images = [
            self.black_pawn_small,
            self.black_queen_small,
            self.black_king_small,
            self.black_knight_small,
            self.black_rook_small,
            self.black_bishop_small,
        ]

        # Must match this order in piece_list:
        self.piece_list = ["pawn", "queen", "king", "knight", "rook", "bishop"]

    def new_game(self):
        """Reset everything for a new game."""
        self.game_over = False
        self.winner = ""
        self.white_pieces = [
            "rook",
            "knight",
            "bishop",
            "king",
            "queen",
            "bishop",
            "knight",
            "rook",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
        ]
        self.white_locations = [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0),
            (5, 0),
            (6, 0),
            (7, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
            (5, 1),
            (6, 1),
            (7, 1),
        ]
        self.black_pieces = [
            "rook",
            "knight",
            "bishop",
            "king",
            "queen",
            "bishop",
            "knight",
            "rook",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
            "pawn",
        ]
        self.black_locations = [
            (0, 7),
            (1, 7),
            (2, 7),
            (3, 7),
            (4, 7),
            (5, 7),
            (6, 7),
            (7, 7),
            (0, 6),
            (1, 6),
            (2, 6),
            (3, 6),
            (4, 6),
            (5, 6),
            (6, 6),
            (7, 6),
        ]
        self.captured_pieces_white = []
        self.captured_pieces_black = []
        self.turn_step = 0
        self.selection = 100
        self.valid_moves = []

        self.black_options = self.check_options(
            self.black_pieces, self.black_locations, "black"
        )
        self.white_options = self.check_options(
            self.white_pieces, self.white_locations, "white"
        )

    def draw_board(self):
        """Draw scaled board & lines."""
        # We have 8 rows of squares (0..7). But your code drew 32 squares in a pattern.
        # We'll replicate that logic, but scaled by self.SQUARE_SIZE.

        # Each "row" is 100 px tall => self.SQUARE_SIZE tall
        # Each "column" is 100 px wide => self.SQUARE_SIZE wide
        for i in range(32):
            column = i % 4
            row = i // 4
            # The x,y for each "light gray" square depends on the row/column pattern
            # Original used 600, 700 offsets. We'll scale them:
            # left_x = 600 - (column*200) => int(600*self.SCALE) - (column * 2*SQUARE_SIZE)
            left_x = int(6 * self.SQUARE_SIZE) - (column * 2 * self.SQUARE_SIZE)
            top_y = row * self.SQUARE_SIZE

            pygame.draw.rect(
                self.screen,
                "light gray",
                [left_x, top_y, self.SQUARE_SIZE, self.SQUARE_SIZE],
            )

        # Bottom bar
        pygame.draw.rect(
            self.screen,
            "gray",
            [
                0,
                int(8 * self.SQUARE_SIZE),
                self.SCREEN_WIDTH,
                self.SCREEN_HEIGHT - int(8 * self.SQUARE_SIZE),
            ],
        )
        pygame.draw.rect(
            self.screen,
            "gold",
            [
                0,
                int(8 * self.SQUARE_SIZE),
                self.SCREEN_WIDTH,
                self.SCREEN_HEIGHT - int(8 * self.SQUARE_SIZE),
            ],
            5,
        )

        # Right bar
        pygame.draw.rect(
            self.screen,
            "gold",
            [
                int(8 * self.SQUARE_SIZE),
                0,
                self.SCREEN_WIDTH - int(8 * self.SQUARE_SIZE),
                self.SCREEN_HEIGHT,
            ],
            5,
        )

        status_text = [
            "White: Select a Piece to Move!",
            "White: Select a Destination!",
            "Black: Select a Piece to Move!",
            "Black: Select a Destination!",
        ]
        self.screen.blit(
            self.big_font.render(status_text[self.turn_step], True, "black"),
            (int(20 * self.SCALE), int(820 * self.SCALE)),
        )

        # Lines across the board
        for i in range(9):
            # horizontal lines
            pygame.draw.line(
                self.screen,
                "black",
                (0, i * self.SQUARE_SIZE),
                (8 * self.SQUARE_SIZE, i * self.SQUARE_SIZE),
                2,
            )
            # vertical lines
            pygame.draw.line(
                self.screen,
                "black",
                (i * self.SQUARE_SIZE, 0),
                (i * self.SQUARE_SIZE, 8 * self.SQUARE_SIZE),
                2,
            )

        # "FORFEIT" text (like button) at scaled location
        self.screen.blit(
            self.medium_font.render("FORFEIT", True, "black"),
            (int(810 * self.SCALE), int(830 * self.SCALE)),
        )

    def draw_pieces(self):
        """Draw all white & black pieces with scaled positions."""
        for i, piece_type in enumerate(self.white_pieces):
            loc = self.white_locations[i]
            index = self.piece_list.index(piece_type)

            # If it's a pawn, offset is different
            if piece_type == "pawn":
                # e.g. was loc[0]*100 + 22 => loc[0]*self.SQUARE_SIZE + int(22*self.SCALE)
                x_offset = int(22 * self.SCALE)
                y_offset = int(30 * self.SCALE)
                self.screen.blit(
                    self.white_pawn,
                    (
                        loc[0] * self.SQUARE_SIZE + x_offset,
                        loc[1] * self.SQUARE_SIZE + y_offset,
                    ),
                )
            else:
                x_offset = int(10 * self.SCALE)
                y_offset = int(10 * self.SCALE)
                self.screen.blit(
                    self.white_images[index],
                    (
                        loc[0] * self.SQUARE_SIZE + x_offset,
                        loc[1] * self.SQUARE_SIZE + y_offset,
                    ),
                )

            # highlight
            if self.turn_step < 2 and self.selection == i:
                pygame.draw.rect(
                    self.screen,
                    "red",
                    [
                        loc[0] * self.SQUARE_SIZE + 1,
                        loc[1] * self.SQUARE_SIZE + 1,
                        self.SQUARE_SIZE,
                        self.SQUARE_SIZE,
                    ],
                    2,
                )

        for i, piece_type in enumerate(self.black_pieces):
            loc = self.black_locations[i]
            index = self.piece_list.index(piece_type)

            if piece_type == "pawn":
                x_offset = int(22 * self.SCALE)
                y_offset = int(30 * self.SCALE)
                self.screen.blit(
                    self.black_pawn,
                    (
                        loc[0] * self.SQUARE_SIZE + x_offset,
                        loc[1] * self.SQUARE_SIZE + y_offset,
                    ),
                )
            else:
                x_offset = int(10 * self.SCALE)
                y_offset = int(10 * self.SCALE)
                self.screen.blit(
                    self.black_images[index],
                    (
                        loc[0] * self.SQUARE_SIZE + x_offset,
                        loc[1] * self.SQUARE_SIZE + y_offset,
                    ),
                )

            # highlight
            if self.turn_step >= 2 and self.selection == i:
                pygame.draw.rect(
                    self.screen,
                    "blue",
                    [
                        loc[0] * self.SQUARE_SIZE + 1,
                        loc[1] * self.SQUARE_SIZE + 1,
                        self.SQUARE_SIZE,
                        self.SQUARE_SIZE,
                    ],
                    2,
                )

    def draw_captured(self):
        """Draw small icons for captured pieces at the right side."""
        # White’s captures (i.e. black pieces captured by white)
        for i, captured_piece in enumerate(self.captured_pieces_white):
            index = self.piece_list.index(captured_piece)
            # e.g. (825, 5 + 50*i) => scale them
            x = int(825 * self.SCALE)
            y = int(5 * self.SCALE) + int(50 * self.SCALE) * i
            self.screen.blit(self.small_black_images[index], (x, y))

        # Black’s captures (i.e. white pieces captured by black)
        for i, captured_piece in enumerate(self.captured_pieces_black):
            index = self.piece_list.index(captured_piece)
            x = int(925 * self.SCALE)
            y = int(5 * self.SCALE) + int(50 * self.SCALE) * i
            self.screen.blit(self.small_white_images[index], (x, y))

    def draw_check(self):
        """Flash the king's square if in check."""
        if self.turn_step < 2:
            # white's turn
            if "king" in self.white_pieces:
                king_idx = self.white_pieces.index("king")
                king_loc = self.white_locations[king_idx]
                for moves in self.black_options:
                    if king_loc in moves:
                        if self.counter < 15:  # flash half the time
                            pygame.draw.rect(
                                self.screen,
                                "dark red",
                                [
                                    king_loc[0] * self.SQUARE_SIZE + 1,
                                    king_loc[1] * self.SQUARE_SIZE + 1,
                                    self.SQUARE_SIZE,
                                    self.SQUARE_SIZE,
                                ],
                                5,
                            )
        else:
            # black's turn
            if "king" in self.black_pieces:
                king_idx = self.black_pieces.index("king")
                king_loc = self.black_locations[king_idx]
                for moves in self.white_options:
                    if king_loc in moves:
                        if self.counter < 15:
                            pygame.draw.rect(
                                self.screen,
                                "dark blue",
                                [
                                    king_loc[0] * self.SQUARE_SIZE + 1,
                                    king_loc[1] * self.SQUARE_SIZE + 1,
                                    self.SQUARE_SIZE,
                                    self.SQUARE_SIZE,
                                ],
                                5,
                            )

    def draw_valid(self, moves):
        """Draw small circles for valid moves."""
        color = "red" if self.turn_step < 2 else "blue"
        for mx, my in moves:
            center_x = mx * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            center_y = my * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
            pygame.draw.circle(self.screen, color, (center_x, center_y), 5)

    def draw_game_over(self):
        """Show the final message (scaled) with 'Refresh to play again'."""
        rect_x = int(200 * self.SCALE)
        rect_y = int(200 * self.SCALE)
        rect_w = int(400 * self.SCALE)
        rect_h = int(70 * self.SCALE)

        pygame.draw.rect(self.screen, "black", [rect_x, rect_y, rect_w, rect_h])
        self.screen.blit(
            self.font.render(f"{self.winner} won the game!", True, "white"),
            (rect_x + int(10 * self.SCALE), rect_y + int(10 * self.SCALE)),
        )
        self.screen.blit(
            self.font.render(f"Refresh to play again", True, "white"),
            (rect_x + int(10 * self.SCALE), rect_y + int(40 * self.SCALE)),
        )

    def check_valid_moves(self):
        """Check valid moves for the currently selected piece only."""
        if self.turn_step < 2:
            return self.white_options[self.selection]
        else:
            return self.black_options[self.selection]

    # ------ Piece-based logic ------
    def check_options(self, pieces, locations, turn_color):
        all_moves = []
        for i, piece in enumerate(pieces):
            loc = locations[i]
            if piece == "pawn":
                moves = self.check_pawn(loc, turn_color)
            elif piece == "rook":
                moves = self.check_rook(loc, turn_color)
            elif piece == "knight":
                moves = self.check_knight(loc, turn_color)
            elif piece == "bishop":
                moves = self.check_bishop(loc, turn_color)
            elif piece == "queen":
                moves = self.check_queen(loc, turn_color)
            elif piece == "king":
                moves = self.check_king(loc, turn_color)
            else:
                moves = []
            all_moves.append(moves)
        return all_moves

    def check_king(self, position, color):
        moves_list = []
        if color == "white":
            enemies_list = self.black_locations
            friends_list = self.white_locations
        else:
            enemies_list = self.white_locations
            friends_list = self.black_locations

        offsets = [(1, 0), (1, 1), (1, -1), (-1, 0), (-1, 1), (-1, -1), (0, 1), (0, -1)]
        for dx, dy in offsets:
            tx, ty = position[0] + dx, position[1] + dy
            if (tx, ty) not in friends_list and 0 <= tx <= 7 and 0 <= ty <= 7:
                moves_list.append((tx, ty))
        return moves_list

    def check_queen(self, pos, color):
        return self.check_bishop(pos, color) + self.check_rook(pos, color)

    def check_bishop(self, position, color):
        moves_list = []
        if color == "white":
            enemies_list = self.black_locations
            friends_list = self.white_locations
        else:
            enemies_list = self.white_locations
            friends_list = self.black_locations

        directions = [(1, -1), (-1, -1), (1, 1), (-1, 1)]
        for dx, dy in directions:
            chain = 1
            path_open = True
            while path_open:
                tx = position[0] + chain * dx
                ty = position[1] + chain * dy
                if (tx, ty) not in friends_list and 0 <= tx <= 7 and 0 <= ty <= 7:
                    moves_list.append((tx, ty))
                    if (tx, ty) in enemies_list:
                        path_open = False
                    chain += 1
                else:
                    path_open = False
        return moves_list

    def check_rook(self, position, color):
        moves_list = []
        if color == "white":
            enemies_list = self.black_locations
            friends_list = self.white_locations
        else:
            enemies_list = self.white_locations
            friends_list = self.black_locations

        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            chain = 1
            path_open = True
            while path_open:
                tx = position[0] + chain * dx
                ty = position[1] + chain * dy
                if (tx, ty) not in friends_list and 0 <= tx <= 7 and 0 <= ty <= 7:
                    moves_list.append((tx, ty))
                    if (tx, ty) in enemies_list:
                        path_open = False
                    chain += 1
                else:
                    path_open = False
        return moves_list

    def check_pawn(self, position, color):
        moves_list = []
        if color == "white":
            # forward
            if (
                (position[0], position[1] + 1) not in self.white_locations
                and (position[0], position[1] + 1) not in self.black_locations
                and position[1] < 7
            ):
                moves_list.append((position[0], position[1] + 1))
            if (
                (position[0], position[1] + 2) not in self.white_locations
                and (position[0], position[1] + 2) not in self.black_locations
                and position[1] == 1
            ):
                moves_list.append((position[0], position[1] + 2))
            # captures
            if (position[0] + 1, position[1] + 1) in self.black_locations:
                moves_list.append((position[0] + 1, position[1] + 1))
            if (position[0] - 1, position[1] + 1) in self.black_locations:
                moves_list.append((position[0] - 1, position[1] + 1))
        else:
            # forward
            if (
                (position[0], position[1] - 1) not in self.white_locations
                and (position[0], position[1] - 1) not in self.black_locations
                and position[1] > 0
            ):
                moves_list.append((position[0], position[1] - 1))
            if (
                (position[0], position[1] - 2) not in self.white_locations
                and (position[0], position[1] - 2) not in self.black_locations
                and position[1] == 6
            ):
                moves_list.append((position[0], position[1] - 2))
            # captures
            if (position[0] + 1, position[1] - 1) in self.white_locations:
                moves_list.append((position[0] + 1, position[1] - 1))
            if (position[0] - 1, position[1] - 1) in self.white_locations:
                moves_list.append((position[0] - 1, position[1] - 1))
        return moves_list

    def check_knight(self, position, color):
        moves_list = []
        if color == "white":
            enemies_list = self.black_locations
            friends_list = self.white_locations
        else:
            enemies_list = self.white_locations
            friends_list = self.black_locations

        offsets = [
            (1, 2),
            (1, -2),
            (2, 1),
            (2, -1),
            (-1, 2),
            (-1, -2),
            (-2, 1),
            (-2, -1),
        ]
        for dx, dy in offsets:
            tx = position[0] + dx
            ty = position[1] + dy
            if (tx, ty) not in friends_list and 0 <= tx <= 7 and 0 <= ty <= 7:
                moves_list.append((tx, ty))
        return moves_list

    # ---------- MAIN LOOP ----------
    async def run(self):
        """Run the main game loop asynchronously."""
        self.run_game = True
        while self.run_game:
            self.timer.tick(self.speed)  # use speed from Pyodide
            # Flash logic
            self.counter = (self.counter + 1) % 30

            self.screen.fill("dark gray")
            self.draw_board()
            self.draw_pieces()
            self.draw_captured()
            self.draw_check()

            if self.selection != 100:
                self.valid_moves = self.check_valid_moves()
                self.draw_valid(self.valid_moves)

            # ----- EVENT HANDLING -----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run_game = False
                if (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and not self.game_over
                ):
                    self.handle_mouse_click(event)

            # If we have a winner
            if self.winner != "":
                self.game_over = True
                self.draw_game_over()

            pygame.display.flip()
            await asyncio.sleep(0)

        pygame.quit()

    def handle_mouse_click(self, event):
        x_coord = event.pos[0] // self.SQUARE_SIZE
        y_coord = event.pos[1] // self.SQUARE_SIZE
        click_coords = (x_coord, y_coord)

        # White's turn
        if self.turn_step <= 1:
            # Forfeit check
            # originally (8,8) or (9,8) => we have 8 squares across
            if click_coords in [(8, 8), (9, 8)]:
                self.winner = "black"
                return

            if click_coords in self.white_locations:
                self.selection = self.white_locations.index(click_coords)
                if self.turn_step == 0:
                    self.turn_step = 1

            if click_coords in self.valid_moves and self.selection != 100:
                self.white_locations[self.selection] = click_coords
                if click_coords in self.black_locations:
                    black_idx = self.black_locations.index(click_coords)
                    self.captured_pieces_white.append(self.black_pieces[black_idx])
                    if self.black_pieces[black_idx] == "king":
                        self.winner = "white"
                    self.black_pieces.pop(black_idx)
                    self.black_locations.pop(black_idx)

                self.black_options = self.check_options(
                    self.black_pieces, self.black_locations, "black"
                )
                self.white_options = self.check_options(
                    self.white_pieces, self.white_locations, "white"
                )
                self.turn_step = 2
                self.selection = 100
                self.valid_moves = []

        # Black's turn
        else:
            if click_coords in [(8, 8), (9, 8)]:
                self.winner = "white"
                return

            if click_coords in self.black_locations:
                self.selection = self.black_locations.index(click_coords)
                if self.turn_step == 2:
                    self.turn_step = 3

            if click_coords in self.valid_moves and self.selection != 100:
                self.black_locations[self.selection] = click_coords
                if click_coords in self.white_locations:
                    white_idx = self.white_locations.index(click_coords)
                    self.captured_pieces_black.append(self.white_pieces[white_idx])
                    if self.white_pieces[white_idx] == "king":
                        self.winner = "black"
                    self.white_pieces.pop(white_idx)
                    self.white_locations.pop(white_idx)

                self.black_options = self.check_options(
                    self.black_pieces, self.black_locations, "black"
                )
                self.white_options = self.check_options(
                    self.white_pieces, self.white_locations, "white"
                )
                self.turn_step = 0
                self.selection = 100
                self.valid_moves = []


# ------------------ ASYNC MAIN FUNCTION ------------------
async def main():
    game = ChessGame()
    await game.run()


# In Pyodide, just calling main() will start the loop:
main()
