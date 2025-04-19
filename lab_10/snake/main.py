import pygame
import sys
import config
import db_manager
from game_objects import Player, Food, Wall, Point

pygame.init()
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption('Snake Game')
clock = pygame.time.Clock()

ui_font = pygame.font.SysFont(config.FONT_NAME, config.UI_FONT_SIZE)
pause_font = pygame.font.SysFont(config.FONT_NAME, config.PAUSE_FONT_SIZE)
lose_font = pygame.font.SysFont(config.FONT_NAME, config.LOSE_FONT_SIZE)
info_font = pygame.font.SysFont(config.FONT_NAME, config.INFO_FONT_SIZE)

def draw_text(surface, text, font, color, center_pos, alpha=255):
    """Draws text centered at a given position, optionally with transparency."""
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=center_pos)

    if alpha < 255:

        temp_surface = pygame.Surface(text_rect.size, pygame.SRCALPHA)
        temp_surface.blit(text_surface, (0, 0))
        temp_surface.set_alpha(alpha)
        surface.blit(temp_surface, text_rect)
    else:
        surface.blit(text_surface, text_rect)


def draw_ui(surface, level, score, required_score):
    """Draws the user interface elements (level, score)."""
    surface.fill(config.COLORS['bg_color'])

    for i in range(0, config.SCREEN_WIDTH, config.TILE_SIZE):
        pygame.draw.line(surface, config.COLORS['black'], (i, 0), (i, config.SCREEN_HEIGHT), 1)
    for i in range(0, config.SCREEN_HEIGHT, config.TILE_SIZE):
        pygame.draw.line(surface, config.COLORS['black'], (0, i), (config.SCREEN_WIDTH, i), 1)

    level_text = f'LVL: {level}'
    score_text = f'Score: {score}/{required_score}'
    level_surf = ui_font.render(level_text, True, config.COLORS['text'])
    score_surf = ui_font.render(score_text, True, config.COLORS['text'])

    level_surf.set_alpha(180)
    score_surf.set_alpha(180)

    surface.blit(level_surf, (10, 5))
    surface.blit(score_surf, (config.SCREEN_WIDTH - score_surf.get_width() - 10, 5))

