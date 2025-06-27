# Multi-Podcast Support Guide

This guide explains how to use the memvid pipeline with different podcasts.

## Overview

The pipeline now supports multiple podcasts by:
1. Auto-generating custom taxonomies for each podcast
2. Using command-line arguments for flexible file handling
3. Keeping each podcast's data separate

## Complete Workflow for a New Podcast

### 1. RSS Ingestion and Taxonomy Generation

```bash
# Set the RSS feed URL for your podcast
export RSS_FEED_URL="https://example-podcast.com/rss"
export OPENAI_API_KEY="sk-your-key"

# Create a directory for this podcast
mkdir my_new_podcast
cd my_new_podcast

# Ingest episodes from RSS
python3 ../rss_manager.py ingest

# Clean descriptions (remove ads/promos)
python3 ../rss_manager.py clean

# Generate custom taxonomy for this podcast
python3 ../rss_manager.py generate-taxonomy

# Review the generated taxonomy
cat taxonomy.json

# Tag episodes with the custom taxonomy
python3 ../rss_manager.py tag

# Validate and fix any tagging issues
python3 ../rss_manager.py validate
python3 ../rss_manager.py fix

# Export tagged episodes
python3 ../rss_manager.py export
# This creates export_YYYYMMDD_HHMMSS.json
```

### 2. Transcription

```bash
# Transcribe episodes (note the export filename from previous step)
python3 ../transcribe.py \
  --export-file export_20250627_093000.json \
  --output-dir transcripts_my_podcast/

# The processed file will be auto-created as transcripts_my_podcast_processed.json
```

### 3. Create Search Index

```bash
# Create memvid index
python3 ../file_chat.py \
  --input-dir transcripts_my_podcast/ \
  --chunk-size 2048 \
  --overlap 307 \
  --workers 8 \
  --memory-name my_podcast_index
```

### 4. Run Search API

```bash
# Run API on a different port
python3 ../search_api.py \
  --index-base output/my_podcast_index \
  --port 8001
```

## Directory Structure

For each podcast, you'll have:

```
my_new_podcast/
├── state.json                    # RSS manager state
├── taxonomy.json                 # Auto-generated taxonomy
├── export_*.json                 # Tagged episodes export
├── transcripts_my_podcast/       # Transcript files
└── transcripts_my_podcast_processed.json  # Tracking file
```

## Tips

1. **Taxonomy Review**: After generating taxonomy, review `taxonomy.json` and manually adjust if needed before tagging
2. **Separate Directories**: Keep each podcast in its own directory to avoid conflicts
3. **Port Management**: Use different ports for each podcast's API (8000, 8001, 8002, etc.)
4. **Memory Naming**: Use descriptive names for your indexes (`--memory-name`)

## Example: History Podcast vs Tech Podcast

The auto-generated taxonomies will be very different:

**History Podcast Taxonomy:**
```json
{
  "Format": ["Series Episodes", "Standalone Episodes", "Q&A Episodes"],
  "Theme": ["Ancient History", "Medieval History", "Modern History", ...],
  "Track": ["Roman Empire", "World Wars", "American History", ...]
}
```

**Tech Podcast Taxonomy:**
```json
{
  "Format": ["Interview Episodes", "News Roundup", "Deep Dives"],
  "Theme": ["AI & Machine Learning", "Web Development", "Cybersecurity", ...],
  "Track": ["Python", "JavaScript", "Cloud Computing", ...]
}
```

The taxonomy generation uses OpenAI to analyze your podcast's content and create appropriate categories automatically.