# GoogleFitBuddy

AI Fitness Plan Generator — Flask backend + Gemini API, per the original project guide.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a Gemini API key from https://aistudio.google.com/apikey and set it as an
   environment variable:
   ```
   export GEMINI_API_KEY="your-key-here"      # macOS/Linux
   setx GEMINI_API_KEY "your-key-here"        # Windows
   ```

3. Run the app:
   ```
   python app.py
   ```

4. Open http://127.0.0.1:5000 in your browser.

## How it works

- `templates/index.html` — the input form (goal, experience, equipment, diet).
- `static/style.css` / `static/script.js` — styling and the frontend logic that
  calls the backend and renders the returned plan.
- `app.py` — Flask backend. Builds a prompt from the submitted form data, sends
  it to Gemini (`gemini-1.5-flash`), and returns the parsed JSON plan to the
  frontend at `POST /api/generate-plan`.

## Notes

- This is a general fitness/wellness planning tool, not a medical diagnosis
  system — AI-generated suggestions shouldn't be treated as professional
  medical advice.
- If Gemini occasionally wraps its JSON reply in Markdown code fences,
  `app.py` strips those automatically before parsing.
- To swap in a different Gemini model, change `MODEL_NAME` in `app.py`.
