import requests

def query_ollama_mistral(prompt: str, base_url: str = "http://backend-llm:11434"):
    """Send a prompt to the ollama/mistral model and return the response text."""
    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        },
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    print(f"Response from Ollama: {data}")  # Debugging line to see the response structure
    return data.get("response", "")

#
# Response from Ollama: {'model': 'mistral', 'created_at': '2025-07-09T01:40:50.111488497Z', 'response': " Hello! How can I help you today?\n\nIf you have any questions or need assistance with something, feel free to ask. I'm here to help! If you just want to chat or share some thoughts, we can do that too. Let me know what you'd like to talk about. :)", 'done': True, 'done_reason': 'stop', 'context': [3, 29473, 12782, 4, 29473, 23325, 29576, 2370, 1309, 1083, 2084, 1136, 3922, 29572, 781, 781, 4149, 1136, 1274, 1475, 4992, 1210, 1695, 12379, 1163, 2313, 29493, 2369, 2701, 1066, 2228, 29491, 1083, 29510, 29487, 2004, 1066, 2084, 29576, 1815, 1136, 1544, 1715, 1066, 11474, 1210, 4866, 1509, 8171, 29493, 1246, 1309, 1279, 1137, 2136, 29491, 3937, 1296, 1641, 1535, 1136, 29510, 29483, 1505, 1066, 2753, 1452, 29491, 15876], 'total_duration': 5738611868, 'load_duration': 1137774303, 'prompt_eval_count': 5, 'prompt_eval_duration': 156982143, 'eval_count': 65, 'eval_duration': 4443280613}