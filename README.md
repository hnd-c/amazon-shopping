# Amazon Shopping Assistant

A LangGraph-based agent for querying Amazon product information using natural language.


## Quick Start

1. Set up environment variables. It is setup to work with Anthropic, make changes in config.template.json and configuration.py to make it work with other LLMs:
   ```bash
   # Copy example env file
   cp .env.example .env

   # Edit .env with your API keys
   LANGSMITH_TRACING=true
   LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
   LANGSMITH_API_KEY="your_langsmith_key"
   LANGSMITH_PROJECT="your_project_name"

   ANTHROPIC_API_KEY="your_anthropic_key"
   OPENAI_API_KEY="your_openai_key"

   ```

## Development

2. create venv
```bash
python -m venv venv
source venv/bin/activate
```

3. install dependencies
```bash
make setup
```

4. run the agent in langsmith studio

```bash
langgraph dev
```

5. Should see the agent running in langsmith studio or access the agent:
   - Open [LangSmith Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123)
   - Or follow the [LangChain Academy setup guide](https://github.com/langchain-ai/langchain-academy/blob/main/module-6/connecting.ipynb)

6. input format in json
```
{
  "messages": [
    {
      "content": "Find me a toothpaste under 20$",
      "type": "human"
    }
  ]
}
```