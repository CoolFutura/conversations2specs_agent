import unittest

from src.cli import wiring


class WiringSmokeTests(unittest.TestCase):
    # Verifies that wiring can build all use cases without errors.
    def test_builds_all_use_cases(self):
        self.assertIsNotNone(wiring.build_ingest_use_case())
        self.assertIsNotNone(wiring.build_transform_artifacts_use_case())
        self.assertIsNotNone(wiring.build_transform_oq_use_case())
        self.assertIsNotNone(wiring.build_approve_pu_use_case())
        self.assertIsNotNone(wiring.build_add_decision_use_case())
        self.assertIsNotNone(wiring.build_modify_oq_use_case())
        self.assertIsNotNone(wiring.build_change_artifact_status_use_case())
        self.assertIsNotNone(wiring.build_change_artifact_status_batch_use_case())
        self.assertIsNotNone(wiring.build_list_artifacts_use_case())
        self.assertIsNotNone(wiring.build_list_open_questions_use_case())
        self.assertIsNotNone(wiring.build_list_proposed_updates_use_case())
        self.assertIsNotNone(wiring.build_init_sync_use_case())
        self.assertIsNotNone(wiring.build_reset_data_use_case())
        self.assertIsNotNone(wiring.build_set_last_ts_use_case())
        self.assertIsNotNone(wiring.build_delete_oq_use_case())


if __name__ == "__main__":
    unittest.main()
