# ℹ️ This software is free and open-source; anyone can redistribute it and/or modify it.

import random
from pygame import mixer

import arcade
from PIL import Image

# Constants
SCREEN_TITLE = "Sky Tetris"

# Board settings
ROWS = 20
COLUMNS = 20
CELL_WIDTH = 30
CELL_HEIGHT = 30
MARGIN = 5

# Calculate screen dimensions
SCREEN_WIDTH = (CELL_WIDTH + MARGIN) * COLUMNS + MARGIN
SCREEN_HEIGHT = (CELL_HEIGHT + MARGIN) * ROWS + MARGIN

# Colors (RGB tuples)
COLORS = [
    (0, 0, 0),
    (0, 255, 0),
    (255, 0, 0),
    (0, 255, 255),
    (255, 255, 0),
    (255, 165, 0),
    (0, 0, 255),
    (255, 0, 255)
]

# Tetramino shapes
SHAPES = [
    # S Shape
    [[0, 1, 1],
     [1, 1, 0]],

    # Z Shape
    [[2, 2, 0],
     [0, 2, 2]],

    # I Shape
    [[3, 3, 3, 3]],

    # O Shape
    [[4, 4],
     [4, 4]],

    # J Shape
    [[0, 0, 5],
     [5, 5, 5]],

    # L Shape
    [[6, 0, 0],
     [6, 6, 6]],

    # T Shape
    [[7, 7, 7],
     [0, 7, 0]]
]


def rotate(shape):
    """Rotate the shape matrix 90 degrees clockwise."""
    return [list(row) for row in zip(*shape[::-1])]


def check_collision(board, shape, offset):
    """Check if the given shape will collide with the board."""
    x_off, y_off = offset
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell and (y + y_off >= ROWS or x + x_off < 0 or x + x_off >= COLUMNS or board[y + y_off][x + x_off]):
                return True
    return False


def clear_row(board, row):
    """Remove the specified row from the board and add a new empty row at the top."""
    del board[row]
    return [[0 for _ in range(COLUMNS)]] + board


def join_shapes(board, shape, offset):
    """Merge the shape into the board at the given offset."""
    x_off, y_off = offset
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                board[y + y_off][x + x_off] = cell
    return board


def create_new_board():
    """Create a new game board with an empty grid."""
    board = [[0 for _ in range(COLUMNS)] for _ in range(ROWS)]
    board.append([1 for _ in range(COLUMNS)])  # Bottom boundary
    return board


def get_high_score(filename):
    """Retrieve the high score from a file."""
    try:
        with open(filename, 'r') as f:
            return int(f.read())
    except (FileNotFoundError, ValueError):
        return 0


def create_textures():
    """Generate a list of textures based on the defined colors."""
    texture_list = []
    for color in COLORS:
        image = Image.new('RGB', (CELL_WIDTH, CELL_HEIGHT), color)
        texture = arcade.Texture(str(color), image)
        texture_list.append(texture)
    return texture_list


TEXTURE_LIST = create_textures()


