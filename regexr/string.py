r"""Regular expressions for humans

Predefined patterns:

    START = Raw("^", entire=True)
    START_OF_STRING = Raw(r"\A", entire=True)
    END = Raw("$", entire=True)
    END_OF_STRING = Raw(r"\Z", entire=True)
    NUMBER = DIGIT = Raw(r"\d", entire=True)
    NUMBERS = DIGITS = Raw(r"\d+", entire=True)
    MAYBE_NUMBERS = MAYBE_DIGITS = Raw(r"\d*", entire=True)
    NON_NUMBER = NON_DIGIT = Raw(r"\D", entire=True)
    WORD = Raw(r"\w", entire=True)
    WORDS = Raw(r"\w+", entire=True)
    MAYBE_WORDS = Raw(r"\w*", entire=True)
    NON_WORD = Raw(r"\W", entire=True)
    WORD_BOUNDARY = Raw(r"\b", entire=True)
    NON_WORD_BOUNDARY = Raw(r"\B", entire=True)
    WHITESPACE = Raw(r"\s", entire=True)
    WHITESPACES = Raw(r"\s+", entire=True)
    MAYBE_WHITESPACES = Raw(r"\s*", entire=True)
    NON_WHITESPACE = Raw(r"\S", entire=True)
    SPACE = Raw(" ", entire=True)
    SPACES = Raw(" +", entire=True)
    MAYBE_SPACES = Raw(" *", entire=True)
    TAB = Raw(r"\t", entire=True)
    DOT = Raw(r"\.", entire=True)
    ANYCHAR = Raw(".", entire=True)
    ANYCHARS = Raw(".+", entire=True)
    MAYBE_ANYCHARS = Raw(".*", entire=True)
    LETTER = Raw("[a-zA-Z]", entire=True)
    LETTERS = Raw("[a-zA-Z]+", entire=True)
    MAYBE_LETTERS = Raw("[a-zA-Z]*", entire=True)
    LOWERCASE = Raw("[a-z]", entire=True)
    LOWERCASES = Raw("[a-z]+", entire=True)
    MAYBE_LOWERCASES = Raw("[a-z]*", entire=True)
    UPPERCASE = Raw("[A-Z]", entire=True)
    UPPERCASES = Raw("[A-Z]+", entire=True)
    MAYBE_UPPERCASES = Raw("[A-Z]*", entire=True)
    ALNUM = Raw("[a-zA-Z0-9]", entire=True)
    ALNUMS = Raw("[a-zA-Z0-9]+", entire=True)
    MAYBE_ALNUMS = Raw("[a-zA-Z0-9]*", entire=True)
"""

from __future__ import annotations

import re
from abc import ABC, abstractproperty
from typing import Sequence, Union

SegmentType = Union["Segment", str]


def _flags_to_str(flags: int | str | Sequence[int | str]) -> str:
    """Convert a set of flags to a string

    >>> _flags_to_str(re.IGNORECASE)  # 'i'
    >>> _flags_to_str(re.IGNORECASE | re.MULTILINE)  # 'im'
    """
    if flags is None:
        return ""

    if isinstance(flags, Sequence) and not isinstance(flags, str):
        return "".join(_flags_to_str(flag) for flag in flags)

    if isinstance(flags, int):
        out = []
        if flags & re.A:
            out.append("a")
        if flags & re.I:
            out.append("i")
        if flags & re.L:
            out.append("L")
        if flags & re.M:
            out.append("m")
        if flags & re.S:
            out.append("s")
        if flags & re.U:
            out.append("u")
        if flags & re.X:
            out.append("x")
        return "".join(out)

    # str
    if any(c not in "aiLmsux" for c in flags):
        raise ValueError(
            f"Invalid flag: {flags}, must be a subset of 'aiLmsux'"
        )
    return flags


