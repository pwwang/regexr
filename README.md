# regexr

Regular expressions for humans

Instead of writing a regular expression to match an URL:

```python
# need to be compiled with re.X
regex = r'''
    ^(?P<protocol>http|https|ftp|mailto|file|data|irc)://
    (?P<domain>[A-Za-z0-9-]{0,63}(?:\.[A-Za-z0-9-]{0,63})+)
    (?::(?P<port>\d{1,4}))?
    (?P<path>/*(?:/*[A-Za-z0-9\-._]+/*)*)
    (?:\?(?P<query>.*?))?
    (?:\#(?P<fragment>.*))?$
'''
```

You can write:

```python
regexr = Regexr(
    START,
    ## match the protocol
    Or('http', 'https', 'ftp', 'mailto', 'file', 'data', 'irc', capture="protocol"),
    '://',
    ## match the domain
    Capture(
        Repeat(OneOfChars('A-Z', 'a-z', '0-9', '-'), m=0, n=63),
        OneOrMore(DOT, Repeat(OneOfChars('A-Z', 'a-z', '0-9', '-'), m=0, n=63)),
        name="domain",
    ),
    ## match the port
    Maybe(':', Capture(Repeat(DIGIT, m=1, n=4), name="port")),
    ## match the path
    Capture(
        ZeroOrMore('/'),
        ZeroOrMore(
            ZeroOrMore('/'),
            OneOrMore(OneOfChars('A-Z', 'a-z', '0-9', r'\-._')),
            ZeroOrMore('/'),
        ),
        name="path",
    ),
    ## match the query
    Maybe("?", Capture(Lazy(MAYBE_ANYCHARS), name="query")),
    ## and finally the fragment
    Maybe("#", Capture(MAYBE_ANYCHARS, name="fragment")),
    END,
)
```

Inspired by [rex](https://github.com/r-lib/rex) for R and [Regularity](https://github.com/andrewberls/regularity) for Ruby.

## Why?

We have `re.X` to compile a regular expression in verbose mode, but sometimes it is still difficult to read/write and error-prone.

- Easy to read/write regular expressions

  - For example, `[]]` might need a second to understand it. But we can write it as `OneOfChars("]")` and it will be easier to read.

- Easy to write regular expressions with autocompletions from IDEs

  - When we write raw regex, we can't get any hints from IDEs

- Non-capturing for groups whether possible

  - For example, with `Maybe(Maybe("a", "b))` we get `(?:(?:ab)?)?`

- Easy to avoid unintentional errors

  - For example, sometimes it's difficult to debug with `r"(?P<a>>\d+)\D+\a` when we accidentally put one more `>` after the capturing name.

- Easy to avoid ambiguity

  - For example, `?` could be a quantifier meaning `0` or `1` match. It could also be a non-greedy (lazy) modifier for quantifiers. It's easy to be distinguished by `Maybe(...)` and `Lazy(...)` (or quantifiers with `lazy=True`).

- Easily avoid unbalanced parentheses/brackets/braces

  - Especially when we want to match them. For example, `Capture("(")` instead of `(\()`.

## Usage
### More examples

- Matching a phone number like `XXX-XXX-XXXX` or `(XXX) XXX XXXX`

    ```python
    Regexr(
        START,
        # match the first part
        Maybe(Capture('(', name="open_paren")),
        RepeatExact(DIGIT, m=3),
        Conditional("open_paren", yes=")"),

        Maybe(OneOfChars('- ')),

        # match the second part
        RepeatExact(DIGIT, m=3),

        Maybe(OneOfChars('- ')),

        # match the third part
        RepeatExact(DIGIT, m=4),
        END,
    )

    # compiles to
    # ^(?P<open_paren>\()?\d{3}(?(open_paren)\))[- ]?\d{3}[- ]?\d{4}$
    ```

- Matching an IP address

    ```python
    # Define the pattern for one part of xxx.xxx.xxx.xxx
    ip_part = Or(
        # Use Concat instead of NonCapture to avoid brackets
        # 250-255
        Concat("25", OneOfChars('0-5')),
        # 200-249
        Concat("2", OneOfChars('0-4'), DIGIT),
        # 000-199
        Concat(Or("0", "1"), RepeatExact(DIGIT, m=2)),
        # 00-99
        Repeat(DIGIT, m=1, n=2),
    )

    Regexr(
        START,
        ip_part,
        RepeatExact(DOT, ip_part, m=3),
        END,
    )
    # compiles to
    # ^(?:25[0-5]|2[0-4]\d|(?:0|1)\d{2}|\d{1,2})(?:\.(?:25[0-5]|2[0-4]\d|(?:0|1)\d{2}|\d{1,2})){3}$
    ```

- Matching an HTML tag roughly (without attributes)

    ```python
    Regexr(
        START,
        "<", Capture(WORDS, name="tag"), ">",
        Lazy(ANYCHARS),
        "</", Captured("tag"), ">",
        END,
    )
    # compiles to
    # ^<(?P<tag>\w+)>.+?</(?P=tag)>$
    ```

### Pretty print a `Regexr` object

With the example at the very beginning (matching an URL), we can pretty print it:

```
# print(regexr.pretty())
# prints:

^
(?P<protocol>http|https|ftp|mailto|file|data|irc)
://
(?P<domain>
  [A-Za-z0-9-]{0,63}
  (?:\.[A-Za-z0-9-]{0,63})+
)
(?::(?P<port>\d{1,4}))?
(?P<path>
  /*
  (?:/*[A-Za-z0-9\-._]+/*)*
)
(?:\?(?P<query>.*?))?
(?:\#(?P<fragment>.*))?
$
```

### Compile a `Regexr` directly

```python
Regexr("a").compile(re.I).match("A")
# <re.Match object; span=(0, 1), match='A'>
```

## API documentation

<https://pwwang.github.io/regexr/>

## TODO

- Support bytes
- Support inline flags (e.g. `(?i)`)
