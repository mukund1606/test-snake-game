from pygame import (
    sprite,
    transform,
    time,
    Surface,
    font,
    display,
    image,
    event,
    init,
    key,
    K_RIGHT,
    K_LEFT,
    KEYUP,
    KEYDOWN,
    K_ESCAPE,
    K_SPACE,
    QUIT,
)
import sys
from random import choice
import asyncio

FONT_PATH = "fonts/"
IMAGE_PATH = "images/"
SOUND_PATH = "sounds/"
SOUND_FORMAT = "ogg"

# Dynamically calculate based on canvas size
speed = pyodide.globals.get("speed")
canvas = pyodide.globals.get("canvas")
width, height = canvas.width, canvas.height
min_val = min(width, height)

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)

###############################################################################
# SCALING LOGIC
###############################################################################
# Original design was 800 wide x 600 high.
# Now we treat width=800 as the reference dimension for scaling.
SCALE = min_val / 800.0

SCREEN_WIDTH = int(800 * SCALE)
SCREEN_HEIGHT = int(600 * SCALE)
SCREEN = display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

FONT = FONT_PATH + "space_invaders.ttf"

IMG_NAMES = [
    "ship",
    "mystery",
    "enemy1_1",
    "enemy1_2",
    "enemy2_1",
    "enemy2_2",
    "enemy3_1",
    "enemy3_2",
    "explosionblue",
    "explosiongreen",
    "explosionpurple",
    "laser",
    "enemylaser",
]

IMAGES = {
    name: image.load(IMAGE_PATH + "{}.png".format(name)).convert_alpha()
    for name in IMG_NAMES
}

# The following were originally at 450, 65, 35, etc. Now scaled:
BLOCKERS_POSITION = int(450 * SCALE)
ENEMY_DEFAULT_POSITION = int(65 * SCALE)  # initial y-offset
ENEMY_MOVE_DOWN = int(35 * SCALE)
DIFFICULTY_LEVEL = 5

###############################################################################
# Classes
###############################################################################


