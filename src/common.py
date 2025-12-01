from abc import abstractmethod, ABC

import pygame
from dataclasses import dataclass
from enum import Enum, auto

MOVE_TIME = 1.0
GRID_SIZE = 80
GRID_WIDTH = 8
GRID_HEIGHT = 8
LINE_WIDTH = 5
LINE_COLOUR = (75, 75, 75)

class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

def lerp(a, b, t):
    return a + (b - a) * t

class Drawable(pygame.sprite.Sprite):
    def __init__(self, x_pos, y_pos, texture):
        super().__init__()
        self.__x = x_pos
        self.__y = y_pos
        self.__next_x = self.__x
        self.__next_y = self.__y
        self.__timer = 0
        img = pygame.image.load(texture).convert_alpha()
        self.__img = pygame.transform.scale(img, (GRID_SIZE, GRID_SIZE))

    def move_to(self, x_pos, y_pos):
        next_x = x_pos
        next_y = y_pos

        updated = False
        if next_x != self.__next_x:
            self.__x = self.__next_x
            self.__next_x = next_x
            updated = True

        if next_y != self.__next_y:
            self.__y = self.__next_y
            self.__next_y = next_y
            updated = True

        if updated:
            self.__timer = MOVE_TIME

    def move_by(self, x_amount, y_amount):
        self.move_to(self.__next_x + x_amount, self.__next_y + y_amount)

    def get_position(self):
        return lerp(self.__next_x, self.__x, self.__timer / MOVE_TIME), lerp(self.__next_y, self.__y, self.__timer / MOVE_TIME)

    def advance_timer(self, delta_time):
        self.__timer = self.__timer - delta_time
        if self.__timer < 0:
            self.__timer = 0
            self.__x = self.__next_x
            self.__y = self.__next_y

    def get_x(self):
        return self.__next_x

    def get_y(self):
        return self.__next_y

    def render(self, delta_time):
        x, y = self.get_position()
        self.advance_timer(delta_time)
        pygame.display.get_surface().blit(self.__img, (x * GRID_SIZE, y * GRID_SIZE))

class Santa(Drawable):
    def __init__(self, x_pos, y_pos, name):
        super().__init__(x_pos, y_pos, "../res/santa.png")
        self.name = name
        self.score = 0
        font_name = pygame.font.get_default_font()
        font = pygame.font.Font(font_name, int(GRID_SIZE * 0.3125))
        self.__text = font.render(name, True, (0, 0, 0))

    def __can_move(self, x, y):
        if not (0 <= self.get_x() + x < GRID_WIDTH):
            return False

        if not (0 <= self.get_y() + y < GRID_HEIGHT):
            return False

        return True

    def move(self, direction):
        if direction == Direction.UP:
            vector = (0, -1)
        elif direction == Direction.RIGHT:
            vector = (1, 0)
        elif direction == Direction.DOWN:
            vector = (0, 1)
        elif direction == Direction.LEFT:
            vector = (-1, 0)
        else:
            vector = (0, 0)

        if self.__can_move(*vector):
            self.move_by(*vector)

    def render(self, delta_time):
        x, y = self.get_position()
        super().render(delta_time)
        pygame.display.get_surface().blit(self.__text, (
            x * GRID_SIZE + GRID_SIZE // 2 - self.__text.get_rect().width // 2,
            y * GRID_SIZE + GRID_SIZE + 1
        ))

@dataclass
class SantaID:
    ip: str
    name: str

class Gift(Drawable):
    def __init__(self, x_pos, y_pos):
        super().__init__(x_pos, y_pos, "../res/gift.png")

# shoutout to ChatGPT
class Button:
    def __init__(self, x, y, w, h, text, font, bg, fg):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.bg = bg      # background colour
        self.fg = fg      # text colour
        self.hover = False

    def draw(self, surf):
        # Change color if hovering
        color = tuple(min(255, c + 40) for c in self.bg) if self.hover else self.bg
        pygame.draw.rect(surf, color, self.rect, border_radius=6)

        # Draw text
        text_surf = self.font.render(self.text, True, self.fg)
        surf.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def update(self, events):
        # Update hover state
        self.hover = self.rect.collidepoint(pygame.mouse.get_pos())

        # Check for click
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.hover:
                    return True   # button was clicked
        return False

class GameMode(Enum):
    WAITING = auto()
    PLAYING = auto()
    FINISHED = auto()

@dataclass
class GameState:
    santas: dict[str, Santa]
    gifts: list[Gift]
    game_mode: GameMode = GameMode.WAITING

