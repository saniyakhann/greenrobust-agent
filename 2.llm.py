import ollama

def call_llm(prompt):
    response = ollama.chat(
        model='qwen2.5:14b',
        messages=[{'role': 'user', 'content': prompt}]
    )
    return response['message']['content']
