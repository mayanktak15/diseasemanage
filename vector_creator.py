import os
import sys
import warnings

# Suppress all warnings before any other imports
warnings.filterwarnings('ignore')
os.environ['PYTHONWARNINGS'] = 'ignore'

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    IMPORTS_SUCCESSFUL = True
except Exception as e:
    print(f"Warning: Could not import vector creator dependencies: {e}")
    IMPORTS_SUCCESSFUL = False
    # Create dummy classes to prevent further errors
    class HuggingFaceEmbeddings:
        pass
    class FAISS:
        pass
    class RecursiveCharacterTextSplitter:
        pass


def preprocess_faq_data(file_path, chunk_size=200, chunk_overlap=50):
    if not IMPORTS_SUCCESSFUL:
        raise RuntimeError("Vector creator dependencies not available")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        faq_text = file.read()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return text_splitter.split_text(faq_text)


def get_vector_store(faq_file_path, index_path="faiss_index"):
    if not IMPORTS_SUCCESSFUL:
        raise RuntimeError("Vector creator dependencies not available")
    
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}
    )

    if not os.path.exists(index_path):
        faq_chunks = preprocess_faq_data(faq_file_path)
        vector_store = FAISS.from_texts(faq_chunks, embedding_model)
        vector_store.save_local(index_path)
    else:
        vector_store = FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)

    return vector_store
