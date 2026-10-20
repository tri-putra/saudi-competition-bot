import json
import os
from google import genai
from supabase import create_client

# ==========================================
# 1. CREDENTIALS CONFIGURATION
# ==========================================
# Retrieve credentials from Environment Variables for security
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Using the Secret Key

# Initialize Gemini and Supabase clients
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

    # Call the Gemini model (using gemini-2.5-flash for speed and efficiency)
    response = ai_client.models.generate_content(
        model="gemini-3.8-flash", contents=prompt
    )

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
    # 3. SAVE DATA TO SUPABASE DATABASE
    # ==========================================
    for item in competitions_data:
        # Insert data into the 'competitions' table we created
        response_db = db_client.table("competitions").insert(item).execute()
        print(f"💾 Saved to database: {item.get('title')}")

if __name__ == "__main__":
    fetch_and_filter_competitions()