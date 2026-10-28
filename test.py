import importlib
import os

from dotenv import load_dotenv

load_dotenv()

try:
    Groq = importlib.import_module("groq").Groq
except ImportError:
    Groq = None

if Groq is None:
    raise ImportError("The 'groq' package is not installed. Run: pip install groq")

api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    raise EnvironmentError('GROQ_API_KEY is missing. Add it to .env before running this test.')

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model=os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b'),
    messages=[
        {"role": "system", "content": "Return only valid JSON."},
        {"role": "user", "content": "Create a day-wise 2-day Mumbai itinerary as JSON with itinerary: [{day, activities: [{time, name, duration, cost, description}]}]. Include exactly days 1 and 2."}
    ],
    response_format={"type": "json_object"},
    temperature=0.4
)

print(response.choices[0].message.content)
