import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 400
TILE_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

COLOR_FILE = os.path.join(BASE_DIR, 'color.json')
try:
    with open(COLOR_FILE) as f:
        COLORS = json.loads(f.read())
except FileNotFoundError:
    print(f"Error: {COLOR_FILE} not found. Using default colors.")
    COLORS = {
        "bg_color": [226, 231, 231],
        "black": [0, 0, 0],
        "green": [36, 239, 83],
        "head": [147, 48, 192],
        "blue": [48, 9, 253],
        "red": [255, 0, 0],
        "wall": [134, 11, 11],
        "text": [18, 151, 137],
        "b-green": [0, 255, 188]
    }
except json.JSONDecodeError:
     print(f"Error: Could not decode {COLOR_FILE}. Using default colors.")

INITIAL_SPEED = 5
LEVEL_SPEED_INCREMENT = 1
LEVEL_4_SPEED_INCREMENT = 8
MAX_LEVEL = 4

SCORE_TO_NEXT_LEVEL = 50
INFINITE_LEVEL_SCORE_TARGET = 99999


FOOD_COUNT = 5
FOOD_TIMER_MIN = 30
FOOD_TIMER_MAX = 50
FOOD_COST_MIN = 2
FOOD_COST_MAX = 7
FOOD_EXPIRE_THRESHOLD = 5
FOOD_SPEED_BOOST_CHANCE = 0.5
FOOD_SPEED_BOOST_MIN = 4
FOOD_SPEED_BOOST_MAX = 6
FOOD_SPEED_BOOST_DURATION_MULTIPLIER = 10

DB_NAME = 'suppliers'
DB_USER = 'postgres'
DB_PASSWORD = '1234'
DB_HOST = '127.0.0.1'
DB_PORT = '5432'
DB_TABLE_NAME = 'snake_scores'


FONT_NAME = 'comicsansms'
UI_FONT_SIZE = 35
SCORE_FONT_SIZE = 20
PAUSE_FONT_SIZE = 50
LOSE_FONT_SIZE = 80
INFO_FONT_SIZE = 30

STATE_RUNNING = 0
STATE_PAUSED = 1
STATE_GAME_OVER = 2
STATE_START_SCREEN = 3
STATE_EXIT_CONFIRM = 4

DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
DIR_NONE = (0, 0)