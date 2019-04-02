class ProcessedLine(object):
    def __init__(self, number, statement, comment):
        self.number = number
        self.statement = statement
        self.comment = comment

    def __str__(self):
        return str(self.statement) + '' if not self.comment else '; ' + self.comment

    def __repr__(self):
        return 'Processed Line {number}: {code} {comment}'.format(
            number=self.number,
            code=str(self.statement),
            comment='' if not self.comment else '; ' + self.comment
        )


class RawLine(object):
    def __init__(self, number, content, comment):
        self.number = number
        self.content = content
        self.comment = comment

    def __str__(self):
        return 'Raw Line {number}: {content} {comment}'.format(
            number=self.number,
            content=self.content,
            comment='' if not self.comment else '; ' + self.comment
        )


def get_raw_lines(content):
    lines = content.split('\n')
    raw_lines = []

    for line_index, line in enumerate(lines, 1):
        line = line.strip()
        comment_start = line.find(';')

        if comment_start != -1:
            comment = line[:comment_start]
            line = line[:comment_start]
        else:
            comment = ''

        raw_line = RawLine(
            number=line_index,
            content=line,
            comment=comment
        )

        raw_lines.append(raw_line)

    return raw_lines


def find_first(func, seq, start=0, end=-1):
    if end == -1:
        end = len(seq)

    for i in xrange(start, end):
        if func(seq[i]):
            return i, seq[i]

    return -1, None


def find_line(lines, start_line, end_expression):
    for line_index in xrange(start_line, len(lines)):
        if lines[line_index].content == end_expression:
            return line_index
