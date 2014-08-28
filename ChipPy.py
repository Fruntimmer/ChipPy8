__author__ = 'Laxl'
import pygame
import os.path
from chip8 import Chip8
pygame.init()

class Console():
    font = pygame.font.SysFont("monospace", 20)
    font.set_bold(1)
    token_counter = 0.0
    def __init__(self):
        self.is_active = True
        self.input_str = "LOAD PONG.CH8"
        self.input_token = "_"

    def draw(self, screen, width, height, dt):
        self.token_counter += dt
        if self.token_counter > 20:
            if self.input_token == "_":
                self.input_token = ""
            else:
                self.input_token = "_"
            self.token_counter = 0.0
        pygame.draw.rect(screen, (50, 70, 170), (0, height-40,width, 40), 0)
        label = self.font.render(">"+self.input_str+self.input_token, 1, (255,255,0))
        screen.blit(label, (20, height-30))

    def on_key_press(self, key):
        if key == pygame.K_RETURN:
            w = self.input_str.split()
            return self.read_console(w)
        else:
            try:
                self.input_str += chr(key).upper()
            except:
                pass
        if key == pygame.K_BACKSPACE:
            self.input_str = self.input_str[:len(self.input_str)-2]

    def read_console(self, w):
        try:
            cmd = w[0]
        except IndexError:
            self.is_active = False
            return None
        if cmd == "LOAD":
            rom_path = " ".join(w[1:])
            if os.path.isfile("roms/" + rom_path):
                self.input_str = ""
                self.is_active = False
                return w
            else:
                self.input_str = "ERROR FILE NOT FOUND"
        elif cmd == "RES":
            try:
                width = int(w[1])
                if width < 2:
                    raise ValueError
            except ValueError:
                self.input_str = "ERROR INVALID RESOLUTION"
                return None
            self.input_str = ""
            self.is_active = False
            return w
        elif cmd == "QUIT":
            return w
        elif cmd == "ERROR":
            self.input_str = ""
            return None
        else:
            self.input_str = "ERROR UNKNOWN COMMAND"
            return None

class Chippy8():
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.emu = Chip8()
        self.console = Console()
        self.screen = pygame.display.set_mode((width,height))
        self.run = True

    def draw(self, dt):
        self.screen.fill((0, 0, 0))
        self.emu.draw(self.screen, self.width, self.height)
        if self.console.is_active:
            self.console.draw(self.screen, self.width, self.height, dt)

    def update(self):
        self.emu.update()

    def on_key_press(self, event):
        if event.key == pygame.K_TAB:
            self.console.is_active = not self.console.is_active
        elif self.console.is_active:
            cmd = self.console.on_key_press(event.key)
            if cmd:
                if cmd[0] == "QUIT":
                    self.run = False
                elif cmd[0] == "LOAD":
                    self.emu.handle_load_cmd(cmd[1:])
                elif cmd[0] == "RES":
                    self.width = int(cmd[1])
                    self.height = self.width/2
                    self.screen = pygame.display.set_mode((self.width, self.height))
        else:
            self.emu.on_key_press(event.key)

    def on_key_release(self, event):
        self.emu.on_key_release(event.key)

    def loop(self):
        screen_timer = 0.0
        clock_timer = 0.0
        screen_timer = 0.0
        tick_last_frame = 0.0
        cpu_fudger = 0    # Extra miliseconds per tick
        while self.run:
            t = pygame.time.get_ticks()
            dt = t - tick_last_frame
            screen_timer += dt
            tick_last_frame = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                if event.type == pygame.KEYDOWN:
                    self.on_key_press(event)
                if event.type == pygame.KEYUP:
                    self.on_key_release(event)
            if cpu_fudger > 500:
                self.update()
                cpu_fudger = 0
            if screen_timer > 1.0/60*1000 and self.emu.draw_flag:
                self.draw(dt)
                screen_timer = 0.0
                pygame.display.flip()
            cpu_fudger += 1
            pygame.event.pump()

chippy = Chippy8(1280, 640)
chippy.loop()