class Ship(sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = IMAGES["ship"]

        w, h = self.original_image.get_size()
        scaled_w = int(w * SCALE)
        scaled_h = int(h * SCALE)
        self.image = transform.scale(self.original_image, (scaled_w, scaled_h))
        self.rect = self.image.get_rect(topleft=(int(375 * SCALE), int(540 * SCALE)))
        self.speed = int(5 * SCALE)

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed

        game.screen.blit(self.image, self.rect)


class Bullet(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side):
        super().__init__()
        # Load the bullet image
        bullet_img = IMAGES[filename]

        # Scale the bullet image according to SCALE
        w, h = bullet_img.get_size()
        scaled_w = int(w * SCALE)
        scaled_h = int(h * SCALE)
        self.image = transform.scale(bullet_img, (scaled_w, scaled_h))

        # Position the bullet
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

        # Scale the bullet's speed
        self.speed = int(speed * SCALE)

        self.direction = direction
        self.side = side
        self.filename = filename

    def update(self, keys, *args):
        # Move the bullet
        self.rect.y += self.speed * self.direction

        # Draw the bullet
        game.screen.blit(self.image, self.rect)

        # If it goes off-screen, remove it
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Enemy(sprite.Sprite):
    def __init__(self, row, column):
        super().__init__()
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    def load_images(self):
        # Map from row -> (enemyX_1, enemyX_2) image files
        images_map = {
            0: ["1_2", "1_1"],  # top row
            1: ["2_2", "2_1"],  # next
            2: ["2_2", "2_1"],
            3: ["3_1", "3_2"],
            4: ["3_1", "3_2"],
        }
        img1, img2 = (IMAGES[f"enemy{num}"] for num in images_map[self.row])
        # Original code scaled enemies to (40×35):
        w, h = 40, 35
        w_s, h_s = int(w * SCALE), int(h * SCALE)
        self.images.append(transform.scale(img1, (w_s, h_s)))
        self.images.append(transform.scale(img2, (w_s, h_s)))


class EnemiesGroup(sprite.Group):
    def __init__(self, columns, rows):
        super().__init__()
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 600  # ms between moves
        self.direction = 1
        # how many times the swarm moves horizontally before shifting down
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.timer = time.get_ticks()
        self.bottom = (
            game.enemyPosition + ((rows - 1) * int(45 * SCALE)) + int(35 * SCALE)
        )
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            if self.moveNumber >= max_move:
                # move down
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 + self.leftAddMove
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for enemy in self:
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()
                    if self.bottom < enemy.rect.y + int(35 * SCALE):
                        self.bottom = enemy.rect.y + int(35 * SCALE)
            else:
                velocity = int(10 * SCALE) if self.direction == 1 else -int(10 * SCALE)
                for enemy in self:
                    enemy.rect.x += velocity
                    enemy.toggle_image()
                self.moveNumber += 1

            self.timer += self.moveTime

    def add_internal(self, *sprites):
        super().add_internal(*sprites)
        for s in sprites:
            self.enemies[s.row][s.column] = s

    def remove_internal(self, *sprites):
        super().remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def is_column_dead(self, column):
        return not any(self.enemies[row][column] for row in range(self.rows))

    def random_bottom(self):
        col = choice(self._aliveColumns)
        # from the bottom row up
        col_enemies = (self.enemies[r - 1][col] for r in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def update_speed(self):
        """Speeds up if fewer enemies remain."""
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_dead = self.is_column_dead(enemy.column)
        if is_dead:
            self._aliveColumns.remove(enemy.column)

        if enemy.column == self._rightAliveColumn:
            while self._rightAliveColumn > 0 and is_dead:
                self._rightAliveColumn -= 1
                self.rightAddMove += 5
                is_dead = self.is_column_dead(self._rightAliveColumn)

        elif enemy.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_dead:
                self._leftAliveColumn += 1
                self.leftAddMove += 5
                is_dead = self.is_column_dead(self._leftAliveColumn)


class Blocker(sprite.Sprite):
    def __init__(self, size, color, row, column):
        super().__init__()
        scaled_size = int(size * SCALE)
        self.width = scaled_size
        self.height = scaled_size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)


class Mystery(sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = IMAGES["mystery"]
        # Original was (75, 35)
        w_s, h_s = int(75 * SCALE), int(35 * SCALE)
        self.image = transform.scale(self.image, (w_s, h_s))
        self.rect = self.image.get_rect(topleft=(int(-80 * SCALE), int(45 * SCALE)))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.playSound = True

    def update(self, keys, currentTime, *args):
        resetTimer = False
        passed = currentTime - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > SCREEN_WIDTH) and self.playSound:
                self.playSound = False
            speed_x = int(2 * SCALE)
            if self.direction == 1 and self.rect.x < SCREEN_WIDTH + int(40 * SCALE):
                self.rect.x += speed_x
                game.screen.blit(self.image, self.rect)
            elif self.direction == -1 and self.rect.x > int(-100 * SCALE):
                self.rect.x -= speed_x
                game.screen.blit(self.image, self.rect)

        if self.rect.x > SCREEN_WIDTH + int(30 * SCALE):
            self.playSound = True
            self.direction = -1
            resetTimer = True
        if self.rect.x < int(-90 * SCALE):
            self.playSound = True
            self.direction = 1
            resetTimer = True
        if passed > self.moveTime and resetTimer:
            self.timer = currentTime


class EnemyExplosion(sprite.Sprite):
    def __init__(self, enemy, *groups):
        super().__init__(*groups)
        # Original enemy explosion scale: (40×35), (50×45)
        self.image = transform.scale(
            self.get_image(enemy.row), (int(40 * SCALE), int(35 * SCALE))
        )
        self.image2 = transform.scale(
            self.get_image(enemy.row), (int(50 * SCALE), int(45 * SCALE))
        )
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = time.get_ticks()

    @staticmethod
    def get_image(row):
        # row 0=purple, 1=blue, 2=blue, 3=green, 4=green
        img_colors = ["purple", "blue", "blue", "green", "green"]
        return IMAGES["explosion{}".format(img_colors[row])]

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            game.screen.blit(
                self.image2,
                (self.rect.x - int(6 * SCALE), self.rect.y - int(6 * SCALE)),
            )
        elif passed > 400:
            self.kill()


class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, *groups):
        super().__init__(*groups)
        self.text = Text(
            FONT,
            int(20 * SCALE),
            str(score),
            WHITE,
            mystery.rect.x + int(20 * SCALE),
            mystery.rect.y + int(6 * SCALE),
        )
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or (400 < passed <= 600):
            self.text.draw(game.screen)
        elif passed > 600:
            self.kill()


