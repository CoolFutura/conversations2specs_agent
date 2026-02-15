import unittest

from src.use_cases.set_last_ts import SetLastTsUseCase


class FakeSourcesState:
    def __init__(self):
        self.last_call = None

    def set_last_ts(self, channel_id: str, last_ts: str) -> None:
        self.last_call = (channel_id, last_ts)


class SetLastTsUseCaseTests(unittest.TestCase):
    # Verifies that SetLastTsUseCase computes and stores last_ts.
    def test_sets_last_ts_from_days(self):
        fake_state = FakeSourcesState()
        use_case = SetLastTsUseCase(fake_state)

        result = use_case.execute("C1", 3, now_ts=1_000_000.0)

        expected = 1_000_000.0 - (3 * 86400)
        self.assertEqual(result.last_ts, f"{expected:.6f}")
        self.assertEqual(fake_state.last_call, ("C1", f"{expected:.6f}"))


if __name__ == "__main__":
    unittest.main()
