from pyglet.text.layout import _AbstractBox

__author__ = 'Laxl'
import random

class Chip8:
    def __init__(self):
        self.memory = None  # 4096 (0x1000) memory locations, all of which are 8 bits
        self.v = [0] * 16  # the 16 8-bit V-registers
        self.stack = []  # the 16 8-bit stack-registers, not sure this actually is 16 8-bits. Check.
        self.i = None  # The address register is 16 bits wide and is used with several opcodes that
                               #  involve memory operations /wiki
        self.pc = None # 16-bit program counter
        self.delay_timer, self.sound_timer = 0, 0  # CHIP-8 has two timers. They both count down at 60 hertz.
        self.display_width = 64
        self.display_height = 32
        self.display = [[0 for x in range(self.display_width)] for x in range(self.display_height)]
        self.instr = None
        self.draw_flag = False
        self.op_map = {
                       0x0000: self._00nn,          # 0000 RET and CLS bot have opcode most significant bit 0
                       0x1000: self.jump_nnn,       # 1nnn jump to address nnn
                       0x2000: self.call,           # 2nnn call subroutine at address nnn
                       0x3000: self.skip_x_e_kk,    # 3xkk skip next instruction if Vx = kk
                       0x4000: self.skip_x_ne_kk,   # 4xkk skip next instruction if Vx != kk
                       0x5000: self.skip_x_e_y,     # 5xy0 skip if Vx = Vy. Compare two registers
                       0x6000: self.set_x_kk,       # 6xkk SET Vx = kk
                       0x7000: self.add,            # 7xkk ADD Vx, byte. Vx = Vx + kk
                       0x8000: self._8xy0,          # 8xy0 set Vx = Vy
                       0x9000: self.skip_x_ne_y,    # 9xy0 - SNE Vx, Vy
                       0xA000: self.set_i,          # Annn - LD I, addr
                       0xB000: self.jump_nnn_v0,    # Bnnn - JP V0, addr
                       0xC000: self.set_x_rand_kk,  # Cxkk - RND Vx, byte
                       0xD000: self.display_nbyte,  # Dxyn - DRW Vx, Vy, nibble
                       0xF000: self._fxnn,          # Branch out from all F opcodes
                       0xE000: self._exnn,          # Branch out from all E opcodes
                       }
        self.fonts = [0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
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

    def initialize(self):
        self.memory = [0] * 4096
        self.v = [0] * 16
        self.stack = [0] * 16
        self.i = 0
        self.pc = 0x200
        self.delay_timer, self.sound_timer = 0, 0
        #self.clear_screen()
        self.load_fonts()
        self.load_rom()

    def load_fonts(self):
        for i in range(0, len(self.fonts)):
            self.memory[i] = self.fonts[i]

    def load_rom(self, path = "AD.ch8"):
        rom_bin = open(path, 'rb').read()  # 'rb' opens file in binary
        i = 0
        while i < len(rom_bin):
            self.memory[0x200 + i] = ord(rom_bin[i])
            i += 1

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

    def jump_nnn(self):
        print "jumping to address: " + str(hex(self.instr&0x0FFF))
        #Jump to address contained in the 3 rightmost nibbles of instruction
        self.pc = self.instr & 0x0FFF

    def jump_nnn_v0(self):  # Bnnn - JP V0, addr. Jump to location nnn + V0.
        nnn = self.instr & 0x0FFF
        self.pc = nnn + self.v[0]

    def call(self):
        #push ret address to stack
        self.stack.append(self.pc)
        #Then jump to new location
        self.pc = self.instr & 0x0FFF
        print "CALL to address" + str(hex(self.instr&0x0FFF))

    def skip_x_e_kk(self):
        # 3xkk: if Vx equals kk skip next instruction
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        if self.v[x] == kk:
            print "Vx = kk is True"
            self.pc += 2
        else:
            print "V = kk is False"

    def skip_x_ne_kk(self):
        # 4xkk skip next instruction if Vx != kk
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        if self.v[x] != kk:
            print "Vx != kk is True"
            self.pc += 2
        else:
            print "V != kk is False"

    def skip_x_e_y(self):
        # 5xy0 skip if Vx = Vy. Compare two registers
        x = (self.instr & 0x0F00) >> 8
        y = (self.instr & 0x00F0) >> 4
        if self.v[x] == self.v[y]:
            print "Vx = Vy is True"
            self.pc += 2
        else:
            print "Vx = Vy is False"

    def skip_x_ne_y(self):
        # 9xy0 Skip next instruction if Vx != Vy.
        x = (self.instr & 0x0F00) >> 8
        y = (self.instr & 0x00F0) >> 4
        if self.v[x] != self.v[y]:
            print "Vx != Vy is True"
            self.pc += 2
        else:
            print "Vx != Vy is False"

    def set_i(self):
        #Annn - LD I, addr
        self.i = self.instr & 0x0FFF
        print "LD I, addr"

    def set_x_rand_kk(self):
        #Set Vx = random byte AND kk.
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        self.v[x] = random.randint(0, 255) & kk

    def set_x_kk(self):
        # 6xkk SET Vx = kk
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        self.v[x] = kk
        print "Set V" + str(x) + " to " + str(kk)

    def _00nn(self):
        nn_type = self.instr & 0x00FF
        if nn_type == 0xE0:
            self.clear_screen()
        elif nn_type == 0xEE:
            self.ret()
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _8xy0(self):
        set_type = self.instr & 0x000F
        x = (self.instr & 0x0F00) >> 8
        y = (self.instr & 0x00F0) >> 4
        if set_type == 0:
            # 8xy0 Set Vx = Vy.
            self.v[x] = self.v[y]
            print "Set V" + str(x) + " to V" + str(y)
        elif set_type == 1:
            # 8xy1 SET Vx BITWISE OR Vy
            self.v[x] |= self.v[y]
            print "Vx |= Vy"
        elif set_type == 2:
            # 8xy2 SET Vx BITWISE AND Vy
            self.v[x] &= self.v[y]
            print "Vx &= Vy"
        elif set_type == 3:
            # 8xy3 SET Vx BITWISE XOR Vy
            self.v[x] ^= self.v[y]
            print "Vx ^= Vy"
        elif set_type == 4:
            # 8xy4 SET Vx = Vx + Vy
            self.v[x] += self.v[y]
            if self.v[x] > 255:
                # wraps V[x] if it overflows and set V[F] to 1 as carry bit.
                # For instance Vx = 257 & 255 would wrap to Vx = 1
                self.v[0xF] = 1
                self.v[x] &= 255
            else:
                self.v[0xF] = 0  # Not sure if I should do this but it seems reasonable.
            print "Vx += Vy"
        elif set_type == 5:
            # 8xy5 - SUB Vx, Vy
            # Set Vx = Vx - Vy, set VF = NOT borrow.
            # If Vx > Vy, then VF is set to 1, otherwise 0. Then Vy is subtracted from Vx, and the results stored in Vx.
            if self.v[x] > self.v[y]:
                self.v[0xF] = 1
            else:
                self.v[0xf] = 0
            self.v[x] = abs(self.v[x] - self.v[y])  # Think I should abs this since the minus indicator is stored in VF.
            print "Vx -= Vy"
        elif set_type == 6:
            # 8xy6 - SHR Vx {, Vy}
            # Set Vx = Vx SHR 1.
            # If the least-significant bit of Vx is 1, then VF is set to 1, otherwise 0. Then Vx is divided by 2.
            #What is the purpose of this?
            print "8xy6 - SHR Vx {, Vy}. Unwritten"
        elif set_type == 7:
            # 8xy7 - SUBN Vx, Vy
            # Set Vx = Vy - Vx, set VF = NOT borrow.
            # If Vy > Vx, then VF is set to 1, otherwise 0. Then Vx is subtracted from Vy, and the results stored in Vx.
            #Note order: Vy - Vx \me
            print "8xy7 - SUBN Vx, Vy. Unwritten"
        elif set_type == 0xE:
            # 8xyE
            #Set Vx = Vx SHL 1.
            #If the most-significant bit of Vx is 1, then VF is set to 1, otherwise to 0. Then Vx is multiplied by 2.
            print "Set Vx = Vx SHL 1. Unwritten"
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _exnn(self):
        x = (self.instr & 0x0F00) >> 8
        nn_type = self.instr & 0x00FF
        if nn_type == 0x009E:
            # Skip next instruction if key with the value of Vx is pressed.
            # Checks the keyboard, and if the key corresponding to the
            # value of Vx is currently in the down position, PC is increased by 2
            print "SKP Vx. Unwritten"
        elif nn_type == 0x00A1:
            # Skip next instruction if key with the value of Vx is not pressed.
            #Checks the keyboard, and if the key corresponding to the value of
            # Vx is currently in the up position, PC is increased by 2.
            print "SKNP Vx. Unwritten"
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def _fxnn(self):
        f_type = self.instr&0x00FF
        x = (self.instr & 0x0F00) >> 8
        if f_type == 0x07:
            self.v[x] = self.delay_timer
            print "Vx = delay_timer"
        elif f_type == 0x15:
            self.delay_timer = self.v[x]
            print "delay_timer = Vx"
        elif f_type == 0x0A:
            # Wait for a key press, store the value of the key in Vx.
            # All execution stops until a key is pressed, then the value of that key is stored in Vx.
            print "Wait for keypress. Unwritten."
        elif f_type == 0x18:
            self.sound_timer = self.v[x]
            print "sound_timer = Vx"
        elif f_type == 0x1e:
            #Set I = I + Vx.
            self.i += self.v[x]
            print "i += Vx"
        elif f_type == 0x29:
            # Set I = location of sprite for digit Vx.
            # The value of I is set to the location for the hexadecimal sprite corresponding to the value of Vx.
            # See section 2.4, Display, for more information on the Chip-8 hexadecimal font.
            print "Fx29. LD F, Vx. Unwritten."
        else:
            raise Warning("Unknown instruction: " + hex(self.instr))

    def run(self):
        self.initialize()
        run = True
        while run:
            self.tick()
    def display_nbyte(self):
        # Dxyn - DRW Vx, Vy, nibble
        # Display n-byte sprite starting at memory location I at (Vx, Vy), set VF = collision.
        print "Display_nbyte unwritten"

    def add(self):
        # 7xkk ADD Vx, byte. Vx = Vx + kk
        x = (self.instr & 0x0F00) >> 8
        kk = self.instr & 0x00FF
        self.v[x] += kk

    def clear_screen(self):  # 0x00E0 CLS. Clear screen.
        self.display = [[0 for x in range(self.display_width)] for x in range(self.display_height)]
        self.draw_flag = True
        print "CLS"

    def ret(self):  # 0x00EE RET. Return from a subroutine
        self.pc = self.stack.pop()
        print "RET"


c8 = Chip8()
#c8.initialize()
c8.run()


