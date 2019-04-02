import strparse
import lineparse
import expressions
import expnodes
import blocks

NO_MATCH = None, -1


class BaseDirective(object):
    possible_keywords = []
    starts_with = False

    @classmethod
    def try_parse(cls, raw_lines, current_line):
        if not cls._is_match(raw_lines[current_line]):
            return None, -1

        instance, current_line = cls.parse(raw_lines, current_line)
        return instance, current_line

    @classmethod
    def _is_match(cls, raw_line):
        if not raw_line.content:
            return False

        content = raw_line.content.split()[0]

        if cls.starts_with:
            return any((content.startswith(keyword) for keyword in cls.possible_keywords))
        else:
            return any((content == keyword for keyword in cls.possible_keywords))

    @classmethod
    def parse(cls, raw_lines, current_line):
        raise NotImplemented


class PragmaDirective(BaseDirective):
    possible_keywords = ['#pragma']
    exp = strparse.compile('#pragma {setting:1}')

    def __init__(self, setting):
        self.setting = setting

    def __str__(self):
        return "#pragma {setting}".format(setting=self.setting)

    @classmethod
    def parse(cls, raw_lines, current_line):
        raw_line = raw_lines[current_line]
        exp_result = PragmaDirective.exp.parse(raw_line.content)

        if exp_result is None:
            raise SyntaxError("Error in {line}".format(line=str(raw_line)))

        return PragmaDirective(exp_result['setting']), current_line + 1


class IncludeDirective(BaseDirective):
    possible_keywords = ["#include"]
    exp = strparse.compile("#include {start:1.1}{name:1}{end:1.1}")

    ORDER_SCRIPT_RELATIVE = 1
    ORDER_INCLUDES_RELATIVE = 2

    def __init__(self, name, order_type):
        self.name = name
        self.order_type = order_type

    def __str__(self):
        start, end = self.clause()
        return "include {start}{name}{end}".format(
            start=start,
            name=self.name,
            end=end
        )

    def clause(self):
        if self.order_type == IncludeDirective.ORDER_SCRIPT_RELATIVE:
            return '<', '>'
        return '"', '"'

    @classmethod
    def parse(cls, raw_lines, current_line):
        raw_line = raw_lines[current_line]
        exp_result = IncludeDirective.exp.parse(raw_line.content)

        if exp_result is None:
            raise SyntaxError("Error in {line}".format(line=str(raw_line)))

        start, name, end = exp_result['start'], exp_result['name'], exp_result['end']

        if start == '<' and end == '>':
            order_type = IncludeDirective.ORDER_INCLUDES_RELATIVE

        elif start == '"' and end == '"':
            order_type = IncludeDirective.ORDER_SCRIPT_RELATIVE

        else:
            raise SyntaxError("Error in {line}".format(line=str(raw_line)))

        return IncludeDirective(name, order_type), current_line + 1


class OnAutoItStartRegisterDirective(BaseDirective):
    possible_keywords = ['#OnAutoItStartRegister']
    exp = strparse.compile('#OnAutoItStartRegister "{function_name:1}"')

    def __init__(self, function_name):
        self.function_name = function_name

    def __str__(self):
        return '#OnAutoItStartRegister "{function_name}"'.format(
            function_name=self.function_name
        )

    @classmethod
    def parse(cls, raw_lines, current_line):
        raw_line = raw_lines[current_line]
        exp_result = OnAutoItStartRegisterDirective.exp.parse(raw_line.content)

        if exp_result is None:
            raise SyntaxError("Error in {line}".format(line=str(raw_line)))

        function_name = exp_result['function_name']

        return OnAutoItStartRegisterDirective(function_name), current_line + 1


class CommentsSectionDirective(BaseDirective):
    end_keywords = '#comments-end', '#ce'
    possible_keywords = ['#comments-start', '#cs']

    def __init__(self, comments):
        self.comments = comments

    def __str__(self):
        return "{start}\n{comments}\n{end}".format(
            start=CommentsSectionDirective.possible_keywords[0],
            comments=self.comments,
            end=CommentsSectionDirective.end_keywords[0]
        )

    @classmethod
    def parse(cls, raw_lines, current_line):
        start_line = current_line + 1
        end_line, _ = lineparse.find_first(
            func=lambda line: line.content in CommentsSectionDirective.end_keywords,
            seq=raw_lines,
            start=start_line
            )

        if end_line == -1:
            raise SyntaxError("Missing #comments-end")

        comment_section = '\n'.join(line.content for line in raw_lines[start_line:end_line])
        return CommentsSectionDirective(comment_section), end_line + 1


