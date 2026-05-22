# bot.py
import os
import sys
import json
import requests

def main():
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    event_path = os.getenv("GITHUB_EVENT_PATH")
    
    # Secure Google API endpoint for Gemini 1.5 Flash
    GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
    
    if not event_path:
        print("❌ Error: Missing GITHUB_EVENT_PATH execution context.")
        sys.exit(1)
        
    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)
        
    # Safely get text from either a brand new issue or a comment thread
    if "comment" in event_data:
        issue_text = event_data["comment"]["body"]
    else:
        issue_text = event_data["issue"]["body"]
        
    comments_url = event_data["issue"]["comments_url"]
    
    if "/create-mod" not in issue_text:
        print("ℹ️ Trigger keyword '/create-mod' not found. Skipping.")
        sys.exit(0)
        
    clean_user_prompt = issue_text.replace("/create-mod", "").strip()
    print(f"🎯 Cleaned user prompt text: {clean_user_prompt}")
    
    # Structuring the prompt payload for Gemini's API layout
    payload = {
        "contents": [{
            "parts": [{
                "text": f"You are an expert BepInEx modding assistant. Write clean, complete C# code using HarmonyX patches for Unity based on this prompt:\n\n{clean_user_prompt}\n\nReturn ONLY the raw C# code inside a markdown block. Do not write introductory text."
            }]
        }]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🧠 Sending payload to Google Gemini Engine...")
    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ API Error Code: {response.status_code} - Description: {response.text}")
        ai_response = "⚠️ Server error encountered during Gemini generation execution."
    else:
        raw_result = response.json()
        try:
            # Fixed the IndexError parsing block typo here!
            ai_response = raw_result['candidates'][0]['content']['parts'][0]['text'].strip()
            
            # If Gemini adds code block wraps itself, strip them so we don't double-wrap down below
            if ai_response.startswith("```csharp"):
                ai_response = ai_response.replace("```csharp", "").replace("```", "").strip()
            elif ai_response.startswith("```"):
                ai_response = ai_response.replace("```", "").strip()
        except (KeyError, IndexError):
            ai_response = "⚠️ Failed to cleanly parse response blocks from Gemini API engine."

    github_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    comment_payload = {
        "body": f"🤖 **Automated BepInEx C# Generation Engine (Gemini Powered):**\n\n```csharp\n{ai_response}\n```"
    }
    
    print("✍️ Posting final code output response block back to GitHub issue stream...")
    post_res = requests.post(comments_url, json=comment_payload, headers=github_headers)
    print(f"📡 GitHub Response Status: {post_res.status_code}")

if __name__ == "__main__":
    main()