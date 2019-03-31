import expressions
import pytest
import expnodes


def test_number_node():
    node, node_end = expressions.parse_expression("10")

    assert 10 == node.value
    assert node_end == 2


def test_string_node():
    s = "Hello World!"
    ts = '"{0}"'.format(s)

    node, node_end = expressions.parse_expression(ts)
    assert s == ts[1:-1]
    assert node_end == len(ts)


def test_string_enclosing_error():
    with pytest.raises(SyntaxError) as e_info:
        expressions.parse_expression('"hello world')


def test_get_operator_plus():
    op, op_end = expressions.get_operator("+")

    assert op == '+'
    assert op_end == 1


def test_basic_addition():
    exp = '10 + 20'
    node, node_end = expressions.parse_expression(exp)
    expected = expnodes.BinaryOperatorNode(
        operator='+',
        a=expnodes.ValueNode(10),
        b=expnodes.ValueNode(20)
    )

    assert node == expected
    assert node_end == len(exp)


def test_two_additions():
    exp = '10 + 20 + 30'
    node, node_end = expressions.parse_expression(exp)
    expected = expnodes.BinaryOperatorNode(
        operator='+',
        a=expnodes.BinaryOperatorNode(
            operator='+',
            a=expnodes.ValueNode(10),
            b=expnodes.ValueNode(20)
        ),
        b=expnodes.ValueNode(30)
    )

    assert node == expected
    assert node_end == len(exp)


def test_additions_without_spacing():
    exp = '10+20+30'
    node, node_end = expressions.parse_expression(exp)
    expected = expnodes.BinaryOperatorNode(
        operator='+',
        a=expnodes.BinaryOperatorNode(
            operator='+',
            a=expnodes.ValueNode(10),
            b=expnodes.ValueNode(20)
        ),
        b=expnodes.ValueNode(30)
    )

    assert node == expected
    assert node_end == len(exp)


def test_mul_before_addition():
    exp = '10+20*30'
    node, node_end = expressions.parse_expression(exp)
    expected = expnodes.BinaryOperatorNode(
        operator='+',
        a=expnodes.ValueNode(10),
        b=expnodes.BinaryOperatorNode(
            operator='*',
            a=expnodes.ValueNode(20),
            b=expnodes.ValueNode(30)
        )
    )

    assert node == expected
    assert node_end == len(exp)


def test_insert_sub_node():
    exp = '10+20*30*40'
    node, node_end = expressions.parse_expression(exp)
    expected = expnodes.BinaryOperatorNode(
        operator='+',
        a=expnodes.ValueNode(10),
        b=expnodes.BinaryOperatorNode(
            operator='*',
            a=expnodes.BinaryOperatorNode(
                operator='*',
                a=expnodes.ValueNode(20),
                b=expnodes.ValueNode(30)
            ),
            b=expnodes.ValueNode(40)
        )
    )

    assert node == expected
    assert node_end == len(exp)


def test_insert_sub_node_and_add():
    exp = '10+20*30*40+40'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.BinaryOperatorNode(
            operator='+',
            a=expnodes.BinaryOperatorNode(
                operator='+',
                a=expnodes.ValueNode(10),
                b=expnodes.BinaryOperatorNode(
                    operator='*',
                    a=expnodes.BinaryOperatorNode(
                        operator='*',
                        a=expnodes.ValueNode(20),
                        b=expnodes.ValueNode(30)
                    ),
                    b=expnodes.ValueNode(40)
                )
            ),
            b=expnodes.ValueNode(40)
        )

    assert node == expected
    assert node_end == len(exp)


def test_basic_parenthesis():
    exp = '10+(200+300)'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.BinaryOperatorNode(
            operator='+',
            b=expnodes.BinaryOperatorNode(
                operator='+',
                a=expnodes.ValueNode(200),
                b=expnodes.ValueNode(300)
            ),
            a=expnodes.ValueNode(10)
        )

    assert node == expected
    assert node_end == len(exp)


