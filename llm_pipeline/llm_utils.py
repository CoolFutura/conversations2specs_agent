import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_prompt(name, **kwargs):
    path = os.path.join("llm_pipeline", "prompts", f"{name}.txt")
    with open(path, "r") as f:
        template = f.read()
    
    for key, value in kwargs.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    
    return template

def call_llm(prompt):
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None
