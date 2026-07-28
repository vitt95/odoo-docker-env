"""The five limits, the pool, the messages and the breaker — at their boundaries.

Every assertion here is the kind that is trivial to write now and impossible to
reconstruct later, when a limit has been nudged during an incident and nobody
remembers what the boundary was supposed to be. RE2 is the declared risk that these
limits get loosened under pressure; this file is what makes loosening one a visible
act rather than a diff nobody reads.
"""

import unittest

from nli_dispatch.queue import breaker as breaker_module
from nli_dispatch.queue import limits as limits_module
from nli_dispatch.queue import messages as messages_module
from nli_dispatch.queue import pool as pool_module

LIMITS = limits_module.Limits(pool=8)


def admit(**overrides):
    arguments = {
        "in_flight_for_session": 0,
        "queued": 0,
        "requests_last_minute": 0,
        "limits": LIMITS,
    }
    arguments.update(overrides)
    return limits_module.admit(**arguments)


class TestTheFiveLimits(unittest.TestCase):
    def test_an_ordinary_request_is_accepted(self):
        decision = admit()
        self.assertTrue(decision.accepted)
        self.assertFalse(decision.supersedes)
        self.assertIsNone(decision.reason)

    def test_l1_supersedes_rather_than_queues(self):
        """A person does not ask two questions at once: they changed their mind."""
        decision = admit(in_flight_for_session=1)
        self.assertTrue(decision.accepted, "superseding is not a refusal")
        self.assertTrue(decision.supersedes)

    def test_l3_refuses_at_three_times_the_pool_and_not_before(self):
        self.assertTrue(admit(queued=23).accepted)
        refused = admit(queued=24)
        self.assertFalse(refused.accepted)
        self.assertEqual(refused.reason, limits_module.QUEUE_DEPTH)

    def test_l5_refuses_at_twenty_a_minute_and_not_before(self):
        self.assertTrue(admit(requests_last_minute=19).accepted)
        self.assertEqual(admit(requests_last_minute=20).reason, limits_module.RATE)

    def test_the_rate_is_judged_before_the_depth(self):
        """A client in a loop produces both. Telling it the system is busy would
        describe its own behaviour as a property of the system."""
        decision = admit(requests_last_minute=50, queued=100)
        self.assertEqual(decision.reason, limits_module.RATE)

    def test_an_open_circuit_refuses_before_anything_else(self):
        decision = admit(provider_available=False, requests_last_minute=50)
        self.assertEqual(decision.reason, limits_module.PROVIDER_DOWN)

    def test_l4_expires_strictly_after_thirty_seconds(self):
        self.assertFalse(limits_module.expired(30.0, limits=LIMITS))
        self.assertTrue(limits_module.expired(30.1, limits=LIMITS))

    def test_a_batch_never_exceeds_the_pool(self):
        self.assertEqual(limits_module.batch_size(pending=100, limits=LIMITS), 8)
        self.assertEqual(limits_module.batch_size(pending=3, limits=LIMITS), 3)
        self.assertEqual(limits_module.batch_size(pending=0, limits=LIMITS), 0)

    def test_a_refusal_without_a_reason_cannot_be_built(self):
        with self.assertRaises(ValueError):
            limits_module.Admission(accepted=False)

    def test_an_unknown_reason_cannot_be_built(self):
        with self.assertRaises(ValueError):
            limits_module.Admission(accepted=False, reason="because")


