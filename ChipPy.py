__author__ = 'Laxl'
import pygame
import os.path
import pyglet
import pygame
pygame.init()
from chip8 import Chip8

class Console():
    #arial = pyglet.font.load('monospace', 14, bold=True, italic=False)
    token_counter = 0.0
    def __init__(self):
        self.is_active = True
        self.input_str = "LOAD PONG.CH8"
        self.input_token = "_"

    def increment_counter(self, dt):
        self.token_counter += dt

    def draw(self, width, height):
        if self.token_counter > .4:
            if self.input_token == "_":
                self.input_token = ""
            else:
                self.input_token = "_"
            self.token_counter = 0.0
        #pygame.draw.rect(screen, (50, 70, 170), (0, height-40,width, 40), 0)
        #label = self.font.render(">"+self.input_str+self.input_token, 1, (255,255,0))
        # label = pyglet.text.Label(str(">"+self.input_str+self.input_token), font_name='Times New Roman', font_size='20',
        #                           anchor_x='left', anchor_y='bottom')
        label = pyglet.text.Label(">"+self.input_str+self.input_token,
                          font_name='monospace',
                          font_size=36,
                          x=20, y=20,
                          anchor_x='left', anchor_y='bottom')
        #screen.blit(label, (20, height-30))
        label.draw()

    def on_key_press(self, key):
        if key == pyglet.window.key.ENTER:
            w = self.input_str.split()
            return self.read_console(w)
        else:
            try:
                self.input_str += chr(key).upper()
            except:
                pass
        if key == pyglet.window.key.BACKSPACE:
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


class Chippy8(pyglet.window.Window):
    cpu_fudger = 0    # Extra miliseconds per tick
    screen_timer = 0.0
    def __init__(self, *args, **kwargs):
        super(Chippy8, self).__init__(*args, **kwargs)
        self.emu = Chip8(self.width, self.height)
        self.console = Console()
        self.run = True

    def on_draw(self):
        if self.emu.draw_flag and self.screen_timer >1.0/30:
            self.clear()
            self.emu.draw(self.width, self.height)
            self.screen_timer = 0.0
        if self.console.is_active:
            self.console.draw(self.width, self.height)

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.TAB:
            self.console.is_active = not self.console.is_active
        elif self.console.is_active:
            cmd = self.console.on_key_press(symbol)
            if cmd:
                if cmd[0] == "QUIT":
                    self.run = False
                elif cmd[0] == "LOAD":
                    #self.emu.handle_load_cmd(cmd[1:])
                    pass
                elif cmd[0] == "RES":
                    self.width = int(cmd[1])
                    self.height = self.width/2
                    self.screen = pygame.display.set_mode((self.width, self.height))
        else:
            self.emu.on_key_press(symbol)

    def on_key_release(self, symbol, mmodifiers):
        self.emu.on_key_release(symbol)

    def update(self, dt):
        self.screen_timer += dt
        self.console.increment_counter(dt)
        self.emu.update()
        self.cpu_fudger = 0
        self.cpu_fudger += 1

chippy = Chippy8(1280, 640)
pyglet.clock.schedule(chippy.update)
pyglet.app.run()
