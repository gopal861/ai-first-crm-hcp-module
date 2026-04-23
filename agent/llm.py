import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def call_llm(prompt: str):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content