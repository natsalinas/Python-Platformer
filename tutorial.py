import os 
import random
import math
import pygame 
from os import listdir 
from os.path import isfile, join

# initialize pygame module 
pygame.init()

pygame.display.set_caption("Platformer")

# global variables 
BG_COLOR = (255, 255, 255) #white 
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5 

# create pygame window 
window = pygame.display.set_mode((WIDTH, HEIGHT))

# flips images of sprites (images) when going left 
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

# load all different sprite sheets for our character. 
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    # load every single file inside this directory 
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}
    
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0,0), rect)
            sprites.append(pygame.transform.scale2x(surface))
        
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
        
    return all_sprites

def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0,0), rect)
    return pygame.transform.scale2x(surface)

# Player inherits from Pygame Sprite, makes it easy to do pixel-perfect collision
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1 
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        # velocity values - how fast we are moving out player 
        self.x_vel = 0 
        self.y_vel = 0 
        self.mask = None 
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0 
        self.jump_count = 0 
    
    def jump(self):
        # change velocity to go upwards 
        self.y_vel = -self.GRAVITY * 8  
        self.animation_count = 0
        self.jump_count += 1 
        if self.jump_count == 1:
            self.fall_count = 0
        
            
    
    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def move_left(self, vel): 
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0 

    def move_right(self, vel):
        self.x_vel = vel 
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0 

    # loop function - moves character and updates animation
    def loop(self, fps): 
        # Gravity 
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        self.fall_count += 1 
        self.update_sprite()
    
    def landed(self):
        # stop adding gravity if landed
        self.fall_count = 0
        self.y_vel = 0 
        self.jump_count = 0
    
    def hit_head(self):
        self.count = 0 
        self.y_vel *= -1 

    def update_sprite(self):
        sprite_sheet = "idle" #default sprite sheet 
        if self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1 
        self.update()
    
    def update(self): 
        # rectangle that bounds character is adjusted based on character used
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)
        

    def draw(self, win):
        #self.sprite = self.SPRITES["idle_" + self.direction][0]
        win.blit(self.sprite, (self.rect.x, self.rect.y))

class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name =name 

    def draw(self, win):
        win.blit(self.image, (self.rect.x, self.rect.y))

class Block(Object): 
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0,0))
        self.mask = pygame.mask.from_surface(self.image) # for collisions 

# create background 
def get_background(name): 
    image = pygame.image.load(join("assets", "Background", name))
    # get width and height of image (x,y blank)
    _, _, width, height = image.get_rect() 
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            # denotes the position of the top left corner of the current tile that im adding to tiles list.  
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects):
    # loop through every tile, and fill screen with images 
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window)

    player.draw(window)

    # clear screen after every frame 
    pygame.display.update() 

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player,obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom 
                player.hit_head()

        collided_objects.append(obj)

    return collided_objects 
# move the player 
def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    # only move while holding down the key 
    player.x_vel = 0 

    if keys[pygame.K_LEFT]:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT]:
        player.move_right(PLAYER_VEL)
    
    handle_vertical_collision(player, objects, player.y_vel)


# main function to start the game (event loop)
def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Purple.png")

    block_size = 96
    player = Player(100, 100, 50, 50)

    # create blocks that go to the left and right of screen 
    floor = [Block(i * block_size, HEIGHT - block_size, block_size) 
             for i in range(-WIDTH // block_size, WIDTH *2 // block_size)]

    run = True
    while run:
        clock.tick(FPS) # reglates frame rate across devices 

        for event in pygame.event.get(): 
            if event.type == pygame.QUIT:
                run = False 
                break 
        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
        
        player.loop(FPS)
        handle_move(player, floor)
        draw(window, background, bg_image, player, floor)
    pygame.quit()
    quit()

if __name__ == "__main__": 
    main(window)