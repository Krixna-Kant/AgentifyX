import spacy
import chromadb
from chromadb.utils import embedding_functions

nlp = spacy.load("en_core_web_sm")

#  Initialize ChromaDB (This will create a local folder named 'chroma_db' in your project)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Setup the embedding model (converts text to numbers for semantic search)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Create a collection (like a table in a database)
collection = chroma_client.get_or_create_collection(
    name="agentifyx_solutions", 
    embedding_function=sentence_transformer_ef
)

def chunk_text(text: str, max_chunk_size: int = 500) -> list[str]:
    """Uses spaCy to intelligently chunk text by sentences."""
    doc = nlp(text)
    chunks = []
    current_chunk = ""
    
    for sent in doc.sents:
        # Here, If adding the next sentence exceeds our limit, save the chunk and start a new one
        if len(current_chunk) + len(sent.text) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sent.text + " "
        else:
            current_chunk += sent.text + " "
            
    #Will Add any remaining text
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def store_embeddings(filename: str, text_chunks: list[str]) -> int:
    """Generates embeddings and stores them in ChromaDB."""
    if not text_chunks:
        return 0
        
    # Create unique IDs and metadata for each chunk so we can trace it back to the file
    ids = [f"{filename}_chunk_{i}" for i in range(len(text_chunks))]
    metadatas = [{"source_file": filename} for _ in range(len(text_chunks))]
    
    # Add to ChromaDB (it automatically handles the embedding generation here)
    collection.add(
        documents=text_chunks,
        metadatas=metadatas,
        ids=ids
    )
    
    return len(text_chunks)