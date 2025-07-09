

curl http://localhost:11434/v1/completions   -H "Content-Type: application/json"   -d '{ \
        "model": "mistral", \
        "prompt": "Say hello in French.", \
        "max_tokens": 50 \
      }'