def test_nested_parenthesis():
    exp = '10+((1+2)*(3+4))+30'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.BinaryOperatorNode(
            operator='+',
            a=expnodes.BinaryOperatorNode(
                operator='+',
                a=expnodes.ValueNode(10),
                b=expnodes.BinaryOperatorNode(
                    operator='*',
                    a=expnodes.BinaryOperatorNode(
                        operator='+',
                        a=expnodes.ValueNode(1),
                        b=expnodes.ValueNode(2)
                    ),
                    b=expnodes.BinaryOperatorNode(
                        operator='+',
                        a=expnodes.ValueNode(3),
                        b=expnodes.ValueNode(4)
                    )
                )
            ),
            b=expnodes.ValueNode(30)
        )

    assert node == expected
    assert node_end == len(exp)


def test_variable_exp():
    exp = '10+$value*12'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.BinaryOperatorNode(
            operator='+',
            b=expnodes.BinaryOperatorNode(
                operator='*',
                a=expnodes.VariableNode("$value"),
                b=expnodes.ValueNode(12)
            ),
            a=expnodes.ValueNode(10)
        )

    assert node == expected
    assert node_end == len(exp)


def test_string_nodes():
    exp = '"Bye" & "\'Hello\'"'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.BinaryOperatorNode(
            operator='&',
            a=expnodes.ValueNode("Bye"),
            b=expnodes.ValueNode("\'Hello\'")
        )

    assert node == expected
    assert node_end == len(exp)


def test_boolean_node():
    exp = 'False And True'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.BinaryOperatorNode(
            operator='And',
            a=expnodes.ValueNode(False),
            b=expnodes.ValueNode(True)
        )

    assert node == expected
    assert node_end == len(exp)


def test_array_node():
    exp = '[1, 2, 4, 5, 20+30]'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.ArrayNode(
            [
                expnodes.ValueNode(1),
                expnodes.ValueNode(2),
                expnodes.ValueNode(4),
                expnodes.ValueNode(5),
                expnodes.BinaryOperatorNode(operator='+',
                                            a=expnodes.ValueNode(20),
                                            b=expnodes.ValueNode(30)
                                            )
            ]
        )

    assert node == expected
    assert node_end == len(exp)


def test_function_call():
    exp = 'MyFunc(10, 20)'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.FunctionCallNode(
            function_name='MyFunc',
            arguments=[
                expnodes.ValueNode(10),
                expnodes.ValueNode(20)
            ]
        )

    assert node == expected
    assert node_end == len(exp)


def test_not_call():
    exp = 'Not (10 = 12)'

    node, node_end = expressions.parse_expression(exp)
    expected = \
        expnodes.NotNode(
            value=expnodes.BinaryOperatorNode(
                operator='=',
                a=expnodes.ValueNode(10),
                b=expnodes.ValueNode(12)
            )
        )

    assert node == expected
    assert node_end == len(exp)


def test_unexpected_end():
    exp = '10 +'

    with pytest.raises(SyntaxError) as e_info:
        expressions.parse_expression(exp)


def test_strip_spaces():
    exp = '    10'
    exp, _ = expressions.strip_spaces(exp)
    assert '10' == exp


def test_end_with_spaces():
    expressions.parse_expression('10   ')


def test_get_var():
    var = '$val'
    node, node_end = expressions.parse_expression(var)

    assert node == expnodes.VariableNode(var)
    assert node_end == len(var)


def test_var_function_call():
    var = '$var'
    call = '$var(1, 2)'
    node, node_end = expressions.parse_expression(call)
    assert expnodes.FunctionCallNode(
        function_name=var,
        arguments=[
            expnodes.ValueNode(1),
            expnodes.ValueNode(2)
        ]
    ) == node

    assert node_end == len(call)


def test_multi_char_operators():
    exp = 'True <> False'
    node, node_end = expressions.parse_expression(exp)

    assert node == expnodes.BinaryOperatorNode(
        operator='<>',
        a=expnodes.ValueNode(True),
        b=expnodes.ValueNode(False)
    )

    assert node_end == len(exp)