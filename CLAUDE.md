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

## RSS Manager

Minimal RSS feed manager for podcast episodes:

```bash
# Set environment variables (or create .env file)
export RSS_FEED_URL="https://your-podcast-feed.com/rss"
export OPENAI_API_KEY="sk-your-key"

# Activate virtual environment
source memvid-env/bin/activate

# Commands (run in order)
python3 rss_manager.py ingest    # Fetch episodes from RSS feed
python3 rss_manager.py clean     # Clean descriptions with OpenAI
python3 rss_manager.py tag       # Tag episodes with taxonomy
python3 rss_manager.py validate  # Check tags are valid
python3 rss_manager.py fix       # Auto-fix validation errors
python3 rss_manager.py export    # Export to JSON
```

- Uses OpenAI model: **gpt-4o-mini**
- State stored in: `state.json`
- Non-destructive: Re-running commands only processes new/unprocessed episodes
- Progress saved after each episode (resilient to interruptions)
- `clean` command uses OpenAI to remove promotional content
- `fix` command automatically corrects validation errors

## Podcast Transcription

Transcribe podcast episodes using whisper.cpp:

```bash
# Uses export.json as source of episodes
python3 transcribe.py
```

- Continues from where previous transcriptions left off (742 completed)
- Downloads MP3 → Transcribes with whisper.cpp → Saves to `transcripts/`
- Progress tracked in `processed_transcripts.json`
- Requires whisper.cpp installed at `/Users/douglasvonkohorn/whisper.cpp/`

## Project Structure

- `file_chat.py` - Script for creating memvid indexes from documents
- `search_api.py` - FastAPI server for searching indexed content
- `test_search_api.py` - Unit tests for the search API
- `rss_manager.py` - Minimal RSS feed processor with OpenAI tagging
- `podcast_transcripts/` - Directory containing podcast transcript files (proprietary, not in git)
- `output/` - Directory containing generated memvid indexes

## Key Parameters

- **Chunk Size**: 2048 characters (optimal for QR code limits and search quality)
- **Overlap**: 15% of chunk size (e.g., 307 for 2048 chunks)
- **Workers**: 8 (for parallel processing on modern machines)

## System Architecture

This project is part of a larger podcast processing pipeline:

### 1. **RSS Ingest Library**
- Ingests new podcast episodes from RSS feeds
- Prepares episodes for download and transcription
- Entry point for new content

### 2. **MP3 Processor (Transcription Library)**
- Downloads and transcribes new podcast episodes
- Converts audio to text files
- Outputs to transcript files

### 3. **Backend Codebase (Taxonomy/Metadata)**
- Tags episodes according to custom taxonomy
- Creates episode metadata
- Generates list of categorized episodes

### 4. **memvid-attempt-3 (This Repository)**
This repository serves two purposes:
- **Indexer**: Creates memvid indexes from transcribed files (`file_chat.py`)
- **API Server**: Provides search API for the frontend (`search_api.py`)
- Much more efficient than previous vector database approach
- Uses less memory and provides better search results

### 5. **Frontend Repository**
- Queries the search API provided by this repository
- Simple API consumption via GET/POST endpoints
- User interface for searching podcast content

### Data Flow
```
RSS Feeds → RSS Ingest → MP3 Processor → Transcripts → Backend (Tagging) → memvid-attempt-3 (Indexing) → memvid-attempt-3 (API) → Frontend
```

## VPS Deployment

### Upload Index to VPS
```bash
# Edit upload.sh to set your VPS details, then:
./upload.sh

# Or manually:
rsync -avz output/podcasts_2048_chunk* user@vps-ip:/opt/podcast-api/output/
```

### Service Management
```bash
# Restart API service
ssh user@vps-ip 'sudo systemctl restart podcast-api'

# Check service status
ssh user@vps-ip 'sudo systemctl status podcast-api'

# View logs
ssh user@vps-ip 'sudo journalctl -u podcast-api -f'
```

### Resource Usage
- **Memory**: ~360MB when loaded
- **CPU**: <5% during queries
- **Query time**: 100-170ms
- **Suitable for**: $5-6/month VPS

See DEPLOYMENT.md for full VPS setup instructions.

## Regular Maintenance Tasks

### When You Add New Episodes

1. **On your local machine:**
   ```bash
   # Re-index with new episodes
   python3 file_chat.py --input-dir podcast_transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name podcasts_2048_chunk
   
   # Upload to VPS
   ./upload.sh
   ```

2. **The upload script will ask to restart the service**

### Check API Status
```bash
# Check service status
ssh podcast@your-vps-ip 'sudo systemctl status podcast-api'

# View recent logs
ssh podcast@your-vps-ip 'sudo journalctl -u podcast-api -n 50'
```

## Security Considerations

- The API is open to the internet (CORS allows all origins)
- If you need authentication later, you can add API keys
- Monitor your DigitalOcean bandwidth usage
- Regular security updates: `sudo apt update && sudo apt upgrade`

## Backup Strategy

Consider backing up your index files:
```bash
# Create a backup script on the VPS
nano /home/podcast/backup_index.sh
```

Add:
```bash
#!/bin/bash
tar -czf /home/podcast/index_backup_$(date +%Y%m%d).tar.gz /opt/podcast-api/output/
# Keep only last 7 backups
find /home/podcast -name "index_backup_*.tar.gz" -mtime +7 -delete
```

## Production API URLs

- **API URL**: https://your-subdomain.your-domain.com
- **Health Check**: https://your-subdomain.your-domain.com/health
- **Search**: https://your-subdomain.your-domain.com/query?search=YOUR_QUERY
- **Server**: Your VPS provider

## Notes

- The podcast transcripts are proprietary and should never be committed to git
- Maximum practical chunk size is ~2800 characters due to QR code version 40 limit
- The large index (podcasts_2048_chunk) contains 21,861 chunks from 742 podcasts
- This memvid approach replaces a previous vector database library, offering better performance and lower memory usage

## Reminders

- Remember that you need to activate the venv before running commands