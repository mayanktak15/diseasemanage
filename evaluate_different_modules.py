import os
import warnings

# Suppress all warnings
warnings.filterwarnings('ignore')
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ['PYTHONWARNINGS'] = 'ignore::RuntimeWarning'

# Try to import dependencies with error handling
# Temporarily disable vector_creator to avoid crashes
VECTOR_STORE_AVAILABLE = False
get_vector_store = None
print("Info: Vector store disabled to prevent import crashes")

# Temporarily disable transformers to avoid crashes
TRANSFORMERS_AVAILABLE = False
print("Info: Transformers disabled to prevent import crashes")

# Temporarily disable langchain to avoid crashes  
LANGCHAIN_AVAILABLE = False
print("Info: LangChain disabled to prevent import crashes")

# Temporarily disable torch to avoid crashes
TORCH_AVAILABLE = False
print("Info: PyTorch disabled to prevent import crashes")

# Define minimal stubs so import-time name resolution succeeds when libs are unavailable
def pipeline(*args, **kwargs):
    raise RuntimeError("transformers.pipeline is unavailable")
class AutoTokenizer:
    @staticmethod
    def from_pretrained(*args, **kwargs):
        raise RuntimeError("transformers.AutoTokenizer unavailable")
class AutoModelForSeq2SeqLM:
    @staticmethod
    def from_pretrained(*args, **kwargs):
        raise RuntimeError("transformers.AutoModelForSeq2SeqLM unavailable")

class torch:  # type: ignore
    bfloat16 = None

class HuggingFacePipeline:  # type: ignore
    def __init__(self, *args, **kwargs):
        pass

class RetrievalQA:  # type: ignore
    @classmethod
    def from_chain_type(cls, *args, **kwargs):
        return cls()
    def __call__(self, *args, **kwargs):
        return {"result": ""}

class PromptTemplate:  # type: ignore
    def __init__(self, *args, **kwargs):
        pass

class StrOutputParser:  # type: ignore
    def __call__(self, x):
        return str(x)

class PeftModel:  # type: ignore
    @staticmethod
    def from_pretrained(*args, **kwargs):
        raise RuntimeError("peft.PeftModel unavailable")

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError as e:
    print("Warning: Google Generative AI not available")
    GENAI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()  # load variables from .env file
    DOTENV_AVAILABLE = True
except ImportError as e:
    print(f"Warning: python-dotenv not available: {e}")
    DOTENV_AVAILABLE = False

