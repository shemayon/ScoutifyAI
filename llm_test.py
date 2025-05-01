#litellm test

from litellm import completion

response = completion(
    model="openai/gpt-4o-mini",
    messages = [{
        "content":"Where is petronas twin tower located?",
        "role":"user"
    }],
    temperature = 0.5
)

print(response.choices[0].message.content)