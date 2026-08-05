"""Where threads, cursors and environments are allowed to exist.

The split between this package and `queue/` is deliberate and is the reason the load
control can be tested at all: `queue/` decides, `runtime/` acts. Nothing here chooses
a limit, a pool size or a message; nothing in `queue/` opens a cursor.
"""

from . import claim, pipeline, progress, worker
