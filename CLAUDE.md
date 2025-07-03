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
# Index single podcast (e.g., The Rest Is History)
python3 file_chat.py --input-dir transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name rest_is_history_2048

# Index multiple podcasts together
python3 file_chat.py --input-dir transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name all_podcasts_2048

# Index podcast-specific transcripts
python3 file_chat.py --input-dir winenglish/transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name wine_podcast_2048
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

Minimal RSS feed manager for podcast episodes with multi-podcast support:

```bash
# Set environment variables (or create .env file)
export RSS_FEED_URL="https://your-podcast-feed.com/rss"
export OPENAI_API_KEY="sk-your-key"

# Activate virtual environment
source memvid-env/bin/activate

# For existing podcast (The Rest Is History)
cd the-rest-is-history-pod
python3 ../rss_manager.py ingest    # Fetch episodes from RSS feed
python3 ../rss_manager.py clean     # Clean descriptions with OpenAI
python3 ../rss_manager.py tag       # Tag episodes with taxonomy
python3 ../rss_manager.py validate  # Check tags are valid
python3 ../rss_manager.py fix       # Auto-fix validation errors
python3 ../rss_manager.py export    # Export to JSON

# For new podcasts
mkdir new-podcast-name
cd new-podcast-name
python3 ../rss_manager.py generate-taxonomy  # Auto-generate taxonomy based on content
python3 ../rss_manager.py ingest
# ... continue with normal workflow
```

- Uses OpenAI model: **gpt-4o-mini**
- State stored in: `state.json` (in each podcast directory)
- Taxonomy stored in: `taxonomy.json` (auto-generated or custom)
- Non-destructive: Re-running commands only processes new/unprocessed episodes
- Progress saved after each episode (resilient to interruptions)
- `clean` command uses OpenAI to remove promotional content
- `fix` command automatically corrects validation errors
- `generate-taxonomy` analyzes up to 180k tokens of content to create custom taxonomies

## Podcast Transcription

Transcribe podcast episodes using faster-whisper INT8 models or OpenAI API:

```bash
# Using local faster-whisper INT8 (default) - ~7x real-time with small model
cd the-rest-is-history-pod
python3 ../transcribe.py --export-file export.json --output-dir ../transcripts/

# Optimize CPU threads for your system (default: 8)
python3 ../transcribe.py --export-file export.json --output-dir ../transcripts/ --cpu-threads 6  # For M1
python3 ../transcribe.py --export-file export.json --output-dir ../transcripts/ --cpu-threads 10 # For M1 Pro/Max

# Using OpenAI Whisper API (requires OPENAI_API_KEY in .env)
cd new-podcast-name
python3 ../transcribe.py --export-file export.json --output-dir transcripts/ --use-openai-transcribe

# Note: All modes pre-process with silence removal + 2x speed to reduce transcription time
```

- Continues from where previous transcriptions left off
- Downloads MP3 → Transcribes → Saves to specified output directory
- Progress tracked in `processed_transcripts.json` (in each podcast directory)
- **Local mode now uses faster-whisper with INT8 quantized models:**
  - Whisper small INT8 model (1.1GB) for ~7x real-time speed on M1
  - CPU-optimized with configurable threads (--cpu-threads flag)
  - Auto-detects language (no longer forced to English)
  - Optimized beam_size=1 for small model performance
  - First-time model loading takes ~10s, then cached
  - Models must be downloaded first (see setup below)
- OpenAI mode requires `OPENAI_API_KEY` environment variable
- Both modes produce identical output format (.txt files)
- Both modes pre-process audio with silence removal + 2x speed + mono 16kHz 64kbps
  - Reduces transcription time by ~60-70%
  - Saves ~30% on OpenAI API costs
- OpenAI mode handles large files (>25MB) by chunking:
  - Calculates optimal chunk size based on bitrate
  - Maintains context between chunks using token-based prompts
- Supports custom export files and output directories via CLI arguments

### Faster-Whisper Setup

```bash
# One-time setup: Download INT8 models
source memvid-env/bin/activate
huggingface-cli download ctranslate2-4you/whisper-small-ct2-int8_float16 --local-dir models/whisper-small-int8

# Models are stored in models/ directory (1.1GB total)
# After download, transcription will use these automatically
```

### Performance Notes

- **Small model**: ~7x real-time, 1.1GB RAM, 7-8% WER
- **Large-v3 model**: ~1.4x real-time, 3.6GB RAM, 3-4% WER
- Use small for speed, large-v3 for accuracy

## Project Structure

### Main Files
- `file_chat.py` - Script for creating memvid indexes from documents
- `search_api.py` - FastAPI server for searching indexed content
- `test_search_api.py` - Unit tests for the search API
- `rss_manager.py` - Minimal RSS feed processor with OpenAI tagging
- `transcribe.py` - Audio transcription with faster-whisper INT8 models
- `transcripts/` - Directory containing podcast transcript files (proprietary, not in git)
- `output/` - Directory containing generated memvid indexes

### Podcast Directories
Each podcast has its own directory containing:
```
podcast-name/
├── state.json                  # RSS manager state and metadata
├── taxonomy.json               # Custom taxonomy for the podcast
├── export.json                 # Tagged episodes ready for indexing
├── processed_transcripts.json  # Transcription progress tracking
└── transcripts/               # (optional) Podcast-specific transcripts
```

Currently organized podcasts:
- `the-rest-is-history-pod/` - The Rest Is History podcast (784 episodes)
- `winenglish/` - Wine-related podcast

### Key JSON Files

- **`state.json`** - Comprehensive metadata file used by RSS manager
  - Contains full episode metadata: title, descriptions, tags, URLs, timestamps
  - Tracks RSS ingestion → cleaning → tagging workflow
  - Each episode has ~10 fields including cleaned descriptions and taxonomy tags
  - Object structure keyed by GUID for fast lookups

- **`taxonomy.json`** - Podcast-specific content categories
  - Auto-generated by analyzing episode content with OpenAI
  - Contains Format, Theme, and Track categorizations
  - Customized for each podcast's content focus

- **`processed_transcripts.json`** - Simple transcription tracking file
  - Minimal data: guid, title, and transcript_file location
  - Used by transcribe.py to track which episodes are already transcribed
  - Array structure for sequential processing
  - Maps episodes to their transcript files

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
   python3 file_chat.py --input-dir transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name podcasts_2048_chunk
   
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