class Segment(ABC):
    """Segments of a regular expression

    ClassVars:
        NONCAPTURING_WRAPPING: Whether we should wrap the segment with brackets
            when `capture` is `False`.
            In some cases, for example, `(abc)+` is already an entire group, it
            won't confuse the parser when it comes with other segments, such as
            `(abc)+d`. We don't need an extra brackets to separate it from other
            segments. However, we need brackets for other segments, such as
            `a|b|c`, because `a|b|cd` will confuse the parser. In such a case,
            we need `(?:a|b|c)d` if we don't need to capture the segment.

    Args:
        args: Another segments to be wrapped by this one.
        capture: The name of the capture, False to disable capturing and
            True to capture without name.
        flags: The flags to be used when compiling this segment.
        deflags: Remove the flags from `re.compile()` while compiling
            this segment.
    """

    __slots__ = ("args", "capture", "flags")

    NONCAPTURING_WRAPPING = True

    def __init__(
        self,
        *args: SegmentType,
        capture: bool | str = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        """Constructor"""
        if isinstance(capture, str) and not capture.isidentifier():
            raise ValueError(f"Invalid capture name: {capture}")

        flags = _flags_to_str(flags)
        deflags = _flags_to_str(deflags)
        for flag in flags:
            if flag in deflags:
                raise ValueError(
                    f"Flag `{flag}` turned on and off"
                )

        if deflags:
            deflags = f"-{deflags}"

        self.args = args
        self.capture = capture
        self.flags = f"{flags}{deflags}"

    def _str_raw(self) -> str:
        """Stringify this segment, without capturing/non-capturing brackets

        Returns:
            str: The stringified segment.
        """
        return "".join(
            str(part) if isinstance(part, Segment) else re.escape(part)
            for part in self.args
        )

    def _pretty_raw(self, indent: str) -> str:
        """Pretty string representation of this segment, without
        capturing/non-capturing brackets
        """
        out = []
        for arg in self.args:
            if isinstance(arg, Segment):
                out.append(arg.pretty(indent, 0))
            else:  # str
                out.append(re.escape(arg))

        return "\n".join(out)

    def pretty(self, indent: str, level: int) -> str:
        """Pretty print this segment, depending on `capture`

        Args:
            indent: The indent string.
            level: The indent level.
        """
        arg = self._pretty_raw(indent)
        if (
            not self.capture
            and not self.NONCAPTURING_WRAPPING
            and not self.flags
        ):
            return "\n".join(
                f"{indent * level}{line}" for line in arg.splitlines()
            )

        capture_start = (
            "(" if self.capture is True
            else f"(?P<{self.capture}>" if self.capture
            else ""
        )
        capture_end = ")" if self.capture else ""
        flags_start = f"(?{self.flags}:" if self.flags else ""
        flags_end = ")" if self.flags else ""

        if self.capture:
            start = f"{indent * level}{capture_start}{flags_start}"
            end = f"{indent * level}{flags_end}{capture_end}"
        elif self.__class__.NONCAPTURING_WRAPPING and not self.flags:
            start = f"{indent * level}(?:"
            end = f"{indent * level})"
        else:  # self.flags not ""
            start = f"{indent * level}{flags_start}"
            end = f"{indent * level}{flags_end}"

        if "\n" not in arg:
            return "".join((start, arg, end))

        return "\n".join(
            (
                f"{start}",
                *(
                    f"{indent * (level + 1)}{line}"
                    for line in arg.splitlines()
                ),
                f"{end}",
            )
        )

    def __str__(self) -> str:
        """String representation of this segment, depending on
        `capture`

        Returns:
            The final string representation of this segment.
        """
        arg = self._str_raw()
        flags_start = f"(?{self.flags}:" if self.flags else ""
        flags_end = ")" if self.flags else ""
        arg = f"{flags_start}{arg}{flags_end}"
        if self.capture is True:
            return f"({arg})"
        if self.capture:
            return f"(?P<{self.capture}>{arg})"
        if self.__class__.NONCAPTURING_WRAPPING and not self.flags:
            return f"(?:{arg})"
        return arg


# Character classes
class CharClass(Segment, ABC):
    """Used to indicat a set of characters wrapped by `[]`"""

    NONCAPTURING_WRAPPING = False

    def _pretty_raw(self, indent: str) -> str:
        return self._str_raw()

    def _str_raw(self) -> str:
        """Stringify this segment, without capturing/non-capturing brackets

        Returns:
            str: The stringified segment.
        """
        return "".join(
            str(part) if isinstance(part, Segment) else str(part)
            for part in self.args
        )


class OneOfChars(CharClass):
    """Positive character set `[...]`"""

    def _str_raw(self) -> str:
        return f"[{super()._str_raw()}]"


class NoneOfChars(CharClass):
    """Negative character set `[^...]`"""

    def _str_raw(self) -> str:
        return f"[^{super()._str_raw()}]"


# Look ahead/behind
class Look(Segment, ABC):
    """Look ahead or behind"""

    NONCAPTURING_WRAPPING = False
    PREFIX = "?="

    def _str_raw(self) -> str:
        return f"({self.__class__.PREFIX}{super()._str_raw()})"

    def _pretty_raw(self, indent: str) -> str:
        prettied = super()._pretty_raw(indent)
        if "\n" not in prettied:
            return f"({self.__class__.PREFIX}{prettied})"

        return "\n".join([
            f"({self.__class__.PREFIX}",
            *(f"{indent}{line}" for line in prettied.splitlines()),
            ")",
        ])


class LookAhead(Look):
    """Look ahead `(?=...)`"""


class LookBehind(Look):
    """Look behind `(?<=...)`"""

    PREFIX = "?<="


class LookAheadNot(Look):
    """Look ahead not `(?!...)`"""

    PREFIX = "?!"


class LookBehindNot(Look):
    """Look behind not `(?<!...)`"""

    PREFIX = "?<!"


# Quantifiers


class Quantifier(Segment, ABC):
    """Quantifier `+`, `*`, `?`, `{m}` or `{m,n}`"""

    __slots__ = ("lazy",)
    NONCAPTURING_WRAPPING = False

    def __init__(
        self,
        *args: SegmentType,
        lazy: bool = False,
        capture: bool = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        super().__init__(*args, capture=capture, flags=flags, deflags=deflags)
        self.lazy = lazy

    @abstractproperty
    def _quantifier(self) -> str:
        """The quantifier to quantify the pattern"""

    def _str_raw(self) -> str:
        qmark = "?" if self.lazy else ""
        if (
            len(self.args) > 1
            or (
                isinstance(self.args[0], str)
                and len(self.args[0]) > 1
            )
            or (
                isinstance(self.args[0], Raw)
                and not self.args[0].entire
                and not self.args[0].capture
            )
            or (
                isinstance(self.args[0], Segment)
                and not isinstance(
                    self.args[0], (Raw, Capture, Captured, CharClass)
                )
                and not self.args[0].NONCAPTURING_WRAPPING
                and not self.args[0].capture
            )
        ):
            return f"(?:{super()._str_raw()}){self._quantifier}{qmark}"

        return f"{super()._str_raw()}{self._quantifier}{qmark}"

    def _pretty_raw(self, indent: str) -> str:
        return self._str_raw()


class ZeroOrMore(Quantifier):
    """`*` zero or more times"""

    _quantifier = "*"


class OneOrMore(Quantifier):
    """`+` one or more times"""

    _quantifier = "+"


class Maybe(Quantifier):
    """`?` zero or one times"""

    _quantifier = "?"


class Repeat(Quantifier):
    """Match from `m` to `n` repetitions `{m,n}` or `{m,}`"""

    __slots__ = ("m", "n")

    def __init__(
        self,
        *args: SegmentType,
        m: int,
        n: int = None,
        lazy: bool = False,
        capture: bool = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        super().__init__(
            *args,
            capture=capture,
            flags=flags,
            deflags=deflags,
            lazy=lazy,
        )
        if m < 0:
            raise ValueError("`m` must be positive for `Repeat`")
        if n is not None and n < m:
            raise ValueError(
                "`n` must be greater than or equal to `m` for `Repeat`"
            )
        self.m = m
        self.n = n

    @property
    def _quantifier(self) -> str:
        n = "" if self.n is None else self.n
        return f"{{{self.m},{n}}}"


class RepeatExact(Quantifier):
    """Match exact `m` repetitions `{m}`"""

    __slots__ = ("m",)

    def __init__(
        self,
        *args: SegmentType,
        m: int,
        lazy: bool = False,
        capture: bool = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        super().__init__(
            *args,
            capture=capture,
            flags=flags,
            deflags=deflags,
            lazy=lazy,
        )
        if m <= 0:
            raise ValueError("`m` must be greater than 0 for `Repeat`")
        self.m = m

    @property
    def _quantifier(self) -> str:
        return f"{{{self.m}}}"


class Lazy(Segment):
    """Non-greedy modifier `+?`, `*?`, `??`, `{m,}?` or `{m,n}?`"""

    NONCAPTURING_WRAPPING = False

    def __init__(
        self,
        *args: SegmentType,
        capture: bool = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        if len(args) != 1:
            raise ValueError("`Lazy` must have exactly one positional argument")

        if (
            not isinstance(args[0], Quantifier)
            and not (
                isinstance(args[0], Raw)

            )
            and not (
                isinstance(args[0], str)
                and (
                    args[0][-1] in ("+", "*", "?")
                    or re.match(r"\{\d+(?:,\d+)?\}", args[0])
                )
            )
        ):
            raise ValueError("`Lazy` must be applied to a quantifier")

        super().__init__(*args, capture=capture, flags=flags, deflags=deflags)

    def _str_raw(self) -> str:
        return f"{super()._str_raw()}?"

    def _pretty_raw(self, indent: str) -> str:
        return f"{super()._pretty_raw(indent)}?"


class Flag(Segment):
    """Flag `(?aiLmsux)`"""
    NONCAPTURING_WRAPPING = False

    def __init__(self, *args: str | int) -> None:
        transformed_args = _flags_to_str(args)
        super().__init__(transformed_args, capture=False)

    def _str_raw(self) -> str:
        return f"(?{super()._str_raw()})"

    def _pretty_raw(self, indent: str) -> str:
        return self._str_raw()


class InlineFlag(Segment):
    """Inline flag `(?aiLmsux-imsx:...)`"""

    NONCAPTURING_WRAPPING = False

    def __init__(
        self,
        *args: SegmentType,
        capture: bool | str = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        if flags is None and deflags is None:
            raise ValueError("`InlineFlag` must have `flags` or `deflags`")

        super().__init__(
            *args, capture=capture, flags=flags, deflags=deflags,
        )


class Raw(Segment):
    """Raw strings without escaping"""
    __slots__ = ("entire",)
    NONCAPTURING_WRAPPING = False

    def __init__(
        self,
        *args: SegmentType,
        capture: bool = False,
        entire: bool = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        if not all(isinstance(arg, str) for arg in args):
            raise ValueError("`Raw` must be applied to strings.")
        super().__init__(*args, capture=capture, flags=flags, deflags=deflags)
        self.entire = entire

    def _str_raw(self) -> str:
        return "".join(str(part) for part in self.args)

    def _pretty_raw(self, indent: str) -> str:
        return self._str_raw()


# Other segments
class Or(Segment):
    """`|` connected segments"""

    def _str_raw(self) -> str:
        return "|".join(str(part) for part in self.args)

    def _pretty_raw(self, indent: str) -> str:
        """Pretty string representation of this segment, without
        capturing/non-capturing brackets
        """
        out = []
        has_newline = False
        for arg in self.args:
            if isinstance(arg, Segment):
                pretty_str = arg.pretty(indent, 0)
            else:
                pretty_str = str(arg)
            if "\n" in pretty_str:
                has_newline = True
            out.append(pretty_str)

        if not has_newline:
            return "|".join(out)
        return "\n|".join(out)


# Capture/non-capture
class Capture(Segment):
    """Capture a match `(...)`"""

    NONCAPTURING_WRAPPING = False

    def __init__(
        self,
        *args: SegmentType,
        name: bool | str = None,
        capture: bool | str = None,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        """Constructor"""
        if name is None and capture is None:
            capture = True
        elif capture is None:
            capture = name

        assert capture is not False
        super().__init__(*args, capture=capture, flags=flags, deflags=deflags)


class NonCapture(Segment):
    """Non-capturing grouping `(?:...)`"""

    NONCAPTURING_WRAPPING = True

    def __init__(
        self,
        *args: SegmentType,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        """Constructor"""
        super().__init__(*args, capture=False, flags=flags, deflags=deflags)


class Concat(Segment):
    """Concatenate segments"""

    NONCAPTURING_WRAPPING = False


class Conditional(Segment):
    """`(?(...)yes|no)` conditional pattern"""

    __slots__ = ("id_or_name", "yes", "no")
    NONCAPTURING_WRAPPING = False

    def __init__(
        self,
        id_or_name: Captured | str | int,
        yes: SegmentType,
        no: SegmentType = None,
        capture: bool = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        """Constructor"""
        if isinstance(capture, str) and not capture.isidentifier():
            raise ValueError(f"Invalid capture name: {capture}")
        if isinstance(id_or_name, str) and not id_or_name.isidentifier():
            raise ValueError(f"Invalid id or name: {id_or_name}")

        self.id_or_name = id_or_name
        self.yes = re.escape(yes) if isinstance(yes, str) else yes
        self.no = re.escape(no) if isinstance(no, str) else no
        super().__init__(capture=capture, flags=flags, deflags=deflags)

    def _str_raw(self) -> str:
        id_or_name = (
            self.id_or_name.id_or_name
            if isinstance(self.id_or_name, Captured)
            else self.id_or_name
        )
        no = f"|{self.no}" if self.no else ""

        return f"(?({id_or_name}){self.yes}{no})"

    def _pretty_raw(self, indent: str) -> str:
        id_or_name = (
            self.id_or_name.id_or_name
            if isinstance(self.id_or_name, Captured)
            else self.id_or_name
        )
        yes = (
            self.yes.pretty(indent, 0)
            if isinstance(self.yes, Segment)
            else str(self.yes)
        )
        no = (
            "" if not self.no
            else f"|{self.no.pretty(indent, 0)}"
            if isinstance(self.no, Segment)
            else f"|{self.no}"
        )

        if "\n" in yes or "\n" in no:
            yes = "\n".join(f"{indent}{line}" for line in yes.split("\n"))
            no = "\n".join(f"{indent}{line}" for line in no.split("\n"))
            return f"(?({id_or_name})\n{yes}\n{no}\n)"

        return f"(?({id_or_name}){yes}{no})"


class Captured(Segment):
    """`(?P=name)` captured group or \\1, \\2, ..."""

    __slots__ = ("id_or_name",)
    NONCAPTURING_WRAPPING = False

    def __init__(
        self,
        id_or_name: str | int,
        capture: bool = False,
        flags: int | str | Sequence[int | str] = None,
        deflags: int | str | Sequence[int | str] = None,
    ) -> None:
        """Constructor"""
        if isinstance(capture, str) and not capture.isidentifier():
            raise ValueError(f"Invalid capture name: {capture}")
        if isinstance(id_or_name, str) and not id_or_name.isidentifier():
            raise ValueError(f"Invalid id or name: {id_or_name}")

        self.id_or_name = id_or_name
        super().__init__(capture=capture, flags=flags, deflags=deflags)

    def _str_raw(self) -> str:
        if isinstance(self.id_or_name, str):
            return f"(?P={self.id_or_name})"
        return f"\\{self.id_or_name}"

    def _pretty_raw(self, indent: str) -> str:
        return self._str_raw()


# Predefined patterns
START = Raw("^", entire=True)
START_OF_STRING = Raw(r"\A", entire=True)
END = Raw("$", entire=True)
END_OF_STRING = Raw(r"\Z", entire=True)
NUMBER = DIGIT = Raw(r"\d", entire=True)
NUMBERS = DIGITS = Raw(r"\d+", entire=True)
MAYBE_NUMBERS = MAYBE_DIGITS = Raw(r"\d*", entire=True)
NON_NUMBER = NON_DIGIT = Raw(r"\D", entire=True)
WORD = Raw(r"\w", entire=True)
WORDS = Raw(r"\w+", entire=True)
MAYBE_WORDS = Raw(r"\w*", entire=True)
NON_WORD = Raw(r"\W", entire=True)
WORD_BOUNDARY = Raw(r"\b", entire=True)
NON_WORD_BOUNDARY = Raw(r"\B", entire=True)
WHITESPACE = Raw(r"\s", entire=True)
WHITESPACES = Raw(r"\s+", entire=True)
MAYBE_WHITESPACES = Raw(r"\s*", entire=True)
NON_WHITESPACE = Raw(r"\S", entire=True)
SPACE = Raw(" ", entire=True)
SPACES = Raw(" +", entire=True)
MAYBE_SPACES = Raw(" *", entire=True)
TAB = Raw(r"\t", entire=True)
DOT = Raw(r"\.", entire=True)
ANYCHAR = Raw(".", entire=True)
ANYCHARS = Raw(".+", entire=True)
MAYBE_ANYCHARS = Raw(".*", entire=True)
LETTER = Raw("[a-zA-Z]", entire=True)
LETTERS = Raw("[a-zA-Z]+", entire=True)
MAYBE_LETTERS = Raw("[a-zA-Z]*", entire=True)
LOWERCASE = Raw("[a-z]", entire=True)
LOWERCASES = Raw("[a-z]+", entire=True)
MAYBE_LOWERCASES = Raw("[a-z]*", entire=True)
UPPERCASE = Raw("[A-Z]", entire=True)
UPPERCASES = Raw("[A-Z]+", entire=True)
MAYBE_UPPERCASES = Raw("[A-Z]*", entire=True)
ALNUM = Raw("[a-zA-Z0-9]", entire=True)
ALNUMS = Raw("[a-zA-Z0-9]+", entire=True)
MAYBE_ALNUMS = Raw("[a-zA-Z0-9]*", entire=True)


# Main class
class Regexr(str):
    """The entrance of the package to compose a regular expression

    It is actually a subclass of `str`, but with an extra method `compile`,
    which compiles the regular expression and returns a `re.Pattern` object.

    Args:
        *segments: The segments of the regular expression.
            When composing the regular expression, the segments are concatenated
    """

    __slots__ = ("_segments",)

    def __new__(cls, *segments: SegmentType) -> Regexr:
        if (
            any(isinstance(part, Flag) for part in segments)
            and not isinstance(segments[0], Flag)
        ):
            raise ValueError("Flags must be the first segment.")

        regexr = str.__new__(
            cls,
            "".join(
                re.escape(part) if isinstance(part, str) else str(part)
                for part in segments
            )
        )
        regexr._segments = segments  # type: ignore
        return regexr

    def compile(self, flags: int = 0) -> re.Pattern:
        """Compile the regular expression and return a `re.Pattern` object

        See also `re.compile()`

        Args:
            flags: The flags to be used when compiling the regular expression.
        """
        return re.compile(self, flags=flags)

    def pretty(self, indent: str = "  ") -> str:
        """Pretty print the regular expression"""
        return "\n".join(
            part.pretty(indent, level=0)
            if isinstance(part, Segment)
            else re.escape(part)
            for part in self._segments  # type: ignore
        )

    def __repr__(self) -> str:
        """String representation of this regular expression"""
        return f"<Regexr: r'{self}'>"
