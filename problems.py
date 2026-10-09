"""Генератор випадкових математичних задач для 5-9 класів."""
from __future__ import annotations

import math
import random
from fractions import Fraction
from typing import Callable, NamedTuple

GRADES = (5, 6, 7, 8, 9)

TOPICS = (
    "Дроби",
    "Відсотки",
    "Числа й дії",
    "Рівняння",
    "Системи рівнянь",
    "Степені та корені",
    "Геометрія",
    "Многочлени",
    "Функція",
    "Середнє та ймовірність",
    "Одиниці вимірювання",
)

_SQUAREFREE = (2, 3, 5, 6, 7, 10, 11, 13, 14, 15, 17, 19, 21, 22, 23)
_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


class Problem(NamedTuple):
    question: str
    answer: str
    topic: str = ""
    hint: str = ""
    difficulty: int = 1


class Spec(NamedTuple):
    fn: Callable[[], Problem]
    topic: str
    hint: str
    difficulty: int


# ---------------------------------------------------------------- formatting

def _sup(n: int | str) -> str:
    return str(n).translate(_SUP)


def _int(n: int) -> str:
    return str(n).replace("-", "−")


def _term(n: int) -> str:
    return f"+ {_int(n)}" if n >= 0 else f"− {abs(n)}"


def _term_x(n: int) -> str:
    if n == 1:
        return "+ x"
    if n == -1:
        return "− x"
    return f"+ {_int(n)}x" if n >= 0 else f"− {abs(n)}x"


def _poly2(a: int, b: int, c: int) -> str:
    """ax² + bx + c з прибранняю одиниць і нулів."""
    parts = []
    if a != 1:
        parts.append(f"{_int(a)}x²")
    else:
        parts.append("x²")
    if b != 0:
        parts.append(_term_x(b))
    if c != 0 or not parts:
        parts.append(_term(c))
    return " ".join(parts) + " = 0"


def _frac(f: Fraction) -> str:
    """Змішане число з мінусом-рискою."""
    neg = f < 0
    f = abs(f)
    whole, rem = divmod(f.numerator, f.denominator)
    if rem == 0:
        s = str(whole)
    elif whole == 0:
        s = f"{rem}/{f.denominator}"
    else:
        s = f"{whole} {rem}/{f.denominator}"
    return ("−" + s) if neg else s


def _dec_h(h: int) -> str:
    """Число, записане у сотих (h = значення * 100)."""
    neg = h < 0
    h = abs(h)
    whole, frac = divmod(h, 100)
    if frac == 0:
        s = str(whole)
    elif frac % 10 == 0:
        s = f"{whole},{frac // 10}"
    else:
        s = f"{whole},{frac:02d}"
    return ("−" + s) if neg else s


