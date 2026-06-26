import re

KEYWORDS = {
    # control flow
    'if', 'else', 'elif', 'while', 'for', 'do', 'switch', 'case', 'default',
    'break', 'continue', 'return', 'goto', 'pass', 'yield',
    # declarations / types
    'int', 'float', 'double', 'char', 'bool', 'boolean', 'void', 'string',
    'long', 'short', 'unsigned', 'signed', 'byte', 'var', 'let', 'const',
    'auto', 'def', 'function', 'class', 'struct', 'enum', 'interface',
    'public', 'private', 'protected', 'static', 'final', 'abstract',
    'virtual', 'override', 'extends', 'implements', 'namespace', 'package',
    'template', 'typename', 'typedef', 'union',
    # literals / values
    'true', 'false', 'True', 'False', 'null', 'None', 'nil', 'undefined',
    'NULL',
    # logical / membership operators-as-words
    'and', 'or', 'not', 'in', 'is', 'xor',
    # module / oop
    'import', 'from', 'as', 'export', 'new', 'this', 'self', 'super',
    'delete', 'instanceof', 'sizeof',
    # exceptions
    'try', 'except', 'catch', 'finally', 'throw', 'throws', 'raise',
    # misc builtins commonly tested in toy lexers
    'print', 'input', 'len', 'range', 'global', 'nonlocal', 'lambda',
    'async', 'await', 'with',
}

token_specification = [
    # Comments (skipped, never emitted as tokens)
    ('COMMENT',    r'//[^\n]*|/\*[\s\S]*?\*/|'),

    # Whitespace (skipped)
    ('WHITESPACE', r'[ \t\r\n]+'),

    # String literals — double quoted, with escape handling.
    # Triple-quoted Python strings handled too.
    ('STRING',     r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"\\\n]*(?:\\.[^"\\\n]*)*"'),

    # Char literal (single quote, single char or escape) — must come before
    # the generic single-quoted-string fallback below.
    ('CHAR',       r"'[^'\\\n]'|'\\.'"),

    # Fallback single-quoted string (JS/Python use 'single quotes' for strings too)
    ('STRING2',    r"'[^'\\\n]*(?:\\.[^'\\\n]*)*'"),

    # Numbers: hex, binary, scientific notation, decimals, ints
    ('NUMBER',     r'0[xX][0-9a-fA-F]+|0[bB][01]+|\d+\.\d+(?:[eE][+-]?\d+)?[fFdD]?|\.\d+(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+|\d+[fFdDlLuU]?'),

    # Identifiers / keywords share a pattern; split afterward by lookup
    ('IDENTIFIER', r'[a-zA-Z_]\w*'),

    # Multi-char operators BEFORE single-char ones
    ('OPERATOR',   r'\*\*=?|//=?|<<=?|>>=?|->|=>|::|\+\+|--|&&|\|\||'
                   r'==|!=|<=|>=|[+\-*/%=<>!&|^~]=?|/|\?|:'),

    # Delimiters / punctuation
    ('DELIMITER',  r'[(){}\[\];,.:?]'),

    # Anything else is unrecognized -> ERROR (keeps the lexer crash-free)
    ('ERROR',      r'.'),
]

_combined_pattern = '|'.join(
    f'(?P<{name}>{pattern})' for name, pattern in token_specification
)
_regex = re.compile(_combined_pattern)


def _line_col_lookup(source_code):
    """Pre-compute newline positions for fast O(log n) line/col lookup."""
    newline_positions = [i for i, ch in enumerate(source_code) if ch == '\n']

    def get_line_col(index):
        lo, hi = 0, len(newline_positions)
        while lo < hi:
            mid = (lo + hi) // 2
            if newline_positions[mid] < index:
                lo = mid + 1
            else:
                hi = mid
        line = lo + 1  # 1-based
        col = (index + 1) if lo == 0 else (index - newline_positions[lo - 1])
        return line, col

    return get_line_col


def tokenize(source_code):
    """
    Convert source_code (str) into a list of token dicts:
        { 'lexeme': str, 'type': str, 'line': int, 'column': int }

    Guarantees:
      - Never raises an exception for malformed/unrecognized input.
      - Whitespace and comments are skipped (not emitted).
      - Unrecognized characters are emitted as type 'ERROR' rather
        than stopping the scan.
    """
    if source_code is None:
        return []

    get_line_col = _line_col_lookup(source_code)
    tokens = []

    for match in _regex.finditer(source_code):
        token_type = match.lastgroup
        lexeme = match.group(0)
        start_pos = match.start()

        if token_type in ('WHITESPACE', 'COMMENT'):
            continue

        # Normalize the "STRING2" (single-quoted) bucket into STRING
        if token_type == 'STRING2':
            token_type = 'STRING'

        # Reclassify identifiers that are actually reserved keywords
        if token_type == 'IDENTIFIER' and lexeme in KEYWORDS:
            token_type = 'KEYWORD'

        line, col = get_line_col(start_pos)
        tokens.append({
            'lexeme': lexeme,
            'type': token_type,
            'line': line,
            'column': col,
        })

    return tokens