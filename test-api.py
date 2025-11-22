from openai import OpenAI

client = OpenAI(api_key="sk-ijklmnopqrstuvwxijklmnopqrstuvwxijklmnop")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Hello, testing API connection."}
        ]
    )
    print(response.choices[0].message["content"])
except Exception as e:
    print("API call failed:")
    print(e)
