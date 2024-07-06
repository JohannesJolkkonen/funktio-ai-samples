from langchain_community.vectorstores import Qdrant
from langchain.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader

from qdrant_client import QdrantClient, models
from .openai_utils import get_embedding
from decouple import config

qdrant_api_key = config("QDRANT_API_KEY")
qdrant_url = config("QDRANT_URL")
collection_name = "Websites"

client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key
)

vector_store = Qdrant(
    client=client,
    collection_name=collection_name,
    embeddings=OpenAIEmbeddings(
        api_key=config("OPENAI_API_KEY")
    )
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=20, 
    length_function=len
)

def create_collection(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
    )
    print(f"Collection {collection_name} created successfully")

def upload_website_to_collection(url:str):
    if not client.collection_exists(collection_name=collection_name):
        create_collection(collection_name)
        
    loader = WebBaseLoader(url)
    docs = loader.load_and_split(text_splitter)
    for doc in docs:
        doc.metadata = {"source_url": url}
    
    vector_store.add_documents(docs)
    return f"Successfully uploaded {len(docs)} documents to collection {collection_name} from {url}"


def qdrant_search(query: str):
    vector_search = get_embedding(query)
    docs = client.search(
        collection_name=collection_name,
        query_vector=vector_search,
        limit=4
    )
    return docs


# create_collection(collection_name)
# upload_website_to_collection("https://hamel.dev/blog/posts/evals/")
