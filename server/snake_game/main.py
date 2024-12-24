import sys, random
import asyncio
from pygame.math import Vector2
import pygame

import asyncio

pygame.init()

# Dynamically calculate based on canvas size
fps = pyodide.globals.get("fps")
canvas = pyodide.globals.get("canvas")
width, height = canvas.width, canvas.height
min_val = min(width, height)

title_size = min_val // 15
score_size = round(min_val / 22.5)
title_font = pygame.font.Font("fonts/font.otf", title_size)
score_font = pygame.font.Font("fonts/font.otf", score_size)

GREEN = (173, 204, 96)
DARK_GREEN = (43, 51, 24)


cell_size = min_val // 30
number_of_cells = (min_val // cell_size) - 4
OFFSET = min_val // 15


class Food:
    def __init__(self, snake_body):
        self.position = self.generate_random_pos(snake_body)

    def draw(self):
        # Calculate the center position of the circle
        center_x = OFFSET + self.position.x * cell_size + cell_size // 2
        center_y = OFFSET + self.position.y * cell_size + cell_size // 2

        # Set the radius of the circle
        radius = cell_size // 2

        # Draw the circle
        pygame.draw.circle(
            screen,
            DARK_GREEN,
            (center_x, center_y),  # Center of the circle
            radius,  # Radius of the circle
        )

    def generate_random_cell(self):
        x = random.randint(0, number_of_cells - 1)
        y = random.randint(0, number_of_cells - 1)
        return Vector2(x, y)

    def generate_random_pos(self, snake_body):
        position = self.generate_random_cell()
        while position in snake_body:
            position = self.generate_random_cell()
        return position


# Class for Snake
class Snake:
    def __init__(self):
        self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]
        self.direction = Vector2(1, 0)
        self.add_segment = False

    def draw(self):
        for segment in self.body:
            segment_rect = (
                OFFSET + segment.x * cell_size,
                OFFSET + segment.y * cell_size,
                cell_size,
                cell_size,
            )
            pygame.draw.rect(screen, DARK_GREEN, segment_rect, 0, round(cell_size / 4))

    def update(self):
        self.body.insert(0, self.body[0] + self.direction)
        if self.add_segment:
            self.add_segment = False
        else:
            self.body = self.body[:-1]

    def reset(self):
        self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]
        self.direction = Vector2(1, 0)


class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food(self.snake.body)
        self.state = "RUNNING"
        self.score = 0

    def draw(self):
        if self.state == "RUNNING":
            self.food.draw()
            self.snake.draw()
        elif self.state == "STOPPED":
            game_over_text = title_font.render("Game Over", True, DARK_GREEN)
            refresh_text = score_font.render("Refresh to play again", True, DARK_GREEN)

            screen.blit(
                game_over_text,
                (
                    (width - game_over_text.get_width()) // 2,
                    (height - game_over_text.get_height()) // 2 - 20,
                ),
            )
            screen.blit(
                refresh_text,
                (
                    (width - refresh_text.get_width()) // 2,
                    (height - refresh_text.get_height()) // 2 + 20,
                ),
            )

    def update(self):
        if self.state == "RUNNING":
            self.snake.update()
            self.check_collision_with_food()
            self.check_collision_with_edges()
            self.check_collision_with_tail()

    def check_collision_with_food(self):
        if self.snake.body[0] == self.food.position:
            self.food.position = self.food.generate_random_pos(self.snake.body)
            self.snake.add_segment = True
            self.score += 1
            pyodide.globals.get("setScore")(self.score)

    def check_collision_with_edges(self):
        if self.snake.body[0].x == number_of_cells or self.snake.body[0].x == -1:
            self.game_over()
        if self.snake.body[0].y == number_of_cells or self.snake.body[0].y == -1:
            self.game_over()

    def game_over(self):
        self.state = "STOPPED"
        pyodide.globals.get("setIsGameEnded")(True)

    def check_collision_with_tail(self):
        headless_body = self.snake.body[1:]
        if self.snake.body[0] in headless_body:
            self.game_over()
        headless_body = self.snake.body[1:]
        if self.snake.body[0] in headless_body:
            self.game_over()


# Set up the screen
screen = pygame.display.set_mode((min_val, min_val))
pygame.display.set_caption("Retro Snake")

# Initialize game
game = Game()


async def game_update_task():
    while True:
        game.update()
        await asyncio.sleep(0.2)


async def main():
    task = asyncio.create_task(game_update_task())

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and game.state == "RUNNING":
                if event.key == pygame.K_UP and game.snake.direction != Vector2(0, 1):
                    game.snake.direction = Vector2(0, -1)
                if event.key == pygame.K_DOWN and game.snake.direction != Vector2(
                    0, -1
                ):
                    game.snake.direction = Vector2(0, 1)
                if event.key == pygame.K_LEFT and game.snake.direction != Vector2(1, 0):
                    game.snake.direction = Vector2(-1, 0)
                if event.key == pygame.K_RIGHT and game.snake.direction != Vector2(
                    -1, 0
                ):
                    game.snake.direction = Vector2(1, 0)

        screen.fill(GREEN)
        pygame.draw.rect(
            screen,
            DARK_GREEN,
            (
                OFFSET - 5,
                OFFSET - 5,
                cell_size * number_of_cells + 10,
                cell_size * number_of_cells + 10,
            ),
            5,
        )
        game.draw()
        title_surface = title_font.render("Retro Snake New", True, DARK_GREEN)
        score_surface = score_font.render(str(game.score), True, DARK_GREEN)
        screen.blit(title_surface, (OFFSET - 5, OFFSET - title_size - 2))
        screen.blit(
            score_surface, (OFFSET - 5, OFFSET + cell_size * number_of_cells + 5)
        )

        pygame.display.update()
        await asyncio.sleep(1 / fps)


main()
