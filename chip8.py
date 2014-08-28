__author__ = 'Laxl'
import random
import pygame

class Chip8():
    #Debug stuff
    debug = False
    step_instruction = False
    step = False
    step_key = pygame.K_RIGHT

    rom_path = "roms/Ibm.ch8"
    #CPU variables
    memory = None                           # 4096 (0x1000) memory locations, all of which are 8 bits
    v = [0] * 16                            # the 16 8-bit V-registers
    stack = []                              # the 16 8-bit stack-registers, not sure this actually is 16 8-bits. Check.
    i = 0                                   # The address register is 16 bits wide and is used with several opcodes that
                                            # involve memory operations /wiki
    pc = None                               # 16-bit program counter
    delay_timer, sound_timer = 0, 0         # CHIP-8 has two timers. They both count down at 60 hertz.
    #instruction variables. I'll have a 0f00, 0ff0, 00ff available for all functions to use. Bit cleaner.
    instr = None                            # Contains the 16-bit instruction to be read and executed
    x, y, nn = None, None, None
    draw_flag = False                       # Indicate if screen should be redrawn
    #Input map, each valid key is given the address to the key value in input buffer
    keypad = {pygame.K_x: 0x0,  # key 0
              pygame.K_1: 0x1,  # key 1
              pygame.K_2: 0x2,  # key 2
              pygame.K_3: 0x3,  # key 3
              pygame.K_q: 0x4,  # key 4
              pygame.K_w: 0x5,  # key 5
              pygame.K_e: 0x6,  # key 6
              pygame.K_a: 0x7,  # key 7
              pygame.K_s: 0x8,  # key 8
              pygame.K_d: 0x9,  # key 9
              pygame.K_z:     0xA,  # key A
              pygame.K_c:     0xB,  # key B
              pygame.K_4:     0xC,  # key C
              pygame.K_r:     0xD,  # key D
              pygame.K_f:     0xE,  # key E
              pygame.K_v:     0xF,  # key F
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

    def __init__(self):
        self.beep = pygame.mixer.Sound('beep.wav', buffer=True)
        self.display_buffer = [[0 for y in range(32)] for x in range(64)]
        self.op_map = {0x0000: self._00nn,          # 0000 RET and CLS bot have opcode most significant bit 0
                       0x1000: self._0nnn,          # 1nnn jump to address nnn
                       0x2000: self._2nnn,          # 2nnn call subroutine at address nnn
                       0x3000: self._3xkk,          # 3xkk skip next instruction if Vx = kk
                       0x4000: self._4xll,          # 4xkk skip next instruction if Vx != kk
                       0x5000: self._5xy0,          # 5xy0 skip if Vx = Vy. Compare two registers
                       0x6000: self._6xkk,          # 6xkk SET Vx = kk
                       0x7000: self._7xkk,          # 7xkk ADD Vx, byte. Vx = Vx + kk
                       0x8000: self._8xy0,          # 8xy0 set Vx = Vy
                       0x9000: self._9xy0,          # 9xy0 - SNE Vx, Vy
                       0xA000: self._Annn,          # Annn - LD I, addr
                       0xB000: self._Bnnn,          # Bnnn - JP V0, addr
                       0xC000: self._cxkk,          # Cxkk - RND Vx, byte
                       0xD000: self._dxyn,          # Dxyn - DRW Vx, Vy, nibble
                       0xF000: self._fxnn,          # Branch out from all F opcodes
                       0xE000: self._exnn,          # Branch out from all E opcodes
                       }
        self.initialize()

    def _00nn(self):
        if self.nn == 0xE0:
            self.log("00E0: CLS", True)
            self.clear_screen()
        elif self.nn == 0xEE:
            self.log("00EE: RET", True)
            self.pc = self.stack.pop()
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _0nnn(self):
        self.log("0nnn: JUMP nnn:")
        #Jump to address contained in the 3 rightmost nibbles of instruction
        self.pc = self.instr & 0x0FFF

    def _2nnn(self): # Call nnn
        self.log("2nnn: CALL nnn", True)
        #push ret address to stack
        self.stack.append(self.pc)
        #Then jump to new location
        self.pc = self.instr & 0x0FFF

    def _3xkk(self):
        # 3xkk: if Vx equals kk skip next instruction
        self.log("3xkk: Vx == kk")
        self.log(self.log_x() + ", " + self.log_kk())
        if self.v[self.x] == self.nn:
            self.log("Vx == kk is True", True)
            self.pc += 2
        else:
            self.log("V == kk is False", True)

    def _4xll(self):
        # 4xkk skip next instruction if Vx != kk
        self.log("4xkk: Vx != kk")
        self.log(self.log_x() + ", " + self.log_kk())
        if self.v[self.x] != self.nn:
            self.log("Vx != kk is True", True)
            self.pc += 2
        else:
            self.log("V != kk is False", True)

    def _5xy0(self):
        # 5xy0 skip if Vx = Vy. Compare two registers
        self.log("5xy0: Vx == Vy\n"+self.log_xy())
        if self.v[self.x] == self.v[self.y]:
            self.log("Vx == Vy is True", True)
            self.pc += 2
        else:
            self.log("Vx == Vy is False", True)

    def _6xkk(self):
        # 6xkk SET Vx = kk
        self.log("6xkk: Set Vx to kk\n"+self.log_x()+"}, " + self.log_kk())
        self.v[self.x] = self.nn
        self.log("Result: " + self.log_x(), True)

    def _7xkk(self):
        # 7xkk ADD Vx, byte. Vx = Vx + kk
        self.log("7xkk: Vx = Vx +kk\n"+self.log_x()+", "+self.log_kk())
        self.v[self.x] += self.nn
        if self.v[self.x] > 255:
            self.log("OVERFLOW. VF = 1")
            self.v[0x0F] = 1
        else:
            self.v[0x0F] = 0
        self.v[self.x] &= 255  #Wrap
        self.log("Result: "+self.log_x(), True)

    def _8xy0(self):
        set_type = self.instr & 0x000F
        if set_type == 0:
            # 8xy0 Set Vx = Vy.
            self.log("8xy0: Vx = Vy\n"+self.log_xy())
            self.v[self.x] = self.v[self.y]
            self.log("Result: "+self.log_x(), True)
        elif set_type == 1:
            # 8xy1 SET Vx BITWISE OR Vy
            self.log("8xy1: Vx |= Vy")
            self.v[self.x] |= self.v[self.y]
        elif set_type == 2:
            # 8xy2 SET Vx BITWISE AND Vy
            self.log("8xy2: Vx &= Vy")
            self.v[self.x] &= self.v[self.y]
        elif set_type == 3:
            # 8xy3 SET Vx BITWISE XOR Vy
            self.log("8xy3: Vx ^= Vy")
            self.v[self.x] ^= self.v[self.y]
        elif set_type == 4:
            # 8xy4 SET Vx = Vx + Vy
            self.log("8xy4: Vx += Vy\n"+ self.log_xy())
            self.v[self.x] += self.v[self.y]
            if self.v[self.x] > 255:
                self.log("OVERFLOW. VF set to 1")
                self.v[0xF] = 1
                self.v[self.x] &= 0xff
            else:
                self.v[0xF] = 0  # Not sure if I should do this but it seems reasonable.
            self.log("Result:" + self.log_x(), True)

        elif set_type == 5:
            # 8xy5 - SUB Vx, Vy. Set Vx = Vx - Vy, set VF = NOT borrow.
            # If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.
            self.log("8xy5: Vx -= Vy\n" +self.log_xy())
            if self.v[self.x] >= self.v[self.y]:
                self.v[0xF] = 1
            else:
                self.v[0xf] = 0
            self.v[self.x] = (self.v[self.x] - self.v[self.y]) & 0xff  # I wrap it so 0-1 = 255. Not sure if this is right
            self.log(self.log_x(), True)

        elif set_type == 6:
            # 8xy6 - SHR Vx {, Vy}
            #Set VF to least significant bit of Vx. Set Vx = Vx SHR 1.
            self.log("8xy6: SHR Vx {, Vy}. (Vx/2)\n"+self.log_x())
            self.v[0x0F] = self.v[self.x]&0x0001
            self.v[self.x] >>= 1  # Divide Vx by 2 basically
            self.log("Result: "+self.log_x(), True)

        elif set_type == 7:
            # 8xy7 - SUBN Vx, Vy. Set Vx = Vy - Vx, set VF = NOT borrow.
            # If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.
            self.log("8xy7: Vx = Vy - Vx\n" + self.log_xy())
            if self.v[self.y] >= self.v[self.x]:
                self.v[0x0F] = 1
            else:
                self.v[0x0F] = 0
            self.v[self.x] = (self.v[self.y] - self.v[self.x]) & 0xff
            self.log("Result: "+self.log_x(),True)

        elif set_type == 0xE:
            # 8xyE. Set Vx = Vx SHL 1.
            #If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
            self.log("8xyE: Set Vx = Vx << 1\n"+self.log_x())
            msb = (self.v[self.x] & 0xff)>> 7  # get most significant bit
            self.v[0x0F] = msb
            self.v[self.x] <<= 1 # Left shift. Basically multiply by 2
            self.v[self.x] &= 0xff  # wrap
            self.log("Result: "+ self.log_x(), True)

        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _9xy0(self):
        # 9xy0 Skip next instruction if Vx != Vy.
        self.log("9xy0: Vx != Vy\n"+self.log_xy())
        if self.v[self.x] != self.v[self.y]:
            self.log("Result: Vx != Vy is True", True)
            self.pc += 2
        else:
            self.log("Result: Vx != Vy is False", True)

    def _Annn(self):
        #Annn - LD I, addr
        self.log("Annn: LD I, addr", True)
        self.i = self.instr & 0xFFF

    def _Bnnn(self):  # Bnnn - JP V0, addr. Jump to location nnn + V0.
        self.log("Bnnn: JP V0, addr", True)
        nnn = self.instr & 0x0FFF
        self.pc = nnn + self.v[0]

    def _cxkk(self):
        #Set Vx = random byte AND kk.
        self.log("Cxkk: Set Vx = random byte AND kk.", True)
        kk = self.nn
        self.v[self.x] = random.randint(0, 255) & kk
        #self.v[self.x] &= 0xff

    def _dxyn(self):
        self.log("Dxyn: Draw nbyte sprite to screen_buffer", True)
        pos_x = self.v[self.x]
        pos_y = self.v[self.y]
        height = self.instr & 0x000F

        self.v[0x0F] = 0
        for y_offset in range(0, height):
            byte = self.memory[self.i+y_offset]
            byte_string = format(byte, 'b').zfill(8)
            for x_offset in range(0, 8):
                curr_x = (pos_x+x_offset)&63
                curr_y = (pos_y+y_offset)&31
                bit = int(byte_string[x_offset])
                displayed_pixel = self.display_buffer[curr_x][curr_y]
                bit_xor = displayed_pixel ^ bit
                if displayed_pixel == 1 and bit_xor == 0:
                    self.v[0x0F] = 1
                self.display_buffer[curr_x][curr_y] = bit_xor
            #self.i += height
            self.draw_flag = True

    def _exnn(self):
        if self.nn == 0x9E:
            # Skip next instruction if key with the value of Vx is pressed.
            # Checks the keyboard, and if the key corresponding to the
            # value of Vx is currently in the down position, PC is increased by 2
            self.log("Ex9E: SKP Vx",True)
            if self.input_buffer[self.v[self.x]] == 1:
                self.pc += 2
        elif self.nn == 0xA1:
            # Skip next instruction if key with the value of Vx is not pressed.
            # Checks the keyboard, and if the key corresponding to the value of
            # Vx is currently in the up position, PC is increased by 2.
            self.log("ExA1: SKNP Vx",True)
            if self.input_buffer[self.v[self.x]] != 1:
                self.pc += 2
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _fxnn(self):
        if self.nn == 0x07:
            self.log("Fx07: Vx = delay_timer.\n delay_timer = "+str(self.delay_timer))
            self.v[self.x] = self.delay_timer
            self.log("Result: "+self.log_x(), True)
        elif self.nn == 0x0A:
            # Wait for a key press, store the value of the key in Vx.
            self.log("Fx0A: Wait for keypress", True)
            key_found = False
            for i in range(0, 16):
                if self.input_buffer[i] == 1:
                    self.v[self.x] = i
                    key_found = True
            if not key_found:
                self.pc -= 2  # If no key press found. Decrement PC to loop in same instruction
        elif self.nn == 0x15:
            self.log("delay_timer = Vx\n"+self.log_x())
            self.delay_timer = self.v[self.x]
            self.log("Result: delay_timer = " + str(self.delay_timer), True)
        elif self.nn == 0x18:
            self.log("Fx18: sound_timer = Vx")
            self.sound_timer = self.v[self.x]
        elif self.nn == 0x1e:
            #Set I = I + Vx.
            self.log("Fx1e: i += Vx\ni = " + str(self.i) + ", " + self.log_x())
            self.i += self.v[self.x]
            # if self.i > 0xFFF:
            #     self.v[0x0F] = 1
            #     self.i &= 0xFFF
            self.log("Result: i = " + str(self.i))
        elif self.nn == 0x29:
            # Set I = location of sprite for digit Vx.
            # The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx.
            self.log("Fx29. LD F, Vx.", True)
            self.i = 5*self.v[self.x]

        elif self.nn == 0x33:
            # Fx33 - LD B, Vx. Store BCD representation of Vx in memory locations I, I+1, and I+2.
            # The interpreter takes the decimal value of Vx, and places the hundreds digit in memory
            # at location in I, the tens digit at location I+1, and the ones digit at location I+2.
            self.log("Fx33: LD B, Vx", True)
            self.memory[self.i] = self.v[self.x]//100
            self.memory[self.i+1] = (self.v[self.x] % 100)//10
            self.memory[self.i+2] = self.v[self.x] % 10
        elif self.nn == 0x55:
            # LD [I], Vx. Store registers V0 through Vx in memory starting at location I.
            #The interpreter copies the values of registers V0 through Vx into memory, starting at the address in I.
            self.log("Fx55. LD B, Vx.", True)
            for reg_pos in range(0, self.x+1):
                self.memory[self.i+reg_pos] = self.v[reg_pos]
        elif self.nn == 0x65:
            # Fx65 - LD Vx, [I]. Read registers V0 through Vx from memory starting at location I.
            # The interpreter reads values from memory starting at location I into registers V0 through Vx.
            self.log("Fx65: LD B, Vx2",  True)
            for reg_pos in range(0, self.x+1):
                self.v[reg_pos] = self.memory[self.i+reg_pos]

        else:
            raise Warning("Unknown instruction: " + str(hex(self.instr)))

    def clear_screen(self):
        self.display_buffer = self.display_buffer = [[0 for y in range(32)] for x in range(64)]
        self.draw_flag = True
        self.log("CLS")

    #Helper functions for logging.
    def log_x(self):
        return "Vx = " + str(self.v[self.x])

    def log_y(self):
        return "Vy = " + str(self.v[self.y])

    def log_xy(self):
        return self.log_x()+", "+self.log_y()

    def log_kk(self):
        return "kk = " + str(self.nn)

    def log(self, str, end = False):
        if self.debug:
            print str
            if end:
                print "--------------"

    #start up functions
    def load_fonts(self):
        for i in range(0, 80):
            self.memory[i] = self.fonts[i]

    def load_rom(self, path):
        rom_bin = open(path, 'rb').read()  # 'rb' opens file in binary
        i = 0
        while i < len(rom_bin):
            self.memory[0x200 + i] = ord(rom_bin[i])
            i += 1

    def initialize(self):
        self.input_buffer = [0]*16
        self.memory = [0] * 4096
        self.v = [0] * 16
        self.stack = []
        self.i = 0
        self.pc = 0x200
        self.delay_timer, self.sound_timer = 0, 0
        self.clear_screen()
        self.load_fonts()
        self.load_rom(self.rom_path)

    def draw(self, screen, scr_width, scr_height):  # Draws the screen. Pyglet.window.draw() override
        side = scr_width/64
        for x in range (0, len(self.display_buffer)):
            for y in range(0, len(self.display_buffer[x])):
                if self.display_buffer[x][y] == 1:
                    pygame.draw.rect(screen, (255, 255, 255), (side*x, side*y,side, side), 0)

    def on_key_press(self, key):  # overrides Window.on_key_press
        if key == pygame.K_SPACE:
            self.step_instruction = not self.step_instruction
            self.debug = self.step_instruction
        elif key == self.step_key:
            self.step = True
        else:
            try:
                self.input_buffer[self.keypad[key]] = 1
            except KeyError:
                pass

    def on_key_release(self, key):
        try:
            self.input_buffer[self.keypad[key]] = 0
        except KeyError:
            pass

    def set_clock(self, w):
        try:
            t = int(w[0])
            if t < 1:
                raise ValueError
            self.clock_speed = 1.0/t
            self.input_str = ""
        except ValueError:
            self.input_str = "ERROR NOT A VALID VALUE"

    def handle_load_cmd(self, w):
        rom_string = " ".join(w)
        try:
            self.rom_path = "roms/"+rom_string
            self.initialize()
        except IOError:
            self.input_str = "ERROR COULD NOT FIND ROM"

    #CPU functions
    def fetch_instruction(self):
        i1 = self.memory[self.pc]
        i2 = self.memory[self.pc+1]
        i1 <<= 8
        return i1 | i2

    def cpu_tick(self):
        #fetch instruction
        self.instr = self.fetch_instruction()
        self.pc += 2
        #decode instruction
        #Parts of instruction usually used individually
        opcode = self.instr & 0xF000
        self.x = (self.instr & 0x0F00) >> 8
        self.y = (self.instr & 0x00F0) >> 4
        self.nn = (self.instr & 0x00FF)
        #execute instruction
        try:
            self.op_map[opcode]()
        except KeyError:
            print "Unknown command: " + hex(self.instr)[2:]

    def update(self):
        if (self.step_instruction and self.step) or not self.step_instruction:
            self.cpu_tick()
            self.step = False
            if self.delay_timer > 0:
                self.delay_timer -= 1
            if self.sound_timer > 0:
                if self.sound_timer == 1:
                    self.beep.play()
                self.sound_timer -= 1



