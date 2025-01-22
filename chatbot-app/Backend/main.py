from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
import pandas as pd
import chardet
import os

# Load API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input structure for the API
class QueryRequest(BaseModel):
    query: str

# Constants
CSV_FILE_PATH = "./data/Beliebteste_Vornamen_aller_Linzer_am_1_1_2024_Etym.csv"  # Path to CSV file
CHROMA_DB_PATH = "./chroma_db"  # Path to persist ChromaDB

def detect_encoding(file_path):
    # Detect encoding of .csv the file
    with open(file_path, 'rb') as file:
        result = chardet.detect(file.read())
    return result['encoding']

# Function to load and clean the csv document for data handling and vectoring
def load_csv_to_documents(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CSV file not found at {file_path}")
    
    # Detect the encoding of the CSV file
    encoding = detect_encoding(file_path)
    
    # Load the CSV file
    csv_data = pd.read_csv(file_path, sep=";", engine="python", encoding=encoding)
    
    # Clean column names by stripping extra spaces or quotes
    csv_data.columns = [col.strip().strip('"') for col in csv_data.columns]
    csv_data = csv_data.applymap(lambda x: str(x).strip().strip('"'))

    # Initialize context summary
    context_summary = f"The dataset contains {len(csv_data)} rows and the following columns:\n" + ", ".join(csv_data.columns) + "\n\n"
    
    # Check for numerical columns
    numerical_columns = csv_data.select_dtypes(include=['number']).columns
    if not numerical_columns.empty:
        context_summary += f"Numerical columns include: {', '.join(numerical_columns)}.\n"
    
    # Check for categorical columns
    categorical_columns = csv_data.select_dtypes(include=['object']).columns
    if not categorical_columns.empty:
        context_summary += f"Categorical columns include: {', '.join(categorical_columns)}.\n"
    
    # Check for presence of any missing data
    missing_data = csv_data.isnull().sum()
    missing_data_summary = missing_data[missing_data > 0]
    if not missing_data_summary.empty:
        context_summary += f"Missing data exists in the following columns: {', '.join(missing_data_summary.index)}.\n"
    
    # Sample the rows for general understanding
    context_summary += f"Sample Data:\n{csv_data.to_string(index=False)}\n"
    
    # Return context as a Document object for the chatbot to use
    return [Document(page_content=context_summary, metadata={"source": "csv_summary"})]



# Initialize ChromaDB with Gemini embeddings
def initialize_chromadb(documents):
    # Gemini embeddings
    gemini_embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )
    # Create and persist ChromaDB vector store
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=gemini_embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    return vectorstore

# Create Retrieval Chain
def create_retrieval_qa_chain(vectorstore):
    retriever = vectorstore.as_retriever(search_kwargs={"k": min(5, len(vectorstore))})
    gemini_llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=GEMINI_API_KEY,
        temperature=0.7,
        top_p=0.85,
        max_output_tokens=256
    )
    
    # Prompt template for the QA task
    prompt_template = PromptTemplate.from_template("""
Du bist ein Chatbot-Assistent. Du erhältst CSV-Dateien als Datensätze, die du sorgfältig lesen und analysieren sollst. Analysiere die Daten und beantworte die Fragen der Benutzer genau und ausführlich. Der Datensatz enthält die beliebtesten Namen in Linz im Jahr 2023. Er umfasst männliche und weibliche Namen, die nach Beliebtheit sortiert sind.

Data Context:
{context}

User Question:
{question}

Antwort in mehr als einem Satz. Begründe und erläutere, warum die Antwort so ist, falls möglich:

Your Answer:
""")

    
    # Combine retriever and LLM Model into a RetrievalQA chain
    chain = RetrievalQA.from_chain_type(
        llm=gemini_llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=False,
        chain_type_kwargs={"prompt": prompt_template}
    )
    return chain

# Initialize the vector store and QA chain
try:
    documents = load_csv_to_documents(CSV_FILE_PATH)
    vectorstore = initialize_chromadb(documents)
    qa_chain = create_retrieval_qa_chain(vectorstore)
except Exception as e:
    print(f"Error initializing the application: {e}")
    qa_chain = None

# Endpoint to ask questions and retrieve answers from the chatbot
@app.post("/ask")
async def ask_csv(request: QueryRequest):
    if qa_chain is None:
        raise HTTPException(status_code=500, detail="System is not initialized. Check the logs.")
    try:
        response = qa_chain.invoke({"query": request.query})
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))