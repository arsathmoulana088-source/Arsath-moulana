"""
GoogleFitBuddy — Flask backend
Receives fitness details from the frontend, builds a prompt, sends it to
Gemini, and returns a structured JSON fitness plan.

Setup:
    1. pip install -r requirements.txt
    2. Set your Gemini API key as an environment variable:
         export GEMINI_API_KEY="your-key-here"      (macOS/Linux)
         setx GEMINI_API_KEY "your-key-here"         (Windows)
    3. python app.py
    4. Open http://127.0.0.1:5000
"""

import json
import os
import re

from flask import Flask, jsonify, render_template, request
import google.generativeai as genai

app = Flask(__name__)

API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

MODEL_NAME = "gemini-1.5-flash"

PLAN_SCHEMA_EXAMPLE = """{
  "user_summary": {
    "recommended_daily_calories": 2200,
    "target_protein_g": 160,
    "target_carbs_g": 200,
    "target_fats_g": 65
  },
  "weekly_schedule": [
    {
      "day": "Day 1",
      "focus": "Full Body Strength",
      "workout": {
        "warmup": ["5 mins Jumping Jacks", "Arm Circles"],
        "exercises": [
          {
            "name": "Goblet Squats",
            "sets": 3,
            "reps": "10-12",
            "rest_seconds": 60,
            "notes": "Keep chest upright and core engaged."
          }
        ],
        "cooldown": ["Hamstring Stretch", "Child's Pose"]
      },
      "meals": {
        "breakfast": "Vegetable poha topped with roasted peanuts and a glass of curd",
        "lunch": "2 roti with moong dal, paneer bhurji, and cucumber-tomato salad",
        "dinner": "Grilled tandoori chicken (or paneer tikka) with jeera rice and sauteed lauki",
        "snack": "Roasted chana with a cup of curd"
      }
    }
  ],
  "grocery_list": {
    "proteins": ["Paneer", "Moong Dal", "Chana", "Curd/Dahi", "Eggs or Chicken"],
    "carbs_and_grains": ["Roti/Atta", "Rice", "Poha", "Oats"],
    "produce": ["Lauki", "Spinach", "Tomato", "Cucumber"],
    "pantry": ["Peanuts", "Roasted Chana", "Ghee", "Spices"]
  }
}"""


def build_prompt(goal, level, equipment, diet):
    return f"""Generate a full 7-day (Monday through Sunday) workout and meal plan for a user whose goal is {goal}.

User Profile:
- Level: {level}
- Equipment: {equipment}
- Diet: {diet}

Return ONLY a valid JSON object matching exactly this structure (same keys, same nesting),
with exactly 7 entries in weekly_schedule (one per day of the week), and no extra commentary
or Markdown formatting:

{PLAN_SCHEMA_EXAMPLE}

Requirements:
- Meals must reflect everyday Indian food culture and regional variety across the week
  (e.g. dal, roti/chapati, sabzi, paneer, curd/dahi, idli, dosa, poha, upma, chana, rajma,
  sprouts, besan chilla, khichdi). Lean on Indian protein sources: paneer, dal/lentils, curd,
  chana, rajma, eggs, chicken or fish (if not vegetarian/vegan), soya chunks or tofu for
  vegan/plant-based needs. Avoid defaulting to generic Western meals (no "grilled chicken
  breast with quinoa" style plans) unless the diet preference specifically calls for it.
- Every exercise must have a specific numeric sets value, a specific reps value (a number or
  a tight range like "12-15", never vague placeholders), and a specific rest_seconds value —
  fill in real, appropriate numbers for every single exercise, not just the first one.
- Vary each day's focus across the week and include at least one full rest or active-recovery
  day.
- Tailor exercises to the stated equipment (bodyweight only if "No equipment") and scale sets,
  reps and rest to the stated experience level.
"""


def extract_json(text):
    """Gemini sometimes wraps JSON in ```json ... ``` fences — strip them if present."""
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    return json.loads(cleaned)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate-plan", methods=["POST"])
def generate_plan():
    if not API_KEY:
        return jsonify({
            "error": "GEMINI_API_KEY is not set on the server. "
                     "Set it as an environment variable and restart the app."
        }), 500

    data = request.get_json(force=True) or {}
    goal = data.get("goal", "General fitness")
    level = data.get("level", "Beginner")
    equipment = data.get("equipment", "No equipment")
    diet = data.get("diet", "No restriction")

    prompt = build_prompt(goal, level, equipment, diet)

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        plan = extract_json(response.text)
        return jsonify(plan)
    except json.JSONDecodeError:
        return jsonify({"error": "Gemini returned a response that wasn't valid JSON. Try again."}), 502
    except Exception as exc:  # noqa: BLE001 — surface any Gemini/network error to the client
        return jsonify({"error": f"Plan generation failed: {exc}"}), 502


if __name__ == "__main__":
    app.run(debug=True)
