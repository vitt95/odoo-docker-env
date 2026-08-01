"""Asynchronous execution of the interpretation (`ai/05-esecuzione-asincrona.md`).

Part 6. The rule that shapes every file here is the one from part 2: **the chain
never assumes it runs inside an HTTP request**. Because it was respected, this module
is a wrapper and not a rewrite — acceptance, a queue, a dispatcher and a
notification, with the chain itself unchanged underneath.

The risk being answered, RA3, is the only one in the project whose damage lands
*outside* the product: four users writing a sentence at the same time are enough to
stop the ERP for everybody else (§1.1). So the measure of success is not how fast
this module is, it is that an accountant issuing an invoice cannot tell that somebody
else is talking to the ERP.
"""

from . import models
