#!/bin/bash

# Upload script for syncing memvid index files to VPS
# Usage: ./upload.sh [vps-user@vps-ip]

# Configuration - edit these values for your setup
DEFAULT_VPS="user@your-vps-ip"  # Change this to your VPS details
VPS_PATH="/opt/podcast-api/output/"
LOCAL_PATH="output/podcasts_2048_chunk"

# Use provided VPS or default
VPS="${1:-$DEFAULT_VPS}"

# Check if index files exist
if ! ls ${LOCAL_PATH}* 1> /dev/null 2>&1; then
    echo "Error: No index files found at ${LOCAL_PATH}*"
    echo "Please run the indexing command first:"
    echo "python3 file_chat.py --input-dir podcast_transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name podcasts_2048_chunk"
    exit 1
fi

# Show files to be uploaded
echo "Files to upload:"
ls -lh ${LOCAL_PATH}* | awk '{print "  " $9 " (" $5 ")"}'
echo

# Calculate total size
TOTAL_SIZE=$(du -ch ${LOCAL_PATH}* | grep total | awk '{print $1}')
echo "Total upload size: $TOTAL_SIZE"
echo

# Confirm upload
read -p "Upload to $VPS? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Upload cancelled."
    exit 0
fi

# Upload files with progress
echo "Starting upload..."
rsync -avz --progress ${LOCAL_PATH}* ${VPS}:${VPS_PATH}

if [ $? -eq 0 ]; then
    echo
    echo "✅ Upload completed successfully!"
    echo
    echo "To restart the API service, run:"
    echo "ssh $VPS 'sudo systemctl restart podcast-api'"
    echo
    read -p "Restart API service now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ssh $VPS 'sudo systemctl restart podcast-api'
        echo "✅ API service restarted"
    fi
else
    echo "❌ Upload failed!"
    exit 1
fi