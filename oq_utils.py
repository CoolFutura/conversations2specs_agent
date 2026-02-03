from storage_utils import load_json, update_json_list
import json
import os

def create_pu_from_oq(oq_id, decision, rationale=None):
    oq_data = load_json("open_questions.json")
    target_oq = None
    for oq in oq_data.get("questions", []):
        if oq["id"] == oq_id:
            target_oq = oq
            oq["status"] = "TRANSFORMED"
            break
    
    if not target_oq:
        print(f"OQ {oq_id} not found.")
        return None

    # Update open_questions.json with TRANSFORMED status
    path = os.path.join("data", "open_questions.json")
    with open(path, "w") as f:
        json.dump(oq_data, f, indent=2)

    pu = {
        "id": f"pu_from_oq_{uuid.uuid4().hex[:8]}",
        "artifact_id": target_oq["artifact_id"],
        "source_oq_id": oq_id,
        "rephrasing": target_oq["question"],
        "context": target_oq["context"],
        "decision": decision,
        "rationale": rationale or "Transformed from OQ",
        "status": "DRAFT"
    }
    
    update_json_list("proposed_updates.json", "updates", pu)
    return pu

import uuid # Ensure uuid is available