class TestThePoolIsDerived(unittest.TestCase):
    """RE4: the ceiling is PostgreSQL connections, not the CPU."""

    def test_the_recommended_deployment_gets_the_full_pool(self):
        deployment = pool_module.Deployment(
            db_maxconn=64, http_workers=4, max_cron_threads=4)
        self.assertEqual(pool_module.pool_size(deployment), 8)
        self.assertTrue(pool_module.connections_within_budget(deployment, 8))
        self.assertEqual(pool_module.connections_used(deployment, 8), 16)

    def test_a_tight_database_shrinks_the_pool_instead_of_exhausting_it(self):
        deployment = pool_module.Deployment(
            db_maxconn=16, http_workers=4, max_cron_threads=4)
        size = pool_module.pool_size(deployment)
        self.assertEqual(size, 4, "0.8 x 16 = 12, minus 8 already spoken for")
        self.assertTrue(pool_module.connections_within_budget(deployment, size))

    def test_a_pool_chosen_by_feel_would_breach_the_budget(self):
        """The failure this file exists to prevent, stated as an assertion."""
        deployment = pool_module.Deployment(
            db_maxconn=16, http_workers=4, max_cron_threads=4)
        self.assertFalse(pool_module.connections_within_budget(deployment, 8))

    def test_the_budget_is_split_between_dispatcher_records(self):
        """D20f: capacity is added with N dispatcher records, within one ceiling."""
        deployment = pool_module.Deployment(
            db_maxconn=100, http_workers=8, max_cron_threads=4, dispatchers=4)
        size = pool_module.pool_size(deployment)
        self.assertEqual(size, 8)
        self.assertTrue(pool_module.connections_within_budget(deployment, size))

    def test_an_installation_with_no_dispatcher_is_a_configuration_error(self):
        with self.assertRaises(ValueError):
            pool_module.pool_size(pool_module.Deployment(
                db_maxconn=64, http_workers=4, max_cron_threads=4, dispatchers=0))

    def test_the_pool_is_never_zero(self):
        deployment = pool_module.Deployment(
            db_maxconn=8, http_workers=8, max_cron_threads=4)
        self.assertEqual(pool_module.pool_size(deployment), 1)


class TestTheRefusalMessages(unittest.TestCase):
    """D69 — the three properties, asserted for every message that exists."""

    def test_every_reason_has_a_message(self):
        self.assertEqual(
            set(messages_module.MESSAGES), set(limits_module.REFUSAL_REASONS),
            "a refusal the user cannot read is one they will report as a defect")

    def test_no_message_blames_the_user_or_sounds_like_a_fault(self):
        for reason, message in messages_module.MESSAGES.items():
            rendered = f"{message.text} {message.action}".lower()
            for word in messages_module.FORBIDDEN_WORDS:
                self.assertNotIn(word, rendered, f"{reason}: {word!r}")

    def test_every_message_offers_an_action(self):
        for reason, message in messages_module.MESSAGES.items():
            self.assertTrue(message.action.strip(), reason)

    def test_a_message_without_an_action_cannot_be_built(self):
        with self.assertRaises(ValueError):
            messages_module.Refusal(reason="x", text="y", action="")

    def test_an_unknown_reason_fails_loudly(self):
        with self.assertRaises(KeyError):
            messages_module.refusal("something_new")


class TestTheCircuitBreaker(unittest.TestCase):
    def test_it_opens_on_the_fifth_consecutive_failure(self):
        state = breaker_module.Breaker()
        for _ in range(4):
            state = state.after_failure(1000.0)
        self.assertTrue(state.admits(1000.0))
        state = state.after_failure(1000.0)
        self.assertFalse(state.admits(1000.0))
        self.assertEqual(state.state(1000.0), breaker_module.OPEN)

    def test_a_success_between_failures_resets_the_count(self):
        """Consecutive, not cumulative: an isolated timeout is not an outage."""
        state = breaker_module.Breaker()
        for _ in range(4):
            state = state.after_failure(1000.0)
        state = state.after_success()
        state = state.after_failure(1001.0)
        self.assertTrue(state.admits(1001.0))

    def test_it_half_opens_after_the_cooling_period_and_admits_one_turn(self):
        state = breaker_module.Breaker()
        for _ in range(5):
            state = state.after_failure(1000.0)
        self.assertFalse(state.admits(1029.0))
        self.assertEqual(state.state(1030.0), breaker_module.HALF_OPEN)
        self.assertTrue(state.admits(1030.0))

    def test_a_successful_probe_closes_it(self):
        state = breaker_module.Breaker(consecutive_failures=5, opened_at=1000.0)
        self.assertEqual(state.after_success().state(1000.0), breaker_module.CLOSED)


if __name__ == "__main__":
    unittest.main()
