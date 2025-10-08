from whitespace.parser import Parser
from whitespace.exceptions import WExit


def unbleach(n):
    return n.replace(' ', 's').replace('\t', 't').replace('\n', 'n')

def bleach(n):
    return n.replace("s", " ").replace("t", "\t").replace("n", "\n")

def run(code, input_stream = '', debug=False):
    parser = Parser(code)
    main = parser.parse()
    main.input = input_stream

    while True:
        try:
            main.next_instruction()
        except WExit:
            break
    if debug:
        print("\nSTACK:")
        print(main.stack)
        print("\nHEAP:")
        print(main.heap)
        print("\nINPUT:")
        print(main.input)
        print("\nOUTPUT:")
        print(main.output)
        
    return main.output

