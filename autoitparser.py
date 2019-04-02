import directives
import expressions
import traceback
import blocks


def evaluate_loop():
    while True:
        val = raw_input(">> ")

        try:
            root, root_end = expressions.parse_expression(val)
        except Exception as e:
            traceback.print_exc()
        else:
            print str(root)


block = blocks.parse_content(open('testfile.au3').read())

for line in block.processed_lines:
    print line
    print
