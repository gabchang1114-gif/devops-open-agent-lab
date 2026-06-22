①  User ─·─·─► React ─·─·─► FastAPI Auth ─·─·─► JWT (SQLite / PostgreSQL)

②  User selects AWS Account + Region ─·─·─► Python Backend

③  Python ─·─·─► boto3 / AWS APIs ─·─·─► Fetches AWS resources

④  Python ─·─·─► FastAPI Progress API ─·─·─► React (progress updates)

⑤  Python ─·─·─► OpenAI / Anthropic / Ollama / OpenRouter ─·─·─► Cost analysis

⑥  Python ─·─·─► SQLite / PostgreSQL ─·─·─► Stores analysis history

⑦  React ◄·─·─·─ Final cost report with savings, suggestions & fixes