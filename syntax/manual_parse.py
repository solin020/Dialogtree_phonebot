import re

constituency_lex_dict = {
    'lpar': r'\(',
    'rpar': r'\)',
    'whitespace': r'[ \t\n]+',
    'word': r'[^\)\( \t\n]+',
        }

constituency_lex_regex = '|'.join(
        f'(?P<{k}>{v})' for k, v in constituency_lex_dict.items()
        )

def find_entry(dict_):
    for k, v in dict_.items():
        if v: 
            return (k, v)


def constituency_lex(input_string):
    for match in re.finditer(constituency_lex_regex, input_string):
        k, v = find_entry(match.groupdict())
        if k != 'whitespace':
            yield (k, v)

def constituency_parse(input_, start = True):
    from depth import ConstituencyTree
    if start:
        input_ = constituency_lex(input_)
        assert next(input_)[0] == 'lpar', 'Syntax error'
    k, node_type = next(input_)
    assert k == 'word', 'Syntax error'
    
    children = []
    
    k, potential_word = next(input_)
    assert k != 'rpar', 'Syntax error'
    if k == 'word':
        assert next(input_)[0] == 'rpar', 'Syntax error'
        return ConstituencyTree(node_type, word=potential_word)
    elif k == 'lpar':
        children.append(constituency_parse(input_, False))
    
    for k, constituency_lexeme in input_:
        assert k != 'word', 'Syntax error'
        if k == 'lpar':
            children.append(constituency_parse(input_, False))
        elif k == 'rpar':
            return ConstituencyTree(node_type, children)

dependency_lex_dict = {
    'lpar': r'\(',
    'rpar': r'\)',
    'whitespace': r'[ \t\n]+',
    'comma': r',',
    'word': r'[^\)\( \t\n\-,]+',
    'dash': r'-',
        }

dependency_lex_regex = '|'.join(
        f'(?P<{k}>{v})' for k, v in dependency_lex_dict.items()
        )

def dependency_lex(input_string):
    for match in re.finditer(dependency_lex_regex, input_string):
        k, v = find_entry(match.groupdict())
        if k != 'whitespace':
            yield (k, v)

def dependency_parse(input_):
    from depth import DependencyTree
    input_ = dependency_lex(input_)
    dt = DependencyTree()
    try:
        while True:
            k, relation_type = next(input_)
            assert k == 'word', 'Syntax error'
            k, lpar = next(input_)
            assert k == 'lpar', 'Syntax error'
            k, head = next(input_)
            assert k == 'word', 'Syntax error'
            k, dash = next(input_)
            assert k == 'dash', 'Syntax error'
            k, head_pos = next(input_)
            assert k == 'word', 'Syntax error'
            k, comma = next(input_)
            assert k == 'comma', 'Syntax error'
            k, tail = next(input_)
            assert k == 'word', 'Syntax error'
            k, dash = next(input_)
            assert k == 'dash', 'Syntax error'
            k, tail_pos = next(input_)
            assert k == 'word', 'Syntax error'
            k, rpar = next(input_)
            assert k == 'rpar', 'Syntax error'
            dt.add(head, int(head_pos), relation_type, tail, int(tail_pos))
    except StopIteration:
        return dt
