import lineparse
import directives


class CodeBlock(object):
    def __init__(self, processed_lines):
        self.processed_lines = processed_lines

    def __str__(self):
        return '\n'.join(map(str, self.processed_lines))

    def __repr__(self):
        return 'CodeBlock(processed_lines={})'.format(
            ','.join(map(repr, self.processed_lines)),
        )


def parse_lines(raw_lines, current_line_index,
                end_condition=None, end_err=None):
    processed_lines = []

    while current_line_index < len(raw_lines):
        if end_condition is not None and \
                end_condition(raw_lines[current_line_index].content):
            break

        parsed_line_index = current_line_index
        directive_instance, current_line_index = directives.parse(raw_lines, current_line_index)

        if directive_instance is None:
            raise Exception("Error parsing line {line}".format(line=str(raw_lines[parsed_line_index])))

        processed_lines.append(lineparse.ProcessedLine(
            number=parsed_line_index,
            statement=directive_instance,
            comment=raw_lines[parsed_line_index].comment
        ))
    else:
        if end_condition is not None:
            raise SyntaxError("One of the end lines was not met: " + end_err)

    return CodeBlock(processed_lines=processed_lines), current_line_index


def parse_content(content):
    raw_lines = lineparse.get_raw_lines(content)
    block, _ = parse_lines(raw_lines, 0)
    return block
