# bot.py
import os
import sys
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import ExtendedRequestOptions

# This forces the script to use a specific IP for Hugging Face, bypassing GitHub's broken DNS entirely
class DirectIPAdapter(HTTPAdapter):
    def __init__(self, ip_address, **kwargs):
        self.ip_address = ip_address
        super().__init__(**kwargs)
    def get_connection(self, url, proxies=None):
        # Direct connection routing override
        return super().get_connection(url.replace("api-inference.huggingface.co", self.ip_address), proxies=proxies)

def main():
    github_token = os.getenv("GITHUB_TOKEN")
    hf_token = os.getenv("HF_TOKEN")
    event_path = os.getenv("GITHUB_EVENT_PATH")
    
    # We use Hugging Face's direct cloud edge IP address 
    HF_IP = "18.232.128.21" 
    HF_API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-1.5B-Instruct"
    
    if not event_path:
        print("❌ Error: Missing GITHUB_EVENT_PATH execution context.")
        sys.exit(1)
        
    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)
        
    issue_text = event_data["comment"]["body"] if "comment" in event_data else event_data["issue"]["body"]
    comments_url = event_data["issue"]["comments_url"]
    
    if "/create-mod" not in issue_text:
        print("ℹ️ Trigger keyword '/create-mod' not found. Skipping.")
        sys.exit(0)
        
    clean_user_prompt = issue_text.replace("/create-mod", "").strip()
    print(f"🎯 Cleaned user prompt text: {clean_user_prompt}")
    
    payload = {
        "inputs": f"<|im_start|>system\nYou are an expert BepInEx modding assistant. Write clean C# code using HarmonyX patches.<|im_end|>\n<|im_start|>user\n{clean_user_prompt}<|im_end|>\n<|im_start|>assistant\n",
        "parameters": {"max_new_tokens": 1024, "temperature": 0.2, "return_full_text": False}
    }
    
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
        "Host": "api-inference.huggingface.co" # Vital so HF knows which server we want at that IP
    }
    
    # Set up the custom networking session
    session = requests.Session()
    session.mount("https://", DirectIPAdapter(HF_IP))
    
    print(f"🧠 Sending payload directly to Hugging Face IP ({HF_IP})...")
    response = session.post(HF_API_URL, json=payload, headers=headers, verify=False) # skip SSL hostname check for direct IP mapping
    
    if response.status_code != 200:
        print(f"❌ API Error Code: {response.status_code} - Description: {response.text}")
        ai_response = "⚠️ Server error encountered during direct IP generation."
    else:
        raw_result = response.json()
        if isinstance(raw_result, list) and len(raw_result) > 0:
            ai_response = raw_result[0].get("generated_text", "").strip()
        else:
            ai_response = str(raw_result).strip()
        ai_response = ai_response.split("<|im_end|>")[0].strip()

    github_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    comment_payload = {
        "body": f"🤖 **Automated BepInEx C# Generation Engine:**\n\n```csharp\n{ai_response}\n```"
    }
    
    print("✍️ Posting final code output response block back to GitHub...")
    post_res = requests.post(comments_url, json=comment_payload, headers=github_headers)
    print(f"📡 GitHub Response Status: {post_res.status_code}")

if __name__ == "__main__":
    main()