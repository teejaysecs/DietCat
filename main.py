from flask import Flask, render_template, request, jsonify
import subprocess
import json
import os
from google import genai
from google.genai import types

app = Flask(__name__)

# Reads terminal environment variables automatically
raw_key = os.environ.get("GEMINI_API_KEY")

# Put your API key ONLY inside the quotes on line 14 below:
if not raw_key or raw_key.strip() == "":
    raw_key = "PASTE_YOUR_API_KEY_HERE"

api_key = raw_key.strip() if raw_key else None

# Initialize the modern client correctly with the key
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None

def get_executable_path():
    """Helper function to find the right binary for Linux or Windows"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Render (Linux) will use 'app', Windows will fallback to 'app.exe'
    linux_path = os.path.join(base_dir, 'app')
    windows_path = os.path.join(base_dir, 'app.exe')
    
    if os.path.exists(linux_path):
        return linux_path
    return windows_path

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/categorize', methods=['POST'])
def categorize_only():
    try:
        data = request.json
        age = data.get('age', '0')
        
        app_path = get_executable_path()
        
        if not os.path.exists(app_path):
            return jsonify({"category": f"Error: Executable file not found at {os.path.basename(app_path)}"})

        result = subprocess.run([app_path, str(age)], capture_output=True, text=True, timeout=5)
        category = result.stdout.strip()
        
        return jsonify({"category": category})
    except Exception as e:
        return jsonify({"category": f"Error: {str(e)}"})

@app.route('/api/plan', methods=['POST'])
def get_plan():
    if not client:
        return jsonify({"error": "API key missing. Please configure your GEMINI_API_KEY."}), 200

    try:
        data = request.json
        name = data.get('name', 'User')
        age = data.get('age', '0')
        focus = data.get('focus', 'General Balanced Diet')

        app_path = get_executable_path()

        category = "Youth"
        if os.path.exists(app_path):
            try:
                result = subprocess.run([app_path, str(age)], capture_output=True, text=True, timeout=5)
                category = result.stdout.strip()
            except Exception:
                pass

        prompt = (
            f"Provide a healthy Monday to Sunday meal plan for a {age}-year-old categorized as a '{category}' "
            f"focusing strictly on nutrition requirements for '{focus}'. "
            f"You MUST format the output strictly as a JSON object with this exact structure: "
            '{"Monday": {"Morning": "meal detail", "Afternoon": "meal detail", "Night": "meal detail"}, '
            '"Tuesday": {"Morning": "meal detail", "Afternoon": "meal detail", "Night": "meal detail"}, '
            '"Wednesday": {"Morning": "meal detail", "Afternoon": "meal detail", "Night": "meal detail"}, '
            '"Thursday": {"Morning": "meal detail", "Afternoon": "meal detail", "Night": "meal detail"}, '
            '"Friday": {"Morning": "meal detail", "Afternoon": "meal detail", "Night": "meal detail"}, '
            '"Saturday": {"Morning": "meal detail", "Afternoon": "meal detail", "Night": "meal detail"}, '
            '"Sunday": {"Morning": "meal detail", "Afternoon": "meal detail", "Night": "meal detail"}} '
            "Do not write any introductory or concluding text. Do not wrap in markdown tags. Output raw JSON only."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        raw_text = response.text.strip()
        
        if "```" in raw_text:
            raw_text_parts = raw_text.split("```")
            for part in raw_text_parts:
                clean_part = part.strip()
                if clean_part.startswith("json"):
                    clean_part = clean_part[4:].strip()
                if clean_part.startswith("{") and clean_part.endswith("}"):
                    raw_text = clean_part
                    break

        meal_plan_json = json.loads(raw_text)
        
        return jsonify({
            "category": category,
            "meal_plan": meal_plan_json
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed compiling dashboard graphics: {str(e)}"}), 200

if __name__ == '__main__':
    app.run(debug=True)
