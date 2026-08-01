"""The Executor: one of the two components that know Odoo exists (`04` §6.5).

Surface: the ORM — search, read, aggregate — plus actions and views. Count
before retrieval (D68), default limit 80 and hard ceiling 500 (D13).

Deliberately thin: together with the Catalogue this is the whole upgrade surface
of the product across Odoo major versions. Filled in part 4.
"""

from . import executor
