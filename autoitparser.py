import directives
import lineparse
import expressions
import expnodes
import traceback
directive_classes = directives.get_directives()


def parse_content(content):
    raw_lines = lineparse.get_raw_lines(content)
    current_line = 0
    statements = []

    while current_line < len(raw_lines):
        directive_instance, current_line = directives.parse(raw_lines, current_line)

        if directive_instance is None:
            raise Exception("Error parsing line {line}".format(line=str(raw_lines[current_line])))
        statements.append(directive_instance)

    return statements


def evaluate_loop():
    while True:
        val = raw_input(">> ")

        try:
            root, root_end = expressions.parse_expression(val)
        except Exception as e:
            traceback.print_exc()
        else:
            print str(root)


#evaluate_loop()
#exit()
instructions = parse_content(open('testfile.au3').read())

for inst in instructions:
    print inst
    print