class DirectiveFlag(BaseDirective):
    possible_keywords = ['#']
    exp = strparse.compile('#{flag_name}')
    starts_with = True

    def __init__(self, flag_name):
        self.flag_name = flag_name

    def __str__(self):
        return "#{flag_name}".format(flag_name=self.flag_name)

    @classmethod
    def parse(cls, lines, current_line):
        line = lines[current_line]
        exp_result = DirectiveFlag.exp.parse(line.content)

        if exp_result is None:
            raise SyntaxError

        flag_name = exp_result['flag_name']
        return DirectiveFlag(flag_name), current_line + 1


class EmptyLine(BaseDirective):
    def __str__(self):
        return ''

    @classmethod
    def _is_match(cls, line):
        return not line.content

    @classmethod
    def parse(cls, _, current_line):
        return EmptyLine(), current_line + 1


class VariableDeclaration(object):

    Local = 'Local'
    Global = 'Global'
    Dim = 'Dim'
    Const = 'Const'
    keywords = [Local, Global, Dim, Const]

    def __init__(self, scope_type, is_const, variables):
        self.scope_type = scope_type
        self.is_const = is_const
        self.variables = dict(variables)

    def __repr__(self):
        return "VariableDecleration(scope_type={}, is_const={}, variables={})".format(
            repr(self.scope_type),
            repr(self.is_const),
            repr(self.variables)
        )

    def __str__(self):
        line = self.scope_type + ' '

        if self.is_const:
            line += 'Const '

        line += ', '.join(['{} = {}'.format(key, value) for key, value in self.variables.iteritems()])
        return line

    @classmethod
    def try_parse(cls, raw_lines, current_line):
        # {scope} {name} at least!
        line_content = raw_lines[current_line].content
        parts = line_content.split(' ', 1)

        if len(parts) < 2:
            return NO_MATCH

        scope_type, is_const, assignments = cls.get_declaration_properties(parts)

        if scope_type is None:
            return NO_MATCH

        variables = {}

        while assignments:
            var_name, var_node, var_end = cls.parse_first_assignment(assignments)
            variables[var_name] = var_node
            assignments = assignments[var_end:]

        node = VariableDeclaration(scope_type=scope_type,
                                   is_const=is_const,
                                   variables=variables)

        return node, current_line+1

    @classmethod
    def parse_first_assignment(cls, assignment):

        c_index, c = lineparse.find_first(lambda current_char: current_char in (',', '='), assignment)

        if c_index == -1:  # If assignment / next variable not found
            c_index = len(assignment)

        variable_name = assignment[:c_index].strip()

        if not variable_name.startswith('$'):
            raise SyntaxError("Variable name must start in '$'! Variable: {variable}".format(
                variable=variable_name
            ))

        # Initialized with an expression
        if c == '=':
            # Parse the expression
            if len(assignment) == c_index:
                raise SyntaxError("Empty Assignment Value")

            exp_str = assignment[c_index+1:]
            exp_tree, exp_end = expressions.parse_expression(exp_str,
                                                             end_options=(',',),
                                                             allow_more=True)
            variable_value = exp_tree
        else:
            variable_value = expnodes.ValueNode(value='')
            exp_end = len(assignment)

        return variable_name, variable_value, c_index+1+exp_end+1

    @classmethod
    def get_declaration_properties(cls, parts):
        first_keyword = parts[0]
        is_const = False

        if first_keyword == VariableDeclaration.Local:
            scope_type = VariableDeclaration.Local

        elif first_keyword == VariableDeclaration.Const:
            scope_type = VariableDeclaration.Local
            is_const = True

        elif first_keyword == VariableDeclaration.Dim:
            scope_type = VariableDeclaration.Dim

        elif first_keyword == VariableDeclaration.Global:
            scope_type = VariableDeclaration.Global

        else:
            return None, None, None

        if not is_const and parts[1].startswith(VariableDeclaration.Const + ' '):
            is_const = True
            assignments = parts[1].split(' ', 1)

            if len(assignments) < 2:
                raise SyntaxError("Missing assignments: " + ' '.join(parts))

            assignments = assignments[1]
        else:
            assignments = parts[1]

        return scope_type, is_const, assignments


