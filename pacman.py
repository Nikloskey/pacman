import curses
import time
import random

# The classic Pacman map (simplified)
MAP = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###--### ##.#     ",
    "######.## #      # ##.######",
    "      .   #      #   .      ",
    "######.## #      # ##.######",
    "     #.## ######## ##.#     ",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#o..##.......  .......##..o#",
    "###.##.##.########.##.##.###",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################"
]

class PacmanGame:
    def __init__(self, stdscr):
        self.stdscr = stdscr

        # Check minimum terminal size
        max_y, max_x = self.stdscr.getmaxyx()
        self.map = [list(row) for row in MAP]
        self.height = len(self.map)
        self.width = len(self.map[0])

        if max_y < self.height + 2 or max_x < self.width * 2 + 1:
            curses.endwin()
            print(f"Terminal too small. Please resize to at least {self.width * 2 + 1}x{self.height + 2}")
            exit(1)

        curses.curs_set(0) # Hide cursor
        self.stdscr.nodelay(1) # Non-blocking input
        self.stdscr.timeout(100) # 100ms timeout for getch()

        # Initialize colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Walls
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Dots
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Pacman
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # Blinky
        curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)   # Inky
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)# Pinky
        curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Clyde
        curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_BLACK)    # Scared Ghost

        # Find start position for Pacman and count dots
        self.pacman_start_y, self.pacman_start_x = 23, 13
        self.pacman_y, self.pacman_x = self.pacman_start_y, self.pacman_start_x
        self.pacman_dir = curses.KEY_RIGHT
        self.next_dir = curses.KEY_RIGHT

        self.score = 0
        self.lives = 3
        self.level = 1
        self.total_dots = sum(row.count('.') + row.count('o') for row in self.map)
        self.scared_timer = 0

        # Characters (Optimized for JetBrains Mono / Nerd Fonts)
        self.char_wall = '█'
        self.char_dot = '·'
        self.char_pellet = '●'
        self.char_pacman = '󰊠' # Nerd font pacman icon

        # Ghosts (store start position for resets)
        self.ghosts = [
            {'y': 11, 'x': 13, 'start_y': 11, 'start_x': 13, 'color': 4, 'char': '󰊢', 'dir': curses.KEY_UP, 'scared': False},
            {'y': 14, 'x': 11, 'start_y': 14, 'start_x': 11, 'color': 5, 'char': '󰊢', 'dir': curses.KEY_UP, 'scared': False},
            {'y': 14, 'x': 13, 'start_y': 14, 'start_x': 13, 'color': 6, 'char': '󰊢', 'dir': curses.KEY_UP, 'scared': False},
            {'y': 14, 'x': 15, 'start_y': 14, 'start_x': 15, 'color': 7, 'char': '󰊢', 'dir': curses.KEY_UP, 'scared': False},
        ]

        self.running = True
        self.game_over = False
        self.win = False
        self.frame_count = 0

    def draw_map(self):
        for y in range(self.height):
            for x in range(self.width):
                char = self.map[y][x]
                if char == '#':
                    self.stdscr.addstr(y, x * 2, self.char_wall * 2, curses.color_pair(1))
                elif char == '.':
                    self.stdscr.addstr(y, x * 2, f" {self.char_dot}", curses.color_pair(2))
                elif char == 'o':
                    self.stdscr.addstr(y, x * 2, f" {self.char_pellet}", curses.color_pair(2))
                elif char == '-':
                    self.stdscr.addstr(y, x * 2, '--', curses.color_pair(2))
                else:
                    self.stdscr.addstr(y, x * 2, '  ')

    def draw_entities(self):
        # Draw ghosts
        for g in self.ghosts:
            color = 8 if g['scared'] else g['color']
            self.stdscr.addstr(g['y'], g['x'] * 2, f" {g['char']}", curses.color_pair(color))

        # Draw pacman
        # Just use the single icon for now, animations can be tricky with specific font glyphs
        pac_char = self.char_pacman

        self.stdscr.addstr(self.pacman_y, self.pacman_x * 2, f" {pac_char}", curses.color_pair(3))

    def move_pacman(self):
        dy, dx = 0, 0
        if self.next_dir == curses.KEY_UP: dy = -1
        elif self.next_dir == curses.KEY_DOWN: dy = 1
        elif self.next_dir == curses.KEY_LEFT: dx = -1
        elif self.next_dir == curses.KEY_RIGHT: dx = 1

        # Check if next_dir is valid
        ny, nx = self.pacman_y + dy, self.pacman_x + dx

        # Tunnel
        if nx < 0: nx = self.width - 1
        elif nx >= self.width: nx = 0

        if self.map[ny][nx] not in ['#', '-']:
            self.pacman_dir = self.next_dir
        else:
            # Keep moving in current direction if next_dir is blocked
            dy, dx = 0, 0
            if self.pacman_dir == curses.KEY_UP: dy = -1
            elif self.pacman_dir == curses.KEY_DOWN: dy = 1
            elif self.pacman_dir == curses.KEY_LEFT: dx = -1
            elif self.pacman_dir == curses.KEY_RIGHT: dx = 1
            ny, nx = self.pacman_y + dy, self.pacman_x + dx

            if nx < 0: nx = self.width - 1
            elif nx >= self.width: nx = 0

            if self.map[ny][nx] in ['#', '-']:
                return # Blocked

        self.pacman_y, self.pacman_x = ny, nx

        # Eat dots
        if self.map[self.pacman_y][self.pacman_x] == '.':
            self.map[self.pacman_y][self.pacman_x] = ' '
            self.score += 10
            self.total_dots -= 1
        elif self.map[self.pacman_y][self.pacman_x] == 'o':
            self.map[self.pacman_y][self.pacman_x] = ' '
            self.score += 50
            self.total_dots -= 1
            self.scared_timer = 50 # About 5 seconds at 10fps
            for g in self.ghosts:
                g['scared'] = True

        if self.total_dots == 0:
            self.level_up()

    def move_ghosts(self):
        for g in self.ghosts:
            if g['scared'] and self.frame_count % 2 == 0:
                # Scared ghosts move at half speed
                pass
            else:
                possible_moves = []
                for d in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                    dy, dx = 0, 0
                    if d == curses.KEY_UP: dy = -1
                    elif d == curses.KEY_DOWN: dy = 1
                    elif d == curses.KEY_LEFT: dx = -1
                    elif d == curses.KEY_RIGHT: dx = 1

                    ny, nx = g['y'] + dy, g['x'] + dx

                    # Tunnel
                    if nx < 0: nx = self.width - 1
                    elif nx >= self.width: nx = 0

                    if self.map[ny][nx] != '#':
                        # Prevent instant reverse unless stuck
                        reverse_dir = {
                            curses.KEY_UP: curses.KEY_DOWN,
                            curses.KEY_DOWN: curses.KEY_UP,
                            curses.KEY_LEFT: curses.KEY_RIGHT,
                            curses.KEY_RIGHT: curses.KEY_LEFT
                        }.get(g['dir'])

                        if d != reverse_dir:
                            possible_moves.append((d, ny, nx))

                if not possible_moves:
                    # If stuck, allow reverse
                    dy, dx = 0, 0
                    reverse_dir = {
                        curses.KEY_UP: curses.KEY_DOWN,
                        curses.KEY_DOWN: curses.KEY_UP,
                        curses.KEY_LEFT: curses.KEY_RIGHT,
                        curses.KEY_RIGHT: curses.KEY_LEFT
                    }.get(g['dir'])

                    if reverse_dir == curses.KEY_UP: dy = -1
                    elif reverse_dir == curses.KEY_DOWN: dy = 1
                    elif reverse_dir == curses.KEY_LEFT: dx = -1
                    elif reverse_dir == curses.KEY_RIGHT: dx = 1

                    ny, nx = g['y'] + dy, g['x'] + dx
                    if self.map[ny][nx] != '#':
                        g['dir'] = reverse_dir
                        g['y'], g['x'] = ny, nx
                else:
                    # Simple AI: just pick a random valid move
                    move = random.choice(possible_moves)
                    g['dir'] = move[0]
                    g['y'], g['x'] = move[1], move[2]

            # Collision check
            if g['y'] == self.pacman_y and g['x'] == self.pacman_x:
                if g['scared']:
                    self.score += 200
                    g['y'], g['x'] = g['start_y'], g['start_x']
                    g['scared'] = False
                else:
                    self.handle_death()
                    break # Break out of ghost loop if handled death

        if not self.game_over:
            # Check collision again after all ghosts have moved, to prevent pass-through
            for g in self.ghosts:
                if g['y'] == self.pacman_y and g['x'] == self.pacman_x:
                    if g['scared']:
                        self.score += 200
                        g['y'], g['x'] = g['start_y'], g['start_x']
                        g['scared'] = False
                    else:
                        self.handle_death()
                        break

    def level_up(self):
        self.level += 1
        self.map = [list(row) for row in MAP]
        self.total_dots = sum(row.count('.') + row.count('o') for row in self.map)
        # Increase speed/difficulty
        new_timeout = max(30, 100 - (self.level - 1) * 10)
        self.stdscr.timeout(new_timeout)
        self.reset_positions()

    def reset_positions(self):
        self.pacman_y, self.pacman_x = self.pacman_start_y, self.pacman_start_x
        self.pacman_dir = curses.KEY_RIGHT
        self.next_dir = curses.KEY_RIGHT
        for g in self.ghosts:
            g['y'], g['x'] = g['start_y'], g['start_x']
            g['dir'] = curses.KEY_UP
            g['scared'] = False
        self.scared_timer = 0
        # brief pause before resuming
        self.stdscr.erase()
        self.draw_map()
        self.draw_entities()
        self.stdscr.addstr(self.height, 0, f"Level: {self.level}  Score: {self.score}  Dots left: {self.total_dots}  Lives: {self.lives}", curses.color_pair(2))
        self.stdscr.addstr(self.height // 2, (self.width * 2 - 5) // 2, "READY", curses.color_pair(3))
        self.stdscr.refresh()
        time.sleep(2)

    def handle_death(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self.reset_positions()

    def loop(self):
        # Initial Ready pause
        self.stdscr.erase()
        self.draw_map()
        self.draw_entities()
        self.stdscr.addstr(self.height, 0, f"Level: {self.level}  Score: {self.score}  Dots left: {self.total_dots}  Lives: {self.lives}", curses.color_pair(2))
        self.stdscr.addstr(self.height // 2, (self.width * 2 - 5) // 2, "READY", curses.color_pair(3))
        self.stdscr.refresh()
        time.sleep(2)

        while self.running:
            self.frame_count += 1
            if self.scared_timer > 0:
                self.scared_timer -= 1
                if self.scared_timer == 0:
                    for g in self.ghosts:
                        g['scared'] = False

            # Handle input
            ch = self.stdscr.getch()
            if ch == ord('q'):
                self.running = False
            elif ch in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                self.next_dir = ch

            if self.game_over:
                self.stdscr.clear()
                msg = "YOU WIN!" if self.win else "GAME OVER!"
                self.stdscr.addstr(self.height // 2, (self.width * 2 - len(msg)) // 2, msg, curses.color_pair(3))
                self.stdscr.addstr(self.height // 2 + 1, (self.width * 2 - 20) // 2, f"Score: {self.score}", curses.color_pair(2))
                self.stdscr.addstr(self.height // 2 + 2, (self.width * 2 - 30) // 2, "Press 'R' to Restart or 'Q' to Quit", curses.color_pair(2))
                self.stdscr.refresh()

                # Wait for user input to restart or quit
                self.stdscr.nodelay(0) # Blocking input for end screen
                while True:
                    ch_end = self.stdscr.getch()
                    if ch_end in [ord('q'), ord('Q')]:
                        self.running = False
                        break
                    elif ch_end in [ord('r'), ord('R')]:
                        return True # Return True to indicate restart
                break

            if ch in [ord('r'), ord('R')]:
                return True # Restart from middle of game

            # Update
            self.move_pacman()
            self.move_ghosts()

            # Render
            self.stdscr.erase()
            self.draw_map()
            self.draw_entities()

            # Draw score
            self.stdscr.addstr(self.height, 0, f"Level: {self.level}  Score: {self.score}  Dots left: {self.total_dots}  Lives: {self.lives}", curses.color_pair(2))

            self.stdscr.refresh()

            # time.sleep is handled by stdscr.timeout()

def main(stdscr):
    while True:
        game = PacmanGame(stdscr)
        restart = game.loop()
        if not restart:
            break

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
