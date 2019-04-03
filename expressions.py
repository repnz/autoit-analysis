import lineparse
import string
import itertools
import expnodes

operators_by_precedence =\
    (
        ('And', 'Or'),
        ('<=', '>=', '<>', '==', '<', '>', '='),
        ('&',),
        ('+', '-'),
        ('*', '/'),
        ('^',)
    )

needs_space = ('And', 'Or', 'Not')

all_operators = list(itertools.chain(*operators_by_precedence))


def get_precedence_level(operator):
    index, _ = lineparse.find_first(lambda ops: operator in ops, operators_by_precedence)
    return index


OPEN_PARENTHESIS = '('
CLOSE_PARENTHESIS = ')'

OPEN_BRACKETS = '['
CLOSE_BRACKETS = ']'


def strip_spaces(exp):
    i = 0

    for c in exp:
        if not (c == ' ' or c == '\t'):
            break
        else:
            i += 1

    return exp[i:], i


def read_values(exp, end_options=(), allow_more=False):
    if not exp:
        raise SyntaxError("Empty expression")

    end_options = list(end_options)
    is_error = True
    end_index = 0

    while exp and exp[0] not in end_options:
        exp, space_num = strip_spaces(exp)
        end_index += space_num

        node, node_end_index = get_first_node(exp)

        if node_end_index == -1:
            break

        is_error = False
        yield node
        end_index += node_end_index

        exp = exp[node_end_index:]

        exp, space_num = strip_spaces(exp)
        end_index += space_num

        op, op_end_index = get_operator(exp)

        if op_end_index == -1:
            break

        is_error = True
        exp = exp[op_end_index:]
        op = expnodes.BinaryOperatorNode(operator=op)
        end_index += op_end_index

        yield op

    exp, spaces_cnt = strip_spaces(exp)

    if not allow_more and end_options and (not exp or exp[0] not in end_options):
        raise SyntaxError("End character ({}) not met: {}".format(end_options, exp))

    if not allow_more and not end_options and exp:
        raise SyntaxError("Left chars in the expression: " + repr(exp))

    if is_error:
        raise SyntaxError("Missing operand:" + exp)

    yield end_index+spaces_cnt


def parse_expression(exp, end_options=(), allow_more=False):
    values = iter(list(read_values(exp, end_options, allow_more)))

    node = next(values)
    new_op = next(values)

    if isinstance(new_op, int):
        return node, new_op

    # Build first operator node
    new_op.a = node
    new_op.b = next(values)
    node = new_op
    new_op = next(values)

    # While has a next node
    while not isinstance(new_op, int):
        op_ptr = node

        # Get the correct level of the node
        while isinstance(op_ptr.b, expnodes.BinaryOperatorNode) and new_op.level > op_ptr.b.level:
            op_ptr = op_ptr.b

        # If it is lower
        if new_op.level > op_ptr.level:
            # Insert the operator lower
            new_op.a = op_ptr.b
            op_ptr.b = new_op
            new_op.b = next(values)
        else:
            # If it is higher
            # Make the new operator the root operator
            new_op.a = node
            new_op.b = next(values)
            node = new_op

        new_op = next(values)

    return node, new_op


def get_operator(exp):
    op_index, op = lineparse.find_first(lambda cur_op: exp.startswith(cur_op), all_operators)

    if op_index == -1:
        return None, op_index

    if op in needs_space and exp[len(op):len(op)+1] != ' ':
        raise SyntaxError("Operator {} needs space", op)

    return op, len(op)


def get_first_node(exp):
    exp, end_of_spaces = strip_spaces(exp)
    exp_node, end_index = get_first_node_without_spaces(exp)
    return exp_node, end_index + end_of_spaces


def get_first_node_without_spaces(exp):
    """
    Get the first node in an expression string
    :param exp: The expression string
    :return: (ExpressionNode node_object, int end_index)
    """

    if not exp:
        raise SyntaxError("Empty node")

    if exp[0] == OPEN_PARENTHESIS:
        return get_parenthesis_exp(exp)

    if exp[0].isdigit():
        return get_number(exp)

    if exp.startswith('0x'):
        return get_number(exp[2:], base=16)

    if exp[0] in ['@', '$']:
        var_end_index = get_name_end(exp[1:]) + 1
        var_name = exp[:var_end_index]

        # Variable containing a function
        if len(exp) > var_end_index and exp[var_end_index] == OPEN_PARENTHESIS:
            return get_function_call(var_name, exp[var_end_index:])

        # Normal variable usage
        else:
            return expnodes.VariableNode(name=var_name), var_end_index

    if exp[0] in ['"', "'"]:
        return get_string(exp)

    if exp[0] == OPEN_BRACKETS:
        return get_array(exp)

    name_end = get_name_end(exp)
    name = exp[:name_end]

    if name == 'True':
        return expnodes.ValueNode(True), name_end

    if name == 'False':
        return expnodes.ValueNode(False), name_end

    if name == 'Not':
        return get_not_node(exp, name_end)

    if len(exp) > name_end and exp[name_end] == OPEN_PARENTHESIS:
        return get_function_call(name, exp[name_end:])

    if len(name) > 0:
        return expnodes.FunctionReferenceNode(function_name=name), name_end

    raise SyntaxError('Error parsing value from {0}'.format(exp))