# Try to get API key from multiple environment variable names
api_key = os.getenv("API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key and GENAI_AVAILABLE:
    genai.configure(api_key=api_key)
    # Masked log to avoid leaking keys
    print("Google API configured with key: ******")
else:
    print("Warning: No Google API key found or Google AI not available")


# Suppress TensorFlow and duplicate library issues

# ======== Vector Store Initialization ========
if VECTOR_STORE_AVAILABLE:
    try:
        vector_store = get_vector_store("faq.txt")
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        print("Vector store initialized successfully")
    except Exception as e:
        print(f"Error initializing vector store: {e}")
        retriever = None
else:
    print("Vector store not available, using simple FAQ responses only")
    retriever = None

# ======== Simple FAQ Response Function ========
def get_simple_faq_response(user_query):
    """Simple FAQ responses that don't require AI API"""
    query_lower = user_query.lower()
    
    if "fever" in query_lower or "temperature" in query_lower or "hot" in query_lower:
        return """I understand you have a fever. Here's some general guidance:

🌡️ **For fever management:**
- Stay hydrated with plenty of fluids
- Rest and avoid strenuous activities
- Monitor your temperature regularly
- Consider over-the-counter fever reducers if appropriate

⚠️ **When to seek medical attention:**
- Fever above 103°F (39.4°C)
- Fever lasting more than 3 days
- Severe symptoms like difficulty breathing
- Signs of dehydration

📋 **Next steps:**
Please fill out a consultation form on your dashboard with your specific symptoms so our doctors can provide proper medical advice. We cannot provide specific medical treatment through this chat."""
    
    elif "docify" in query_lower or "what is" in query_lower:
        return """Docify Online is a platform for filling out medical certificates and consultation forms, with support from our chatbot. 
        
We connect you with qualified healthcare professionals 24/7 for medical consultations from the comfort of your home."""
    
    elif "submit" in query_lower or "consultation" in query_lower or "form" in query_lower:
        return """To submit a consultation form:
1. Log in to your account
2. Go to the dashboard
3. Fill out the form with your symptoms
4. You can also update past submissions anytime"""
    
    elif "secure" in query_lower or "data" in query_lower or "privacy" in query_lower:
        return """Yes, your data is secure! We use password hashing and store data securely in our database. 
        User details are also exported to CSV files for backup purposes."""
    
    elif "support" in query_lower or "contact" in query_lower or "help" in query_lower:
        return """You can reach our support team via:
- This chatbot for immediate assistance
- Email at support@docify.online
- Through your dashboard consultation form"""
    
    elif "symptoms" in query_lower:
        return """When describing symptoms, please include:
- Detailed description of what you're experiencing
- Duration (how long you've had the symptoms)
- Severity level
- Any relevant medical history"""
    
    elif any(greeting in query_lower for greeting in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]):
        return """Hello! Welcome to Docify Online. I'm here to help you with information about our medical consultation services. 
        
What would you like to know about our platform?"""
    
    elif "fever" in query_lower:
        return """**About Fever:**
Fever is a common symptom where your body temperature rises above normal (usually above 100.4°F/38°C). It's often your body's way of fighting infection.

**General Tips:**
• Stay hydrated with water and fluids
• Rest adequately
• Monitor your temperature regularly
• Use a cool compress if needed

**When to consult a doctor:**
If fever persists for more than 2-3 days, is very high (above 103°F), or accompanied by severe symptoms, please submit a consultation form on your dashboard for professional medical advice.

Would you like to know more about any other symptoms or how to use Docify's services?"""
    
    elif any(health_term in query_lower for health_term in ["pain", "headache", "cough", "cold", "sick", "unwell"]):
        return """I can help with general information about common symptoms!

**For immediate guidance:**
• **Headache**: Rest in a quiet, dark room, stay hydrated
• **Cough/Cold**: Get plenty of rest, drink warm fluids, use a humidifier
• **General pain**: Rest the affected area, apply ice/heat as appropriate

**Need professional advice?**
If symptoms are severe or persistent, please submit a consultation form on your dashboard. Our qualified doctors will review your case and provide personalized medical guidance.

What specific symptom would you like to know more about?"""
    
    else:
        return """I'm here to help with questions about Docify Online. You can ask me about:
- Our medical consultation services
- How to submit consultation forms
- Data security and privacy
- Contact information
- Platform features

For medical concerns, please fill out a consultation form on your dashboard to speak with qualified doctors.

What would you like to know?"""

# ======== Query Processor Function ========
def process_query(user_query, symptoms=None):
    """Basic query processor with FAQ fallback"""
    try:
        # If retriever is not available, use simple FAQ response
        if retriever is None:
            return get_simple_faq_response(user_query)
            
        symptoms_section = f"User Symptoms: {symptoms}\nIncorporate these symptoms into your response if relevant." if symptoms else ""
        top_docs = retriever.invoke(user_query)[:3]  # Fixed deprecated method

        result = ""
        for i, doc in enumerate(top_docs):
            doc_text = f"Doc {i + 1}: {doc.page_content}\n" + "-" * 50 + "\n"
            result += doc_text
        print(result)
        return result if result.strip() else get_simple_faq_response(user_query)
    except Exception as e:
        print(f"Error in process_query: {e}")
        return get_simple_faq_response(user_query)
def process_query2(user_query, symptoms=None):
    # Prepare the symptoms section if provided
    symptoms_section = f"User Symptoms: {symptoms}\nIncorporate these symptoms into your response if relevant." if symptoms else ""

    # Retrieve the top 3 relevant documents
    top_docs = retriever.get_relevant_documents(user_query)[:3]

    # Debug: Print the retrieved documents
    print("--- Retrieved Documents ---")
    for i, doc in enumerate(top_docs):
        print(f"Doc {i+1}: {doc.page_content}")
        print("-" * 50)

    # Pass the relevant documents to the chain for processing
    from langchain_community.llms import Ollama
    ollama = Ollama(base_url='http://localhost:11434', model="docify")
    result=ollama(f"answer user query base on retrived information{user_query}+{top_docs} give short and summerized answer"
                  f"do not recomand and medication ask them to fill the form and consult a doc")
    print(result)
    return result
# Optional: Manual evaluation function

