import os
import random
import requests
import json
import base64
from google import genai

# ---------------------------------------------------------
# 1. READ SECRETS SAFELY FROM ENVIRONMENT VARIABLES
# ---------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
GITHUB_TOKEN = os.getenv("GH_TOKEN")
GITHUB_REPO = "ashrafsattar423-glitch/pulsetrips"

# Target locations list for content generation
TARGET_LOCATIONS = [
    "Kyoto, Japan", "Santorini, Greece", "Maui, Hawaii", 
    "Reykjavik, Iceland", "Banff, Canada", "Amalfi Coast, Italy", 
    "Queenstown, New Zealand", "Swiss Alps, Switzerland", 
    "Cape Town, South Africa", "Bora Bora, French Polynesia"
]

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------
def get_pexels_image(query):
    if not PEXELS_API_KEY:
        return "https://images.pexels.com/photos/346885/pexels-photo-346885.jpeg"
        
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200 and res.json().get('photos'):
            return res.json()['photos'][0]['src']['large']
    except Exception as e:
        print(f"[-] Pexels Fetch Error: {e}")
        
    return "https://images.pexels.com/photos/346885/pexels-photo-346885.jpeg"

def generate_gemini_content(location):
    if not GEMINI_API_KEY:
        return f"Explore top attractions, best times to visit, and insider travel tips for {location}."
        
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
        Write a brief Pinterest description for '{location}' (under 500 characters).
        Highlight top places to visit and best time to travel. Keep it engaging.
        """
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        # Ensure description is strictly under 800 characters for Pinterest limits
        return response.text[:750]
    except Exception as e:
        print(f"[-] Gemini API Error: {e}")
        return f"Discover the best travel guides, itinerary tips, and places to explore in {location}."

def generate_landing_page_html(location, content):
    formatted_content = content.replace('\n', '<br>')
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Explore {location} - PulseTrips</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #0066cc; }}
        .content {{ background: #f9f9f9; padding: 20px; border-radius: 8px; border-left: 5px solid #0066cc; }}
    </style>
</head>
<body>
    <h1>Travel Guide: {location}</h1>
    <div class="content">
        {formatted_content}
    </div>
</body>
</html>"""
    return html_template

def push_to_github(location, html_content):
    if not GITHUB_TOKEN:
        print("[-] GH_TOKEN missing, skipping HTML push.")
        return f"https://pulsetrips.com/destinations/{location.lower().replace(' ', '-').replace(',', '')}.html"

    filename = f"destinations/{location.lower().replace(' ', '-').replace(',', '')}.html"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        get_res = requests.get(url, headers=headers, timeout=15)
        sha = get_res.json().get('sha') if get_res.status_code == 200 else None

        encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        
        payload = {
            "message": f"Add/Update landing page for {location}",
            "content": encoded_content
        }
        if sha:
            payload["sha"] = sha

        put_res = requests.put(url, headers=headers, json=payload, timeout=15)
        if put_res.status_code in [200, 201]:
            clean_filename = filename.replace("destinations/", "")
            page_url = f"https://pulsetrips.com/destinations/{clean_filename}"
            print(f"[+] Page successfully created/updated: {page_url}")
            return page_url
        else:
            print(f"[-] GitHub API Error: {put_res.status_code} - {put_res.text}")
    except Exception as e:
        print(f"[-] Push to GitHub Exception: {e}")

    return f"https://pulsetrips.com/destinations/{location.lower().replace(' ', '-').replace(',', '')}.html"

def send_to_make_webhook(landing_url, image_url, title, description):
    if not WEBHOOK_URL:
        print("[-] Error: WEBHOOK_URL environment variable is missing!")
        return

    payload = {
        "image_url": image_url,
        "title": title[:100],  # Pinterest title character limit safety
        "description": description[:750],  # Pinterest description limit safety
        "link": landing_url
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        res = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers, timeout=30)
        if res.status_code == 200:
            print("[+] Successfully sent data payload to Make.com Webhook!")
        else:
            print(f"[-] Make Webhook Error: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[-] Webhook Exception: {e}")

# ---------------------------------------------------------
# 3. MAIN WORKFLOW EXECUTION
# ---------------------------------------------------------
def run_autopilot_task():
    location = random.choice(TARGET_LOCATIONS)
    print(f"\n--- Running Autopilot for Location: {location} ---")
    
    print("[*] Fetching HD image from Pexels...")
    image_url = get_pexels_image(location)
    
    print("[*] Generating AI travel guide content using Gemini...")
    content = generate_gemini_content(location)
    
    print("[*] Creating landing page and pushing to GitHub Pages...")
    html_data = generate_landing_page_html(location, content)
    landing_url = push_to_github(location, html_data)
    
    print("[*] Sending Pin data to Make.com Webhook...")
    pin_title = f"Top Things to Do in {location}"
    send_to_make_webhook(landing_url, image_url, pin_title, content)
    print("[+] Autopilot Workflow Completed Successfully!")

if __name__ == "__main__":
    run_autopilot_task()
