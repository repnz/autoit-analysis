import expressions

BINARY_OPERATOR = 'BINARY_OPERATOR'
FUNCTION_CALL = 'FUNCTION_CALL'
VARIABLE = 'VARIABLE'
VALUE = 'VALUE'
ARRAY = 'ARRAY'
NOT = 'NOT'
PARENTHESIS = 'PARENTHESIS'
FUNCTION_REFERENCE = 'FUNCTION_REFERENCE'


class ExpressionNode(object):
    def __init__(self, node_type):
        self.node_type = node_type

    def __ne__(self, other):
        return not (self == other)


class NotNode(ExpressionNode):
    def __init__(self, value):
        super(NotNode, self).__init__(NOT)
        self.value = value

    def __str__(self):
        return "Not {value}".format(
            value=self.value,
        )

    def __eq__(self, other):
        if not isinstance(other, NotNode):
            return NotImplemented
        return other.value == self.value

    def __repr__(self):
        return "{cls}(value={value})".format(
            cls=NotNode.__name__,
            value=repr(self.value)
        )


class BinaryOperatorNode(ExpressionNode):
    def __init__(self, operator, a=None, b=None):
        super(BinaryOperatorNode, self).__init__(BINARY_OPERATOR)
        self.operator = operator
        self.a = a
        self.b = b
        self.level = expressions.get_precedence_level(self.operator)

    def __str__(self):
        return "({a} {operator} {b})".format(
            a=self.a,
            operator=self.operator,
            b=self.b
        )

    def __repr__(self):
        return "{cls}(operator={op}, a={a}, b={b})".format(
            cls=BinaryOperatorNode.__name__,
            op=repr(self.operator),
            a=repr(self.a),
            b=repr(self.b)
        )

    def __eq__(self, other):
        if not isinstance(other, BinaryOperatorNode):
            return False

        return (self.operator, self.a, self.b) == (other.operator, other.a, other.b)


class FunctionCallNode(ExpressionNode):
    def __init__(self, function_name, arguments):
        super(FunctionCallNode, self).__init__(FUNCTION_CALL)
        self.function_name = function_name
        self.arguments = arguments

    def __str__(self):
        return '{function_name}({arguments})'.format(
            function_name=self.function_name,
            arguments=', '.join(map(str, self.arguments))
        )

    def __repr__(self):
        return "{cls}(function_name={function_name}, arguments={arguments}".format(
            cls=FunctionCallNode.__name__,
            function_name=repr(self.function_name),
            arguments=repr(self.arguments)
        )

    def __eq__(self, other):
        if not isinstance(other, FunctionCallNode):
            return NotImplemented

        return (self.function_name, self.arguments) == (other.function_name, other.arguments)


class VariableNode(ExpressionNode):
    def __init__(self, name):
        super(VariableNode, self).__init__(VARIABLE)
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{cls}(name={name})'.format(
            name=repr(self.name),
            cls=VariableNode.__name__
        )

    def __eq__(self, other):
        if not isinstance(other, VariableNode):
            return NotImplemented

        return self.name == other.name


class ValueNode(ExpressionNode):
    def __init__(self, value):
        super(ValueNode, self).__init__(VALUE)
        self.value = value

    def __str__(self):
        value = self.value

        if isinstance(self.value, str):
            value = expressions.escape_string(self.value)

        return str(value)

    def __repr__(self):
        return "{cls}(value={value})".format(
            cls=ValueNode.__name__,
            value=repr(self.value)
        )

    def __eq__(self, other):
        if not isinstance(other, ValueNode):
            return NotImplemented

        if not isinstance(other.value, type(self.value)):
            return NotImplemented

        return self.value == other.value


class ArrayNode(ExpressionNode):
    def __init__(self, items):
        super(ArrayNode, self).__init__(ARRAY)
        self.items = items

    def __str__(self):
        return str(self.items)

    def __repr__(self):
        return repr(self.items)

    def __eq__(self, other):
        if not isinstance(other, ArrayNode):
            return NotImplemented

        return self.items == other.items


class FunctionReferenceNode(ExpressionNode):
    def __init__(self, function_name):
        super(FunctionReferenceNode, self).__init__(FUNCTION_REFERENCE)
        self.function_name = function_name

    def __str__(self):
        return self.function_name

    def __repr__(self):
        return '{cls}(function_name={name})'.format(
            cls=FunctionReferenceNode.__name__,
            name=repr(self.function_name)
        )

    def __eq__(self, other):
        if not isinstance(other, FunctionReferenceNode):
            return NotImplemented

        return self.function_name == other.function_name
