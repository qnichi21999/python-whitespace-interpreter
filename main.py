from abc import ABC, abstractmethod
from dataclasses import dataclass


# INTERNALS

class Main:
    instruction_stack: list = list()
    call_stack: list = list()
    instruction_pointer: int = 0
    input_pointer: int = 0
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
class Subroutine:
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

    def check_skippable(self, symbol):
        if symbol not in " \t\n":
            return True

    def parse(self):
        keyword = ""
        for symbol, symbol_index in self.iterate():
            if self.skip_to:
                if symbol_index == self.skip_to[-1]:
                    self.skip_to.pop()
                continue
            if self.check_skippable(symbol):
                continue
            
            keyword += symbol
            if instruction := self.parse_stack_manipulation(keyword, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                keyword = ""
                continue
            if instruction := self.parse_arithmetic(keyword, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                keyword = ""
                continue
            if instruction := self.parse_flow_control(keyword, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                keyword = ""
                continue
            if instruction := self.parse_heap_access(keyword, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                keyword = ""
                continue

        return self.namespace
            
    
    def parse_stack_manipulation(self, keyword, symbol_index):        
        if keyword != " ":
            return None
        keyword = ""

        for symbol, symbol_index in self.iterate(symbol_index+1):
            if self.check_skippable(symbol):
                continue
            keyword += symbol
            match keyword:
                case " ":
                    number = self.parse_number(symbol_index+1)
                    return PushNumber(self.namespace, number)
                case "\t\n":
                    number = self.parse_number(symbol_index+1)
                    return DiscardTopN(self.namespace, number)
                case "\t ":
                    number = self.parse_number(symbol_index+1)
                    return DuplicateN(self.namespace, number)
                case "\n ":
                    self.skip_to.append(symbol_index+1)
                    return DuplicateTop(self.namespace)
                case "\n\t":
                    self.skip_to.append(symbol_index+1)
                    return SwapTop(self.namespace)
                case "\n\n":
                    self.skip_to.append(symbol_index+1)
                    return DiscardTop(self.namespace) 
        raise Exception

    def parse_arithmetic(self, keyword, symbol_index):
        if keyword != "\t ":
            return None

        keyword = ""
        for symbol, symbol_index in self.iterate(symbol_index+1):
            if self.check_skippable(symbol):
                continue
            keyword += symbol
            match keyword:
                case "  ":
                    self.skip_to.append(symbol_index)
                    return PushAdd(self.namespace)
                case " \t":
                    self.skip_to.append(symbol_index)
                    return PushSubtract(self.namespace)
                case " \n":
                    self.skip_to.append(symbol_index)
                    return PushMultiply(self.namespace)
                case "\t ":
                    self.skip_to.append(symbol_index)
                    return PushDivide(self.namespace)
                case "\t\t":
                    self.skip_to.append(symbol_index)
                    return PushModulo(self.namespace)


    def parse_heap_access(self, keyword, symbol_index):
        if keyword != "\t\t":
            return None
        keyword = ""
        for symbol, symbol_index in self.iterate(symbol_index+1):
            if self.check_skippable(symbol):
                continue
            keyword += symbol
            match keyword:
                case " ":
                    self.skip_to.append(symbol_index)
                    return HeapStore(self.namespace)
                case "\t":
                    self.skip_to.append(symbol_index)
                    return HeapPush(self.namespace)
            
    
    def parse_io(self, keyword, symbol_index):
        if keyword != "\t\n":
            return None
        keyword = ""
        for symbol, symbol_index in self.iterate(symbol_index+1):
            if self.check_skippable(symbol):
                continue
            keyword += symbol
            match keyword:
                case "  ":
                    self.skip_to.append(symbol_index)
                    return OutputChar(self.namespace)
                case " \t":
                    self.skip_to.append(symbol_index)
                    return OutputNumber(self.namespace)
                case "\t ":
                    return ReadCharToHeap(self.namespace)
                case "\t\t":
                    return ReadNumberToHeap(self.namespace)

    def parse_flow_control(self, keyword, symbol_index):
        if keyword != "\n":
            return None
        keyword = ""
        for symbol, symbol_index in self.iterate(symbol_index+1):
            if self.check_skippable(symbol):
                continue
            keyword += symbol
            match keyword:
                case "\n\n":
                    self.skip_to.append(symbol_index)
                    return Exit(self.namespace)
                    
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

        self.namespace.heap[b] = a

@dataclass
class ReadNumberToHeap(Instruction):
    def callback(self):
        prefix = ""
        number = ""
        is_bin = False
        is_hex = False
        for symbol in self.namespace.input[self.namespace.input_pointer:]:
            self.namespace.input_pointer += 1
            if symbol == "\n":
                break
            if is_bin or is_hex:
                number += symbol
            elif len(prefix) < 2:
                prefix += symbol
                continue
            elif prefix == "0b":
                is_bin == True
                continue
            elif prefix == "0x":
                is_hex == True
                continue
            else:
                raise Exception
        if not number:
            raise Exception
        if is_bin:
            return 
            
            
        self.namespace.heap[b] = a


# FLOW CONTROL

@dataclass
class Exit(Instruction):
    def callback(self):
        raise WExit


# TODO
# EXCEPTIONS

class WExit(Exception):
    pass

# MAIN

def unbleach(n):
    return n.replace(' ', 's').replace('\t', 't').replace('\n', 'n')

def bleach(n):
    return n.replace("s", " ").replace("t", "\t").replace("n", "\n")

def whitespace(code, inp = 'f'):
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


print(whitespace(bleach("ssstsstn.ssstsssttttn.......nnn")))
