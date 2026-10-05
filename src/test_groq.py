from src.groq_client import ask_groq


prompt = """
Explain MCP (Model Context Protocol) in simple terms
for a beginner who knows Python.
"""


print("Sending request to Groq...")
print()

response = ask_groq(prompt)

print("GROQ RESPONSE")
print("=" * 60)
print(response)