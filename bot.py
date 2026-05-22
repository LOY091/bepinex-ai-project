# bot.py
import os
import sys
import json
import requests

def main():
    # 1. Grab environment paths and tokens from the GitHub Action runner environment
    github_token = os.getenv("GITHUB_TOKEN")
    hf_token = os.getenv("HF_TOKEN")
    event_path = os.getenv("GITHUB_EVENT_PATH")
    
    # We query Hugging Face's serverless pipeline endpoint for lightning-fast free execution
    HF_API_URL = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-1.5B-Instruct"
    
    if not event_path:
        print("❌ Error: Missing GITHUB_EVENT_PATH execution context.")
        sys.exit(1)
        
    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)
        
    # Extract the comment body context text and destination response stream URL
    issue_text = event_data["issue"]["body"]
    comments_url = event_data["issue"]["comments_url"]
    
    # Stop processing if the issue doesn't contain our custom trigger word
    if "/create-mod" not in issue_text:
        print("ℹ️ Trigger keyword '/create-mod' not found in issue text. Skipping.")
        sys.exit(0)
        
    # Strip the trigger keyword away to isolate the prompt text
    clean_user_prompt = issue_text.replace("/create-mod", "").strip()
    print(f"🎯 Cleaned user prompt text: {clean_user_prompt}")
    
    # 2. Package the request using ChatML structure formatting
    payload = {
        "inputs": f"<|im_start|>system\nYou are an expert BepInEx modding assistant. Write clean C# code using HarmonyX patches.<|im_end|>\n<|im_start|>user\n{clean_user_prompt}<|im_end|>\n<|im_start|>assistant\n",
        "parameters": {
            "max_new_tokens": 1024, 
            "temperature": 0.2,
            "return_full_text": False
        }
    }
    
    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json"
    }
    
    print("🧠 Sending prompt payload to Hugging Face serverless client...")
    response = requests.post(HF_API_URL, json=payload, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ HF API Error Code: {response.status_code} - Description: {response.text}")
        ai_response = "⚠️ Server error encountered while executing Hugging Face Inference generation."
    else:
        raw_result = response.json()
        # Parse the text response block safely
        if isinstance(raw_result, list) and len(raw_result) > 0:
            ai_response = raw_result[0].get("generated_text", "").strip()
        else:
            ai_response = str(raw_result).strip()

        # Clean text artifacts if they leak out past the stop tokens
        ai_response = ai_response.split("<|im_end|>")[0].strip()

    # 3. Deliver the code response back to the GitHub Issue thread
    github_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    comment_payload = {
        "body": f"🤖 **Automated BepInEx C# Generation Engine:**\n\n```csharp\n{ai_response}\n```"
    }
    
    print("✍️ Posting final code output response block back to GitHub issue stream...")
    post_res = requests.post(comments_url, json=comment_payload, headers=github_headers)
    print(f"📡 GitHub Response Status: {post_res.status_code}")

if __name__ == "__main__":
    main()