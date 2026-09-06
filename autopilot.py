import os
import json
import requests
import google.generativeai as genai

# --- API KEYS & ENV VARIABLES ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# --- CONFIGURE GEMINI ---
genai.configure(api_key=GEMINI_API_KEY)

# UPDATED GEMINI MODEL TO PREVENT 404 ERROR
model = genai.GenerativeModel("gemini-1.5-flash")

location = "Bora Bora, French Polynesia"
print(f"--- Running Autopilot for Location: {location} ---")

# 1. Fetch Image from Pexels
print("[*] Fetching HD image from Pexels...")
headers = {"Authorization": PEXELS_API_KEY}
pexels_url = f"https://api.pexels.com/v1/search?query={location}&per_page=1"
pexels_res = requests.get(pexels_url, headers=headers).json()

if pexels_res.get("photos"):
    image_url = pexels_res["photos"][0]["src"]["large"]
else:
    image_url = "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg"

# 2. Generate Content with Gemini
print("[*] Generating AI travel guide content using Gemini...")
prompt = f"Write a catchy Pinterest title and a short compelling travel snippet (under 500 characters) for {location}. Format as JSON with keys 'title' and 'description'."

try:
    response = model.generate_content(prompt)
    # Clean output if wrapped in markdown
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean_text)
    title = data.get("title", f"Explore {location}")
    description = data.get("description", f"Discover the beauty of {location}.")
except Exception as e:
    print(f"[-] Gemini Error: {e}")
    title = f"Visit {location} - Ultimate Travel Guide"
    description = f"Plan your dream luxury getaway to {location} with our exclusive travel insights."

landing_page_link = f"https://pulsetrips.com/destinations/{location.lower().replace(', ', '-').replace(' ', '-')}.html"

# 3. Send Payload to Make.com Webhook
print("[*] Sending Pin data to Make.com Webhook...")
if not WEBHOOK_URL:
    print("[-] Error: WEBHOOK_URL environment variable is missing!")
else:
    payload = {
        "image_url": image_url,
        "title": title,
        "description": description,
        "link": landing_page_link
    }
    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 200:
        print("[+] Successfully sent data payload to Make.com Webhook!")
    else:
        print(f"[-] Webhook Failed with status code: {res.status_code}")

print("[+] Autopilot Workflow Completed Successfully!")