def get_not_node(exp, name_end):
    node, node_end = get_first_node(exp[name_end:])
    return expnodes.NotNode(value=node), node_end+name_end


def get_array(exp):
    items, end_index = parse_node_list(exp, end_char=CLOSE_BRACKETS)
    return expnodes.ArrayNode(items), end_index+1


def escape_string(unescaped_string, enclosing="'"):
    escaped_string = enclosing

    for char in unescaped_string:
        if char == enclosing:
            escaped_string += enclosing
        escaped_string += char
    escaped_string += enclosing
    return escaped_string


def get_string(exp):
    enclosing = exp[0]
    current_index = 1
    output_string = ""

    while True:
        if current_index == len(exp):
            raise SyntaxError("Missing closing {0}".format(enclosing))

        if exp[current_index] == enclosing:
            if (current_index+1) == len(exp) or \
                    exp[current_index+1] != enclosing:
                break
            else:
                current_index += 1

        output_string += exp[current_index]
        current_index += 1

    return expnodes.ValueNode(output_string), current_index+1


def get_function_call(func_name, exp):
    arguments, end_index = parse_node_list(exp, end_char=CLOSE_PARENTHESIS)
    return expnodes.FunctionCallNode(
        function_name=func_name,
        arguments=arguments
    ), end_index+len(func_name)+1


def parse_node_list(exp, end_char):
    """
    :param exp:
    A list of nodes ended in end_char
    For example, two arguments: "({node1}, {node2})" when end_char = ')'
    :param end_char: Signals the end of the node list
    :return: Returns a node representing the function call
    """

    current_index = 1

    # Skip open parenthesis
    arguments = []

    if exp[current_index] != end_char:
        while True:
            argument_node, argument_end = parse_expression(exp[current_index:],
                                                           end_options=(',', CLOSE_PARENTHESIS),
                                                           allow_more=True)
            arguments.append(argument_node)
            current_index += argument_end

            if current_index >= len(exp):
                raise SyntaxError("Missing Node List End: " + exp)

            if exp[current_index] == end_char:
                break

            if exp[current_index] != ',':
                raise SyntaxError("Missing ',' between items")

            current_index += 1

    return arguments, current_index


def get_parenthesis_exp(exp):
    node, end_index = parse_expression(exp[1:], end_options=(CLOSE_PARENTHESIS,))
    return node, end_index+2


def get_number(exp, base=10):
    end_index, dot_index = get_number_end(exp)
    number_value = exp[:end_index]

    if not number_value:
        raise SyntaxError("Number is empty")

    if dot_index != -1:
        if base == 16:
            raise SyntaxError("Hex values cannot contain dots: {0}".format(number_value))
        number_value = float(number_value)
    else:
        number_value = int(number_value, base)

    return expnodes.ValueNode(value=number_value), end_index


def get_number_end(exp):
    dot_index = -1
    char_index = -1

    for char_index, char in enumerate(exp):
        if char == '.':
            if dot_index != -1:
                raise SyntaxError("Number with multiple dots: {exp}".format(
                    exp=exp
                ))

            dot_index = char_index

        elif not char.isdigit():
            char_index -= 1
            break

    return char_index+1, dot_index


name_chars = string.letters + string.digits + '_'
name_first_letter = string.letters + '_'


def get_name_end(exp):
    if not exp:
        raise SyntaxError("Empty variable name")

    if exp[0] not in name_first_letter:
        raise SyntaxError("First letter is invalid: {0}".format(exp[0]))

    char_index, _ = lineparse.find_first(lambda char: char not in name_chars, exp)

    if char_index == -1:
        char_index = len(exp)

    return char_index


def validate_symbol_name(name):
    if not name:
        raise SyntaxError("Empty symbol name")

    if name[0] not in name_first_letter:
        raise SyntaxError("First letter is invalid: {}".format(name[0]))

    if not all(c in name_chars for c in name):
        raise SyntaxError("Invalid chars in symbol name: " + name)


def validate_variable_name(name):
    return name.startswith('$') and validate_symbol_name(name[1:])