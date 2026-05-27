import os


FAQ_FILE_PATH = os.getenv("FAQ_FILE_PATH", "faq.txt")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("CHATBOT_TOP_K", "3"))
MAX_CONTEXT_CHARS = int(os.getenv("CHATBOT_MAX_CONTEXT_CHARS", "1500"))
HYBRID_WEIGHT_KEYWORD = float(os.getenv("CHATBOT_WEIGHT_KEYWORD", "0.6"))
