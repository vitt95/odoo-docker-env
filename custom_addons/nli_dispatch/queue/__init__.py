"""The load control, in the pure zone.

`05` §4.1 is blunt about why this is half the design rather than a complement:

    A queue without limits does not remove the saturation: **it moves it and makes
    it invisible.**

Every decision here is a function of numbers — how many turns are in flight, how deep
the queue is, how old a turn is, how many connections the database allows. None of it
needs Odoo, and keeping it out of Odoo is what lets the limits be tested at the
boundary values instead of by running the system and hoping.

That matters more here than elsewhere. **RE2** is the declared risk that these limits
get loosened under pressure, and a limit whose behaviour at the boundary is asserted
in a test is much harder to loosen by accident than one buried in a dispatcher.
"""

from . import breaker, limits, messages, pool
