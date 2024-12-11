from g4f.client import Client
def answer(text = str(), prompt = str()):
    client = Client()
    prompt = f"{prompt}. С введённым текстом после \":\" ты и должен работать:"
    response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": f"{prompt}: {text}"}])
    return response.choices[0].message.content