class ConditionBlock(object):
    def __init__(self, exp, block):
        self.exp = exp
        self.block = block


class IfStatement(BaseDirective):
    if_exp = strparse.compile('If {exp} Then')
    elseif_exp = strparse.compile('ElseIf {exp} Then')

    def __init__(self, condition_blocks, else_block):
        self.condition_blocks = condition_blocks
        self.else_block = else_block

    def __str__(self):
        x = str(self.condition_blocks[0].exp)
        s = 'If {exp} Then\n'.format(exp=str(self.condition_blocks[0].exp))
        s += str(self.condition_blocks[0].block) + '\n'

        for else_if in self.condition_blocks[1:]:
            s += 'ElseIf {exp} Then\n'.format(exp=str(else_if.exp))
            s += str(else_if.block) + '\n'

        if self.else_block is not None:
            s += 'Else\n' + str(self.else_block) + '\n'

        s += 'EndIf'
        return s

    @classmethod
    def try_parse(cls, raw_lines, current_line):
        line = raw_lines[current_line].content

        if not line.startswith('If '):
            return NO_MATCH

        exp_result = IfStatement.if_exp.parse(line)

        if exp_result is None:
            raise SyntaxError("Cannot parse If line: {}".format(line))

        if_expression = exp_result['exp']

        condition_blocks = []

        if_expression_node, _ = expressions.parse_expression(if_expression)
        block, current_line = blocks.parse_lines(raw_lines, current_line+1,
                                                 end_condition=cls.__end_condition)

        condition_blocks.append(ConditionBlock(exp=if_expression_node, block=block))

        else_if_blocks, current_line = cls.__parse_else_if_blocks(raw_lines, current_line)

        condition_blocks += else_if_blocks

        if raw_lines[current_line].content == 'Else':
            else_block, current_line = blocks.parse_lines(raw_lines,
                                                          current_line+1,
                                                          end_condition=lambda x: x == 'EndIf')
        else:
            else_block = None

        return IfStatement(
            condition_blocks=condition_blocks,
            else_block=else_block
        ), current_line+1

    @classmethod
    def __parse_else_if_blocks(cls, raw_lines, current_line):
        condition_blocks = []

        while current_line < len(raw_lines) and \
                raw_lines[current_line].content.startswith('ElseIf '):

            else_if_expression = IfStatement.elseif_exp.parse(raw_lines[current_line].content)

            if else_if_expression is None:
                raise SyntaxError("Could not parse ElseIf Expression: " + str(raw_lines[current_line]))

            else_if_expression_node, _ = expressions.parse_expression(else_if_expression['exp'])

            else_if_block, current_line = blocks.parse_lines(
                raw_lines,
                current_line + 1,
                end_condition=cls.__end_condition
            )

            condition_blocks.append(ConditionBlock(exp=else_if_expression_node,
                                                   block=else_if_block))

        return condition_blocks, current_line

    @classmethod
    def __end_condition(cls, line_content):
        if line_content == 'Else':
            return True

        if line_content == 'EndIf':
            return True

        if line_content.startswith('ElseIf '):
            return True

        return False


def get_directives():
    return (
        PragmaDirective,
        IncludeDirective,
        OnAutoItStartRegisterDirective,
        CommentsSectionDirective,
        DirectiveFlag,
        VariableDeclaration,
        IfStatement,
        EmptyLine
    )


def parse(raw_lines, current_line):

    for directive in get_directives():
        val = directive.try_parse(raw_lines, current_line)

        if val != NO_MATCH:
            return val

    raise Exception("No matching directive for {line}".format(
        line=str(raw_lines[current_line])
    ))
