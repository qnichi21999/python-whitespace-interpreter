from whitespace.internals import (Main,
                       PushNumber, DiscardTopN, DuplicateN,
                       DuplicateTop, SwapTop, DiscardTop,
                       PushAdd, PushSubtract, PushMultiply, PushDivide, PushModulo,
                       HeapStore, HeapPush,
                       OutputChar, OutputNumber,
                       ReadCharToHeap, ReadNumberToHeap,
                       Mark, Jump, JumpIfZero, JumpIfLess, CallSub, EndSub, Exit)
from whitespace.exceptions import WRuntimeError, WExit


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
            if instruction := self.parse_io(keyword, symbol_index):
                self.namespace.instruction_stack.append(instruction)
                keyword = ""
                continue
            if len(keyword) >= 2:
                raise WRuntimeError("Unknown IMP")

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
                    self.skip_to.append(symbol_index)
                    return DuplicateTop(self.namespace)
                case "\n\t":
                    self.skip_to.append(symbol_index)
                    return SwapTop(self.namespace)
                case "\n\n":
                    self.skip_to.append(symbol_index)
                    return DiscardTop(self.namespace) 
        raise WRuntimeError("Unknown command")

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
                    self.skip_to.append(symbol_index)
                    return ReadCharToHeap(self.namespace)
                case "\t\t":
                    self.skip_to.append(symbol_index)
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
                case "  ":
                    label = self.parse_label(symbol_index+1)
                    if label in self.namespace.labels.keys():
                        raise WRuntimeError("Label already exists")
                    self.namespace.labels[label] = len(self.namespace.instruction_stack)-1
                    return Mark(self.namespace, label)
                case " \t":
                    label = self.parse_label(symbol_index+1)
                    return CallSub(self.namespace, label)
                case " \n":
                    label = self.parse_label(symbol_index+1)
                    return Jump(self.namespace, label)
                case "\t ":
                    label = self.parse_label(symbol_index+1)
                    return JumpIfZero(self.namespace, label)
                case "\t\t":
                    label = self.parse_label(symbol_index+1)
                    return JumpIfLess(self.namespace, label)
                case "\t\n":
                    self.skip_to.append(symbol_index)
                    return EndSub(self.namespace)
                case "\n\n":
                    self.skip_to.append(symbol_index)
                    return Exit(self.namespace)
    
    def parse_number(self, from_symbol):
        binary = ""
        sign = ""

        for symbol, symbol_index in self.iterate(from_symbol):
            if self.check_skippable(symbol):
                continue
            if not sign:
                if symbol == " ":
                    sign = "+"
                elif symbol == "\t":
                    sign = "-"
                else:
                    raise WRuntimeError(...)
                continue
            if symbol == "\n":
                break
            elif symbol == " ":
                binary += "0"
                continue
            elif symbol == "\t":
                binary += "1"
                continue
            else:
                raise WRuntimeError(...)

        self.skip_to.append(symbol_index)

        if not binary:
            return 0
        
        if sign == "+":
            number = int(binary, 2)
        elif sign == "-":
            number = -(int(binary, 2))
        
        return number
    
    def parse_label(self, from_symbol):
        label = ""
        for symbol, symbol_index in self.iterate(from_symbol):
            if self.check_skippable(symbol):
                continue
            if symbol == "\n":
                break
            if symbol in " \t":
                label += symbol
            else:
                raise WRuntimeError(...)
        self.skip_to.append(symbol_index)
        return label
