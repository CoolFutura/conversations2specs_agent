import json
from llm_pipeline.llm_utils import load_prompt, call_llm
from storage_utils import update_json_list
import uuid

def classify_conversation(conversation_text):
    prompt = load_prompt("classify_discussion", conversation=conversation_text)
    response_text = call_llm(prompt)
    
    try:
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        print("Error parsing LLM response.")
        return None

def create_artifact_from_classification(conv_id, classification):
    artifact = {
        "id": f"art_{uuid.uuid4().hex[:8]}",
        "conversation_id": conv_id,
        "type": classification.get("type"),
        "status": "PENDING",
        "rephrasing": classification.get("rephrasing", ""),
        "rationale": classification.get("rationale", ""),
        "summary_of_context": classification.get("summary_of_context", "")
    }
    
    update_json_list("artifacts.json", "artifacts", artifact)
    return artifact
