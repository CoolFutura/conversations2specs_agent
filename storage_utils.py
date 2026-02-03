import json
import os

DATA_DIR = "data"

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def update_json_list(filename, list_key, new_item, match_key="id"):
    data = load_json(filename)
    items = data.get(list_key, [])
    
    # Check for existing item to update or append
    for i, item in enumerate(items):
        if item.get(match_key) == new_item.get(match_key):
            items[i] = new_item
            break
    else:
        items.append(new_item)
    
    data[list_key] = items
    save_json(filename, data)
