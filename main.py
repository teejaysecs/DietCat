import os
import platform
import subprocess
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# System Architecture Verification
if platform.system() == "Windows":
    BINARY_PATH = os.path.join(os.path.dirname(__file__), "app.exe")
else:
    BINARY_PATH = os.path.join(os.path.dirname(__file__), "app")
    if os.path.exists(BINARY_PATH):
        os.chmod(BINARY_PATH, 0o755)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/categorize', methods=['POST'])
def categorize():
    try:
        if not os.path.exists(BINARY_PATH):
            return jsonify({"error": "Backend binary engine missing"}), 500

        age = request.form.get('age')
        if not age:
            return jsonify({"error": "Age metrics required"}), 400

        process = subprocess.run(
            [BINARY_PATH, str(age)],
            capture_output=True,
            text=True,
            check=True
        )
        category = process.stdout.strip()
        
        return jsonify({
            "category": category,
            "result": category
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate_diet', methods=['POST'])
def generate_diet():
    if not client:
        return jsonify({"error": "API Authentication Key configuration error"}), 500

    try:
        name = request.form.get('name', 'User')
        age = request.form.get('age', 'Unspecified')
        goal = request.form.get('goal', 'General Health')
        
        # Pull down category inference engine locally using system fallback
        category = "Standard Profile"
        if os.path.exists(BINARY_PATH) and age.isdigit():
            res = subprocess.run([BINARY_PATH, str(age)], capture_output=True, text=True)
            if res.returncode == 0:
                category = res.stdout.strip()

        # Build prompt requiring structural markdown elements
        prompt = (
            f"Generate a brief 1-day meal plan recommendation structured with distinct breakfast, lunch, "
            f"and dinner headers for {name}, a {age}-year-old categorized as '{category}' seeking to '{goal}'."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        return jsonify({"diet_plan": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))