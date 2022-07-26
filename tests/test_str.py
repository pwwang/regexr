import re
from typing import Tuple

import pytest
from regexr import *


@pytest.mark.parametrize(
    "regexr,string",
    [
        (Regexr("x"), "x"),
        (Regexr(ZeroOrMore("x")), "x*"),
        (Regexr(OneOrMore("x")), "x+"),
        (Regexr(Or("ab", "ba", capture=True)), "(ab|ba)"),
        (Regexr(Or(Capture("a"), Capture("b"), Capture("c"), capture=True)), "((a)|(b)|(c))"),
        (Regexr(OneOrMore(DIGIT)), r"\d+"),
        (Regexr(DIGITS), r"\d+"),
        (Regexr(ANYCHAR), r"."),
        (Regexr(Capture(ANYCHAR)), r"(.)"),
        (Regexr(Capture("x", name="a")), r"(?P<a>x)"),
        (Regexr(Capture("x", name="unk")), r"(?P<unk>x)"),
        (Regexr(Capture("")), r"()"),
        (Regexr(START, MAYBE_WHITESPACES), r"^\s*"),
        (
            Regexr(Capture("x", name="a"), Captured("a"), Conditional("a", "y")),
            r"(?P<a>x)(?P=a)(?(a)y)",
        ),
        (
            Regexr(Capture("x", name="a1"), Captured("a1"), Conditional("a1", "y")),
            r"(?P<a1>x)(?P=a1)(?(a1)y)",
        ),
        (Regexr(Capture("x", name="a1"), Captured(1), Conditional(1, "y")), r"(?P<a1>x)\1(?(1)y)"),
        (
            Regexr(Capture("x", name="μ"), Captured("μ"), Conditional("μ", "y")),
            r"(?P<μ>x)(?P=μ)(?(μ)y)",
        ),
        (
            Regexr(Capture("x", name="𝔘𝔫𝔦𝔠𝔬𝔡𝔢"), Captured("𝔘𝔫𝔦𝔠𝔬𝔡𝔢"), Conditional("𝔘𝔫𝔦𝔠𝔬𝔡𝔢", "y")),
            r"(?P<𝔘𝔫𝔦𝔠𝔬𝔡𝔢>x)(?P=𝔘𝔫𝔦𝔠𝔬𝔡𝔢)(?(𝔘𝔫𝔦𝔠𝔬𝔡𝔢)y)",
        ),
        (Regexr(Capture("x", name="a"), Capture("y", name="b")), r"(?P<a>x)(?P<b>y)"),
        (
            Regexr(Or(Capture("a"), Capture("b"), capture=True), Maybe(Capture("c"))),
            "((a)|(b))(c)?",
        ),
        (
            Regexr(
                Or(Capture("a", name="a1"), Capture("b", name="b2")), Maybe(Capture("c", name="c3"))
            ),
            "(?:(?P<a1>a)|(?P<b2>b))(?P<c3>c)?",
        ),
        (Regexr(Lazy(MAYBE_ANYCHARS), END), ".*?$"),
        (Regexr("a", Lazy(MAYBE_ANYCHARS), "b"), "a.*?b"),
        (Regexr("ab", LookAhead("c"), "cd"), "ab(?=c)cd"),
        (Regexr("ab", LookBehind("b"), "cd"), "ab(?<=b)cd"),
        (Regexr("ab", LookAhead(Raw("a|ab")), "cd"), "ab(?=a|ab)cd"),
        (
            Regexr(
                START,
                Maybe(Capture("(")),
                OneOrMore(NoneOfChars("()"), capture=True),
                Conditional(1, yes=")"),
                END,
            ),
            r"^(\()?([^()]+)(?(1)\))$",
        ),
        (
            Regexr(
                START,
                Or(Capture("a"), "c"),
                Conditional(1, yes="b", no="d", capture=True),
                END,
            ),
            r"^(?:(a)|c)((?(1)b|d))$",
        ),
        (
            Regexr(
                Capture("a", name="g1"),
                Maybe(Capture("b", name="g2")),
                Capture(Conditional("g2", "c", "d")),
            ),
            r"(?P<g1>a)(?P<g2>b)?((?(g2)c|d))",
        ),
        (
            Regexr(START, RepeatExact(Capture(WORD), m=1)),
            r"^(\w){1}",
        ),
        (
            Regexr(START, Repeat(Capture(WORD), m=1, n=2)),
            r"^(\w){1,2}",
        ),
        (
            Regexr(START, Repeat(Capture(WORD), m=1, n=2, lazy=True)),
            r"^(\w){1,2}?",
        ),
        (
            Regexr(Capture("a", LookAhead(WHITESPACE, NoneOfChars("a")))),
            r"(a(?=\s[^a]))",
        ),
        (
            Regexr(Capture("a", LookAhead(WHITESPACE, ZeroOrMore(NoneOfChars("a"))))),
            r"(a(?=\s[^a]*))",
        ),
        (
            Regexr(Capture("a", LookAhead(WHITESPACE, OneOfChars("abc")))),
            r"(a(?=\s[abc]))",
        ),
        (
            Regexr(Capture("a", LookAhead(WHITESPACE, ZeroOrMore(OneOfChars("abc"))))),
            r"(a(?=\s[abc]*))",
        ),
        (
            Regexr(Capture("a"), LookAhead(WHITESPACE, Captured(1))),
            r"(a)(?=\s\1)",
        ),
        (
            Regexr(Capture("a"), LookAhead(WHITESPACE, ZeroOrMore(Captured(1)))),
            r"(a)(?=\s\1*)",
        ),
        (
            Regexr(Capture("a"), LookAhead(WHITESPACE, Or("abc", "a", capture=True))),
            r"(a)(?=\s(abc|a))",
        ),
        (
            Regexr(Capture("a", LookAheadNot(WHITESPACE, NoneOfChars("a")))),
            r"(a(?!\s[^a]))",
        ),
        (
            Regexr(Capture("a", LookAheadNot(WHITESPACE, OneOfChars("abc")))),
            r"(a(?!\s[abc]))",
        ),
        (
            Regexr(Capture("a", LookAheadNot(WHITESPACE, Captured(1)))),
            r"(a(?!\s\1))",
        ),
        (
            Regexr(Capture("a", LookAheadNot(WHITESPACE, Or("abc", "a", capture=True)))),
            r"(a(?!\s(abc|a)))",
        ),
        (
            Regexr(Capture("a"), "b", LookAhead(Captured(1)), "c"),
            r"(a)b(?=\1)c",
        ),
        (
            Regexr(Or(Capture("a"), Capture("x")), "b", LookAhead(Conditional(Captured(2), "x", "c")), "c"),
            r"(?:(a)|(x))b(?=(?(2)x|c))c",
        ),
        (
            Regexr("ab", LookBehind("c"), "c"),
            r"ab(?<=c)c",
        ),
        (
            Regexr("ab", LookBehindNot("b"), "c"),
            r"ab(?<!b)c",
        ),
        (
            Regexr(Capture("a"), "a", LookBehind(Captured(1)), "c"),
            r"(a)a(?<=\1)c",
        ),
        (
            Regexr(Capture("a"), "b", LookBehindNot(Captured(1)), "a"),
            r"(a)b(?<!\1)a",
        ),
        (
            Regexr(Or(Capture("a"), Capture("x")), "b", LookBehind(Conditional(Captured(1), "b", "x")), "c"),
            r"(?:(a)|(x))b(?<=(?(1)b|x))c",
        ),
        (
            Regexr(ZeroOrMore(Maybe("a")), "y"),
            r"(?:a?)*y",
        ),
        (
            Regexr(ZeroOrMore(Maybe("a"), lazy=True), "y"),
            r"(?:a?)*?y",
        ),
        (
            Regexr(OneOrMore(Maybe("a")), "y"),
            r"(?:a?)+y",
        ),
        (
            Regexr(OneOrMore(Maybe("a"), lazy=True), "y"),
            r"(?:a?)+?y",
        ),
        (
            Regexr(Repeat(Maybe("a"), m=2), "y"),
            r"(?:a?){2,}y",
        ),
        (
            Regexr(Repeat(Maybe("a"), m=2, lazy=True), "y"),
            r"(?:a?){2,}?y",
        ),
        (
            Regexr(START, ZeroOrMore(Or(Capture("a"), "b", capture=True))),
            r"^((a)|b)*",
        ),
        (
            Regexr(START, ZeroOrMore(Or(OneOfChars("ab"), "c", capture=True))),
            r"^([ab]|c)*",
        ),
        (
            Regexr(START, ZeroOrMore(Or(Concat(Capture("a"), "c"), OneOfChars("ab"), capture=True), lazy=True), "c"),
            r"^((a)c|[ab])*?c",
        ),
        (
            Regexr(Capture("a"), ZeroOrMore(Concat(LookAhead(ZeroOrMore(Capture("b"))), "c"))),
            r"(a)(?:(?=(b)*)c)*",
        ),
        (
            Regexr(Capture("a"), ZeroOrMore(LookAheadNot(ZeroOrMore(Capture("b")), capture=True))),
            r"(a)((?!(b)*))*",
        ),
        (
            Regexr(NonCapture("abc")),
            r"(?:abc)",
        ),
    ],
)
def test_regexr(regexr: Regexr, string: str) -> None:
    assert regexr == string


