# Chemical Database Agent

A LangGraph-based agent for querying chemical product information using natural language.

## Prerequisites
- Docker and Docker Compose
- Python 3.8+
- Git

## Quick Start

1. Set up environment variables:
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

   SUPABASE_URL="your_supabase_url"
   SUPABASE_KEY="your_supabase_key"
   ```

2. Build the LangGraph image:
   ```bash
   langgraph build -t my-image
   ```

3. Start the services:
   ```bash
   docker compose up
   ```

4. Access the agent:
   - Open [LangSmith Studio](https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123)
   - Or follow the [LangChain Academy setup guide](https://github.com/langchain-ai/langchain-academy/blob/main/module-6/connecting.ipynb)

## Development

create venv
```bash
python -m venv venv
source venv/bin/activate
```

install dependencies
```bash
pip install -e .
```

run the agent in langsmith studio

```bash
langgraph dev
```

input format in json
```
{
  "messages": [
    {
      "content": "What companies sell nail polish?",
      "type": "human"
    }
  ]
}
```

"python -m playwright install" add it during docker compose //note to self