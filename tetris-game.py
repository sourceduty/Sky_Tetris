import PIL #used to create textures for the game
import arcade #used to create the game
from pygame import mixer




SCREEN_TITLE = "Open Tetris"

image = arcade.load_texture("logo.png")

# Initialize music mixer at the beginning
mixer.init() 
MUSIC_VOLUME = 0.5

# Game board (20x20 cells) customizable
ROWS = 20
COLUMNS = 20

# Setup each cell size [width x height]
WIDTH = 30
HEIGHT = 30
MARGIN = 5 # distance between cells

# Calculate screen width and height
SCREEN_W = (WIDTH + MARGIN) * COLUMNS + MARGIN
SCREEN_H = (HEIGHT + MARGIN) * ROWS + MARGIN

# Define colors and shapes of the tetraminos
colors = [
    (0, 0, 0),
    (0, 255, 0), 
    (255, 0, 0), 
    (0, 255, 255), 
    (255, 255, 0), 
    (255, 165, 0), 
    (0, 0, 255), 
    (255, 0, 255)
]

shapes = [
    #S Shape
    [[0, 1, 1],
     [1, 1, 0]],

    #Z Shape
    [[2, 2, 0],
     [0, 2, 2]],
    
    #I Shape
    [[3, 3, 3, 3]],

    #O Shape
    [[4, 4],
     [4, 4]],

    #J Shape
    [[0, 0, 5],
    [5, 5, 5]],

    #L Shape
    [[6, 0, 0],
     [6, 6, 6]],

    #T Shape
    [[7, 7, 7],
    [0, 7, 0]]
]

def rotate(shape):
    # Rotate the shape matrix 90 degrees clockwise
    return [[shape[y][x] for y in range(len(shape))] for x in range(len(shape[0]) - 1, -1, -1)]

def check_collision(board, shape, offset):
    # Check if the given shape will collide with the board 
    # or the currently placed pieces. Offset is a tuple of coordinates in the (x, y) form

    x_off, y_off = offset
    for y_cell, row in enumerate(shape): #for each row of the board
        for x_cell, cell in enumerate(row): #for each column of the row (cell)
            if cell and board[y_cell + y_off][x_cell + x_off]:
                return True #if the cell and the board are colliding
    return False #if the cell and the board are not colliding

def clear_row(board, row):
    # Remove the row from the board
    del board[row]
    # Replace deleted row with a new one on top of the board
    return [[0 for _ in range(COLUMNS)]] + board

def join_shapes(shape_a, shape_b, offset):
    # Join matrixes of two shapes at the given offset
    x_off, y_off = offset
    for y_cell, row in enumerate(shape_b):
        for x_cell, cell in enumerate(row):
            shape_a[y_cell + y_off - 1][x_cell + x_off] += cell # Add a new piece to the board
    return shape_a #return fused shapes
    
def new_board():
    # Create the game board, the grid is made of 0s in empty slots
    # and 1s at the bottom for a faster collision check
    board = [[0 for x in range(COLUMNS)] for y in range(ROWS)]
    # add the bottom line of 1s to the board
    board += [[1 for x in range(COLUMNS)]]
    return board

def get_high_score(filename):
    # Read high score from file high_score.txt
    with open(filename, 'r') as f:
        return int(f.read())

def texture():
    texture_list = []
    # Create a list of images for sprites based on the global colors
    for i in range(len(colors)):
        sprite = PIL.Image.new('RGB', (WIDTH, HEIGHT), colors[i]) # create a new image
        texture_list.append(arcade.Texture(str(colors[i]), sprite)) # add it to the list
    return texture_list

texture_list = texture() # create a list of textures

import random as rand #used to generate random choices