def test_wrong_number_for_repeat():
    with pytest.raises(ValueError):
        Repeat("a", m=-1)
    with pytest.raises(ValueError):
        Repeat("a", m=2, n=1)
    with pytest.raises(ValueError):
        RepeatExact("a", m=-1)


def test_lazy_on_non_quantifier():
    with pytest.raises(ValueError):
        Lazy("a")


def test_lazy_wrong_args():
    with pytest.raises(ValueError):
        Lazy("a", "b")


def test_raw_not_on_strings():
    with pytest.raises(ValueError):
        Raw(Capture("b"))


def test_invalid_capture_name():
    with pytest.raises(ValueError):
        Maybe("a", capture="a.b")


def test_compile():
    assert Regexr("a").compile().match("a")
    assert Regexr("a").compile(re.I).match("A")


def test_repr():
    assert repr(Regexr("a")) == "<Regexr: r'a'>"


def test_invalid_id_or_capture_name():
    with pytest.raises(ValueError):
        Maybe("a", capture="a.b")
    with pytest.raises(ValueError):
        Conditional("a.b", yes="b", no="c")
    with pytest.raises(ValueError):
        Conditional("ab", yes="b", no="c", capture="a.b")
    with pytest.raises(ValueError):
        Captured("a.b")
    with pytest.raises(ValueError):
        Captured("ab", capture="a.b")


