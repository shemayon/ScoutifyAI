from pinecone import Pinecone
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

def get_pinecone_index():
    """Lazily initialize and return the Pinecone index."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        logger.error("PINECONE_API_KEY is not set.")
        return None
    
    try:
        pc = Pinecone(api_key=api_key)
        index_name = "job-search-tool"
        # Check if index exists or just try to get it
        return pc.Index(index_name)
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone index: {str(e)}")
        return None

# For backward compatibility with existing imports
# Note: This might still be used as a global, so we try's to initialize it safely
try:
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index("job-search-tool")
except Exception as e:
    logger.warning(f"Global Pinecone index initialization failed (expected if index 'job-search-tool' is not yet created): {str(e)}")
    index = None