class Tetris(arcade.Window):
    """Main class for the Tetris game."""

    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.BLACK)

        # Initialize game state
        self.board = None
        self.frame_count = 0
        self.score = 0
        self.high_score = get_high_score("save/high_score.txt")
        self.player = ""
        self.game_over = False
        self.paused = False
        self.begin = True

        self.board_sprite_list = arcade.SpriteList()
        self.tetramino = None
        self.x_tetramino = 0
        self.y_tetramino = 0

        self.load_logo()
        self.initialize_mixer()
        self.set_user()
        self.set_mouse_visible(False)

    def load_logo(self):
        """Load the game logo texture."""
        self.logo_texture = arcade.load_texture("logo.png")

    def initialize_mixer(self):
        """Initialize the music mixer."""
        mixer.init()
        mixer.music.set_volume(0.5)

    def set_user(self):
        """Prompt the user to enter their name."""
        self.player = input('Type your name: ')

    def setup(self):
        """Set up the game state."""
        self.board = create_new_board()
        mixer.music.load('music/level_music.mp3')
        mixer.music.play(-1)

        # Create sprites for the board
        for row in range(len(self.board)):
            for column in range(len(self.board[0])):
                sprite = arcade.Sprite()
                sprite.append_texture(TEXTURE_LIST[self.board[row][column]])
                sprite.set_texture(0)
                sprite.center_x = (MARGIN + CELL_WIDTH) * column + CELL_WIDTH // 2 + MARGIN
                sprite.center_y = SCREEN_HEIGHT - (MARGIN + CELL_HEIGHT) * row - CELL_HEIGHT // 2 - MARGIN
                self.board_sprite_list.append(sprite)

        self.new_tetramino()
        self.update_board()

    def new_tetramino(self):
        """Create a new tetramino and check for game over."""
        self.tetramino = random.choice(SHAPES)
        self.x_tetramino = COLUMNS // 2 - len(self.tetramino[0]) // 2
        self.y_tetramino = 0

        if check_collision(self.board, self.tetramino, (self.x_tetramino, self.y_tetramino)):
            self.game_over = True
            mixer.music.stop()
            if self.score > self.high_score:
                mixer.music.load('music/high_score.mp3')
                self.high_score = self.score
                self.save_high_score()
            else:
                mixer.music.load('music/game_over.mp3')
                self.save_score()
            mixer.music.play()
            self.set_mouse_visible(True)

    def save_high_score(self):
        """Save the new high score to the file."""
        with open("save/high_score.txt", "w") as f:
            f.write(f"{self.high_score}\t\t{self.player}")

    def save_score(self):
        """Append the current score to the scores file."""
        with open("save/scores.txt", "a") as f:
            f.write(f"{self.score}\t\t{self.player}\n")

    def drop(self):
        """Move the tetramino one row down and handle collisions."""
        if not self.game_over and not self.paused and not self.begin:
            self.y_tetramino += 1
            if check_collision(self.board, self.tetramino, (self.x_tetramino, self.y_tetramino)):
                self.y_tetramino -= 1
                self.board = join_shapes(self.board, self.tetramino, (self.x_tetramino, self.y_tetramino))
                self.clear_full_rows()
                self.update_board()
                self.new_tetramino()

    def clear_full_rows(self):
        """Check and clear any full rows on the board."""
        rows_cleared = 0
        for row_index in range(len(self.board) - 1):
            if all(cell != 0 for cell in self.board[row_index]):
                self.board = clear_row(self.board, row_index)
                self.score += 10
                rows_cleared += 1
        if rows_cleared > 0:
            mixer.music.play()

    def pause_game(self):
        """Toggle the paused state of the game."""
        self.paused = not self.paused
        if self.paused:
            mixer.music.pause()
        else:
            mixer.music.unpause()

    def rotate_tetramino(self):
        """Rotate the current tetramino if possible."""
        if not self.game_over and not self.paused:
            new_shape = rotate(self.tetramino)
            if not check_collision(self.board, new_shape, (self.x_tetramino, self.y_tetramino)):
                self.tetramino = new_shape

    def on_update(self, delta_time):
        """Update the game state."""
        if not self.paused and not self.game_over and not self.begin:
            self.frame_count += 1
            if self.frame_count % 11 == 0:
                self.drop()

    def move_tetramino(self, delta_x):
        """Move the tetramino horizontally."""
        if not self.game_over and not self.paused:
            new_x = self.x_tetramino + delta_x
            new_x = max(0, min(new_x, COLUMNS - len(self.tetramino[0])))
            if not check_collision(self.board, self.tetramino, (new_x, self.y_tetramino)):
                self.x_tetramino = new_x

    def on_key_press(self, key, modifiers):
        """Handle key press events."""
        if self.begin:
            self.begin = False

        if key == arcade.key.LEFT:
            self.move_tetramino(-1)
        elif key == arcade.key.RIGHT:
            self.move_tetramino(1)
        elif key == arcade.key.UP:
            self.rotate_tetramino()
        elif key == arcade.key.DOWN:
            self.drop()
        elif key == arcade.key.P:
            self.pause_game()
        elif key == arcade.key.ESCAPE:
            self.close()

    def draw_tetramino(self):
        """Draw the current tetramino on the screen."""
        for y, row in enumerate(self.tetramino):
            for x, cell in enumerate(row):
                if cell:
                    color = COLORS[cell]
                    pos_x = (MARGIN + CELL_WIDTH) * (self.x_tetramino + x) + MARGIN + CELL_WIDTH // 2
                    pos_y = SCREEN_HEIGHT - (MARGIN + CELL_HEIGHT) * (self.y_tetramino + y) - CELL_HEIGHT // 2 - MARGIN
                    arcade.draw_rectangle_filled(pos_x, pos_y, CELL_WIDTH, CELL_HEIGHT, color)

    def update_board(self):
        """Update the sprite list to match the current board state."""
        for row in range(ROWS):
            for column in range(COLUMNS):
                cell = self.board[row][column]
                index = row * COLUMNS + column
                self.board_sprite_list[index].set_texture(cell)

    def on_draw(self):
        """Render the screen."""
        arcade.start_render()
        self.board_sprite_list.draw()
        self.draw_tetramino()

        # Display score
        arcade.draw_text(f"{self.player}'s Score: {self.score}", 10, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, 20)

        if self.game_over:
            arcade.draw_text("Game Over!", SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT / 2,
                             arcade.color.CYAN, 50, anchor_x="center")
            arcade.draw_text("Press ESC to Exit", SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 - 60,
                             arcade.color.CYAN, 30, anchor_x="center")

        if self.begin:
            arcade.draw_texture_rectangle(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 500, 300,
                                          self.logo_texture, 0)
            arcade.draw_text("PRESS ANY BUTTON", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 150,
                             arcade.color.CYAN, 30, anchor_x="center")

    def main_menu(self):
        """Display the main menu (if needed)."""
        pass  # Placeholder for any main menu logic


def main():
    """Main function to start the game."""
    game = Tetris(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
