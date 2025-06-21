# Project-Specific Knowledge for Claude

This file contains project-specific commands and knowledge for the memvid-attempt-3 project.

## Common Commands

### Virtual Environment
```bash
# Activate the virtual environment
source memvid-env/bin/activate
```

### Running the Search API
```bash
# Start the API server
python3 search_api.py --index-base output/podcasts_2048_chunk --port 8000

# Start in background with logging
nohup python3 search_api.py --index-base output/podcasts_2048_chunk --port 8000 > api.log 2>&1 &
```

### Process Management
```bash
# Kill process on specific port (PREFERRED METHOD)
lsof -ti:8000 | xargs kill -9

# Check if port is in use
lsof -i:8000
```

### Indexing Podcasts
```bash
# Index with 2048 character chunks (recommended)
python3 file_chat.py --input-dir podcast_transcripts/ --chunk-size 2048 --overlap 307 --workers 8

# Index with custom memory name
python3 file_chat.py --input-dir podcast_transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name podcasts_2048_chunk
```

### Testing
```bash
# Run all tests
python3 -m pytest test_search_api.py -v

# Run specific test
python3 -m pytest test_search_api.py::TestAPIEndpoints::test_query_endpoint_exists -v
```

### API Usage Examples
```bash
# POST endpoint
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "murder of richard ii", "top_k": 3}'

# GET endpoint (for frontend compatibility)
curl "http://localhost:8000/query?search=murder%20of%20richard%20ii&top_k=3"
```

## Project Structure

- `file_chat.py` - Script for creating memvid indexes from documents
- `search_api.py` - FastAPI server for searching indexed content
- `test_search_api.py` - Unit tests for the search API
- `podcast_transcripts/` - Directory containing podcast transcript files (proprietary, not in git)
- `output/` - Directory containing generated memvid indexes

## Key Parameters

- **Chunk Size**: 2048 characters (optimal for QR code limits and search quality)
- **Overlap**: 15% of chunk size (e.g., 307 for 2048 chunks)
- **Workers**: 8 (for parallel processing on modern machines)

## Notes

- The podcast transcripts are proprietary and should never be committed to git
- Maximum practical chunk size is ~2800 characters due to QR code version 40 limit
- The large index (podcasts_2048_chunk) contains 21,861 chunks from 742 podcasts