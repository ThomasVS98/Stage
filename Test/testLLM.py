from llama_index.llms.ollama import Ollama

llm = Ollama(model="llama3.2:3b",
             request_timeout=120,
             context_window=4096)

response = llm.complete("Leg in 1 zin uit wat Kaltura is?")
print("Response received:")
print(response.text)