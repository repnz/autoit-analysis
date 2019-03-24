import strparse
import lineparse
import expressions

NO_MATCH = False, None, -1


class BaseDirective(object):
    possible_keywords = []
    starts_with = False

    @classmethod
    def try_parse(cls, raw_lines, current_line):
        if not cls.is_match(raw_lines[current_line]):
            return False, None, -1

        instance, current_line = cls.parse(raw_lines, current_line)
        return True, instance, current_line

    @classmethod
    def is_match(cls, raw_line):
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


class EmptyLine(object):
    def __str__(self):
        return ''

    @classmethod
    def is_match(cls, line):
        return not line.content

    @classmethod
    def parse(cls, raw_lines, current_line):
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

    @classmethod
    def try_parse(cls, line):
        parts = line.content.split()

        if len(parts) < 2:
            return NO_MATCH

        scope_type, is_const = cls.get_declaration_properties(parts)

        if scope_type is None:
            return NO_MATCH

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

        expressions.parse_expression(assignment)

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
            return None, None

        if parts[1] == VariableDeclaration.Const:
            is_const = True

        return scope_type, is_const


def get_directives():
    return (
        PragmaDirective,
        IncludeDirective,
        OnAutoItStartRegisterDirective,
        CommentsSectionDirective,
        DirectiveFlag,
        EmptyLine
    )


def get_match(raw_line):
    for directive in get_directives():
        if directive.is_match(raw_line):
            return directive


def parse(raw_lines, current_line):
    match_directive = get_match(raw_lines[current_line])

    if match_directive is None:
        raise Exception("No matching directive for {line}".format(
            line=str(raw_lines[current_line])
        ))

    return match_directive.parse(raw_lines, current_line)
