from openai import OpenAI

client = OpenAI(base_url="http://localhost:4891/v1",api_key="None")
 
 
model = "/models/DeepSeek-R1-Distill-Qwen-14B"
 
completion = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "user", "content": "escrive un poema de 10 palabras "},
    ],
    max_tokens = 2000,
    temperature=0.1,
)
print(completion.choices[0].message.content)
