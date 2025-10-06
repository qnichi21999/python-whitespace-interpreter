from abc import ABC, abstractmethod
from dataclasses import dataclass


# INTERNALS

class Main:
    instruction_stack: list = list()
    instruction_pointer: int = 0
    subroutines: list = list()
    stack: list = list()
    heap: dict = dict()
    input: str = ""
    output: str = ""

    def next_instruction(self):
        if isinstance(self.instruction_stack[self.instruction_pointer], Instruction):
            self.instruction_stack[self.instruction_pointer].execute()
        self.instruction_pointer += 1

# TODO BRUH
class Procedure:
    pass


class Parser:
    def __init__(self, source):
        self.code = source
        self.skip_to = list()
        self.namespace = Main()

        
    def iterate(self, from_symbol=0):
        symbol_index = from_symbol
        for symbol in self.code[from_symbol:]:
            yield (symbol, symbol_index)
            symbol_index += 1
    
    def parse(self):
        for symbol, symbol_index in self.iterate():
            if self.skip_to:
                if symbol_index == self.skip_to[-1]:
                    self.skip_to.pop()
                continue

            if instruction := self.parse_stack_manipulation(symbol, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                continue
            if instruction := self.parse_arithmetic(symbol, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                continue
            if instruction := self.parse_flow_control(symbol, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                continue
            if instruction := self.parse_heap_access(symbol, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                continue

        return self.namespace
            
    
    def parse_stack_manipulation(self, symbol, symbol_index):        
        if symbol != " ":
            return None
        
        lookahead = self.code[symbol_index+1:]
        if lookahead[0] == " ":
            number = self.parse_number(symbol_index+3, lookahead[1])
            return PushNumber(self.namespace, number)
        if lookahead[:2] == "\t\n":
            number = self.parse_number(symbol_index+4, lookahead[2])
            return DiscardTopN(self.namespace, number)
        if lookahead[:2] == "\t ":
            number = self.parse_number(symbol_index+4, lookahead[2])
            return DuplicateN(self.namespace, number)
        if lookahead[:2] == "\n ":
            self.skip_to.append(symbol_index+3)
            return DuplicateTop(self.namespace)
        if lookahead[:2] == "\n\t":
            self.skip_to.append(symbol_index+3)
            return SwapTop(self.namespace)
        if lookahead[:2] == "\n\n":
            self.skip_to.append(symbol_index+3)
            return DiscardTop(self.namespace)

    def parse_arithmetic(self, symbol, symbol_index):

        lookahead = self.code[symbol_index:]
        if lookahead[:2] != "\t ":
            return None
        
        lookahead = lookahead[2:]
        if lookahead[:2] == "  ":
            self.skip_to.append(symbol_index+3)
            return PushAdd(self.namespace)
        if lookahead[:2] == " \t":
            self.skip_to.append(symbol_index+3)
            return PushSubtract(self.namespace)
        if lookahead[:2] == " \n":
            self.skip_to.append(symbol_index+3)
            return PushMultiply(self.namespace)
        if lookahead[:2] == "\t ":
            self.skip_to.append(symbol_index+3)
            return PushDivide(self.namespace)
        if lookahead[:2] == "\t\t":
            self.skip_to.append(symbol_index+3)
            return PushModulo(self.namespace)

    def parse_heap_access(self, symbol, symbol_index):
        lookahead = self.code[symbol_index:]
        if lookahead[:2] != "\t\t":
            return None

        lookahead = lookahead[2:]
        if lookahead[0] == " ":
            self.skip_to.append(symbol_index+2)
            return HeapStore(self.namespace)
        if lookahead[0] == "\t":
            self.skip_to.append(symbol_index+2)
            return HeapPush(self.namespace)
    
    def parse_io(self, symbol, symbol_index):
        lookahead = self.code[symbol_index:]
        if lookahead[:2] != "\t\n":
            return None
        lookahead = lookahead[2:]

        

    def parse_flow_control(self, symbol, symbol_index):
        if symbol != "\n":
            return None
        lookahead = self.code[symbol_index+1:]
        if lookahead[:2] == "\n\n":
            self.skip_to.append(symbol_index+3)
            return Exit(self.namespace)
    
    

    def parse_number(self, from_symbol, sign_symbol):
        binary = ""
        
        match sign_symbol:
            case " ":
                negative = False
            case "\t":
                negative = True
            case _:
                raise Exception

        for symbol, symbol_index in self.iterate(from_symbol):
            if symbol == "\n":
                break
            if symbol == " ":
                binary += "0"
                continue
            if symbol == "\t":
                binary += "1"
                continue

        self.skip_to.append(symbol_index)

        if not binary:
            return 0
        
        return int(binary, 2) * -1 if negative else int(binary, 2)

#
# INSTRUCTIONS
#

@dataclass
class Instruction(ABC):
    namespace: Main

    def execute(self):
        self.callback()
        print(self.namespace.stack)
        # space for some debug shit
        
    @abstractmethod
    def callback(self):
        pass

# STACK MANIPULATION

@dataclass
class PushNumber(Instruction):
    value: int

    def callback(self):
        self.namespace.stack.append(self.value)

@dataclass
class DiscardTopN(Instruction):
    n: int

    def callback(self):
        if self.n < 0 or self.n > len(self.namespace.stack):
            self.namespace.stack = self.namespace.stack[-1:]
        else:
            self.namespace.stack = self.namespace.stack[:-self.n-1] + self.namespace.stack[-1:]

@dataclass
class DuplicateN(Instruction):
    n: int

    def callback(self):
        self.namespace.stack.append(self.namespace.stack[-self.n-1])

@dataclass
class DuplicateTop(Instruction):
    def callback(self):
        self.namespace.stack.append(self.namespace.stack[-1])

@dataclass
class SwapTop(Instruction):
    def callback(self):
        self.namespace.stack.insert(-1, self.namespace.stack.pop())

@dataclass
class DiscardTop(Instruction):
    def callback(self):
        self.namespace.stack.pop()

# ARITHMETICS

@dataclass
class PushAdd(Instruction):
    def callback(self):
        self.namespace.stack[-2] += self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushSubtract(Instruction):
    def callback(self):
        self.namespace.stack[-2] -= self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushMultiply(Instruction):
    def callback(self):
        self.namespace.stack[-2] *= self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushDivide(Instruction):
    def callback(self):
        self.namespace.stack[-2] //= self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushModulo(Instruction):
    def callback(self):
        self.namespace.stack[-2] %= self.namespace.stack[-1]
        self.namespace.stack.pop()


# HEAP ACCESS

@dataclass
class HeapStore(Instruction):
    def callback(self):
        a = self.namespace.stack.pop()
        b = self.namespace.stack.pop()
        self.namespace.heap[b] = a

@dataclass
class HeapPush(Instruction):
    def callback(self):
        a = self.namespace.stack.pop()
        self.namespace.stack.append(self.namespace.heap[a])

# INPUT/OUTPUT
# not really sure if these are working

@dataclass
class OutputChar(Instruction):
    def callback(self):
        character = self.namespace.stack.pop()
        self.namespace.output += char(character)

@dataclass
class OutputNumber(Instruction):
    def callback(self):
        number = self.namespace.stack.pop()
        self.namespace.output += str(number)

@dataclass
class ReadCharToHeap(Instruction):
    def callback(self):
        a = ord(self.namespace.input)
        b = self.namespace.stack.pop()
        self.namespace.heap[b] = a

@dataclass
class ReadNumberToHeap(Instruction):
    def callback(self):
        a = int(self.namespace.input)
        b = self.namespace.stack.pop()
        self.namespace.heap[b] = a


# FLOW CONTROL

@dataclass
class Exit(Instruction):
    def callback(self):
        raise WExit


# EXCEPTIONS

class WExit(Exception):
    pass

# MAIN

def unbleach(n):
    return n.replace(' ', 's').replace('\t', 't').replace('\n', 'n')

def bleach(n):
    return n.replace("s", " ").replace("t", "\t").replace("n", "\n")

def whitespace(code, inp = ''):
    parser = Parser(code)
    main = parser.parse()
    main.input = inp
    while True:
        try:
            main.next_instruction()
        except WExit:
            break

    print("\nSTACK:")
    print(main.stack)
    print("\nHEAP:")
    print(main.heap)
    return main.output


print(whitespace("codeherebtw"))