class Tetris(arcade.Window):
    # Define the main class for the game
    def __init__(self, width, height, title):
        # Setup the application
        super().__init__(width, height, title) # Call the parent class initializer

        arcade.set_background_color(arcade.color.BLACK) # Set the background color

        self.board = None # Initialize the game board
        self.frame_count = 0 # Initialize the frame count, used for animating the screen
        self.score = 0  # Initialize the player score
        self.high_score = get_high_score("save/high_score.txt") # Initialize the high score
        self.player = None # Initialize the player name
        self.game_over = False # Initialize the game over flag
        self.paused = False # Initialize the pause flag
        self.pause2 = True
        self.begin = True

        self.board_sprite_list = None # Initialize the board sprite list, used to animate tetraminos

        self.tetramino = None # Initialize the falling tetramino
        self.x_tetramino = 0 # horizontal position of the tetramino
        self.y_tetramino = 0 # vertical position of the tetramino

        self.set_user() # Set the user name
        self.set_mouse_visible(False) # Initialize the mouse visibility

    def new_tetramino(self):
        # Randomly create a new tetramino,
        # if we immediately collide at the top of the screen is game-over
        
        self.tetramino = rand.choice(shapes) # choose a random shape

        self.x_tetramino = int(COLUMNS / 2) - int(len(self.tetramino[0]) / 2)
        self.y_tetramino = -20

        if check_collision(self.board, self.tetramino, (self.x_tetramino, self.y_tetramino)):
            self.game_over = True
            if(self.score > self.high_score):
                mixer.music.stop() # stop the music
                mixer.music.load('music/high_score.mp3')
                mixer.music.play() # play the music
                # If the score is higher than the high score, save it
                self.high_score = self.score
                with open("save/high_score.txt", "w") as f:
                    # Write the high score to the file
                    f.write(str(self.high_score) + "\t\t" + str(self.player))
            else:
                mixer.music.stop() # stop the music
                mixer.music.load('music/game_over.mp3')
                mixer.music.play() # play the music
                # If the score is lower than the high score, save it in a different file
                with open("save/scores.txt", "a") as f:
                    # Write the high score to the file
                    f.write(str(self.score) + "\t\t" + str(self.player) + "\n")
            self.set_mouse_visible(True) # make the mouse visible

    def set_user(self):
        # Set the user name
        name = 'your'
        self.player = name

    def setup(self):
        self.board = new_board() # Create a new board

        # start music engine and play the music
        mixer.music.load('music/level_music.mp3') # Load the music
        mixer.music.play(-1) # Play the music in loop

        self.board_sprite_list = arcade.SpriteList() # Create a new sprite list for the board
        for row in range(len(self.board)):
            for column in range(len(self.board[0])):
                sprite = arcade.Sprite() 
                # Associate texture to sprite
                for texture in texture_list:
                    sprite.append_texture(texture)
                sprite.set_texture(0)
                sprite.center_x = (MARGIN + WIDTH) * column + WIDTH // 2 + MARGIN
                sprite.center_y = SCREEN_H - (MARGIN + HEIGHT) * row + HEIGHT // 2 + MARGIN
                
                self.board_sprite_list.append(sprite)
        if self.begin:
            self.start()
        self.new_tetramino() # Create a new tetramino
        self.update_board() # Update the board

    def drop(self):
        # Drop the tetramino one place down,
        # then check for collisions
        if self.game_over == False and self.paused == False and not self.begin:
            self.y_tetramino += 1 #move the tetramino one row down
            if check_collision(self.board, self.tetramino, (self.x_tetramino, self.y_tetramino)):
                self.board = join_shapes(self.board, self.tetramino, (self.x_tetramino, self.y_tetramino))
                while True:
                    # Check for rows to clear
                    for _, row in enumerate(self.board[:-1]):
                        if 0 not in row:
                            self.score += 10
                            self.board = clear_row(self.board, _)
                            break
                    else:
                        break
                self.update_board() # Update the board
                self.new_tetramino() # Create a new tetramino
    
    def pause(self):
        self.paused = not self.paused
        if self.paused == True:
            mixer.music.pause()
        elif self.paused == False:
            mixer.music.unpause()

    def start(self):
        self.pause2 =  self.pause2
        # if self.pause2:
        #     mixer.music.pause()
        # else:
        #     mixer.music.unpause()

    def rotate_tetramino(self):
        if self.game_over == False and self.paused == False:
            new_tetramino = rotate(self.tetramino)
            # Check for collision, if place is free then rotate
            if not check_collision(self.board, new_tetramino, (self.x_tetramino, self.y_tetramino)):
                self.tetramino = new_tetramino

    def on_update(self, dt):
        self.frame_count += 1
        if self.frame_count % 11 == 0: #move a piece down every 10 frames
            self.drop()

    def move(self, delta):
        # move the tetramino horizzontally
        if self.game_over == False and self.paused == False:
            new_pos = self.x_tetramino + delta
            # check if the tetramino is moved outside from the game board
            if new_pos < 0:
                new_pos = 0
            if new_pos > COLUMNS - len(self.tetramino[0]):
                new_pos = COLUMNS - len(self.tetramino[0])
            # check if the tetramino does collide, if not then move it
            if not check_collision(self.board, self.tetramino, (new_pos, self.y_tetramino)):
                self.x_tetramino = new_pos

    def on_key_press(self, key, modifiers):
        # Handle user interaction with the keyboard

        if self.begin:
            self.begin = False
        if key == arcade.key.LEFT:
            self.move(-1)
        elif key == arcade.key.RIGHT:
            self.move(1)
        elif key == arcade.key.UP:
            self.rotate_tetramino()
        elif key == arcade.key.DOWN:
            self.drop()
        elif key == arcade.key.P:
            self.pause()
        elif key == arcade.key.ESCAPE:
            self.close()

        

        

    def draw_grid(self, grid, x_off, y_off):
        # Draw the grid
        for row in range(len(grid)):
            for column in range(len(grid[0])):
                if grid[row][column]:
                    color = colors[grid[row][column]] # get the color of the block
                    # Calculate the cell where to draw
                    x = (MARGIN + WIDTH) * (column + x_off) + MARGIN + WIDTH // 2
                    y = SCREEN_H - (MARGIN + HEIGHT) * (-row - y_off) + MARGIN + HEIGHT // 2

                    arcade.draw_rectangle_filled(x, y, WIDTH, HEIGHT, color) # Draw the cell color

    def update_board(self):
        # Update the sprite list to reflect the content of our game board
        for row in range(len(self.board)): 
            for column in range(len(self.board[0])): 
                cell = self.board[-row][column]
                index = row * COLUMNS + column
                
                # Set the texture of the sprite
                self.board_sprite_list[index].set_texture(cell) 
    
    def on_draw(self):
        # Render the screen
        arcade.start_render() # Initialize screen rendering before we start
        self.board_sprite_list.draw()
        
        arcade.draw_text(str(self.player)+" Score: "+ str(self.score), 0, SCREEN_H-700, arcade.color.WHITE, 20) # Draw score text
        self.draw_grid(self.tetramino, self.x_tetramino, self.y_tetramino)
        if self.game_over:
            arcade.draw_text("Game Over!", 190, SCREEN_H-300, arcade.color.CYAN, 50) # Draw score text
            arcade.draw_text("Press ESC to Exit", 90, SCREEN_H-400, arcade.color.CYAN, 50) # Draw score text

        if self.begin:
            
          

            # Draw some text using your custom font
            arcade.draw_texture_rectangle(SCREEN_W/2+10,550, 500, 300, image, 0)
            arcade.draw_text("Press any button to play", 130, SCREEN_H-350, arcade.color.CYAN, 30) # Draw score text


def main():
    # main function
    game = Tetris(SCREEN_W, SCREEN_H, SCREEN_TITLE)
    game.setup() # Setup the game
    arcade.run() # Run the game

if __name__ == "__main__":
    main()

