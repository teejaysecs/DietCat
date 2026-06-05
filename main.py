import os
import platform
import subprocess
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# 1. SMART PATH DETECTION (Fixes the "app.exe not found" error on Render)
if platform.system() == "Windows":
    BINARY_PATH = os.path.join(os.path.dirname(__file__), "app.exe")
else:
    # On Render (Linux), there is no .exe extension
    BINARY_PATH = os.path.join(os.path.dirname(__file__), "app")
    # Give the Linux binary execution permissions just in case
    if os.path.exists(BINARY_PATH):
        os.chmod(BINARY_PATH, 0o755)

# 2. INITIALIZE GEMINI CLIENT
# Make sure you have added GEMINI_API_KEY to your Render Environment Variables!
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/categorize', bytes_methods=['POST'])
def categorize():
    try:
        # Check if the compiled backend file even exists
        if not os.path.exists(BINARY_PATH):
            return jsonify({"error": f"Backend binary not found at {os.path.basename(BINARY_PATH)}"}), 500

        # Get age from the frontend form
        age = request.form.get('age')
        if not age:
            return jsonify({"error": "Age is required"}), 400

        # Run your compiled C++ application as a subprocess
        process = subprocess.run(
            [BINARY_PATH, str(age)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Grab the stdout text outputted from your C++ program
        category = process.stdout.strip()
        return jsonify({"category": category})

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"C++ Backend Error: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_diet', methods=['POST'])
def generate_diet():
    if not client:
        return jsonify({"error": "Gemini API key is missing. Please set GEMINI_API_KEY in Render."}), 500

    try:
        category = request.form.get('category')
        goal = request.form.get('goal') # e.g., lose weight, build muscle
        
        prompt = f"Create a simple, healthy 1-day meal plan for a person categorized as '{category}' whose fitness goal is to '{goal}'."
        
        # Using the updated 2026 google-genai SDK layout
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return jsonify({"diet_plan": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Default local port for testing
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))