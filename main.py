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
    models_to_try = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]
    response = None
    success = False

    for model_name in models_to_try:
      if success:
        break
      max_retries = 3
      for attempt in range(max_retries):
        try:
          print(
              f"🤖 Calling Gemini AI using {model_name} (Attempt {attempt + 1}"
              f"/{max_retries})..."
          )
          response = ai_client.models.generate_content(
              model=model_name, contents=prompt
          )
          success = True
          break  # Success! Exit retry loop
        except ServerError as e:
          if "503" in str(e) and attempt < max_retries - 1:
            wait_time = (attempt + 1) * 15  # 15s, then 30s wait
            print(
                f"⚠️ Model {model_name} busy (503). Retrying in {wait_time}"
                " seconds..."
            )
            time.sleep(wait_time)
          else:
            print(f"⚠️ Model {model_name} failed. Trying next available model...")
            break

    if not response:
      raise Exception(
          "❌ All backup Gemini models are currently experiencing high demand"
          " (503). Please try again later."
      )

  # ==========================================
  # 4. SAVE DATA TO SUPABASE DATABASE
  # ==========================================
  for item in competitions_data:
    response_db = db_client.table("competitions").insert(item).execute()
    print(f"💾 Saved to database: {item.get('title')}")


if __name__ == "__main__":
  fetch_and_filter_competitions()