
import pygame
import random
import os
import config

class Point:
    """Represents a coordinate point on the grid."""
    def __init__(self, x, y, timer=0, cost=0, add_speed=0):
        self.x = x
        self.y = y
        self.timer = timer
        self.cost = cost
        self.add_speed = add_speed

    def __eq__(self, other):
        """Check equality based on coordinates."""
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        """Allow points to be used in sets/dictionaries based on coordinates."""
        return hash((self.x, self.y))

    def __str__(self):
        return f"Point(x={self.x}, y={self.y})"


class GameObject:
    """Base class for objects on the game grid."""
    def __init__(self, points, color, tile_size):
        if not isinstance(points, list):
             raise TypeError("GameObject points must be a list of Point objects.")
        self.points = points
        self.color = color
        self.tile_size = tile_size

    def draw(self, surface):
        """Draws the object on the surface as rectangles."""
        for point in self.points:
            rect = pygame.Rect(point.x, point.y, self.tile_size, self.tile_size)
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, config.COLORS['black'], rect, 1)

    def get_random_empty_point(self, occupied_points_set):
        """
        Finds a random empty point on the grid.

        Args:
            occupied_points_set (set): A set of Point objects currently occupied.

        Returns:
            Point: A random Point object that is not in occupied_points_set,
                   or None if the grid is full (highly unlikely in Snake).
        """
        possible_points = set()
        for r in range(config.GRID_HEIGHT):
            for c in range(config.GRID_WIDTH):
                 possible_points.add(Point(c * self.tile_size, r * self.tile_size))

        empty_points = list(possible_points - occupied_points_set)

        if not empty_points:
            print("Warning: No empty points found on the grid!")
            return None

        return random.choice(empty_points)


