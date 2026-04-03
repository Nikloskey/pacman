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
        curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_BLUE)    # Scared Ghost

        # Find start position for Pacman and count dots
        self.pacman_y, self.pacman_x = 23, 13
        self.pacman_dir = curses.KEY_RIGHT
        self.next_dir = curses.KEY_RIGHT

        self.score = 0
        self.total_dots = sum(row.count('.') + row.count('o') for row in self.map)

        # Characters
        self.char_wall = '█'
        self.char_dot = '·'
        self.char_pellet = '●'
        self.char_pacman = 'C'

        # Ghosts
        self.ghosts = [
            {'y': 11, 'x': 13, 'color': 4, 'char': 'ᗣ', 'dir': curses.KEY_UP},
            {'y': 14, 'x': 11, 'color': 5, 'char': 'ᗣ', 'dir': curses.KEY_UP},
            {'y': 14, 'x': 13, 'color': 6, 'char': 'ᗣ', 'dir': curses.KEY_UP},
            {'y': 14, 'x': 15, 'color': 7, 'char': 'ᗣ', 'dir': curses.KEY_UP},
        ]

        self.running = True
        self.game_over = False
        self.win = False

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
            self.stdscr.addstr(g['y'], g['x'] * 2, f" {g['char']}", curses.color_pair(g['color']))

        # Draw pacman
        pac_char = 'C'
        if self.pacman_dir == curses.KEY_LEFT: pac_char = ')'
        elif self.pacman_dir == curses.KEY_RIGHT: pac_char = 'C'
        elif self.pacman_dir == curses.KEY_UP: pac_char = 'V'
        elif self.pacman_dir == curses.KEY_DOWN: pac_char = '^'

        # Animate mouth
        if int(time.time() * 4) % 2 == 0:
            pac_char = 'O'

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
            # Power pellet logic could go here

        if self.total_dots == 0:
            self.win = True
            self.game_over = True

    def move_ghosts(self):
        for g in self.ghosts:
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
                self.game_over = True

        # Check collision again after all ghosts have moved, to prevent pass-through
        for g in self.ghosts:
            if g['y'] == self.pacman_y and g['x'] == self.pacman_x:
                self.game_over = True

    def loop(self):
        while self.running:
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
                self.stdscr.refresh()
                time.sleep(3)
                break

            # Update
            self.move_pacman()
            self.move_ghosts()

            # Render
            self.stdscr.erase()
            self.draw_map()
            self.draw_entities()

            # Draw score
            self.stdscr.addstr(self.height, 0, f"Score: {self.score}  Dots left: {self.total_dots}", curses.color_pair(2))

            self.stdscr.refresh()

            # time.sleep is handled by stdscr.timeout()

def main(stdscr):
    game = PacmanGame(stdscr)
    game.loop()

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
