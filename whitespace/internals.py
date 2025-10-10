from abc import ABC, abstractmethod
from dataclasses import dataclass
from whitespace.exceptions import WExit


class Main:
    def __init__(self):
        self.instruction_stack: list = list()
        self.call_stack: list = list()
        self.instruction_pointer: int = 0
        self.input_pointer: int = 0
        self.labels: dict = dict()
        self.stack: list = list()
        self.heap: dict = dict()
        self.input: str = ""
        self.output: str = ""

    def next_instruction(self):
        if isinstance(self.instruction_stack[self.instruction_pointer], Instruction):
            self.instruction_stack[self.instruction_pointer].execute()
        self.instruction_pointer += 1

@dataclass
class Instruction(ABC):
    namespace: Main

    def execute(self):
        self.callback()
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
        if self.n < 0 or self.n > len(self.namespace.stack)-1:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack.append(self.namespace.stack[-self.n-1])

@dataclass
class DuplicateTop(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 1:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack.append(self.namespace.stack[-1])

@dataclass
class SwapTop(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 2:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack.insert(-1, self.namespace.stack.pop())

@dataclass
class DiscardTop(Instruction):
    def callback(self):
        if len(self.nameapce.stack) < 1:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack.pop()

# ARITHMETICS

@dataclass
class PushAdd(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 2:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack[-2] += self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushSubtract(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 2:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack[-2] -= self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushMultiply(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 2:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack[-2] *= self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushDivide(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 2:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack[-2] //= self.namespace.stack[-1]
        self.namespace.stack.pop()

@dataclass
class PushModulo(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 2:
            raise WRuntimeError("Not enough size of stack")
        self.namespace.stack[-2] %= self.namespace.stack[-1]
        self.namespace.stack.pop()


# HEAP ACCESS

@dataclass
class HeapStore(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 2:
            raise WRuntimeError("Not enough size of stack")
        a = self.namespace.stack.pop()
        b = self.namespace.stack.pop()
        self.namespace.heap[b] = a

@dataclass
class HeapPush(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 1:
            raise WRuntimeError("Not enough size of stack")
        a = self.namespace.stack.pop()
        self.namespace.stack.append(self.namespace.heap[a])

# INPUT/OUTPUT

@dataclass
class OutputChar(Instruction):
    def callback(self):
        character = self.namespace.stack.pop()
        self.namespace.output += chr(character)

@dataclass
class OutputNumber(Instruction):
    def callback(self):
        if len(self.namespace.stack) < 1:
            raise Exception
        number = self.namespace.stack.pop()
        self.namespace.output += str(number)

@dataclass
class ReadCharToHeap(Instruction):
    def callback(self):
        a = ord(self.namespace.input[self.namespace.input_pointer])
        self.namespace.input_pointer += 1
        b = self.namespace.stack.pop()
        self.namespace.heap[b] = a

@dataclass
class ReadNumberToHeap(Instruction):
    def callback(self):
        number = ""
        is_dec = False
        is_hex = False
        b = self.namespace.stack.pop()
        if self.namespace.input[self.namespace.input_pointer:self.namespace.input_pointer+3] == "0x":
            is_hex = True
        else:
            is_dec = True
        for symbol in self.namespace.input[self.namespace.input_pointer:]:
            self.namespace.input_pointer += 1
            if symbol == "\n":
                break
            number += symbol
        if not number:
            raise WRuntimeError("Invalid number input")
        if is_dec:
            a = int(number)
        if is_hex:
            a = int(number, 16)
        

        self.namespace.heap[b] = a


# FLOW CONTROL

@dataclass
class Mark(Instruction):
    label: str

    def callback(self):
        return
        

@dataclass
class CallSub(Instruction):
    label: str

    def callback(self):
        if self.label not in self.namespace.labels.keys():
            raise WRuntimeError("CallSub: Label doesnt exist")
        self.namespace.call_stack.append(self.namespace.instruction_pointer)
        self.namespace.instruction_pointer = self.namespace.labels[self.label]

@dataclass
class Jump(Instruction):
    label: str

    def callback(self):
        if self.label not in self.namespace.labels.keys():
            raise WRuntimeError("Jump: Label doesnt exist")
        self.namespace.instruction_pointer = self.namespace.labels[self.label]

@dataclass
class JumpIfZero(Instruction):
    label: str

    def callback(self):
        if len(self.namespace.stack) < 1:
            raise WRuntimeError("Not enough size of stack")
        n = self.namespace.stack.pop()
        if n != 0:
            return
        if self.label not in self.namespace.labels.keys():
            raise WRuntimeError("JumpIfZero: Label doesnt exist")
        self.namespace.instruction_pointer = self.namespace.labels[self.label]


@dataclass
class JumpIfLess(Instruction):
    label: str

    def callback(self):
        if len(self.namespace.stack) < 1:
            raise WRuntimeError("Not enough size of stack")
        n = self.namespace.stack.pop()
        if n >= 0:
            return
        if self.label not in self.namespace.labels.keys():
            raise WRuntimeError("JumpIfLess: Label doesnt exist")
        self.namespace.instruction_pointer = self.namespace.labels[self.label]

@dataclass
class EndSub(Instruction):
    def callback(self):
        if len(self.namespace.call_stack) < 1:
            raise WRuntimeError("EndSub: Not enough size of call stack")
        self.namespace.instruction_pointer = self.namespace.call_stack.pop()  

@dataclass
class Exit(Instruction):
    def callback(self):
        raise WExit
