__author__ = 'Laxl'

def print8(n):
    print format(n, 'b').zfill(8)

def print16(n):
    print format(n, 'b').zfill(16)

class Ant:
    def __init__(self):
        self.val = 5
    def load(self):
        print self.val


class Dis:
    def __init__(self):
        self.instr = None #current instruction
        self.memory= [0] * 4096
        self.pc = 0
        self.op_map = {0x1000: self.jump,
                       0x2000: self.call}

    def run(self):
        self.load_rom()
        self.pc = 0x200
        file = open("dis.txt", 'w')
        while self.pc < len(self.memory):
            cmd = self.next_command()
            file.write(cmd + "\n")
            self.pc += 2
        file.close()

    def load_rom(self, path = "AD.ch8"):
        rom_bin = open(path, 'rb').read()  # 'rb' opens file in binary
        i = 0
        self.memory = [0] * 4096
        while i < len(rom_bin):
            self.memory[0x200 + i] = ord(rom_bin[i])
            i += 1
        #return memory
    def next_command(self):
        i1 = self.memory[self.pc]
        i2 = self.memory[self.pc+1]
        i1 <<= 8
        self.instr = i1 | i2
        opcode = self.instr & 0xF000
        try:
            decoded_opcode = self.op_map[opcode]()
            return decoded_opcode
            #trans = opcode[(instr&0xF000)]
            #return hex(instr)[2:].zfill(4) + " - " + trans
        except KeyError:
            return "UNKNOWN"

    opcode = {0x1000: "JP",  # 1nnn JUMP to location nnn
              0x2000: "CALL",  # CALL subroutine at nnn
              0x3000: "SE",  # 3xkk skip next instruction if Vx = kk
              0x4000: "SNE",  # 4xkk skip next instruction if Vx != kk
              0x5000: "SE",  # 5xy0 skip if Vx = Vy. Compare two registers
              0x6000: "LD",  # 6xkk SET Vx = kk
              0x7000: "ADD",  # 7xkk ADD Vx, byte. Vx = Vx + kk
              0x8000: "LD",  # 8xy0 set Vx = Vy
              0x9000: "UNDEF",
              0xA000: "UNDEF",}

    def jump(self):
        return "JP " + str(hex(self.instr&0x0FFF))[2:]

    def call(self):
        return "CALL " + str(hex(self.instr&0x0FFF))[2:]

    #def skip_equal(self):
        #return "SE("


d = Dis()
d.run()
#pc = 0x200
#mem = load_rom()
#file = open("dis.txt", 'w')
#while pc < len(mem):
#    cmd = next_command(mem)
#    file.write(cmd+"\n")
#    pc +=2
#file.close()