@pytest.mark.parametrize("regexr, prettied", [
    # single-line
    (Regexr("a"), "a"),
    # single-line with capture
    (Regexr(Capture("a")), "(a)"),
    # or
    (Regexr(Or("a", "b")), "(?:a|b)"),
    # or with multiple lines
    (
        Regexr(Or(Capture("a", "b"), "c", "d")),
        """\
(?:
  (
    a
    b
  )
  |c
  |d
)"""
    ),
    # maybe
    (Regexr(Maybe("a")), "a?"),
    # maybe with lazy
    (Regexr(Lazy(Maybe("a"))), "a??"),
    # lazy with raw string
    (Regexr(Lazy(Raw("a?"))), "a??"),
    # multi-level
    (
        Regexr(Capture("a", Capture("b", Capture("c", name="d")), name="a")),
        """\
(?P<a>
  a
  (
    b
    (?P<d>c)
  )
)"""
    ),
    # Character classes
    (Regexr(OneOfChars("a")), "[a]"),
    # Conditional
    (Regexr(Conditional(Captured("a"), "b", "c")), "(?(a)b|c)"),
    # Conditional
    (Regexr(Conditional(Captured("a"), "b", Capture("c", "d"))), """\
(?(a)
  b
  |(
    c
    d
  )
)"""
    ),
    # captured
    (Regexr(Capture(DIGITS, name="a"), "abc", Captured("a")), "(?P<a>\\d+)\nabc\n(?P=a)"),
    # lookahead
    (Regexr("a", LookAhead("a")), "a\n(?=a)"),
    (Regexr("a", LookAhead("a", "b")), "a\n(?=\n  a\n  b\n)"),
    # raw
    (Regexr(Raw(r"\d")), r"\d"),
    (Regexr(r"\d"), r"\\d"),
])
def test_pretty(regexr: Regexr, prettied: str) -> None:
    assert regexr.pretty() == prettied