class Game(ABC):
    @abstractmethod
    def get_santa_ids(self) -> list[SantaID]:
        pass

    @abstractmethod
    def request_santas(self) -> None:
        pass

    @abstractmethod
    def received_santas(self) -> bool:
        pass

    @abstractmethod
    def get_santas(self) -> list[Direction]:
        pass

    @abstractmethod
    def start_server(self):
        pass

    @abstractmethod
    def lock_server(self):
        pass

    @abstractmethod
    def stop_server(self):
        pass

    @abstractmethod
    def get_server_ip(self) -> str:
        pass

    def __init__(self):
        window_width = GRID_WIDTH * GRID_SIZE
        window_height = GRID_HEIGHT * GRID_SIZE

        pygame.display.init()
        pygame.font.init()
        pygame.display.set_mode((window_width, window_height))

        self.__game_state = GameState(dict(), [Gift(3, 3)], GameMode.WAITING)
        self.__font = pygame.font.Font(pygame.font.get_default_font(), 25)
        self.__big_font = pygame.font.Font(pygame.font.get_default_font(), 40)

        self.__clock = pygame.time.Clock()
        self.__running = False
        self.__last_turn_ms = pygame.time.get_ticks()
        self.__awaiting_santas = False
        self.__start_button = Button(GRID_SIZE, (GRID_HEIGHT - 2) * GRID_SIZE, GRID_SIZE * 3, GRID_SIZE, "START", self.__big_font, (0, 200, 0), (255, 255, 255))

        background_tile_img = pygame.image.load("../res/snow.png").convert()
        background_tile = pygame.transform.scale(background_tile_img, (GRID_SIZE, GRID_SIZE))
        self.__background = pygame.surface.Surface((window_width, window_height))
        self.__grid = pygame.surface.Surface((window_width, window_height), pygame.SRCALPHA)
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                self.__background.blit(background_tile, (x * GRID_SIZE, y * GRID_SIZE))

        for x in range(1, GRID_WIDTH):
            pygame.draw.line(self.__grid, LINE_COLOUR, (x * GRID_SIZE, 0), (x * GRID_SIZE, window_height), LINE_WIDTH)

        for y in range(1, GRID_HEIGHT):
            pygame.draw.line(self.__grid, LINE_COLOUR, (0, y * GRID_SIZE), (window_width, y * GRID_SIZE), LINE_WIDTH)

    def get_gifts(self) -> list[tuple[int, int]]:
        return [(g.get_x(), g.get_y()) for g in self.__game_state.gifts]

    def get_santa_position(self, ip) -> tuple[int, int]:
        santa = self.__game_state.santas[ip]
        return santa.get_x(), santa.get_y()

    def run(self):
        self.__running = True
        self.start_server()
        while self.__running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.__running = False

            delta_time = self.__clock.tick(60) / 1000.0

            self.update(events)
            self.render(delta_time)

    def __update_waiting(self, events):
        # add any new santas
        santa_ids = self.get_santa_ids()
        for santa_id in santa_ids:
            if santa_id.ip not in self.__game_state.santas.keys():
                self.__game_state.santas[santa_id.ip] = Santa(0, 0, santa_id.name)

        # remove any santas that are no longer with us D:
        santa_ids = self.__game_state.santas.keys()
        for santa_id in santa_ids:
            if santa_id not in santa_ids:
                self.__game_state.santas.pop(santa_id)

        if self.__start_button.update(events):
            self.lock_server()
            self.__game_state.game_mode = GameMode.PLAYING

    def __update_playing(self):
        if self.__last_turn_ms + MOVE_TIME * 1000 < pygame.time.get_ticks() and not self.__awaiting_santas:
            remove_gifts = list()
            for santa in self.__game_state.santas.values():
                for i, gift in enumerate(self.__game_state.gifts):
                    if santa.get_x() == gift.get_x() and santa.get_y() == gift.get_y():
                        remove_gifts.append(i)
                        santa.score += 1

            for remove_gift in remove_gifts:
                self.__game_state.gifts.pop(remove_gift)

            if len(self.__game_state.gifts) <= 0:
                self.stop_server()
                self.__game_state.game_mode = GameMode.FINISHED
            else:
                self.request_santas()
                self.__awaiting_santas = True

        if self.__awaiting_santas and self.received_santas():
            # hopefully this never happens but just in case
            directions = self.get_santas()
            if len(directions) > len(self.__game_state.santas):
                directions = directions[:len(self.__game_state.santas)]
            for ip, direction in directions:
                self.__game_state.santas[ip].move(direction)

            self.__awaiting_santas = False
            self.__last_turn_ms = pygame.time.get_ticks()

    def update(self, events):
        if self.__game_state.game_mode == GameMode.WAITING:
            self.__update_waiting(events)
        elif self.__game_state.game_mode == GameMode.PLAYING:
            self.__update_playing()

    def render(self, delta_time):
        pygame.display.get_surface().blit(self.__background, (0, 0))

        if self.__game_state.game_mode == GameMode.WAITING:
            title =  self.__big_font.render("Waiting for players:", True, (0, 0, 0))
            pygame.display.get_surface().blit(title, (GRID_SIZE, GRID_SIZE))

            server_ip = self.__font.render(f"Server IP: {self.get_server_ip()}", True, (0, 0, 0))
            pygame.display.get_surface().blit(server_ip, (GRID_SIZE, int(2 * GRID_SIZE)))

            y = 3 * GRID_SIZE
            for santa in self.__game_state.santas.values():
                text = self.__font.render(santa.name, True, (0, 0, 0))
                pygame.display.get_surface().blit(text, (int(1.5 * GRID_SIZE), y))
                y += int(text.get_rect().height * 1.5)

            y += GRID_SIZE // 2

            self.__start_button.draw(pygame.display.get_surface())
        elif self.__game_state.game_mode == GameMode.PLAYING:
            pygame.display.get_surface().blit(self.__grid, (0, 0))

            for gift in self.__game_state.gifts:
                gift.render(delta_time)

            for santa in self.__game_state.santas.values():
                santa.render(delta_time)
        elif self.__game_state.game_mode == GameMode.FINISHED:
            title =  self.__big_font.render("Game Over!", True, (0, 0, 0))
            pygame.display.get_surface().blit(title, (GRID_SIZE, GRID_SIZE))

            y = 2 * GRID_SIZE
            santa_scores = [(santa.name, santa.score) for santa in self.__game_state.santas.values()]
            santa_scores.sort(key=lambda item: item[1])
            for name, score in santa_scores:
                text = self.__font.render(f"{name}: {score}", True, (0, 0, 0))
                pygame.display.get_surface().blit(text, (int(1.5 * GRID_SIZE), y))
                y += int(text.get_rect().height * 1.5)
        pygame.display.flip()
