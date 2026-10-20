import json
import os
import time
from google import genai
from google.genai.errors import ServerError
from supabase import create_client

# ==========================================
# 1. CREDENTIALS CONFIGURATION
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY)
db_client = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_and_filter_competitions():
  print("🤖 Starting the automated search and AI filtering process...")

  # ==========================================
  # 2. STRICT PROMPT FOR THE AI
  # ==========================================
  prompt = """
    Search and provide information regarding the latest academic competitions, hackathons, 
    or events currently open or opening soon in Saudi Arabia specifically for active 
    Undergraduate students in Computer Science, Science, or Engineering faculties.
    
    Mandatory Criteria:
    1. Target Audience: Undergraduate students.
    2. Field: Computer Science, Science, or Engineering.
    3. Location: Saudi Arabia (either on-site at Saudi universities or online open to students there).
    
    Provide the output in a pure JSON format as an array of objects. 
    Each object MUST have keys matching these exact names:
    - "title" (string)
    - "organizer" (string)
    - "target_audience" (string)
    - "important_dates" (string)
    - "registration_link" (string)
    - "summary" (string)
    - "location" (string)
    
    Ensure the output contains ONLY pure JSON text without any markdown formatting or extra characters.
    """

  # ==========================================
  # 3. AI CALL WITH AUTOMATIC RETRY (Handles 503)
  # ==========================================
  response = None
  max_retries = 3
  for attempt in range(max_retries):
    try:
      print(f"🤖 Calling Gemini AI (Attempt {attempt + 1}/{max_retries})...")
      response = ai_client.models.generate_content(
          model="gemini-3.8-flash", contents=prompt
      )
      break  # Success! Exit loop
    except ServerError as e:
      if "503" in str(e) and attempt < max_retries - 1:
        print(
            "⚠️ Model experiencing high demand (503). Retrying in 10 seconds..."
        )
        time.sleep(10)
      else:
        raise e

  # Clean the AI text response to ensure it's pure JSON
  raw_text = response.text.strip()
  if raw_text.startswith("```json"):
    raw_text = raw_text[7:-3].strip()

  try:
    competitions_data = json.loads(raw_text)
    print(f"✅ AI successfully filtered {len(competitions_data)} competitions.")
  except json.JSONDecodeError:
    print("❌ Failed to parse JSON from AI response. Raw text:")
    print(raw_text)
    return

  # ==========================================
  # 4. SAVE DATA TO SUPABASE DATABASE
  # ==========================================
  for item in competitions_data:
    response_db = db_client.table("competitions").insert(item).execute()
    print(f"💾 Saved to database: {item.get('title')}")


if __name__ == "__main__":
  fetch_and_filter_competitions()