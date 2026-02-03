from storage_utils import load_json, save_json
import datetime
import uuid

STATE_FILE = "state.json"

class StateManager:
    VALID_STATES = ["IDLE", "ARTIFACTS PROCESSING", "OQ PROCESSING", "PU PROCESSING", "FINALIZE"]

    def __init__(self):
        self.state = load_json(STATE_FILE)
        if not self.state:
            self.state = {
                "current_state": "IDLE",
                "last_run": None,
                "active_run_id": None
            }
            self.save()

    def get_current_state(self):
        return self.state.get("current_state", "IDLE")

    def set_state(self, new_state):
        if new_state not in self.VALID_STATES:
            raise ValueError(f"Invalid state: {new_state}")
        self.state["current_state"] = new_state
        self.save()

    def start_run(self):
        self.state["active_run_id"] = str(uuid.uuid4())
        self.state["last_run"] = datetime.datetime.now().isoformat()
        self.save()

    def end_run(self):
        self.state["active_run_id"] = None
        self.save()

    def save(self):
        save_json(STATE_FILE, self.state)