def _dec_t(t: int) -> str:
    """Число, записане у десятих (t = значення * 10)."""
    neg = t < 0
    t = abs(t)
    s = f"{t // 10},{t % 10}" if t % 10 else str(t // 10)
    return ("−" + s) if neg else s


def _roots(r1, r2) -> str:
    if r1 == r2:
        return f"x₁ = x₂ = {r1}"
    return f"x₁ = {r1}; x₂ = {r2}"


# ---------------------------------------------------------------- 5 клас

def _g5_add_fractions() -> Problem:
    while True:
        b, d = random.randint(2, 12), random.randint(2, 12)
        f1 = Fraction(random.randint(1, b - 1), b)
        f2 = Fraction(random.randint(1, d - 1), d)
        if random.random() < 0.5:
            q, val = f"{f1.numerator}/{f1.denominator} + {f2.numerator}/{f2.denominator}", f1 + f2
        else:
            hi, lo = (f1, f2) if f1 >= f2 else (f2, f1)
            val = hi - lo
            if val == 0:
                continue
            q = f"{hi.numerator}/{hi.denominator} − {lo.numerator}/{lo.denominator}"
        return Problem(f"Обчисліть: {q} = ?", _frac(val))


def _g5_percent_of() -> Problem:
    k, m = random.randint(2, 30), random.randint(1, 10)
    n, p = 20 * k, 5 * m
    return Problem(
        f"Скільки становить {p}% від {n}?",
        str(k * m),
    )


def _g5_decimals() -> Problem:
    a, b = random.randint(11, 99), random.randint(11, 99)
    if random.random() < 0.5:
        return Problem(
            f"Обчисліть: {_dec_t(a)} + {_dec_t(b)}",
            _dec_t(a + b),
        )
    return Problem(
        f"Обчисліть: {_dec_t(a)} × {_dec_t(b)}",
        _dec_h(a * b),
    )


def _g5_rectangle() -> Problem:
    variant = random.randint(0, 2)
    w = random.randint(3, 20)
    if variant == 0:
        n = random.randint(2, 5)
        return Problem(
            f"Ширина прямокутника {w} см, а довжина у {n} рази більша. Знайдіть периметр прямокутника.",
            f"{2 * w * (n + 1)} см",
        )
    if variant == 1:
        l = random.randint(w + 1, 25)
        return Problem(
            f"Знайдіть периметр прямокутника зі сторонами {w} см і {l} см.",
            f"{2 * (w + l)} см",
        )
    l = random.randint(3, 15)
    return Problem(
        f"Знайдіть площу прямокутника зі сторонами {w} см і {l} см.",
        f"{w * l} см²",
    )


def _g5_order_ops() -> Problem:
    a, b, c = random.randint(2, 15), random.randint(2, 15), random.randint(2, 9)
    d = random.randint(1, (a + b) * c - 1)
    return Problem(
        f"Обчисліть: ({a} + {b}) × {c} − {d}",
        str((a + b) * c - d),
    )


def _g5_lcm_gcd() -> Problem:
    a, b = random.randint(4, 60), random.randint(4, 60)
    if random.random() < 0.5:
        return Problem(f"Знайдіть НСК (найменше спільне кратне) чисел {a} і {b}.", str(math.lcm(a, b)))
    return Problem(f"Знайдіть НСД (найбільший спільний дільник) чисел {a} і {b}.", str(math.gcd(a, b)))


def _g5_fraction_of() -> Problem:
    d, k = random.randint(2, 12), random.randint(2, 15)
    a = random.randint(1, d - 1)
    return Problem(
        f"Скільки становить {a}/{d} від {d * k}?",
        str(a * k),
    )


def _g5_units() -> Problem:
    variant = random.randint(0, 2)
    if variant == 0:
        n = random.randint(1, 8)
        half = random.choice([True, False])
        hours = n + (0.5 if half else 0)
        mins = (2 * n + 1) * 30 if half else n * 60
        return Problem(f"Скільки хвилин у {_dec_t(hours * 10)} годин?", str(mins))
    if variant == 1:
        n = random.randint(1, 12)
        half = random.choice([True, False])
        km = n + (0.5 if half else 0)
        meters = (2 * n + 1) * 500 if half else n * 1000
        return Problem(f"Скільки метрів у {_dec_t(km * 10)} кілометрах?", str(meters))
    n = random.randint(2, 7)
    return Problem(f"Скільки кілограмів у {n} тоннах?", str(n * 1000))


# ---------------------------------------------------------------- 6 клас

def _g6_int_ops() -> Problem:
    if random.random() < 0.5:
        a, b, c = random.randint(-15, 15), random.randint(-9, 9), random.randint(2, 9)
        d = random.randint(-20, 20)
        return Problem(
            f"Обчисліть: {_int(a)} + {_int(b)} × {_int(c)} − {_int(d)}",
            _int(a + b * c - d),
        )
    a, b, c = random.randint(-12, 12), random.randint(-8, 8), random.randint(2, 9)
    return Problem(
        f"Обчисліть: ({_int(a)} {_term(b)}) × {_int(c)}",
        _int((a + b) * c),
    )


def _g6_fraction_ops() -> Problem:
    f1 = Fraction(random.randint(1, 9), random.randint(2, 9))
    f2 = Fraction(random.randint(1, 9), random.randint(2, 9))
    if random.random() < 0.5:
        return Problem(
            f"Обчисліть: {f1.numerator}/{f1.denominator} × {f2.numerator}/{f2.denominator}",
            _frac(f1 * f2),
        )
    return Problem(
        f"Обчисліть: {f1.numerator}/{f1.denominator} : {f2.numerator}/{f2.denominator}",
        _frac(f1 / f2),
    )


def _g6_percent_change() -> Problem:
    k = random.choice([10, 20, 25, 50])
    p = 20 * random.randint(3, 40)
    if random.random() < 0.5:
        new = p * (100 + k) // 100
        return Problem(
            f"Ціна товару зросла з {p} грн до {new} грн. На скільки відсотків зросла ціна?",
            f"{k}%",
        )
    new = p * (100 - k) // 100
    return Problem(
        f"Ціна товару зменшилася з {p} грн до {new} грн. На скільки відсотків зменшилася ціна?",
        f"{k}%",
    )


def _g6_linear_eq() -> Problem:
    a, x = random.randint(2, 9), random.randint(2, 12)
    b = random.randint(-20, 20)
    c = a * x + b
    return Problem(
        f"Розв'яжіть рівняння: {_int(a)}x {_term(b)} = {_int(c)}",
        f"x = {x}",
    )


def _g6_ratio() -> Problem:
    r1, r2 = random.randint(1, 5), random.randint(1, 5)
    total = (r1 + r2) * random.randint(5, 30)
    part = total // (r1 + r2)
    a, b = part * r1, part * r2
    return Problem(
        f"Поділіть {total} у співвідношенні {r1} : {r2}. Запишіть обидві частини.",
        f"{min(a, b)} і {max(a, b)}",
    )


def _g6_proportion() -> Problem:
    per = random.randint(20, 100)
    n1 = random.randint(3, 10)
    n2 = random.randint(2, 15)
    while n2 == n1:
        n2 = random.randint(2, 15)
    return Problem(
        f"{n1} зошитів коштують {per * n1} грн. Скільки коштують {n2} зошитів?",
        f"{per * n2} грн",
    )


def _g6_unit_convert() -> Problem:
    variant = random.randint(0, 2)
    if variant == 0:
        n = random.randint(1, 9)
        kg = n + (0.5 if random.random() < 0.4 else 0)
        return Problem(
            f"Скільки грамів у {_dec_t(kg * 10)} кілограмах?",
            str(int(kg * 1000)),
        )
    if variant == 1:
        h = random.randint(2, 12)
        return Problem(f"Скільки хвилин у {h} годинах?", str(h * 60))
    l = random.randint(1, 9)
    return Problem(f"Скільки мілілітрів у {l} літрах?", str(l * 1000))


# ---------------------------------------------------------------- 7 клас

def _g7_eq_fraction() -> Problem:
    c, d = random.randint(2, 9), random.randint(2, 12)
    b = random.randint(-15, 15)
    x = c * d - b
    if x == 0:
        d += 1
        x = c * d - b
    return Problem(
        f"Розв'яжіть рівняння: (x {_term(b)}) : {c} = {d}",
        f"x = {_int(x)}",
    )


def _g7_negative_fractions() -> Problem:
    f1 = Fraction(random.randint(1, 9), random.randint(2, 12)) * random.choice([1, -1])
    f2 = Fraction(random.randint(1, 9), random.randint(2, 12)) * random.choice([1, -1])
    if random.random() < 0.5:
        q = f"{f1.numerator}/{f1.denominator} + {f2.numerator}/{f2.denominator}" if f1 >= 0 and f2 >= 0 \
            else f"({_int(f1.numerator)}/{f1.denominator}) + ({_int(f2.numerator)}/{f2.denominator})"
        return Problem(f"Обчисліть: {q}", _frac(f1 + f2))
    q = f"({_int(f1.numerator)}/{f1.denominator}) − ({_int(f2.numerator)}/{f2.denominator})"
    return Problem(f"Обчисліть: {q}", _frac(f1 - f2))


def _g7_powers() -> Problem:
    while True:
        if random.random() < 0.35:
            base, e = random.choice([-2, -3, 3]), random.randint(3, 4)
            other = random.randint(2, 9)
            val = base ** e - other ** 2
            if val == 0:
                continue
            return Problem(
                f"Обчисліть: ({_int(base)}){_sup(e)} − {other}²",
                _int(val),
            )
        base = random.choice([2, 3, 5, 10])
        e1 = random.randint(3, 6) if base <= 5 else random.randint(2, 4)
        e2 = random.randint(2, 4)
        e3 = random.randint(1, e1)
        exp = e1 + e2 - e3
        if exp < 1 or base ** exp > 10 ** 6:
            continue
        if random.random() < 0.5:
            q = f"{base}{_sup(e1)} × {base}{_sup(e2)} : {base}{_sup(e3)}"
        else:
            q = f"{base}{_sup(e1)} : {base}{_sup(e3)} × {base}{_sup(e2)}"
        return Problem(f"Обчисліть: {q}", str(base ** exp))


def _g7_percent_whole() -> Problem:
    p = random.choice([2, 4, 5, 8, 10, 12, 15, 20, 25, 40, 50])
    m = random.randint(2, 20)
    return Problem(
        f"{p}% числа дорівнює {p * m}. Знайдіть це число.",
        str(100 * m),
    )


def _g7_polygon() -> Problem:
    if random.random() < 0.5:
        n = random.randint(5, 12)
        return Problem(
            f"Знайдіть суму всіх кутів опуклої {n}-кутника.",
            f"{(n - 2) * 180}°",
        )
    s = random.randint(3, 10) * 180
    return Problem(
        f"Сума всіх кутів опуклої многокутника дорівнює {s}°. Скільки у нього сторін?",
        str(s // 180 + 2),
    )


def _g7_proportion_eq() -> Problem:
    a, k, x = random.randint(2, 12), random.randint(2, 8), random.randint(1, 15)
    c, b = a * k, x * k
    return Problem(
        f"Розв'яжіть пропорцію: x : {a} = {b} : {c}",
        f"x = {x}",
    )


def _g7_polynomial() -> Problem:
    a = random.randint(2, 5)
    c = random.randint(1, 3)
    b = random.randint(-7, 7)
    while b == 0:
        b = random.randint(-7, 7)
    d = random.randint(-7, 7)
    while d == 0:
        d = random.randint(-7, 7)
    x2, x1, const = a * c, a * d + b * c, b * d
    answer_parts = []
    answer_parts.append(f"{_int(x2)}x²" if x2 != 1 else "x²")
    if x1 != 0:
        answer_parts.append(_term_x(x1))
    if const != 0:
        answer_parts.append(_term(const))
    return Problem(
        f"Помножте: ({_int(a)}x {_term(b)})({_int(c)}x {_term(d)})",
        " ".join(answer_parts),
    )


# ---------------------------------------------------------------- 8 клас

def _g8_quadratic() -> Problem:
    while True:
        r1, r2 = random.randint(-9, 9), random.randint(-9, 9)
        b, c = -(r1 + r2), r1 * r2
        if b == 0:
            continue
        return Problem(
            f"Розв'яжіть рівняння: {_poly2(1, b, c)}",
            _roots(_int(r1), _int(r2)),
        )


def _g8_sqrt() -> Problem:
    k = random.randint(2, 9)
    m = random.choice(_SQUAREFREE + (1,))
    n = k * k * m
    if m == 1:
        return Problem(f"Обчисліть: √{n}", str(k))
    return Problem(
        f"Спростіть вираз: √{n}",
        f"{k}√{m}" if k != 1 else f"√{m}",
    )


def _g8_pythagoras() -> Problem:
    m = random.randint(3, 9)
    n = random.randint(1, m - 1)
    a, b = sorted([m * m - n * n, 2 * m * n])
    c = m * m + n * n
    return Problem(
        f"Катети прямокутного трикутника дорівнюють {a} і {b}. Знайдіть гіпотенузу.",
        str(c),
    )


def _g8_system() -> Problem:
    x0, y0 = random.randint(-6, 6), random.randint(-6, 6)
    m1 = random.randint(-4, 4)
    while m1 == 0:
        m1 = random.randint(-4, 4)
    m2 = random.randint(-4, 4)
    while m2 == 0 or m2 == m1:
        m2 = random.randint(-4, 4)
    b1, b2 = y0 - m1 * x0, y0 - m2 * x0

    def line(m, b):
        if m == 1:
            mx = "x"
        elif m == -1:
            mx = "−x"
        else:
            mx = f"{_int(m)}x"
        return f"y = {mx} {_term(b)}"

    return Problem(
        f"Розв'яжіть систему рівнянь:\n{line(m1, b1)}\n{line(m2, b2)}",
        f"x = {_int(x0)}; y = {_int(y0)}",
    )


def _g8_factor() -> Problem:
    if random.random() < 0.5:
        k = random.randint(2, 12)
        return Problem(
            f"Розкладіть на множники: x² − {k ** 2}",
            f"(x − {k})(x + {k})",
        )
    while True:
        p, q = random.randint(-9, 9), random.randint(-9, 9)
        if p == 0 or q == 0:
            continue
        b, c = p + q, p * q
        hi, lo = max(p, q), min(p, q)
        return Problem(
            f"Розкладіть на множники: {_poly2(1, b, c)}",
            f"(x {_term(hi)})(x {_term(lo)})",
        )


def _g8_exponents() -> Problem:
    while True:
        base = random.choice([2, 3, 5])
        e1, e2 = random.randint(2, 4), random.randint(2, 3)
        e3 = -random.randint(1, e1 * e2)
        exp = e1 * e2 + e3
        if not -2 <= exp <= 6:
            continue
        val = Fraction(base ** exp) if exp >= 0 else Fraction(1, base ** -exp)
        return Problem(
            f"Обчисліть: ({base}{_sup(e1)}){_sup(e2)} × {base}{_sup(e3)}",
            _frac(val) if val.denominator != 1 else str(val.numerator),
        )


def _g8_average() -> Problem:
    while True:
        n = random.randint(4, 6)
        mean = random.randint(12, 30)
        total = mean * n
        others = [random.randint(mean - 6, mean + 6) for _ in range(n - 1)]
        last = total - sum(others)
        if mean - 12 <= last <= mean + 12 and last not in others:
            break
    listed = ", ".join(map(str, others))
    return Problem(
        f"Середнє арифметичне {n} чисел дорівнює {mean}. З них відомо: {listed}. "
        f"Знайдіть невідоме {n}-те число.",
        str(last),
    )


# ---------------------------------------------------------------- 9 клас

def _g9_quadratic_a() -> Problem:
    while True:
        r1 = Fraction(random.randint(-8, 8), random.randint(1, 4))
        r2 = Fraction(random.randint(-8, 8), random.randint(1, 4))
        a = random.randint(1, 5)
        b = -a * (r1 + r2)
        c = a * r1 * r2
        coeffs = [Fraction(a), b, c]
        den = math.lcm(*[f.denominator for f in coeffs])
        A, B, C = int(coeffs[0] * den), int(b * den), int(c * den)
        g = math.gcd(math.gcd(abs(A), abs(B)), abs(C))
        A, B, C = A // g, B // g, C // g
        if A == 1 and abs(B) > 50:
            continue
        return Problem(
            f"Розв'яжіть рівняння: {_poly2(A, B, C)}",
            _roots(_frac(r1), _frac(r2)),
        )


def _g9_discriminant() -> Problem:
    a = random.randint(1, 6)
    b = random.randint(-9, 9)
    c = random.randint(-9, 9)
    if b == 0:
        c = random.randint(1, 9)
    d = b * b - 4 * a * c
    return Problem(
        f"Обчисліть дискримінант рівняння: {_poly2(a, b, c)}",
        f"D = {_int(d)}",
    )


def _g9_square_trinomial() -> Problem:
    m = random.randint(-9, 9)
    if m == 0:
        m = 5
    if m > 0:
        expr = f"x² + {2 * m}x + {m * m}"
        ans = f"(x + {m})²"
    else:
        expr = f"x² − {abs(2 * m)}x + {m * m}"
        ans = f"(x − {abs(m)})²"
    return Problem(
        f"Розкладіть на множники: {expr}",
        ans,
    )


def _g9_system() -> Problem:
    while True:
        x0, y0 = random.randint(-7, 7), random.randint(-7, 7)
        a1 = random.randint(-5, 5) or 1
        b1 = random.randint(-5, 5) or 1
        a2 = random.randint(-5, 5) or 1
        b2 = random.randint(-5, 5) or 1
        det = a1 * b2 - a2 * b1
        if det == 0:
            continue
        c1, c2 = a1 * x0 + b1 * y0, a2 * x0 + b2 * y0

        def line(a, b, c):
            return f"{_int(a)}x {_term(b)}y = {_int(c)}"

        return Problem(
        f"Розв'яжіть систему рівнянь:\n{line(a1, b1, c1)}\n{line(a2, b2, c2)}",
        f"x = {_int(x0)}; y = {_int(y0)}",
        )


def _g9_irrational() -> Problem:
    for _ in range(200):
        d = random.randint(1, 5)
        x0 = random.randint(d, 10)
        c = (x0 - d) ** 2 - x0
        x1 = 2 * d + 1 - x0
        ok1 = x1 < d or x1 + c < 0
        if x0 + c >= 0 and ok1:
            left = f"x {_term(c)}" if c != 0 else "x"
            return Problem(
                f"Розв'яжіть рівняння: √({left}) = x − {d}",
                f"x = {x0}",
            )
    raise RuntimeError("irrational generator failed")


def _g9_percent_two_step() -> Problem:
    k = random.choice([10, 15, 20, 25, 30, 40])
    diff = Fraction(-k * k, 100)
    ans = ("−" + _frac(-diff) if diff < 0 else _frac(diff)) + "%"
    return Problem(
        f"Число зменшили на {k}%, а потім результат збільшили на {k}%. "
        f"На скільки відсотків результат відрізняється від початкового числа?",
        ans,
    )


def _g9_vertex() -> Problem:
    b = 2 * random.randint(-8, 8)
    if b == 0:
        b = 6
    c = random.randint(-12, 12)
    x_v = -b // 2
    return Problem(
        f"Знайдіть абсцису вершини параболи: y = {_poly2(1, b, c).replace(' = 0', '')}",
        f"x = {_int(x_v)}",
    )


def _g9_inscribed() -> Problem:
    central = 2 * random.randint(20, 140)
    return Problem(
        f"Центральний кут дорівнює {central}°. Знайдіть вписаний кут, "
        f"що спирається на ту саму дугу.",
        f"{central // 2}°",
    )


def _g9_probability() -> Problem:
    red = random.randint(2, 7)
    blue = random.randint(2, 7)
    return Problem(
        f"У капелюсі {red} червоних і {blue} синіх кульок. Кульки рівноймовірні. "
        f"Яка ймовірність витягнути червону кульку?",
        _frac(Fraction(red, red + blue)),
    )


# ---------------------------------------------------------------- реєстр

_BY_GRADE: dict[int, list[Spec]] = {
    5: [
        Spec(_g5_add_fractions, "Дроби",
             "Приведи обидва дроби до спільного знаменника, потім додай чисельники", 2),
        Spec(_g5_percent_of, "Відсотки",
             "1% від числа — це число, поділене на 100", 1),
        Spec(_g5_decimals, "Числа й дії",
             "Запиши числа без коми, обчисли, а потім постав кому на місце", 1),
        Spec(_g5_rectangle, "Геометрія",
             "Периметр = 2 · (довжина + ширина), площа = довжина · ширина", 1),
        Spec(_g5_order_ops, "Числа й дії",
             "Правило дій: спочатку дужки, потім множення, а в кінці віднімання", 1),
        Spec(_g5_lcm_gcd, "Числа й дії",
             "НСК двох чисел можна знайти через НСД: НСК = a · b : НСД(a, b)", 2),
        Spec(_g5_fraction_of, "Дроби",
             "Помнож чисельник дробу на число і поділи на знаменник", 1),
        Spec(_g5_units, "Одиниці вимірювання",
             "1 год = 60 хв, 1 км = 1000 м, 1 т = 1000 кг", 1),
    ],
    6: [
        Spec(_g6_int_ops, "Числа й дії",
             "Пам'ятай: спочатку множення, потім додавання й віднімання", 1),
        Spec(_g6_fraction_ops, "Дроби",
             "Множення: чисельники окремо, знаменники окремо. Ділення: помнож на обернений дріб", 2),
        Spec(_g6_percent_change, "Відсотки",
             "Знайди різницю цін і поділи її на початкову ціну", 2),
        Spec(_g6_linear_eq, "Рівняння",
             "Перенеси відоме число в інший бік зі зміною знаку, потім поділи на коефіцієнт при x", 1),
        Spec(_g6_ratio, "Числа й дії",
             "Розділи число на суму частин співвідношення і помнож на кожну частину", 2),
        Spec(_g6_proportion, "Рівняння",
             "Склади пропорцію: ціна за одиницю × кількість", 2),
        Spec(_g6_unit_convert, "Одиниці вимірювання",
             "1 кг = 1000 г, 1 год = 60 хв, 1 л = 1000 мл", 1),
    ],
    7: [
        Spec(_g7_eq_fraction, "Рівняння",
             "Помнож обидві частини на знаменник, щоб позбутися дробу", 2),
        Spec(_g7_negative_fractions, "Дроби",
             "Зведи до спільного знаменника і дуже уважно стеж за знаками", 2),
        Spec(_g7_powers, "Степені та корені",
             "Скористайся правилами aᵐ · aⁿ = aᵐ⁺ⁿ та aᵐ : aⁿ = aᵐ⁻ⁿ", 2),
        Spec(_g7_percent_whole, "Відсотки",
             "Якщо p% числа дорівнюють A, то число = A · 100 : p", 2),
        Spec(_g7_polygon, "Геометрія",
             "Сума кутів опуклої n-кутника = (n − 2) · 180°", 1),
        Spec(_g7_proportion_eq, "Рівняння",
             "Добуток зовнішніх членів пропорції дорівнює добутку внутрішніх", 1),
        Spec(_g7_polynomial, "Многочлени",
             "Кожен член першого множника помнож на кожен член другого", 2),
    ],
    8: [
        Spec(_g8_quadratic, "Рівняння",
             "Спробуй розкласти на множники або застосуй формулу коренів", 2),
        Spec(_g8_sqrt, "Степені та корені",
             "Шукай найбільший повний квадрат: √(k² · m) = k√m", 2),
        Spec(_g8_pythagoras, "Геометрія",
             "Теорема Піфагора: c² = a² + b², де c — гіпотенуза", 2),
        Spec(_g8_system, "Системи рівнянь",
             "Підстав друге рівняння в перше або порівняй їх", 2),
        Spec(_g8_factor, "Многочлени",
             "Шукай два числа: добуток = вільний член, сума = коефіцієнт при x", 2),
        Spec(_g8_exponents, "Степені та корені",
             "(aᵐ)ⁿ = aᵐⁿ, а від'ємний степінь — це одиниця, поділена на число", 3),
        Spec(_g8_average, "Середнє та ймовірність",
             "Помнож середнє на кількість чисел і відніми відомі числа", 2),
    ],
    9: [
        Spec(_g9_quadratic_a, "Рівняння",
             "Спершу скороти всі коефіцієнти на спільний дільник, потім шукай корені", 3),
        Spec(_g9_discriminant, "Рівняння",
             "Формула дискримінанта: D = b² − 4ac", 2),
        Spec(_g9_square_trinomial, "Многочлени",
             "Повний квадрат: x² + 2mx + m² = (x + m)²", 2),
        Spec(_g9_system, "Системи рівнянь",
             "Зведи систему до одного змінного: підстав або додай/відніми рівняння", 3),
        Spec(_g9_irrational, "Рівняння",
             "Обидві частини зведи в квадрат і не забудь перевірити корені!", 3),
        Spec(_g9_percent_two_step, "Відсотки",
             "Простеж за числом: 100% → (100 − k)% → (100 − k)(100 + k) / 100 %", 3),
        Spec(_g9_vertex, "Функція",
             "Абсциса вершини параболи y = ax² + bx + c: x = −b : 2a", 2),
        Spec(_g9_inscribed, "Геометрія",
             "Вписаний кут дорівнює половині центрального, що спирається на ту саму дугу", 1),
        Spec(_g9_probability, "Середнє та ймовірність",
             "Ймовірність = кількість сприятливих випадків : загальна кількість", 2),
    ],
}


def make_problem(grade: int, topics: tuple[str, ...] | list[str] | None = None) -> Problem:
    specs = _BY_GRADE[grade]
    if topics:
        filtered = [s for s in specs if s.topic in topics]
        if filtered:
            specs = filtered
    spec = random.choice(specs)
    base = spec.fn()
    return Problem(base.question, base.answer, spec.topic, spec.hint, spec.difficulty)


def grades_for(topics: tuple[str, ...] | list[str] | None) -> tuple[int, ...]:
    """Класи, які мають хоча б одну задачу з заданих тем."""
    if not topics:
        return GRADES
    result = tuple(
        g for g in GRADES
        if any(s.topic in topics for s in _BY_GRADE[g])
    )
    return result or GRADES


if __name__ == "__main__":
    for g in GRADES:
        print(f"===== {g} клас =====")
        for _ in range(300):
            p = make_problem(g)
            assert p.question and p.answer, p
            assert p.topic in TOPICS, p
            assert p.hint, p
            assert 1 <= p.difficulty <= 3, p
            assert "-" not in p.answer, p
        for _ in range(6):
            p = make_problem(g)
            print(f"  [{p.topic} | {'★' * p.difficulty}] {p.question}")
            print(f"    💡 {p.hint}")
            print(f"    → {p.answer}\n")
