"""Temporal expressions into absolute ranges (§9.2).

**Deterministic zone**: computes with dates, never reads the clock. The reference
instant is an argument, which is what lets the evaluation corpus be re-run at a fixed
instant (§13.3 of `04`) without contrivance — and §9.2 requires exactly that, or the
expected outcome of a case containing `current_month` would change with the calendar
and comparisons between releases would mean nothing.

## The three installation parameters

§9.2 names them, and the third is the one that matters:

* the user's **time zone**;
* the **first day of the week**;
* the start of the **fiscal year**.

> In a company whose year is not the calendar year, *"this year"* means the fiscal
> year, and returning the calendar year would produce a **wrong number of perfectly
> credible appearance** — the canonical form of R1 applied to aggregated data.

Which is why `year_to_date` and `current_year` both resolve against the fiscal start
(D91), and why the parameters are required rather than defaulted to something
plausible.

## Half-open ranges

Every range returned is `[start, end)` — start included, end excluded. Not a
convention chosen for tidiness: a closed range on datetimes has to decide what
"end of day" means, and every system that decides it picks `23:59:59` and loses
whatever happened in the last second. Half-open has no such edge.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

#: Il formato con cui Odoo scrive e confronta un `datetime` nel database. Sempre UTC.
UTC_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class Instant:
    """The reference instant and the installation parameters that qualify it.

    Passed to the Resolver by whoever knows the current time. The Resolver is the
    only component *aware* of time (§4.6); this is the shape that awareness takes.
    """

    #: The reference moment, already in the user's time zone.
    now: datetime
    #: 0 = Monday, 6 = Sunday. Italy and most of Europe start on Monday; the
    #: parameter exists because some installations do not.
    first_weekday: int = 0
    #: Month and day the fiscal year **starts**. 1 January for a calendar year.
    fiscal_year_start_month: int = 1
    fiscal_year_start_day: int = 1
    #: Il nome del fuso dell'utente — `Europe/Rome` — non uno scostamento in ore.
    #:
    #: **Uno scostamento sarebbe sbagliato mezzo anno.** L'ora legale lo cambia, quindi
    #: *«il mese scorso»* chiesto a novembre e *«il mese scorso»* chiesto a giugno non
    #: si convertono allo stesso modo. Il nome porta con se' la regola; il numero no.
    #:
    #: Vuoto vuol dire UTC, che e' anche il comportamento di prima: chi non dichiara un
    #: fuso non ne subisce uno.
    timezone: str = ""

    @property
    def today(self) -> date:
        return self.now.date()

    def as_utc(self, moment: date) -> str:
        """La mezzanotte locale di `moment`, scritta in UTC come la scrive Odoo.

        E' il ponte fra il calendario, che ragiona in **giorni dell'utente**, e le
        colonne `datetime`, che stanno in **UTC**. Senza, i due estremi di un periodo
        finivano confrontati con una colonna in un'altra unita' di misura, e il numero
        usciva vicino a quello giusto e sbagliato.

        Un fuso che il sistema non conosce non fa fallire un'interrogazione: si torna a
        UTC, che e' esattamente cio' che si faceva prima di questa funzione. Una
        risposta con il fuso sbagliato e' un difetto; una conversazione che si rifiuta
        di rispondere perche' un `tz` e' scritto male e' un difetto peggiore.
        """
        naive = datetime(moment.year, moment.month, moment.day)
        if not self.timezone:
            return naive.strftime(UTC_FORMAT)
        try:
            zone = ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            return naive.strftime(UTC_FORMAT)
        return naive.replace(tzinfo=zone).astimezone(ZoneInfo("UTC")).strftime(
            UTC_FORMAT)


@dataclass(frozen=True)
class Range:
    """A half-open interval of dates, `[start, end)`."""

    start: date
    end: date

    def __contains__(self, moment: date) -> bool:
        return self.start <= moment < self.end

    @property
    def days(self) -> int:
        return (self.end - self.start).days


class UnresolvableExpression(Exception):
    """The expression is in the vocabulary but cannot be resolved as given."""


def _add_months(moment: date, months: int) -> date:
    """Month arithmetic that does not overflow into the next month.

    31 January minus one month is 28 or 29 February, not 3 March. Every library gets
    asked this and answers differently; doing it here in four lines removes the
    question from the dependency list.
    """
    total = moment.month - 1 + months
    year = moment.year + total // 12
    month = total % 12 + 1
    last_day = _days_in_month(year, month)
    return date(year, month, min(moment.day, last_day))


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def _week_start(moment: date, first_weekday: int) -> date:
    offset = (moment.weekday() - first_weekday) % 7
    return moment - timedelta(days=offset)


def _quarter_start(moment: date) -> date:
    return date(moment.year, 3 * ((moment.month - 1) // 3) + 1, 1)


def fiscal_year_start(instant: Instant, moment: date | None = None) -> date:
    """The start of the fiscal year containing `moment`.

    A company whose year starts on 1 July is in fiscal 2026 from 1 July 2026 to
    30 June 2027. Getting this wrong is invisible: the query succeeds and the total
    is for the wrong twelve months.
    """
    moment = moment or instant.today
    candidate = date(moment.year, instant.fiscal_year_start_month,
                     instant.fiscal_year_start_day)
    if moment < candidate:
        candidate = date(moment.year - 1, instant.fiscal_year_start_month,
                         instant.fiscal_year_start_day)
    return candidate


#: The interval `n` admits, duplicated from the contract on purpose: this module is a
#: pure zone that computes with dates and imports nothing, and the check here is the
#: **second** lock. Level 2 refuses `month_of_year(13)` before it ever gets here; if it
#: one day stopped refusing it, the Resolver would say so instead of picking a window.
_NAMED_RANGE = {"month_of_year": (1, 12), "quarter_of_year": (1, 4),
                "half_of_year": (1, 2)}

#: How many months each named period spans. A half is two quarters, and saying so once
#: here is what keeps the two from drifting apart.
_NAMED_MONTHS = {"quarter_of_year": 3, "half_of_year": 6}


def _exercise_start(instant: Instant, year: int | None) -> date:
    """The first day of the exercise a named period belongs to.

    Without a year: the exercise in progress. With one: the exercise that **starts**
    in that year, which for a calendar company is simply that year.
    """
    if year is None:
        return fiscal_year_start(instant)
    return date(year, instant.fiscal_year_start_month, instant.fiscal_year_start_day)


def _named_period(expression: str, value: dict, instant: Instant) -> Range:
    """`month_of_year`, `quarter_of_year`, `year_of` into a window (D141)."""
    try:
        which = int(value["n"])
    except (KeyError, TypeError, ValueError) as error:
        raise UnresolvableExpression(
            f"{expression} needs 'n': level 2 should have refused it") from error

    admitted = _NAMED_RANGE.get(expression)
    if admitted and not admitted[0] <= which <= admitted[1]:
        raise UnresolvableExpression(
            f"{expression}({which}) is outside {admitted[0]}-{admitted[1]}: there is "
            f"no such period, and a plausible one would be worse than none"
        )

    year = value.get("year")
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError) as error:
            raise UnresolvableExpression(f"{value['year']!r} is not a year") from error

    if expression == "year_of":
        start = _exercise_start(instant, which)
        return Range(start, _add_months(start, 12))

    exercise = _exercise_start(instant, year)
    if expression in _NAMED_MONTHS:
        span = _NAMED_MONTHS[expression]
        start = _add_months(exercise, span * (which - 1))
        return Range(start, _add_months(start, span))

    # A named month is the one that falls **inside** the exercise. For a calendar
    # company that is the same year; for a July company, January comes six months
    # after the exercise opened, so it belongs to the following calendar year.
    start = date(exercise.year, which, 1)
    if start < exercise:
        start = date(exercise.year + 1, which, 1)
    return Range(start, _add_months(start, 1))


def resolve(value: dict, instant: Instant) -> Range:
    """A temporal value of the contract into a half-open range of dates.

    `value` is the `{"kind": "temporal", ...}` of §8.2, already validated: the symbol
    is in the vocabulary and its parameters are present. What is left here is
    arithmetic.
    """
    expression = value.get("expression")
    today = instant.today

    if expression == "today":
        return Range(today, today + timedelta(days=1))
    if expression == "yesterday":
        return Range(today - timedelta(days=1), today)
    if expression == "tomorrow":
        return Range(today + timedelta(days=1), today + timedelta(days=2))

    if expression == "current_week":
        start = _week_start(today, instant.first_weekday)
        return Range(start, start + timedelta(days=7))
    if expression == "previous_week":
        start = _week_start(today, instant.first_weekday) - timedelta(days=7)
        return Range(start, start + timedelta(days=7))

    if expression == "current_month":
        start = today.replace(day=1)
        return Range(start, _add_months(start, 1))
    if expression == "previous_month":
        start = _add_months(today.replace(day=1), -1)
        return Range(start, _add_months(start, 1))

    if expression == "current_quarter":
        start = _quarter_start(today)
        return Range(start, _add_months(start, 3))
    if expression == "previous_quarter":
        start = _add_months(_quarter_start(today), -3)
        return Range(start, _add_months(start, 3))

    if expression == "current_year":
        start = fiscal_year_start(instant)
        return Range(start, _add_months(start, 12))
    if expression == "previous_year":
        start = _add_months(fiscal_year_start(instant), -12)
        return Range(start, _add_months(start, 12))

    if expression == "year_to_date":
        # D91, and V-D91-1: against the **fiscal** start, like `current_year`. The
        # end is tomorrow because the range is half-open and today counts.
        return Range(fiscal_year_start(instant), today + timedelta(days=1))

    # **D141 — the periods a sentence names.** The fiscal year is the frame for all
    # three, exactly as it is for `current_year`: in a company whose exercise starts in
    # July, *"the first quarter"* is July to September and *"January"* is the January
    # inside the exercise in progress. Answering with the calendar quarter would give a
    # wrong number of perfectly credible appearance (§9.2's warning, D91's argument).
    if expression in ("month_of_year", "quarter_of_year", "half_of_year", "year_of"):
        return _named_period(expression, value, instant)

    if expression == "last_n_days":
        days = int(value["n"])
        return Range(today - timedelta(days=days), today + timedelta(days=1))
    if expression == "last_n_weeks":
        weeks = int(value["n"])
        return Range(today - timedelta(weeks=weeks), today + timedelta(days=1))
    if expression == "last_n_months":
        months = int(value["n"])
        return Range(_add_months(today, -months), today + timedelta(days=1))
    if expression == "next_n_days":
        days = int(value["n"])
        return Range(today, today + timedelta(days=days + 1))

    if expression == "absolute":
        moment = _parse(value["date"])
        return Range(moment, moment + timedelta(days=1))
    if expression == "absolute_range":
        start, end = _parse(value["from"]), _parse(value["to"])
        if end < start:
            raise UnresolvableExpression(
                f"absolute_range ends before it starts: {value['from']} > {value['to']}"
            )
        # The user said "to 15 April" meaning the 15th included; the range is
        # half-open, so the end moves one day on.
        return Range(start, end + timedelta(days=1))

    raise UnresolvableExpression(
        f"{expression!r} reached the Resolver: level 2 should have refused it"
    )


def _parse(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise UnresolvableExpression(f"{value!r} is not an ISO date") from error


def describe(value: dict, instant: Instant, predicate: str = "within") -> str:
    """The resolved period **as the predicate takes it**, for the interpretation (D67).

    *"This month"* confirms itself; only the resolved period makes a non-calendar
    fiscal year verifiable — the canonical form of R1 on aggregated data. So the
    interpretation shows *"1 – 31 July 2026"*, never *"questo mese"*.

    **Why the predicate is here, since 3 August 2026.** It was not, and the turn that
    showed why is worth keeping: the state said `after current_year`, the executed
    domain was `create_date >= 2026-12-31 23:00:00` — after the *end* of the year, no
    records — and the interpretation above the answer said *"2026-01-01 - 2026-12-31"*.
    The product was showing the window of the expression instead of the set it had
    actually queried, so the user read the whole year and got nothing, with no way of
    telling why.

    A description that does not describe is worse than none: the interpretation exists
    to make an answer checkable (§10), and this one was making a wrong answer look
    right. `before` and `after` take one side of the window, and say so.
    """
    resolved = resolve(value, instant)
    last = resolved.end - timedelta(days=1)
    if predicate == "before":
        return f"< {resolved.start.isoformat()}"
    if predicate == "after":
        return f"> {last.isoformat()}"
    if resolved.start == last:
        return resolved.start.isoformat()
    return f"{resolved.start.isoformat()} - {last.isoformat()}"
