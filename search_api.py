#!/usr/bin/env python3
"""
Minimal API wrapper for memvid search functionality
Provides a REST endpoint for searching indexed podcast transcripts
"""

import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============= Pure Functions =============

def map_chunk_to_podcast(chunk_id: int, file_ranges: List[Dict]) -> Optional[str]:
    """Map a chunk ID to its source podcast file"""
    for file_range in file_ranges:
        if file_range["start_chunk"] <= chunk_id <= file_range["end_chunk"]:
            return file_range["file"]
    return None


def calculate_similarity_score(distance: float) -> float:
    """Convert distance to similarity score (0-1, higher is better)"""
    if distance == float('inf'):
        return 0.0
    if distance < 0:
        return 1.0
    return 1.0 / (1.0 + distance)


def transform_search_result(result: Dict, chunk_mapping: Dict[int, str]) -> Dict:
    """Transform memvid result to API format"""
    chunk_id = result.get("chunk_id", 0)
    
    # Get score (handle both 'score' and 'distance' fields)
    if "score" in result:
        score = result["score"]
    elif "distance" in result:
        score = calculate_similarity_score(result["distance"])
    else:
        score = 0.0
    
    return {
        "podcast_title": chunk_mapping.get(chunk_id, "Unknown"),
        "chunk_id": f"chunk_{chunk_id}",
        "text": result.get("text", ""),
        "score": score
    }


def build_chunk_mapping(file_ranges: List[Dict]) -> Dict[int, str]:
    """Build a mapping of chunk_id -> podcast_title"""
    mapping = {}
    for file_range in file_ranges:
        for chunk_id in range(file_range["start_chunk"], file_range["end_chunk"] + 1):
            mapping[chunk_id] = file_range["file"]
    return mapping


def parse_metadata_file_ranges(metadata: Dict) -> List[Dict]:
    """Extract file ranges from metadata"""
    return metadata.get("file_ranges", [])


def validate_index_paths(base_path: Path) -> Tuple[Path, Path, Path]:
    """Generate expected paths for video, index, and metadata files"""
    video_path = base_path.with_suffix(".mkv")
    index_path = base_path.parent / f"{base_path.name}_index.json"
    metadata_path = base_path.parent / f"{base_path.name}_metadata.json"
    return video_path, index_path, metadata_path


# ============= Pydantic Models =============

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(5, ge=1, description="Number of results to return")


class SearchResult(BaseModel):
    podcast_title: str
    chunk_id: str
    text: str
    score: float = Field(..., ge=0.0, le=1.0)


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]


# ============= API Application =============

class SearchAPI:
    """Encapsulates the search functionality and state"""
    
    def __init__(self, index_base: Optional[str] = None):
        self.retriever = None
        self.chunk_mapping = {}
        self.ready = False
        
        if index_base and index_base != "test":
            self._load_index(index_base)
    
    def _load_index(self, index_base: str):
        """Load the memvid index and metadata"""
        try:
            base_path = Path(index_base)
            video_path, index_path, metadata_path = validate_index_paths(base_path)
            
            # Load metadata for chunk mapping
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    file_ranges = parse_metadata_file_ranges(metadata)
                    self.chunk_mapping = build_chunk_mapping(file_ranges)
                    logger.info(f"Loaded chunk mapping with {len(self.chunk_mapping)} chunks")
            else:
                logger.warning(f"Metadata file not found: {metadata_path}")
            
            # Import memvid components only when needed
            from memvid import MemvidRetriever
            from memvid.config import get_default_config
            
            # Load config
            config = get_default_config()
            
            # Initialize retriever (uses positional args)
            self.retriever = MemvidRetriever(
                str(video_path),
                str(index_path)
            )
            
            self.ready = True
            logger.info(f"Successfully loaded index from {index_base}")
            
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise ValueError(f"Failed to load index: {e}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform search and return results"""
        if not self.ready or not self.retriever:
            return []
        
        try:
            # Use search_with_metadata to get scores
            results = self.retriever.search_with_metadata(query, top_k)
            
            # Transform results
            transformed = []
            for result in results:
                transformed.append(transform_search_result(result, self.chunk_mapping))
            
            return transformed
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Global search instance
search_api: Optional[SearchAPI] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    yield
    # Shutdown
    if search_api and hasattr(search_api, 'retriever') and search_api.retriever:
        # Clean up resources if needed
        pass


def create_app(test_mode: bool = False, index_base: Optional[str] = None) -> FastAPI:
    """Create FastAPI application"""
    global search_api
    
    app = FastAPI(
        title="Memvid Search API",
        description="Search indexed podcast transcripts",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize search API
    if test_mode:
        search_api = SearchAPI()  # Empty for testing
    else:
        search_api = SearchAPI(index_base)
    
    # ============= Endpoints =============
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "index_loaded": search_api.ready if search_api else False
        }
    
    @app.post("/search", response_model=SearchResponse)
    async def search(request: SearchRequest):
        """Search the indexed transcripts"""
        if not search_api:
            raise HTTPException(status_code=503, detail="Search service not initialized")
        
        if not search_api.ready:
            # In test mode, return empty results
            if test_mode:
                return SearchResponse(query=request.query, results=[])
            raise HTTPException(status_code=503, detail="Index not loaded")
        
        results = search_api.search(request.query, request.top_k)
        
        return SearchResponse(
            query=request.query,
            results=[SearchResult(**r) for r in results]
        )
    
    return app


# ============= CLI Entry Point =============

def main():
    """Main entry point for running the API"""
    parser = argparse.ArgumentParser(description="Memvid Search API")
    parser.add_argument(
        "--index-base",
        required=True,
        help="Base path to index files (without extension)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the API on (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    
    args = parser.parse_args()
    
    # Create app with index
    app = create_app(index_base=args.index_base)
    
    # Run server
    logger.info(f"Starting API server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()