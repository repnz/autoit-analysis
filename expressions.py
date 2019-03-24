import lineparse
import string


class ExpressionTree(object):
    def __init__(self, root_node):
        self.root_node = root_node


class ExpressionNode(object):
    pass


class BinaryOperatorNode(ExpressionNode):
    def __init__(self, operator, a=None, b=None):
        self.operator = operator
        self.a = a
        self.b = b

    def __str__(self):
        return "{a} {operator} {b}".format(
            a=self.a,
            operator=self.operator,
            b=self.b
        )


class FunctionCallNode(ExpressionNode):
    def __init__(self, function_name, arguments):
        self.function_name = function_name
        self.arguments = arguments


class VariableNode(ExpressionNode):
    def __init__(self, name):
        self.name = name


class ValueNode(ExpressionNode):
    def __init__(self, value):
        self.value = value


class ArrayNode(ExpressionNode):
    def __init__(self, items):
        self.items = items


operators_by_precedence =\
    (
        ('^',),
        ('*', '/'),
        ('+', '-'),
        ('&',),
        ('<', '>', '<=', '>=', '=', '<>', '=='),
        ('And', 'Or')
    )

needs_space = ('And', 'Or', 'Not')

all_operators = tuple(op for op_list in operators_by_precedence for op in operators_by_precedence)


def get_precedence_level(operator):
    index, _ = lineparse.find_first(lambda ops: operator in ops, operators_by_precedence)
    return len(operators_by_precedence) - index


OPEN_PARENTHESIS = '('
CLOSE_PARENTHESIS = ')'

OPEN_BRACKETS = '['
CLOSE_BRACKETS = ']'


def parse_expression(exp, end_char=''):
    exp = exp.strip()

    node, node_end_index = get_first_node(exp)

    exp = exp[node_end_index:]
    op1, op1_end_index = get_operator(exp)

    if op1_end_index == -1:
        return node

    exp = exp[op1_end_index:]
    op1 = BinaryOperatorNode(op1, a=node)

    while True:
        node, node_end_index = get_first_node(exp)
        exp = exp[op1_end_index:]
        op2, op2_end_index = get_operator(exp)

        if op2_end_index == -1:
            op1.b = node
            return op1,
        op2 = BinaryOperatorNode(op2)

        if get_precedence_level(op1.operator) > get_precedence_level(op2.operator):
            op1.b = node
            op2.a = op1
            op1 = op2
            op1_end_index = op2_end_index
        else:
            right_node, right_node_end = parse_expression(exp)

            if right_node_end == -1:
                raise SyntaxError("Missing operands for operator: {0}".format(op2.operator))

            op2.a, op2.b = node, right_node
            op1.b = op2
            break

        if op1_end_index >= len(exp) or exp[0] == end_char:
            break

    if exp != end_char:
        raise SyntaxError("Expressions needs to end with '{0}': Left Chars - '{1}'".format(
            end_char, exp
        ))

    return op1, end_index


def get_operator(exp):
    op_index, op = lineparse.find_first(lambda op: exp.startswith(op), all_operators)

    if op_index == -1:
        return None, op_index

    if op in needs_space and exp[:len(op)] == ' ':
        raise SyntaxError("Operator {} needs space", op)

    return op, len(op)


def get_first_node(exp):
    """
    Get the first node in an expression string
    :param exp: The expression string
    :return: (ExpressionNode node_object, int end_index)
    """

    if exp[0] == OPEN_PARENTHESIS:
        return get_parenthesis_exp(exp)

    if exp[0].isdigit():
        return get_number(exp)

    if exp.startswith('0x'):
        return get_number(exp[2:], base=16)

    if exp[0] in ['@', '$']:
        var_end_index = get_name_end(exp[1:])
        var_name = exp[:var_end_index]

        # Variable containing a function
        if exp[var_end_index] == OPEN_PARENTHESIS:
            return get_function_call(var_name, exp)

        # Normal variable usage
        else:
            return VariableNode(name=var_name), var_end_index

    if exp[0] in ['"', "'"]:
        return get_string(exp)

    if exp[0] == OPEN_BRACKETS:
        return get_array(exp)

    name_end = get_name_end(exp)
    name = exp[:name_end]

    if name in ['False', 'True']:
        return ValueNode(bool(name)), name_end

    if exp[:name_end] == OPEN_PARENTHESIS:
        return get_function_call(name, exp[name_end:])

    raise SyntaxError('Error parsing value from {0}'.format(exp))


def get_array(exp):
    items, end_index = parse_node_list(exp, end_char=CLOSE_BRACKETS)
    return ArrayNode(items), end_index


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

    return ValueNode(output_string), current_index


def get_function_call(func_name, exp):
    arguments, end_index = parse_node_list(exp, end_char=CLOSE_PARENTHESIS)
    return FunctionCallNode(
        function_name=func_name,
        arguments=arguments
    ), end_index


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
            argument_node, argument_end = parse_expression(exp[current_index:])
            arguments.append(argument_node)
            current_index += argument_end

            if exp[current_index] == end_char:
                break

            if exp[current_index] != ',':
                raise SyntaxError("Missing ',' between items")

    return arguments, current_index


def get_closing_parenthesis(exp):
    cnt = 0

    for index, char in enumerate(exp):
        if char == OPEN_PARENTHESIS:
            cnt += 1

        elif char == CLOSE_PARENTHESIS:
            cnt -= 1

            if cnt == 0:
                return index

    raise SyntaxError("Could not find closing parenthesis for expression: {0}".format(exp))


def get_parenthesis_exp(exp):
    end_index = get_closing_parenthesis(exp)

    return parse_expression(exp[1:end_index]), end_index+1


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

    return ValueNode(value=number_value), end_index


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
            return char_index, dot_index

    return char_index, dot_index


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

