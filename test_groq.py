from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

try:
    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Say hello"}],
    )
    print("✅ VALID KEY")
    print(res.choices[0].message.content)

except Exception as e:
    print("❌ INVALID KEY")
    print(e)