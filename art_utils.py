from storage_utils import load_json, update_json_list
import uuid

def transform_all_artifacts():
    data = load_json("artifacts.json")
    artifacts = data.get("artifacts", [])
    
    oq_count = 0
    pu_count = 0
    
    for art in artifacts:
        if art["status"] == "PENDING":
            if art["type"] == "OQ":
                create_oq_from_artifact(art)
                art["status"] = "OQ"
                oq_count += 1
            elif art["type"] == "PU":
                create_pu_from_artifact(art)
                art["status"] = "PU"
                pu_count += 1
            # update_json_list handled inside loop for simplicity in v1, 
            # but ideally we batch update artifacts.json
    
    # Batch save updated artifacts status
    save_json("artifacts.json", data)
    return oq_count, pu_count

def create_oq_from_artifact(artifact):
    oq = {
        "id": f"oq_{uuid.uuid4().hex[:8]}",
        "artifact_id": artifact["id"],
        "question": artifact["rephrasing"],
        "context": artifact["summary_of_context"],
        "status": "OPEN",
        "slack_ts": None
    }
    update_json_list("open_questions.json", "questions", oq)

def create_pu_from_artifact(artifact):
    pu = {
        "id": f"pu_{uuid.uuid4().hex[:8]}",
        "artifact_id": artifact["id"],
        "source_oq_id": None,
        "rephrasing": artifact["rephrasing"],
        "context": artifact["summary_of_context"],
        "decision": "",
        "rationale": artifact["rationale"],
        "status": "DRAFT"
    }
    update_json_list("proposed_updates.json", "updates", pu)

def save_json(filename, data):
    import json
    import os
    path = os.path.join("data", filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
