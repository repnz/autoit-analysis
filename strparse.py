import parse


def collapse_spaces(s):
    return ' '.join(s.split()).strip()


def find_one_of(seq, *options):
    for op in options:
        find_index = seq.find(op)

        if find_index != -1:
            return op, find_index

    return None, -1


def compile(exp):
    return parse.compile(exp, case_sensitive=True)