class Player(GameObject):
    """Represents the snake controlled by the player."""
    def __init__(self, initial_pos):
        super().__init__([initial_pos], config.COLORS['blue'], config.TILE_SIZE)
        self.direction = config.DIR_NONE
        self.next_direction = config.DIR_NONE
        self.grow_pending = 0

    @property
    def head(self):
        """Returns the head Point of the snake."""
        return self.points[0]

    def process_input(self, events):
        """Handles keyboard input to change snake direction."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                new_dir = self.next_direction
                if event.key == pygame.K_UP and self.direction != config.DIR_DOWN:
                    new_dir = config.DIR_UP
                elif event.key == pygame.K_DOWN and self.direction != config.DIR_UP:
                    new_dir = config.DIR_DOWN
                elif event.key == pygame.K_LEFT and self.direction != config.DIR_RIGHT:
                    new_dir = config.DIR_LEFT
                elif event.key == pygame.K_RIGHT and self.direction != config.DIR_LEFT:
                    new_dir = config.DIR_RIGHT

                if new_dir != self.direction:
                     self.next_direction = new_dir


    def move(self, wall_points_set):
        """
        Moves the snake one step in its current direction.
        Checks for collisions with walls, boundaries, and self.

        Args:
            wall_points_set (set): A set of Point objects representing wall locations.

        Returns:
            str or None: A collision type string ('wall', 'boundary', 'self')
                         if a collision occurs, otherwise None.
        """
        if self.next_direction != config.DIR_NONE:
            self.direction = self.next_direction

        if self.direction == config.DIR_NONE:
            return None

        dx, dy = self.direction
        new_head_x = self.head.x + dx * self.tile_size
        new_head_y = self.head.y + dy * self.tile_size
        new_head = Point(new_head_x, new_head_y)

        if not (0 <= new_head_x < config.SCREEN_WIDTH and 0 <= new_head_y < config.SCREEN_HEIGHT):
            return 'boundary'

        if new_head in wall_points_set:
             return 'wall'

        body_segments_to_check = self.points[:-1] if not self.grow_pending else self.points
        if new_head in body_segments_to_check:
            return 'self'

        self.points.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.points.pop()

        return None


    def grow(self, amount=1):
        """Schedules the snake to grow by a number of segments."""
        self.grow_pending += amount

    def draw(self, surface):
        """Draws the snake, highlighting the head."""
        super().draw(surface)
        if self.points:
            head_rect = pygame.Rect(self.head.x, self.head.y, self.tile_size, self.tile_size)
            pygame.draw.rect(surface, config.COLORS['head'], head_rect)
            pygame.draw.rect(surface, config.COLORS['black'], head_rect, 1)


class Food(GameObject):
    """Manages food items on the screen."""
    def __init__(self, initial_occupied_points_set):
        super().__init__([], config.COLORS['green'], config.TILE_SIZE)
        self.font = pygame.font.SysFont(config.FONT_NAME, config.SCORE_FONT_SIZE)
        for _ in range(config.FOOD_COUNT):
            self.add_new_food(initial_occupied_points_set)

    def add_new_food(self, occupied_points_set):
        """Adds a single new food item to a random empty location."""
        current_food_points_set = set(self.points)
        combined_occupied = occupied_points_set.union(current_food_points_set)

        new_point = self.get_random_empty_point(combined_occupied)
        if new_point:
            new_point.timer = random.randint(config.FOOD_TIMER_MIN, config.FOOD_TIMER_MAX)
            new_point.cost = random.randint(config.FOOD_COST_MIN, config.FOOD_COST_MAX)
            new_point.add_speed = 0
            if random.random() < config.FOOD_SPEED_BOOST_CHANCE:
                 new_point.add_speed = random.randint(config.FOOD_SPEED_BOOST_MIN, config.FOOD_SPEED_BOOST_MAX)

            self.points.append(new_point)
        else:
             print("Error: Could not add new food, no empty space found.")


    def check_collision(self, head_point, current_occupied_set):
        """
        Checks if the snake's head collides with any food.
        If collision, removes eaten food, adds new food, returns properties.

        Args:
            head_point (Point): The snake's head position.
            current_occupied_set (set): All currently occupied points (snake, walls).

        Returns:
            tuple (bool, int, int): (eaten, cost, add_speed)
        """
        eaten_food = None
        for food_item in self.points:
            if food_item == head_point:
                eaten_food = food_item
                break

        if eaten_food:
            cost = eaten_food.cost
            add_speed = eaten_food.add_speed
            self.points.remove(eaten_food)
            self.add_new_food(current_occupied_set)
            return True, cost, add_speed
        else:
            return False, 0, 0

    def update_timers(self, current_occupied_set):
        """Decrements food timers and replaces expired food."""
        new_points_list = []
        replaced_count = 0
        for point in self.points:
            point.timer -= 1
            if point.timer > config.FOOD_EXPIRE_THRESHOLD:
                new_points_list.append(point)
            else:
                replaced_count += 1

        self.points = new_points_list
        for _ in range(replaced_count):
             self.add_new_food(current_occupied_set)


    def draw(self, surface):
        """Draws food items, shrinking them based on timer and showing cost."""
        for point in self.points:
            max_timer = config.FOOD_TIMER_MAX
            shrink_factor = max(0, (max_timer - point.timer)) / max_timer
            max_shrink_pixels = self.tile_size // 3
            shrink_pixels = int(shrink_factor * max_shrink_pixels)

            x = point.x + shrink_pixels
            y = point.y + shrink_pixels
            width = self.tile_size - 2 * shrink_pixels
            height = self.tile_size - 2 * shrink_pixels

            food_color = config.COLORS['b-green'] if point.add_speed > 0 else self.color

            if width > 0 and height > 0:
                 food_rect = pygame.Rect(x, y, width, height)
                 pygame.draw.rect(surface, food_color, food_rect)
                 pygame.draw.rect(surface, config.COLORS['black'], food_rect, 1)

                 text_surf = self.font.render(f'{point.cost}', True, config.COLORS['black'])
                 text_rect = text_surf.get_rect(center=(point.x + self.tile_size // 2, point.y + self.tile_size // 2))
                 surface.blit(text_surf, text_rect)


class Wall(GameObject):
    """Represents stationary wall obstacles."""
    def __init__(self, level=1):
        super().__init__([], config.COLORS['wall'], config.TILE_SIZE)

        self.level = level
        level_points = self._load_level()
        self.points = level_points
        self.points_set = set(self.points)

    def _load_level(self):
        """Loads wall points from a level file or generates randomly."""
        points = []
        level_file_path = os.path.join(config.BASE_DIR, 'levels', f'level{self.level}.txt')
        tile_size = self.tile_size

        if self.level >= config.MAX_LEVEL:
            print(f"Level {self.level}: Generating random walls.")
            num_random_walls = 6
            occupied_for_walls = set()
            temp_spawner = GameObject([], self.color, tile_size)
            for _ in range(num_random_walls):
                 random_point = temp_spawner.get_random_empty_point(occupied_for_walls)
                 if random_point:
                      points.append(random_point)
                      occupied_for_walls.add(random_point)
        elif os.path.exists(level_file_path):
            try:
                with open(level_file_path, 'r') as f:
                    level_layout = [line.strip() for line in f.readlines()]

                for r, row_str in enumerate(level_layout):
                    if r >= config.GRID_HEIGHT: break
                    for c, char in enumerate(row_str):
                         if c >= config.GRID_WIDTH: break
                         if char == '#':
                             points.append(Point(c * tile_size, r * tile_size))
            except Exception as e:
                 print(f"Error processing level file {level_file_path}: {e}")
                 points = []
        else:
            print(f"Warning: Level file not found: {level_file_path}. No walls loaded.")
            points = []

        return points

