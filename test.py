import os

print("🔥 SUCCESS! Your developer station is officially live.")
print(f"Your project is running at: {os.getcwd()}")

# Create your blank dataset file automatically so it's ready for Claude
if not os.path.exists("dataset.jsonl"):
    with open("dataset.jsonl", "w") as f:
        f.write('{"prompt": "Test data", "completion": "Test code"}\n')
    print("📁 Created a fresh 'dataset.jsonl' file in your folder!")