def reset_game_state(level, score, player_points_text):
    """Initializes or resets the game state based on loaded/default data."""
    current_level = level
    current_score = score

    base_speed = config.INITIAL_SPEED
    if current_level == 2:
        base_speed += config.LEVEL_SPEED_INCREMENT
    elif current_level == 3:
         base_speed += config.LEVEL_SPEED_INCREMENT * 2
    elif current_level >= config.MAX_LEVEL:
         base_speed += config.LEVEL_SPEED_INCREMENT * 2 + config.LEVEL_4_SPEED_INCREMENT

    wall = Wall(level=current_level)
    wall_set = wall.points_set

    player_points = db_manager.text_to_points(player_points_text)
    if not player_points:
        temp_obj = Wall(level=current_level)
        start_pos = temp_obj.get_random_empty_point(wall_set)
        if start_pos is None:
             print("FATAL ERROR: Cannot find starting position for player!")
             start_pos = Point(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        player_points = [start_pos]

    player = Player(player_points[0])
    player.points = player_points

    player_set = set(player.points)
    occupied_set = wall_set.union(player_set)
    food = Food(occupied_set)

    score_needed = config.SCORE_TO_NEXT_LEVEL if current_level < config.MAX_LEVEL else config.INFINITE_LEVEL_SCORE_TARGET

    game_speed = base_speed
    speed_boost = 0
    boost_timer = 0

    return {
        "level": current_level,
        "score": current_score,
        "score_needed": score_needed,
        "player": player,
        "wall": wall,
        "food": food,
        "game_speed": game_speed,
        "speed_boost": speed_boost,
        "boost_timer": boost_timer,
        "game_state": config.STATE_RUNNING,
        "user_moved": False
    }

def game_loop(user_name, user_data):
    """Main game loop."""

    if user_data:
        print(f"Welcome back, {user_data[0]}!")
        print(f"Loaded Level: {user_data[1]}, Score: {user_data[2]}")
        game_vars = reset_game_state(user_data[1], user_data[2], user_data[3])
    else:
        print("Starting new game.")
        game_vars = reset_game_state(level=1, score=0, player_points_text='')

    running = True
    while running:
        events = pygame.event.get()
        keydown_events = []
        for event in events:
            if event.type == pygame.QUIT:
                print("Saving progress on quit...")
                db_manager.update_user_progress(
                    user_name,
                    game_vars["level"],
                    game_vars["score"],
                    game_vars["player"].points
                )
                running = False
                continue

            if event.type == pygame.KEYDOWN:
                keydown_events.append(event)
                current_state = game_vars["game_state"]

                if event.key == pygame.K_SPACE:
                    if current_state == config.STATE_RUNNING:
                        game_vars["game_state"] = config.STATE_PAUSED
                    elif current_state == config.STATE_PAUSED:
                        game_vars["game_state"] = config.STATE_RUNNING
                    elif current_state == config.STATE_EXIT_CONFIRM:
                        game_vars["game_state"] = config.STATE_RUNNING

                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    if current_state == config.STATE_GAME_OVER:
                        print("Restarting level...")
                        game_vars = reset_game_state(
                            level=game_vars["level"],
                            score=0,
                            player_points_text=''
                        )
                    elif current_state == config.STATE_PAUSED:
                        game_vars["game_state"] = config.STATE_EXIT_CONFIRM
                    elif current_state == config.STATE_EXIT_CONFIRM:
                        print("Saving and exiting...")
                        db_manager.update_user_progress(
                            user_name,
                            game_vars["level"],
                            game_vars["score"],
                            game_vars["player"].points
                        )
                        running = False
                        continue

        current_state = game_vars["game_state"]

        if current_state == config.STATE_RUNNING:
            game_vars["player"].process_input(keydown_events)

            should_attempt_move = game_vars["user_moved"] or \
                                  (not game_vars["user_moved"] and game_vars["player"].next_direction != config.DIR_NONE)

            if should_attempt_move:
                if not game_vars["user_moved"]:
                    game_vars["user_moved"] = True

                wall_set = game_vars["wall"].points_set
                collision_type = game_vars["player"].move(wall_set)

                if collision_type:
                    print(f"Game Over! Collision: {collision_type}")
                    game_vars["game_state"] = config.STATE_GAME_OVER
                    game_vars["collision_type"] = collision_type
                    if game_vars["speed_boost"] > 0:
                        game_vars["game_speed"] -= game_vars["speed_boost"]
                        game_vars["speed_boost"] = 0
                        game_vars["boost_timer"] = 0
                else:
                    player_set = set(game_vars["player"].points)
                    occupied_set = wall_set.union(player_set)
                    eaten, cost, add_speed = game_vars["food"].check_collision(
                        game_vars["player"].head, occupied_set
                    )

                    if eaten:
                        game_vars["player"].grow(1)
                        game_vars["score"] += cost


                        if add_speed > 0:
                            if game_vars["speed_boost"] > 0:
                                game_vars["game_speed"] -= game_vars["speed_boost"]
                            game_vars["speed_boost"] = add_speed
                            game_vars["boost_timer"] = add_speed * config.FOOD_SPEED_BOOST_DURATION_MULTIPLIER
                            game_vars["game_speed"] += add_speed
                            print(f"Speed boost! +{add_speed} for {game_vars['boost_timer']} ticks.")


                        if game_vars["score"] >= game_vars["score_needed"]:
                            if game_vars["level"] < config.MAX_LEVEL:
                                print(f"Level Up! Reached level {game_vars['level'] + 1}")
                                next_level = game_vars['level'] + 1
                                game_vars = reset_game_state(
                                    level=next_level,
                                    score=0,
                                    player_points_text=''
                                )
                                continue
                            else:
                                if game_vars["score_needed"] != config.INFINITE_LEVEL_SCORE_TARGET:
                                     print("Max level reached - infinite mode active.")
                                     game_vars["score_needed"] = config.INFINITE_LEVEL_SCORE_TARGET

                    player_set = set(game_vars["player"].points)
                    occupied_set = wall_set.union(player_set)
                    game_vars["food"].update_timers(occupied_set)

                    if game_vars["boost_timer"] > 0:
                        game_vars["boost_timer"] -= 1
                        if game_vars["boost_timer"] == 0:
                            print("Speed boost expired.")
                            game_vars["game_speed"] -= game_vars["speed_boost"]
                            game_vars["speed_boost"] = 0

        draw_ui(screen, game_vars["level"], game_vars["score"], game_vars["score_needed"])

        game_vars["wall"].draw(screen)
        game_vars["food"].draw(screen)
        game_vars["player"].draw(screen)

        if current_state == config.STATE_PAUSED:
            draw_text(screen, "Paused", pause_font, config.COLORS['blue'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 30))
            draw_text(screen, "Space - Resume", info_font, config.COLORS['blue'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 30))
            draw_text(screen, "Enter - Save & Exit?", info_font, config.COLORS['blue'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 70))

        elif current_state == config.STATE_EXIT_CONFIRM:
            draw_text(screen, "Save and Exit?", pause_font, config.COLORS['red'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 30))
            draw_text(screen, "Enter - Yes", info_font, config.COLORS['red'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 30))
            draw_text(screen, "Space - No (Resume)", info_font, config.COLORS['red'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 70))

        elif current_state == config.STATE_GAME_OVER:
            draw_text(screen, "You Lose!", lose_font, config.COLORS['red'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 - 40))
            draw_text(screen, "Enter - Restart Level", info_font, config.COLORS['red'],
                      (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 40))

        pygame.display.flip()
        clock.tick(game_vars["game_speed"])

    pygame.quit()
    print("Game exited.")
    sys.exit()

if __name__ == "__main__":
    user_name_input = input("Enter user name: ").strip()
    if not user_name_input:
        print("User name cannot be empty. Exiting.")
        sys.exit()

    user_profile = db_manager.find_user(user_name_input)
    if not user_profile:
        print(f"User '{user_name_input}' not found. Creating new profile.")
        if db_manager.create_new_user(user_name_input):
            user_profile = db_manager.find_user(user_name_input)
        else:
            print("Failed to create new user profile. Exiting.")
            sys.exit()

    game_loop(user_name_input, user_profile)