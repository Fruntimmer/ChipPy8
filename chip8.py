from pyglet.text.layout import _AbstractBox

__author__ = 'Laxl'
import random
from pyglet import font
from pyglet import window
from pyglet import graphics
from pyglet.window import key


def log(str):
    if debug:
        print str

debug = True

class Chip8(window.Window):
    step_instruction = False
    step = False
    step_key = key.RIGHT

    one_print = True
    #Input map, each valid key is given the address to the keyvalue in input buffer
    keypad = {key.NUM_1: 0x0,  # key 1
              key.NUM_2: 0x1,  # key 2
              key.NUM_3: 0x2,  # key 3
              key.NUM_4: 0x3,  # key 4
              key.NUM_5: 0x4,  # key 5
              key.NUM_6: 0x5,  # key 6
              key.NUM_7: 0x6,  # key 7
              key.NUM_8: 0x7,  # key 8
              key.NUM_9: 0x8,  # key 9
              key.A:     0xA,  # key A
              key.B:     0xB,  # key B
              key.C:     0xC,  # key C
              key.D:     0xD,  # key D
              key.E:     0xE,  # key E
              key.F:     0xF,  # key F
              }
    input_buffer = [0] * 16

    #5 8-bit values make up one character. I copied this because I'm lazy. Check properly.
    fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
             0x20, 0x60, 0x20, 0x20, 0x70,  # 1
             0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
             0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
             0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
             0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
             0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
             0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
             0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
             0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
             0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
             0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
             0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
             0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
             0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
             0xF0, 0x80, 0xF0, 0x80, 0x80   # F
             ]
    memory = None                           # 4096 (0x1000) memory locations, all of which are 8 bits
    v = [0] * 16                            # the 16 8-bit V-registers
    stack = []                              # the 16 8-bit stack-registers, not sure this actually is 16 8-bits. Check.
    i = None                                # The address register is 16 bits wide and is used with several opcodes that
                                            # involve memory operations /wiki
    pc = None                               # 16-bit program counter
    delay_timer, sound_timer = 0, 0         # CHIP-8 has two timers. They both count down at 60 hertz.
    instr = None                            # Contains the 16-bit instruction to be read and executed
    draw_flag = False                       # Indicate if screen should be redrawn
    wait_input = False                      # Indicate if program should wait for input

    def __init__(self,*args, **kwargs):
        super(Chip8, self).__init__(*args, **kwargs)
        #self.set_size(1080, 640)
        self.display_buffer = [[0 for y in range(32)] for x in range(64)]
        self.op_map = {0x0000: self._00nn,          # 0000 RET and CLS bot have opcode most significant bit 0
                       0x1000: self._0nnn,       # 1nnn jump to address nnn
                       0x2000: self._2nnn,           # 2nnn call subroutine at address nnn
                       0x3000: self._3xkk,    # 3xkk skip next instruction if Vx = kk
                       0x4000: self._4xll,   # 4xkk skip next instruction if Vx != kk
                       0x5000: self._5xy0,     # 5xy0 skip if Vx = Vy. Compare two registers
                       0x6000: self._6xkk,       # 6xkk SET Vx = kk
                       0x7000: self._7xkk,            # 7xkk ADD Vx, byte. Vx = Vx + kk
                       0x8000: self._8xy0,          # 8xy0 set Vx = Vy
                       0x9000: self._9xy0,    # 9xy0 - SNE Vx, Vy
                       0xA000: self._Annn,          # Annn - LD I, addr
                       0xB000: self._Bnnn,    # Bnnn - JP V0, addr
                       0xC000: self._cxkk,  # Cxkk - RND Vx, byte
                       0xD000: self._dxyn,          # Dxyn - DRW Vx, Vy, nibble
                       0xF000: self._fxnn,          # Branch out from all F opcodes
                       0xE000: self._exnn,          # Branch out from all E opcodes
                       }

    def _00nn(self):
        nn_type = self.instr & 0x00FF
        if nn_type == 0xE0:
            self.clear_screen()
        elif nn_type == 0xEE:
            self.pc = self.stack.pop()
            log("RET")
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _0nnn(self):
        #Jump to address contained in the 3 rightmost nibbles of instruction
        self.pc = self.instr & 0x0FFF
        log("jumping to address: " + str(hex(self.instr&0x0FFF)))

    def _2nnn(self): # Call nnn
        #push ret address to stack
        self.stack.append(self.pc)
        #Then jump to new location
        self.pc = self.instr & 0x0FFF
        log("CALL to address" + str(hex(self.instr&0x0FFF)))

    def _3xkk(self):
        # 3xkk: if Vx equals kk skip next instruction
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        if self.v[x] == kk:
            log("Vx = kk is True")
            self.pc += 2
        else:
            log("V = kk is False")

    def _4xll(self):
        # 4xkk skip next instruction if Vx != kk
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        if self.v[x] != kk:
            log("Vx != kk is True")
            self.pc += 2
        else:
            log("V != kk is False")

    def _5xy0(self):
        # 5xy0 skip if Vx = Vy. Compare two registers
        x = (self.instr & 0x0F00) >> 8
        y = (self.instr & 0x00F0) >> 4
        if self.v[x] == self.v[y]:
            log("Vx = Vy is True")
            self.pc += 2
        else:
            log("Vx = Vy is False")

    def _6xkk(self):
        # 6xkk SET Vx = kk
        x = (self.instr & 0x0F00) >> 8
        self.v[x] = self.instr & 0x00FF
        log("6xkk: Set Vx to kk.\nvX = "+ str(self.v[x]) +", kk =  " + str(self.instr & 0x00FF))

    def _7xkk(self):
        # 7xkk ADD Vx, byte. Vx = Vx + kk
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        self.v[x] += kk
        log("ADD")

    def _8xy0(self):
        set_type = self.instr & 0x000F
        x = (self.instr & 0x0F00) >> 8
        y = (self.instr & 0x00F0) >> 4
        if set_type == 0:
            # 8xy0 Set Vx = Vy.
            self.v[x] = self.v[y]
            self.v[x] &= 0xff
            log("8xy0: Set V" + str(x) + " to V" + str(y))

        elif set_type == 1:
            # 8xy1 SET Vx BITWISE OR Vy
            self.v[x] |= self.v[y]
            self.v[x] &= 0xff
            log("8xy1: Vx |= Vy")
        elif set_type == 2:
            # 8xy2 SET Vx BITWISE AND Vy
            self.v[x] &= self.v[y]
            self.v[x] &= 0xff
            log("8xy2: Vx &= Vy")
        elif set_type == 3:
            # 8xy3 SET Vx BITWISE XOR Vy
            self.v[x] ^= self.v[y]
            self.v[x] &= 0xff
            log("8xy3: Vx ^= Vy")
        elif set_type == 4:
            # 8xy4 SET Vx = Vx + Vy
            self.v[x] += self.v[y]
            if self.v[x] > 0xff:
                self.v[0xF] = 1
                self.v[x] &= 0xff
            else:
                self.v[0xF] = 0  # Not sure if I should do this but it seems reasonable.
            log("8xy4: Vx += Vy")

        elif set_type == 5:
            # 8xy5 - SUB Vx, Vy. Set Vx = Vx - Vy, set VF = NOT borrow.
            # If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.
            if self.v[x] > self.v[y]:
                self.v[0xF] = 1
            else:
                self.v[0xf] = 0
            self.v[x] = (self.v[x] - self.v[y]) & 0xff  # I wrap it so 0-1 = 255. Not sure if this is right. use abs?
            log("8xy5: Vx -= Vy")

        elif set_type == 6:
            # 8xy6 - SHR Vx {, Vy}
            #Set VF to least significant bit of Vx. Set Vx = Vx SHR 1.
            self.v[0x0F] = self.v[x]&0x0001
            self.v[x] >>= 1  # Divide Vx by 2 basically
            log("8xy6: SHR Vx {, Vy}")

        elif set_type == 7:
            # 8xy7 - SUBN Vx, Vy. Set Vx = Vy - Vx, set VF = NOT borrow.
            # If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.
            if self.v[y] > self.v[x]:
                self.v[0x0F] = 1
            else:
                self.v[0x0F] = 0
            self.v[x] = (self.v[y] - self.v[x]) & 0xff  # I wrap it so 0-1 = 255. Not sure if this is right. use abs?
            log("8xy7: Vy -= Vx")

        elif set_type == 0xE:
            # 8xyE. Set Vx = Vx SHL 1.
            #If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
            msb = (self.v[x] & 0xff)>> 7  # get most significant bit
            self.v[0x0F] = msb
            self.v[x] <<= 1 # Left shift. Basically multiply by 2
            self.v[x] &= 0xff  # wrap
            log("8xyE: Set Vx = Vx SHL 1")

        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _9xy0(self):
        # 9xy0 Skip next instruction if Vx != Vy.
        x = (self.instr & 0x0F00) >> 8
        y = (self.instr & 0x00F0) >> 4
        if self.v[x] != self.v[y]:
            log("9xy0: Vx != Vy is True")
            self.pc += 2
        else:
            log("9xy0: Vx != Vy is False")

    def _Annn(self):
        #Annn - LD I, addr
        self.i = self.instr & 0x0FFF
        log("LD I, addr")

    def _Bnnn(self):  # Bnnn - JP V0, addr. Jump to location nnn + V0.
        nnn = self.instr & 0x0FFF
        self.pc = nnn + self.v[0]

    def _cxkk(self):
        #Set Vx = random byte AND kk.
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        self.v[x] = random.randint(0, 255) & kk
        self.v[x] &= 0xff
        log("Set Vx = random byte AND kk.")

    def _dxyn(self):
        pos_x = self.v[((self.instr & 0x0F00) >> 8)] & 0xff
        pos_y = self.v[((self.instr & 0x00F0) >> 4)] & 0xff
        height = self.instr & 0x000F

        for i in range(0, height):
            byte = self.memory[self.i+i]
            for offset in range(0, 8):
                bit = (byte >> (7-i)) & 0x01
                if pos_x+offset > 63 or pos_y +i > 31:
                    continue
                displayed_pixel = self.display_buffer[pos_x+offset][pos_y+i]
                bit_xor = displayed_pixel ^ bit
                if displayed_pixel == 1 and bit_xor == 0:
                    self.v[0x0F] = 1
                self.display_buffer[pos_x+offset][pos_y+i] = bit_xor
        self.draw_flag = True
        log("Display_nbyte")

    def _exnn(self):
        x = (self.instr & 0x0F00) >> 8
        nn_type = self.instr & 0x00FF
        if nn_type == 0x009E:
            # Skip next instruction if key with the value of Vx is pressed.
            # Checks the keyboard, and if the key corresponding to the
            # value of Vx is currently in the down position, PC is increased by 2
            if self.input_buffer[self.v[x]] == 1:
                self.pc +=2
            log("SKP Vx")
        elif nn_type == 0x00A1:
            # Skip next instruction if key with the value of Vx is not pressed.
            # Checks the keyboard, and if the key corresponding to the value of
            # Vx is currently in the up position, PC is increased by 2.
            if self.input_buffer[self.v[x]] != 1:
                self.pc +=2
            log("SKNP Vx")
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _fxnn(self):
        f_type = self.instr&0x00FF
        x = (self.instr & 0x0F00) >> 8
        if f_type == 0x07:
            self.v[x] = self.delay_timer
            log("Vx = delay_timer")
        elif f_type == 0x0A:
            # Wait for a key press, store the value of the key in Vx.
            # All execution stops until a key is pressed, then the value of that key is stored in Vx.
            # print "WAITING FOR KEY PRESS"
            key_found = False
            for i in range(0, 16):
                if self.input_buffer[i] == 1:
                    self.v[x] = i
                    key_found = True
            if not key_found:
                self.pc -= 2  # If no key press found. Decrement PC to loop in same instruction
            log("Wait for keypress")
        elif f_type == 0x15:
            self.delay_timer = self.v[x]
            log("delay_timer = Vx")
        elif f_type == 0x18:
            self.sound_timer = self.v[x]
            log("sound_timer = Vx")
        elif f_type == 0x1e:
            #Set I = I + Vx.
            self.i += self.v[x]
            if self.i > 0xfff:
                self.v[0x0F] = 1
            else:
                self.v[0x0F] = 0
            log("i += Vx")
        elif f_type == 0x29:
            # Set I = location of sprite for digit Vx.
            # The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx.
            # If I understand this right this adress will be used for the self.fonts. 5 = width of one font char
            self.i = (5*(self.v[x])) & 0xfff
            log("Fx29. LD F, Vx.")
        elif f_type == 0x33:
            # Fx33 - LD B, Vx. Store BCD representation of Vx in memory locations I, I+1, and I+2.
            # The interpreter takes the decimal value of Vx, and places the hundreds digit in memory
            # at location in I, the tens digit at location I+1, and the ones digit at location I+2.
            self.memory[self.i] = self.v[x]//100
            self.memory[self.i+1] = self.v[x] % 100//10
            self.memory[self.i+2] = self.v[x] % 10

            log("Fx33. LD B, Vx")
        elif f_type == 0x55:
            # LD [I], Vx. Store registers V0 through Vx in memory starting at location I.
            #The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I.
            for reg_pos in range(0, x): #or should it be range(0, self.v[x]? dont think so
                self.memory[self.i+reg_pos] = self.v[reg_pos]
            #self.i += self.v[x] + 1
            log("Fx55. LD B, Vx.")
        elif f_type == 0x65:
            # Fx65 - LD Vx, [I]. Read registers V0 through Vx from memory starting at location I.
            # The interpreter reads values from memory starting at location I into registers V0 through Vx.
            for reg_pos in range(0, self.v[x]):  # I think I want to +1 it so I actually get the last reg as well
                self.v[reg_pos] = self.memory[self.i+reg_pos]
            #self.i += self.v[x] +1
            log("Fx65. LD B, Vx2")
        else:
            raise Warning("Unknown instruction: " + str(hex(self.instr)))

    def clear_screen(self):
        self.display_buffer = self.display_buffer = [[0 for y in range(32)] for x in range(64)]
        self.draw_flag = True
        log("CLS")

    #start up functions
    def load_fonts(self):
        for i in range(0, len(self.fonts)):
            self.memory[i] = self.fonts[i]

    def load_rom(self, path = "Pong.ch8"):
        rom_bin = open(path, 'rb').read()  # 'rb' opens file in binary
        i = 0
        while i < len(rom_bin):
            self.memory[0x200 + i] = ord(rom_bin[i])
            i += 1

    def initialize(self):
        self.input_buffer = [0]*16
        self.memory = [0] * 4096
        self.v = [0] * 16
        self.stack = [0] * 16
        self.i = 0
        self.pc = 0x200
        self.delay_timer, self.sound_timer = 0, 0
        self.clear_screen()
        self.load_fonts()
        self.load_rom()

    #pyglet.window.draw() override
    def draw(self):
        one_print_active = False
        self.clear()
        graphics.glColor3f(1, 1, 1)
        for x in range (0, len(self.display_buffer)):
            for y in range(0, len(self.display_buffer[x])):
                if self.display_buffer[x][y] == 1:
                    one_print_active = True
                    side = self.width/64
                    #vertices of a box
                    v = [side*x, self.height - side*y,
                         side*x, self.height -(side*y+side),
                         side*x+side, self.height -(side*y+side),
                         side*x+side, self.height-side*y
                    ]
                    graphics.draw(4, graphics.gl.GL_QUADS, ('v2i', (v[0],v[1], v[2],v[3], v[4],v[5], v[6],v[7])))

        # if one_print_active:
        #     file = open("log.txt",'w')
        #     for y in range (0, 32):
        #         for x in range(0, 64):
        #             file.write(str(self.display_buffer[x][y]))
        #         file.write("\n")
        #     file.write("#############################")
        #     file.close()
        #     self.one_print= False
            #print "Printed"

    def fetch_instruction(self):
        i1 = self.memory[self.pc]
        i2 = self.memory[self.pc+1]
        i1 <<= 8
        return i1 | i2

    def tick(self):
        #fetch instruction
        self.instr = self.fetch_instruction()
        self.pc += 2  # Advance PC. If done after execution of instruction I think it will mess up CALL and JUMP?
        #decode instruction
        opcode = self.instr & 0xF000
        #execute instruction
        try:
            self.op_map[opcode]()
        except KeyError:
            print "Unknown command: " + hex(self.instr)[2:]
        #update timers
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
        else:
            #play_sound()
            pass

    def on_key_press(self, symbol, modifiers):  # overrides Window.on_key_press
        if symbol == self.step_key:
            self.step = True
        else:
            try:
                self.input_buffer[self.keypad[symbol]] = 1
                print "VALID KEY PRESSED"
            except KeyError:
                print "KEY NOT RECOGNIZED"

    def on_key_release(self, symbol, modifiers):
        try:
            self.input_buffer[self.keypad[symbol]] = 0
            print "VALID KEY RELEASED"
        except KeyError:
            if self.step_instruction and symbol == self.step_key:
                pass
            else:
                print "KEY NOT RECOGNIZED"

    def main(self):
        self.initialize()
        self.draw()
        self.flip()
        while not self.has_exit:
            self.dispatch_events()
            if (self.step_instruction and self.step) or not self.step_instruction:
                self.tick()
                if self.draw_flag:
                    self.draw()
                    self.flip()
                    self.draw_flag = False
            self.step = False



c8 = Chip8(1080, 640)
c8.main()


