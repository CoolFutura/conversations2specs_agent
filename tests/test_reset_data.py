import unittest

from src.use_cases.reset_data import ResetDataUseCase


class FakeDataResetPort:
    def __init__(self):
        self.called = False

    def reset_all(self) -> None:
        self.called = True


class ResetDataUseCaseTests(unittest.TestCase):
    # Verifies that ResetDataUseCase calls the reset port.
    def test_resets_data(self):
        port = FakeDataResetPort()
        use_case = ResetDataUseCase(port)

        result = use_case.execute()

        self.assertTrue(result.success)
        self.assertTrue(port.called)


if __name__ == "__main__":
    unittest.main()
