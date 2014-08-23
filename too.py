from pyglet import font
from pyglet import window
from pyglet import image
from pyglet import graphics
from pyglet.window import key
import random


class Hello(window.Window):

    ft = font.load('Arial', 36)
    text = font.Text(ft, 'Hello, World!')
    pixel = image.load('pix.png')
    screen = [[0 for y in range(32)] for x in range(64)]
    screen[0][0] = 1
    screen[63][31] = 1
    screen[63][0] = 1
    screen[0][31] = 1
    draw_flag = True
    counter = 0
    def draw(self):
        graphics.glColor3f(1, 1, 1)
        for x in range (0, len(self.screen)):
            for y in range(0, len(self.screen[x])):
                if self.screen[x][y] == 1:
                    side = self.width/64
                    v = [side*x, self.height - side*y,
                         side*x, self.height -(side*y+side),
                         side*x+side, self.height -(side*y+side),
                         side*x+side, self.height-side*y
                    ]
                    graphics.draw(4, graphics.gl.GL_QUADS, ('v2i', (v[0],v[1], v[2],v[3], v[4],v[5], v[6],v[7])))
                    #self.pixel.blit(x * 10, y * 10)
                    pass

    def on_key_press(self, symbol, modifiers):  # overrides Window.on_key_press
        if symbol == key.SPACE:
            self.screen[random.randint(0,63)][random.randint(0,31)] = 1
            self.draw_flag = True

    def main(self):
        while not self.has_exit:
            self.dispatch_events() # THIS IS IMPORTANT. your application will hang if this is not called.
            if self.draw_flag:
                self.clear()
                self.draw()
                self.flip()

                self.counter = 100
                self.draw_flag = False
            self.counter -= 1
            if self.counter == 0:
                self.draw_flag == True



h = Hello(1280,640)
h.main()
