import unittest

from src.use_cases.init_sync import InitSyncUseCase


class FakeSourcesState:
    def __init__(self):
        self.last_call = None

    def set_last_ts(self, channel_id: str, last_ts: str) -> None:
        self.last_call = (channel_id, last_ts)


class InitSyncUseCaseTests(unittest.TestCase):
    # Verifies that InitSyncUseCase writes last_ts and returns the same values.
    def test_init_sync_sets_last_ts(self):
        fake_state = FakeSourcesState()
        use_case = InitSyncUseCase(fake_state)

        result = use_case.execute("C123", "1234567890.0")

        self.assertEqual(fake_state.last_call, ("C123", "1234567890.0"))
        self.assertEqual(result.channel_id, "C123")
        self.assertEqual(result.last_ts, "1234567890.0")


if __name__ == "__main__":
    unittest.main()
