import directives
import lineparse

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


instructions = parse_content(open('testfile.au3').read())

for inst in instructions:
    print inst
    print