# Step 5: Process Query and Generate Structured Response
def process_query3(user_query, symptoms=None):
    model_id = "tiiuae/falcon-7b"

    text_generation_pipeline = pipeline(
        "text-generation", model=model_id, model_kwargs={"torch_dtype": torch.bfloat16}, max_new_tokens=400, device=0)

    llm = HuggingFacePipeline(pipeline=text_generation_pipeline)

    prompt_template = """
    <|system|>
    Answer the question based on your knowledge. Use the following context to help:

    {context}

    </s>
    <|user|>
    {question}
    </s>
    <|assistant|>

     """

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_template,
    )

    llm_chain = prompt | llm | StrOutputParser()
    from langchain_core.runnables import RunnablePassthrough

    rag_chain = {"context": retriever, "question": RunnablePassthrough()} | llm_chain

    # Generate and return response
    try:
        response = rag_chain.invoke(prompt)
        response = response.replace("</s>", "").strip()
        print("Model response:", response)
        return response
    except Exception as e:
        print("Model generation error:", e)
        return "Sorry, there was an error generating a response."

# Process Query
def process_query4(user_query, symptoms=None):
    model_name = "google/flan-t5-base"
    finetuned_path = "fine_tuning/lora_flan_t5_small/finetuned"
    tokenizer = AutoTokenizer.from_pretrained(finetuned_path)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    model = PeftModel.from_pretrained(base_model, finetuned_path)
    text2text_pipeline = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=200,
        device=-1
    )

    llm = HuggingFacePipeline(pipeline=text2text_pipeline)

    # RAG Setup
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    print(retriever.metadata)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    context = qa_chain({"query": user_query})['result']
    prompt = f"""
    You are a medical chatbot for Docify Online. Answer the user's query in a structured, clear, and concise manner.
    Use the following FAQ context to inform your response:
    your role is to answer information about what to do in fever
    {context}

    User Query: {user_query}
    """
    if symptoms:
        prompt += f"\nUser Symptoms: {symptoms}\nPlease incorporate the symptoms into your response if relevant."

    prompt += """
    understand the question and situation of a person then answer:
    **Answer**: [Your answer here]
    **Additional Info**: [Any relevant details or suggestions]
    Do not speculate or provide unverified medical advice.
    """

    response = text2text_pipeline(prompt)[0]["generated_text"]
    return response

def process_query5(user_query, symptom=None):
    """Enhanced query processor using Google Gemini with error handling"""
    try:
        # Check if API key is available and valid
        if not api_key or api_key.strip() == '' or api_key == 'your_actual_google_api_key_here':
            print("No valid Google API key available, falling back to simple FAQ response")
            return get_simple_faq_response(user_query)
        
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 15000,
            "response_mime_type": "text/plain",
        }
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
        ]
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
        )
        # Generate summary using Gemini model
        if retriever is not None:
            top_docs = retriever.invoke(user_query)[:3]  # Use invoke instead of deprecated get_relevant_documents
        else:
            top_docs = []
        
        summary = model.generate_content(contents=(
            f"You are a helpful medical assistant chatbot for Docify Online.\n\n"
            f"**About Docify:**\n"
            f"Docify is an online platform that allows users to consult certified doctors from the comfort of their home for health concerns and medical certificates.\n\n"
            f"**Your Role:**\n"
            f"- Provide general health information and guidance about common symptoms\n"
            f"- Answer questions about Docify's services and features\n"
            f"- Help users understand when to seek professional medical consultation\n"
            f"- Be friendly, informative, and supportive\n\n"
            f"**Guidelines:**\n"
            f"- Provide helpful information about common health concerns like fever, cold, cough, headaches, etc.\n"
            f"- For serious symptoms or diagnosis requests, recommend submitting a consultation form on the dashboard\n"
            f"- Do NOT prescribe medications or provide specific medical diagnoses\n"
            f"- Keep responses concise, clear, and friendly (2-4 sentences)\n"
            f"- For unrelated questions (sports, weather, etc.), politely redirect to health/platform topics\n\n"
            f"**User Query:** {user_query}\n"
            f"**Context from FAQ:** {top_docs}\n\n"
            f"Provide a helpful, friendly response:"
        ))

        return summary.text
    
    except Exception as e:
        print(f"Error with Google API: {e}")
        print("Falling back to simple FAQ response")
        return get_simple_faq_response(user_query)


def manual_evaluation():
    test_queries = [
        {"query": "How do I manage a fever?", "symptoms": "Fever for 2 days, 101°F"},
        {"query": "What is Docify Online?", "symptoms": None},
    ]
    for test in test_queries:
        response = process_query(test["query"], test["symptoms"])
        print(f"\nQuery: {test['query']}")
        if test["symptoms"]:
            print(f"Symptoms: {test['symptoms']}")
        print(f"Response: {response}")
