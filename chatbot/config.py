import os


FAQ_FILE_PATH = os.getenv("FAQ_FILE_PATH", "faq.txt")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("CHATBOT_TOP_K", "3"))
MAX_CONTEXT_CHARS = int(os.getenv("CHATBOT_MAX_CONTEXT_CHARS", "1500"))
HYBRID_WEIGHT_KEYWORD = float(os.getenv("CHATBOT_WEIGHT_KEYWORD", "0.6"))

# Optional external backends
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
