import os
import json
import requests
import google.generativeai as genai

# --- 1. ENVIRONMENT VARIABLES ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

location = "Bora Bora, French Polynesia"
print(f"--- Running Autopilot for Location: {location} ---")

# --- 2. FETCH HD IMAGE FROM PEXELS ---
print("[*] Fetching HD image from Pexels...")
headers = {"Authorization": PEXELS_API_KEY}
pexels_url = f"https://api.pexels.com/v1/search?query={location}&per_page=1"

try:
    pexels_res = requests.get(pexels_url, headers=headers).json()
    if pexels_res.get("photos"):
        image_url = pexels_res["photos"][0]["src"]["large"]
    else:
        image_url = "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg"
except Exception as e:
    print(f"[-] Pexels Error: {e}")
    image_url = "https://images.pexels.com/photos/258154/pexels-photo-258154.jpeg"

# --- 3. GENERATE TRAVEL CONTENT WITH GEMINI AI ---
print("[*] Generating AI travel guide content using Gemini...")
prompt = f"Write a catchy Pinterest title and a compelling travel snippet (under 500 characters) for {location}. Format as raw JSON with keys 'title' and 'description'."

try:
    response = model.generate_content(prompt)
    clean_text = response.text.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean_text)
    title = data.get("title", f"Explore {location}")
    description = data.get("description", f"Discover the beauty of {location}.")
except Exception as e:
    print(f"[-] Gemini Error: {e}")
    title = f"Visit {location} - Ultimate Travel Guide"
    description = f"Plan your dream luxury getaway to {location} with our exclusive travel insights."

# --- 4. GENERATE FULL HTML LANDING PAGE ---
print("[*] Creating landing page for GitHub Pages...")
slug = location.lower().replace(', ', '-').replace(' ', '-')
os.makedirs("destinations", exist_ok=True)
page_path = f"destinations/{slug}.html"

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | PulseTrips</title>
    <style>
        body {{ font-family: 'Arial', sans-serif; margin: 0; padding: 0; background-color: #f4f4f9; color: #333; }}
        header {{ background: #ff4757; color: white; text-align: center; padding: 2rem 1rem; }}
        .container {{ max-width: 800px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
        img {{ width: 100%; height: 400px; object-fit: cover; border-radius: 8px; }}
        h1 {{ margin-top: 1rem; color: #2c3e50; }}
        p {{ line-height: 1.6; font-size: 1.1rem; }}
        .btn {{ display: inline-block; background: #ff4757; color: white; padding: 12px 24px; border-radius: 5px; text-decoration: none; font-weight: bold; margin-top: 1rem; }}
        .btn:hover {{ background: #e04040; }}
    </style>
</head>
<body>
    <header>
        <h1>PulseTrips Luxury Destinations</h1>
    </header>
    <div class="container">
        <img src="{image_url}" alt="{title}">
        <h1>{title}</h1>
        <p>{description}</p>
        <a href="https://pulsetrips.com" class="btn">Explore More Destinations</a>
    </div>
</body>
</html>
"""

with open(page_path, "w", encoding="utf-8") as f:
    f.write(html_content)

landing_page_link = f"https://pulsetrips.com/{page_path}"
print(f"[+] Page successfully created/updated: {landing_page_link}")

# --- 5. SEND PAYLOAD TO MAKE.COM WEBHOOK ---
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
    try:
        res = requests.post(WEBHOOK_URL, json=payload)
        if res.status_code == 200:
            print("[+] Successfully sent data payload to Make.com Webhook!")
        else:
            print(f"[-] Webhook Failed with status code: {res.status_code}")
    except Exception as e:
        print(f"[-] Webhook Request Error: {e}")

print("[+] Autopilot Workflow Completed Successfully!")