class ShipExplosion(sprite.Sprite):
    def __init__(self, ship, *groups):
        super().__init__(*groups)
        self.image = IMAGES["ship"]
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            game.screen.blit(self.image, self.rect)
        elif passed > 900:
            self.kill()


class Life(sprite.Sprite):
    def __init__(self, xpos, ypos):
        super().__init__()
        self.image = IMAGES["ship"]
        # Original life icon scale to (23×23)
        self.image = transform.scale(self.image, (int(23 * SCALE), int(23 * SCALE)))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))

    def update(self, *args):
        game.screen.blit(self.image, self.rect)


class Text:
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)


class SpaceInvaders:
    def __init__(self):
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption("Space Invaders")
        self.screen = SCREEN
        self.background = image.load(IMAGE_PATH + "background.jpg").convert()
        # Optionally scale background:
        # self.background = transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        # enemy starting position offset
        self.enemyPosition = ENEMY_DEFAULT_POSITION

        self.titleText = Text(
            FONT,
            int(50 * SCALE),
            "Space Invaders",
            WHITE,
            int(164 * SCALE),
            int(120 * SCALE),
        )
        self.titleText2 = Text(
            FONT,
            int(25 * SCALE),
            "Press any key to continue",
            WHITE,
            int(201 * SCALE),
            int(205 * SCALE),
        )
        self.gameOverText = Text(
            FONT,
            int(50 * SCALE),
            "Game Over",
            WHITE,
            int(250 * SCALE),
            int(270 * SCALE),
        )
        self.nextRoundText = Text(
            FONT,
            int(50 * SCALE),
            "Next Round",
            WHITE,
            int(240 * SCALE),
            int(270 * SCALE),
        )
        self.enemy1Text = Text(
            FONT,
            int(25 * SCALE),
            "   =   10 pts",
            GREEN,
            int(368 * SCALE),
            int(270 * SCALE),
        )
        self.enemy2Text = Text(
            FONT,
            int(25 * SCALE),
            "   =  20 pts",
            BLUE,
            int(368 * SCALE),
            int(320 * SCALE),
        )
        self.enemy3Text = Text(
            FONT,
            int(25 * SCALE),
            "   =  30 pts",
            PURPLE,
            int(368 * SCALE),
            int(370 * SCALE),
        )
        self.enemy4Text = Text(
            FONT,
            int(25 * SCALE),
            "   =  ?????",
            RED,
            int(368 * SCALE),
            int(420 * SCALE),
        )
        self.scoreText = Text(
            FONT, int(20 * SCALE), "Score", WHITE, int(5 * SCALE), int(5 * SCALE)
        )
        self.livesText = Text(
            FONT, int(20 * SCALE), "Lives ", WHITE, int(640 * SCALE), int(5 * SCALE)
        )

        self.life1 = Life(int(715 * SCALE), int(3 * SCALE))
        self.life2 = Life(int(742 * SCALE), int(3 * SCALE))
        self.life3 = Life(int(769 * SCALE), int(3 * SCALE))
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)

    def reset(self, score):
        self.player = Ship()
        self.playerGroup = sprite.Group(self.player)
        self.explosionsGroup = sprite.Group()
        self.bullets = sprite.Group()
        self.mysteryShip = Mystery()
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.enemyBullets = sprite.Group()
        self.make_enemies()

        # Combine everything into allSprites for easy updates
        self.allSprites = sprite.Group(
            self.player, self.enemies, self.livesGroup, self.mysteryShip
        )
        self.keys = key.get_pressed()

        self.timer = time.get_ticks()
        self.noteTimer = time.get_ticks()
        self.shipTimer = time.get_ticks()
        self.score = score

        self.makeNewShip = False
        self.shipAlive = True

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(4):
            for col in range(9):
                blocker = Blocker(10, GREEN, row, col)
                # Original x offset 50 + 200 per block row
                # so: 50 + 200 * number + (col * size)
                # y was ~450. Now we scale all of these.
                blocker.rect.x = (
                    int(50 * SCALE) + int(200 * SCALE) * number + col * blocker.width
                )
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

    def should_exit(self, evt):
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if len(self.bullets) == 0 and self.shipAlive:
                        # Original bullet creation with different power-ups:
                        if self.score <= 100:
                            bullet = Bullet(
                                self.player.rect.x + int(23 * SCALE),
                                self.player.rect.y + int(5 * SCALE),
                                -1,
                                15,
                                "laser",
                                "center",
                            )
                            self.bullets.add(bullet)
                            self.allSprites.add(self.bullets)
                        elif 100 < self.score <= 200:
                            leftbullet = Bullet(
                                self.player.rect.x + int(8 * SCALE),
                                self.player.rect.y + int(5 * SCALE),
                                -1,
                                15,
                                "laser",
                                "left",
                            )
                            right_bullet = Bullet(
                                self.player.rect.x + int(38 * SCALE),
                                self.player.rect.y + int(5 * SCALE),
                                -1,
                                15,
                                "laser",
                                "right",
                            )
                            self.bullets.add(leftbullet)
                            self.bullets.add(right_bullet)
                            self.allSprites.add(self.bullets)
                        else:
                            left_bullet = Bullet(
                                self.player.rect.x + int(8 * SCALE),
                                self.player.rect.y + int(5 * SCALE),
                                -1,
                                15,
                                "laser",
                                "left",
                            )
                            right_bullet = Bullet(
                                self.player.rect.x + int(38 * SCALE),
                                self.player.rect.y + int(5 * SCALE),
                                -1,
                                15,
                                "laser",
                                "right",
                            )
                            center_bullet = Bullet(
                                self.player.rect.x + int(23 * SCALE),
                                self.player.rect.y + int(5 * SCALE),
                                -1,
                                15,
                                "laser",
                                "center",
                            )
                            self.bullets.add(left_bullet)
                            self.bullets.add(center_bullet)
                            self.bullets.add(right_bullet)
                            self.allSprites.add(self.bullets)

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5)  # 10 cols, 5 rows
        for row in range(5):
            for col in range(10):
                enemy = Enemy(row, col)
                # Original offset: x=157 + col*50, y=(row*45) + enemyPosition
                enemy.rect.x = int(157 * SCALE) + col * int(50 * SCALE)
                enemy.rect.y = self.enemyPosition + row * int(45 * SCALE)
                enemies.add(enemy)
        self.enemies = enemies

    def make_enemies_shoot(self):
        # Basic timer-based shooting logic
        if (time.get_ticks() - self.timer) > 700 and self.enemies:
            enemy = self.enemies.random_bottom()
            if enemy:
                bullet = Bullet(
                    enemy.rect.x + int(14 * SCALE),
                    enemy.rect.y + int(20 * SCALE),
                    1,
                    5,
                    "enemylaser",
                    "center",
                )
                self.enemyBullets.add(bullet)
                self.allSprites.add(self.enemyBullets)
            self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores_map = {
            0: 30,
            1: 20,
            2: 20,
            3: 10,
            4: 10,
            5: choice([50, 100, 150, 300]),
        }
        score_gained = scores_map[row]
        self.score += score_gained
        pyodide.globals.get("setScore")(self.score)
        return score_gained

    def create_main_menu(self):
        # Show scaled enemies
        enemy1 = transform.scale(IMAGES["enemy3_1"], (int(40 * SCALE), int(40 * SCALE)))
        enemy2 = transform.scale(IMAGES["enemy2_2"], (int(40 * SCALE), int(40 * SCALE)))
        enemy3 = transform.scale(IMAGES["enemy1_2"], (int(40 * SCALE), int(40 * SCALE)))
        enemy4 = transform.scale(IMAGES["mystery"], (int(80 * SCALE), int(40 * SCALE)))

        self.screen.blit(enemy1, (int(318 * SCALE), int(270 * SCALE)))
        self.screen.blit(enemy2, (int(318 * SCALE), int(320 * SCALE)))
        self.screen.blit(enemy3, (int(318 * SCALE), int(370 * SCALE)))
        self.screen.blit(enemy4, (int(299 * SCALE), int(420 * SCALE)))

    def check_collisions(self):
        # Player bullet vs. enemy bullet
        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)

        # Player bullet hits enemies
        for enemy in sprite.groupcollide(self.enemies, self.bullets, True, True).keys():
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self.explosionsGroup)
            self.gameTimer = time.get_ticks()

        # Player bullet hits mystery
        for mystery in sprite.groupcollide(
            self.mysteryGroup, self.bullets, True, True
        ).keys():
            score = self.calculate_score(mystery.row)
            MysteryExplosion(mystery, score, self.explosionsGroup)
            new_mystery = Mystery()
            self.allSprites.add(new_mystery)
            self.mysteryGroup.add(new_mystery)

        # Enemy bullet hits player
        for player in sprite.groupcollide(
            self.playerGroup, self.enemyBullets, True, True
        ).keys():
            # remove a life
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                pyodide.globals.get("setIsGameEnded")(True)
                self.startGame = False

            ShipExplosion(player, self.explosionsGroup)
            self.makeNewShip = True
            self.shipTimer = time.get_ticks()
            self.shipAlive = False

        # Enemies reaching bottom
        if self.enemies.bottom >= int(540 * SCALE):
            sprite.groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= SCREEN_HEIGHT:
                self.gameOver = True
                pyodide.globals.get("setIsGameEnded")(True)
                self.startGame = False

        # Collisions with blockers
        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        if self.enemies.bottom >= BLOCKERS_POSITION:
            sprite.groupcollide(self.enemies, self.allBlockers, False, True)

    def create_new_ship(self, createShip, currentTime):
        if createShip and (currentTime - self.shipTimer > 900):
            self.player = Ship()
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewShip = False
            self.shipAlive = True

    def create_game_over(self, currentTime):
        self.screen.blit(self.background, (0, 0))
        self.gameOverText.draw(self.screen)

        refreshText = Text(
            FONT,
            int(25 * SCALE),
            "Refresh to play again",
            WHITE,
            int(220 * SCALE),
            int(350 * SCALE),
        )
        refreshText.draw(self.screen)

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    async def main(self):
        while True:
            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.titleText.draw(self.screen)
                self.titleText2.draw(self.screen)
                self.enemy1Text.draw(self.screen)
                self.enemy2Text.draw(self.screen)
                self.enemy3Text.draw(self.screen)
                self.enemy4Text.draw(self.screen)
                self.create_main_menu()

                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    if e.type == KEYUP:
                        # Create blockers for a new game
                        self.allBlockers = sprite.Group(
                            self.make_blockers(0),
                            self.make_blockers(1),
                            self.make_blockers(2),
                            self.make_blockers(3),
                        )
                        self.livesGroup.add(self.life1, self.life2, self.life3)
                        self.reset(0)
                        self.startGame = True
                        self.mainScreen = False

            elif self.startGame:
                # If all enemies are gone and no explosions in progress, new round
                if not self.enemies and not self.explosionsGroup:
                    currentTime = time.get_ticks()
                    if currentTime - self.gameTimer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.scoreText2 = Text(
                            FONT,
                            int(20 * SCALE),
                            str(self.score),
                            GREEN,
                            int(85 * SCALE),
                            int(5 * SCALE),
                        )
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        self.nextRoundText.draw(self.screen)
                        self.livesText.draw(self.screen)
                        self.livesGroup.update()
                        self.check_input()
                    if currentTime - self.gameTimer > 3000:
                        self.enemyPosition += ENEMY_MOVE_DOWN
                        self.reset(self.score)
                        self.gameTimer += 3000
                else:
                    currentTime = time.get_ticks()
                    self.screen.blit(self.background, (0, 0))
                    self.allBlockers.update(self.screen)

                    self.scoreText2 = Text(
                        FONT,
                        int(20 * SCALE),
                        str(self.score),
                        GREEN,
                        int(85 * SCALE),
                        int(5 * SCALE),
                    )
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.livesText.draw(self.screen)

                    self.check_input()
                    self.enemies.update(currentTime)
                    self.allSprites.update(self.keys, currentTime)
                    self.explosionsGroup.update(currentTime)
                    self.check_collisions()
                    self.create_new_ship(self.makeNewShip, currentTime)
                    self.make_enemies_shoot()

            elif self.gameOver:
                currentTime = time.get_ticks()
                self.create_game_over(currentTime)

            display.update()
            # Use user-defined fps
            self.clock.tick(speed)
            await asyncio.sleep(0)


game = SpaceInvaders()
game.main()
