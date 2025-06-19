Directory structure:
└── olow304-memvid/
    ├── README.md
    └── examples/
        └── file_chat.py

================================================
FILE: README.md
================================================
# Memvid - Video-Based AI Memory 🧠📹

**The lightweight, game-changing solution for AI memory at scale**

[![PyPI version](https://badge.fury.io/py/memvid.svg)](https://pypi.org/project/memvid/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Memvid revolutionizes AI memory management by encoding text data into videos, enabling **lightning-fast semantic search** across millions of text chunks with **sub-second retrieval times**. Unlike traditional vector databases that consume massive amounts of RAM and storage, Memvid compresses your knowledge base into compact video files while maintaining instant access to any piece of information.

## 🎥 Demo

https://github.com/user-attachments/assets/ec550e93-e9c4-459f-a8a1-46e122b5851e



## ✨ Key Features

- 🎥 **Video-as-Database**: Store millions of text chunks in a single MP4 file
- 🔍 **Semantic Search**: Find relevant content using natural language queries
- 💬 **Built-in Chat**: Conversational interface with context-aware responses
- 📚 **PDF Support**: Direct import and indexing of PDF documents
- 🚀 **Fast Retrieval**: Sub-second search across massive datasets
- 💾 **Efficient Storage**: 10x compression compared to traditional databases
- 🔌 **Pluggable LLMs**: Works with OpenAI, Anthropic, or local models
- 🌐 **Offline-First**: No internet required after video generation
- 🔧 **Simple API**: Get started with just 3 lines of code

## 🎯 Use Cases

- **📖 Digital Libraries**: Index thousands of books in a single video file
- **🎓 Educational Content**: Create searchable video memories of course materials
- **📰 News Archives**: Compress years of articles into manageable video databases
- **💼 Corporate Knowledge**: Build company-wide searchable knowledge bases
- **🔬 Research Papers**: Quick semantic search across scientific literature
- **📝 Personal Notes**: Transform your notes into a searchable AI assistant

## 🚀 Why Memvid?

### Game-Changing Innovation
- **Video as Database**: Store millions of text chunks in a single MP4 file
- **Instant Retrieval**: Sub-second semantic search across massive datasets
- **10x Storage Efficiency**: Video compression reduces memory footprint dramatically
- **Zero Infrastructure**: No database servers, just files you can copy anywhere
- **Offline-First**: Works completely offline once videos are generated

### Lightweight Architecture
- **Minimal Dependencies**: Core functionality in ~1000 lines of Python
- **CPU-Friendly**: Runs efficiently without GPU requirements
- **Portable**: Single video file contains your entire knowledge base
- **Streamable**: Videos can be streamed from cloud storage

## 📦 Installation

### Quick Install
```bash
pip install memvid
```

### For PDF Support
```bash
pip install memvid PyPDF2
```

### Recommended Setup (Virtual Environment)
```bash
# Create a new project directory
mkdir my-memvid-project
cd my-memvid-project

# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install memvid
pip install memvid

# For PDF support:
pip install PyPDF2
```

## 🎯 Quick Start

### Basic Usage
```python
from memvid import MemvidEncoder, MemvidChat

# Create video memory from text chunks
chunks = ["Important fact 1", "Important fact 2", "Historical event details"]
encoder = MemvidEncoder()
encoder.add_chunks(chunks)
encoder.build_video("memory.mp4", "memory_index.json")

# Chat with your memory
chat = MemvidChat("memory.mp4", "memory_index.json")
chat.start_session()
response = chat.chat("What do you know about historical events?")
print(response)
```

### Building Memory from Documents
```python
from memvid import MemvidEncoder
import os

# Load documents
encoder = MemvidEncoder(chunk_size=512, overlap=50)

# Add text files
for file in os.listdir("documents"):
    with open(f"documents/{file}", "r") as f:
        encoder.add_text(f.read(), metadata={"source": file})

# Build optimized video
encoder.build_video(
    "knowledge_base.mp4",
    "knowledge_index.json",
    fps=30,  # Higher FPS = more chunks per second
    frame_size=512  # Larger frames = more data per frame
)
```

### Advanced Search & Retrieval
```python
from memvid import MemvidRetriever

# Initialize retriever
retriever = MemvidRetriever("knowledge_base.mp4", "knowledge_index.json")

# Semantic search
results = retriever.search("machine learning algorithms", top_k=5)
for chunk, score in results:
    print(f"Score: {score:.3f} | {chunk[:100]}...")

# Get context window
context = retriever.get_context("explain neural networks", max_tokens=2000)
print(context)
```

### Interactive Chat Interface
```python
from memvid import MemvidInteractive

# Launch interactive chat UI
interactive = MemvidInteractive("knowledge_base.mp4", "knowledge_index.json")
interactive.run()  # Opens web interface at http://localhost:7860
```

### Testing with file_chat.py
The `examples/file_chat.py` script provides a comprehensive way to test Memvid with your own documents:

```bash
# Process a directory of documents
python examples/file_chat.py --input-dir /path/to/documents --provider google

# Process specific files
python examples/file_chat.py --files doc1.txt doc2.pdf --provider openai

# Use H.265 compression (requires Docker)
python examples/file_chat.py --input-dir docs/ --codec h265 --provider google

# Custom chunking for large documents
python examples/file_chat.py --files large.pdf --chunk-size 2048 --overlap 32 --provider google

# Load existing memory
python examples/file_chat.py --load-existing output/my_memory --provider google
```

### Complete Example: Chat with a PDF Book
```bash
# 1. Create a new directory and set up environment
mkdir book-chat-demo
cd book-chat-demo
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install memvid PyPDF2

# 3. Create book_chat.py
cat > book_chat.py << 'EOF'
from memvid import MemvidEncoder, chat_with_memory
import os

# Your PDF file
book_pdf = "book.pdf"  # Replace with your PDF path

# Build video memory
encoder = MemvidEncoder()
encoder.add_pdf(book_pdf)
encoder.build_video("book_memory.mp4", "book_index.json")

# Chat with the book
api_key = os.getenv("OPENAI_API_KEY")  # Optional: for AI responses
chat_with_memory("book_memory.mp4", "book_index.json", api_key=api_key)
EOF

# 4. Run it
export OPENAI_API_KEY="your-api-key"  # Optional
python book_chat.py
```

## 🛠️ Advanced Configuration

### Custom Embeddings
```python
from sentence_transformers import SentenceTransformer

# Use custom embedding model
custom_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
encoder = MemvidEncoder(embedding_model=custom_model)
```

### Video Optimization
```python
# For maximum compression
encoder.build_video(
    "compressed.mp4",
    "index.json",
    fps=60,  # More frames per second
    frame_size=256,  # Smaller frames
    video_codec='h265',  # Better compression
    crf=28  # Compression quality (lower = better quality)
)
```

### Distributed Processing
```python
# Process large datasets in parallel
encoder = MemvidEncoder(n_workers=8)
encoder.add_chunks_parallel(massive_chunk_list)
```

## 🐛 Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'memvid'**
```bash
# Make sure you're using the right Python
which python  # Should show your virtual environment path
# If not, activate your virtual environment:
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**ImportError: PyPDF2 is required for PDF support**
```bash
pip install PyPDF2
```

**LLM API Key Issues**
```bash
# Set your API key (get one at https://platform.openai.com)
export GOOGLE_API_KEY="AIzaSyB1-..."  # macOS/Linux
# Or on Windows:
set GOOGLE_API_KEY=AIzaSyB1-...
```

**Large PDF Processing**
```python
# For very large PDFs, use smaller chunk sizes
encoder = MemvidEncoder()
encoder.add_pdf("large_book.pdf", chunk_size=400, overlap=50)
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=memvid tests/

# Format code
black memvid/
```

## 🆚 Comparison with Traditional Solutions

| Feature | Memvid | Vector DBs | Traditional DBs |
|---------|--------|------------|-----------------|
| Storage Efficiency | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Setup Complexity | Simple | Complex | Complex |
| Semantic Search | ✅ | ✅ | ❌ |
| Offline Usage | ✅ | ❌ | ✅ |
| Portability | File-based | Server-based | Server-based |
| Scalability | Millions | Millions | Billions |
| Cost | Free | $$$$ | $$$ |


## 📚 Examples

Check out the [examples/](examples/) directory for:
- Building memory from Wikipedia dumps
- Creating a personal knowledge base
- Multi-language support
- Real-time memory updates
- Integration with popular LLMs

## 🆘 Getting Help

- 📖 [Documentation](https://github.com/olow304/memvid/wiki) - Comprehensive guides
- 💬 [Discussions](https://github.com/olow304/memvid/discussions) - Ask questions
- 🐛 [Issue Tracker](https://github.com/olow304/memvid/issues) - Report bugs
- 🌟 [Show & Tell](https://github.com/olow304/memvid/discussions/categories/show-and-tell) - Share your projects

## 🔗 Links

- [GitHub Repository](https://github.com/olow304/memvid)
- [PyPI Package](https://pypi.org/project/memvid)
- [Changelog](https://github.com/olow304/memvid/releases)


## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Created by [Olow304](https://github.com/olow304) and the Memvid community.

Built with ❤️ using:
- [sentence-transformers](https://www.sbert.net/) - State-of-the-art embeddings for semantic search
- [OpenCV](https://opencv.org/) - Computer vision and video processing
- [qrcode](https://github.com/lincolnloop/python-qrcode) - QR code generation
- [FAISS](https://github.com/facebookresearch/faiss) - Efficient similarity search
- [PyPDF2](https://github.com/py-pdf/pypdf) - PDF text extraction

Special thanks to all contributors who help make Memvid better!

---

**Ready to revolutionize your AI memory management? Install Memvid and start building!** 🚀



================================================
FILE: examples/file_chat.py
================================================
#!/usr/bin/env python3
"""
file_chat.py - Enhanced script for testing MemvidChat with external files

This script allows you to:
1. Create a memory video from your own files with configurable parameters
2. Chat with the created memory using different LLM providers
3. Store results in output/ directory to avoid contaminating the main repo
4. Handle FAISS training issues gracefully
5. Configure chunking and compression parameters

Usage:
    python file_chat.py --input-dir /path/to/documents --provider google
    python file_chat.py --files file1.txt file2.pdf --provider openai --chunk-size 2048
    python file_chat.py --load-existing output/my_memory --provider google
    python file_chat.py --input-dir ~/docs --index-type Flat --codec h265

Examples:
    # Create memory from a directory and chat with Google
    python file_chat.py --input-dir ~/Documents/research --provider google

    # Create memory with custom chunking for large documents
    python file_chat.py --files report.pdf --chunk-size 2048 --overlap 32 --provider openai

    # Use Flat index for small datasets (avoids FAISS training issues)
    python file_chat.py --files single_doc.pdf --index-type Flat --provider google

    # Load existing memory and continue chatting
    python file_chat.py --load-existing output/research_memory --provider google

    # Create memory with H.265 compression
    python file_chat.py --input-dir ~/docs --codec h265 --provider anthropic
"""

import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import json

# Add the parent directory to the path so we can import memvid
sys.path.insert(0, str(Path(__file__).parent.parent))  # Go up TWO levels from examples/

from memvid import MemvidEncoder, MemvidChat
from memvid.config import get_default_config, get_codec_parameters

def setup_output_dir():
    """Create output directory if it doesn't exist"""
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    return output_dir

def generate_memory_name(input_source):
    """Generate a meaningful name for the memory files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if isinstance(input_source, list):
        # Multiple files
        base_name = f"files_{len(input_source)}items"
    else:
        # Directory
        dir_name = Path(input_source).name
        base_name = f"dir_{dir_name}"

    return f"{base_name}_{timestamp}"

def collect_files_from_directory(directory_path, extensions=None):
    """Collect supported files from a directory"""
    if extensions is None:
        extensions = {'.txt', '.md', '.pdf', '.doc', '.docx', '.rtf', '.epub', '.html', '.htm'}

    directory = Path(directory_path)
    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory_path}")

    files = []
    for ext in extensions:
        files.extend(directory.rglob(f"*{ext}"))

    return [str(f) for f in files if f.is_file()]

def create_memory_with_fallback(encoder, video_path, index_path):
    """Create memory with graceful FAISS fallback for training issues"""
    try:
        build_stats = encoder.build_video(str(video_path), str(index_path))
        return build_stats
    except Exception as e:
        error_str = str(e)
        if "is_trained" in error_str or "IndexIVFFlat" in error_str or "training" in error_str.lower():
            print(f"⚠️  FAISS IVF training failed: {e}")
            print(f"🔄 Auto-switching to Flat index for compatibility...")

            # Override config to use Flat index
            original_index_type = encoder.config["index"]["type"]
            encoder.config["index"]["type"] = "Flat"

            try:
                # Recreate the index manager with Flat index
                encoder._setup_index()
                build_stats = encoder.build_video(str(video_path), str(index_path))
                print(f"✅ Successfully created memory using Flat index")
                return build_stats
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                raise
        else:
            raise

def create_memory_from_files(files, output_dir, memory_name, **config_overrides):
    """Create a memory video from a list of files with configurable parameters"""
    print(f"Creating memory from {len(files)} files...")

    # Start timing
    start_time = time.time()

    # Apply config overrides to default config
    config = get_default_config()
    for key, value in config_overrides.items():
        if key in ['chunk_size', 'overlap']:
            config["chunking"][key] = value
        elif key == 'index_type':
            config["index"]["type"] = value
        elif key == 'codec':
            config[key] = value

    # Initialize encoder with config first (this ensures config consistency)
    encoder = MemvidEncoder(config)

    # Get the actual codec and video extension from the encoder's config
    actual_codec = encoder.config.get("codec")  # Use encoder's resolved codec
    video_ext = get_codec_parameters(actual_codec).get("video_file_type", "mp4")

    # Import tqdm for progress bars
    try:
        from tqdm import tqdm
        use_progress = True
    except ImportError:
        print("Note: Install tqdm for progress bars (pip install tqdm)")
        use_progress = False

    processed_count = 0
    skipped_count = 0

    # Process files with progress tracking
    file_iterator = tqdm(files, desc="Processing files") if use_progress else files

    for file_path in file_iterator:
        file_path = Path(file_path)
        if not use_progress:
            print(f"Processing: {file_path.name}")

        try:
            chunk_size = config["chunking"]["chunk_size"]
            overlap = config["chunking"]["overlap"]

            if file_path.suffix.lower() == '.pdf':
                encoder.add_pdf(str(file_path), chunk_size, overlap)
            elif file_path.suffix.lower() == '.epub':
                encoder.add_epub(str(file_path), chunk_size, overlap)
            elif file_path.suffix.lower() in ['.html', '.htm']:
                # Process HTML with BeautifulSoup
                try:
                    from bs4 import BeautifulSoup
                except ImportError:
                    print(f"Warning: BeautifulSoup not available for HTML processing. Skipping {file_path.name}")
                    skipped_count += 1
                    continue

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    clean_text = ' '.join(chunk for chunk in chunks if chunk)
                    if clean_text.strip():
                        encoder.add_text(clean_text, chunk_size, overlap)
            else:
                # Read as text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if content.strip():
                        encoder.add_text(content, chunk_size, overlap)

            processed_count += 1

        except Exception as e:
            print(f"Warning: Could not process {file_path.name}: {e}")
            skipped_count += 1
            continue

    processing_time = time.time() - start_time
    print(f"\n📊 Processing Summary:")
    print(f"  ✅ Successfully processed: {processed_count} files")
    print(f"  ⚠️  Skipped: {skipped_count} files")
    print(f"  ⏱️  Processing time: {processing_time:.2f} seconds")

    if processed_count == 0:
        raise ValueError("No files were successfully processed")

    # Build the video (video_ext already determined from encoder config)
    video_path = output_dir / f"{memory_name}.{video_ext}"
    index_path = output_dir / f"{memory_name}_index.json"

    print(f"\n🎬 Building memory video: {video_path}")
    print(f"📊 Total chunks to encode: {len(encoder.chunks)}")

    encoding_start = time.time()

    # Use fallback-enabled build function
    build_stats = create_memory_with_fallback(encoder, video_path, index_path)

    encoding_time = time.time() - encoding_start
    total_time = time.time() - start_time

    # Enhanced statistics
    print(f"\n🎉 Memory created successfully!")
    print(f"  📁 Video: {video_path}")
    print(f"  📋 Index: {index_path}")
    print(f"  📊 Chunks: {build_stats.get('total_chunks', 'unknown')}")
    print(f"  🎞️  Frames: {build_stats.get('total_frames', 'unknown')}")
    print(f"  📏 Video size: {video_path.stat().st_size / (1024 * 1024):.1f} MB")
    print(f"  ⏱️  Encoding time: {encoding_time:.2f} seconds")
    print(f"  ⏱️  Total time: {total_time:.2f} seconds")

    if build_stats.get('video_size_mb', 0) > 0:
        # Calculate rough compression stats
        total_chars = sum(len(chunk) for chunk in encoder.chunks)
        original_size_mb = total_chars / (1024 * 1024)  # Rough estimate
        compression_ratio = original_size_mb / build_stats['video_size_mb'] if build_stats['video_size_mb'] > 0 else 0
        print(f"  📦 Estimated compression ratio: {compression_ratio:.1f}x")

    # Save metadata about this memory
    metadata = {
        'created': datetime.now().isoformat(),
        'source_files': files,
        'video_path': str(video_path),
        'index_path': str(index_path),
        'config_used': config,
        'processing_stats': {
            'files_processed': processed_count,
            'files_skipped': skipped_count,
            'processing_time_seconds': processing_time,
            'encoding_time_seconds': encoding_time,
            'total_time_seconds': total_time
        },
        'build_stats': build_stats
    }

    metadata_path = output_dir / f"{memory_name}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"  📄 Metadata: {metadata_path}")

    return str(video_path), str(index_path)

def load_existing_memory(memory_path):
    """Load and validate existing memory from the output directory"""
    memory_path = Path(memory_path)

    # Handle different input formats
    if memory_path.is_dir():
        # Directory provided, look for memory files
        # Try all possible video extensions
        video_files = []
        for ext in ['mp4', 'avi', 'mkv']:
            video_files.extend(memory_path.glob(f"*.{ext}"))

        if not video_files:
            raise ValueError(f"No video files found in {memory_path}")

        video_path = video_files[0]
        # Look for corresponding index file
        possible_index_paths = [
            video_path.with_name(video_path.stem + '_index.json'),
            video_path.with_suffix('.json'),
            video_path.with_suffix('_index.json')
        ]

        index_path = None
        for possible_path in possible_index_paths:
            if possible_path.exists():
                index_path = possible_path
                break

        if not index_path:
            raise ValueError(f"No index file found for {video_path}")

    elif memory_path.suffix in ['.mp4', '.avi', '.mkv']:
        # Video file provided
        video_path = memory_path
        index_path = memory_path.with_name(memory_path.stem + '_index.json')

    else:
        # Assume it's a base name, try to find files
        base_path = memory_path
        video_path = None

        # Try different video extensions
        for ext in ['mp4', 'avi', 'mkv']:
            candidate = base_path.with_suffix(f'.{ext}')
            if candidate.exists():
                video_path = candidate
                break

        if not video_path:
            raise ValueError(f"No video file found with base name: {memory_path}")

        index_path = base_path.with_suffix('_index.json')

    # Validate files exist and are readable
    if not video_path.exists():
        raise ValueError(f"Video file not found: {video_path}")
    if not index_path.exists():
        raise ValueError(f"Index file not found: {index_path}")

    # Validate file integrity
    try:
        with open(index_path, 'r') as f:
            index_data = json.load(f)
        chunk_count = len(index_data.get('metadata', []))
        print(f"✅ Index contains {chunk_count} chunks")
    except Exception as e:
        raise ValueError(f"Index file corrupted: {e}")

    # Check video file size
    video_size_mb = video_path.stat().st_size / (1024 * 1024)
    print(f"✅ Video file: {video_size_mb:.1f} MB")

    print(f"Loading existing memory:")
    print(f"  📁 Video: {video_path}")
    print(f"  📋 Index: {index_path}")

    return str(video_path), str(index_path)

def start_chat_session(video_path, index_path, provider='google', model=None):
    """Start an interactive chat session"""
    print(f"\nInitializing chat with {provider}...")

    try:
        chat = MemvidChat(
            video_file=video_path,
            index_file=index_path,
            llm_provider=provider,
            llm_model=model
        )

        print("✓ Chat initialized successfully!")
        print("\nStarting interactive session...")
        print("Commands:")
        print("  - Type your questions normally")
        print("  - Type 'quit' or 'exit' to end")
        print("  - Type 'clear' to clear conversation history")
        print("  - Type 'stats' to see session statistics")
        print("=" * 50)

        # Start interactive chat
        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    # Export conversation before exiting
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    export_path = Path("output") / f"conversation_{timestamp}.json"
                    chat.export_conversation(str(export_path))
                    print(f"💾 Conversation saved to: {export_path}")
                    print("Goodbye!")
                    break

                elif user_input.lower() == 'clear':
                    chat.clear_history()
                    print("🗑️ Conversation history cleared")
                    continue

                elif user_input.lower() == 'stats':
                    stats = chat.get_stats()
                    print(f"📊 Session stats: {stats}")
                    continue

                if not user_input:
                    continue

                # Get response (always stream for better UX)
                chat.chat(user_input, stream=True)

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    except Exception as e:
        print(f"Error initializing chat: {e}")
        return False

    return True

def main():
    parser = argparse.ArgumentParser(
        description="Chat with your documents using MemVid with enhanced configuration options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '--input-dir',
        help='Directory containing documents to process'
    )
    input_group.add_argument(
        '--files',
        nargs='+',
        help='Specific files to process'
    )
    input_group.add_argument(
        '--load-existing',
        help='Load existing memory (provide path to video file or directory)'
    )

    # LLM options
    parser.add_argument(
        '--provider',
        choices=['openai', 'google', 'anthropic'],
        default='google',
        help='LLM provider to use (default: google)'
    )
    parser.add_argument(
        '--model',
        help='Specific model to use (uses provider defaults if not specified)'
    )

    # Memory options
    parser.add_argument(
        '--memory-name',
        help='Custom name for the memory files (auto-generated if not provided)'
    )

    # Processing configuration options
    parser.add_argument(
        '--chunk-size',
        type=int,
        help='Override default chunk size (e.g., 2048, 4096)'
    )
    parser.add_argument(
        '--overlap',
        type=int,
        help='Override default chunk overlap (e.g., 16, 32, 64)'
    )
    parser.add_argument(
        '--index-type',
        choices=['Flat', 'IVF'],
        help='FAISS index type (Flat for small datasets, IVF for large datasets)'
    )
    parser.add_argument(
        '--codec',
        choices=['h264', 'h265', 'mp4v'],
        help='Video codec to use for compression'
    )

    # File processing options
    parser.add_argument(
        '--extensions',
        nargs='+',
        default=['.txt', '.md', '.pdf', '.doc', '.docx', '.epub', '.html', '.htm'],
        help='File extensions to include when processing directories'
    )

    args = parser.parse_args()

    # Setup output directory
    output_dir = setup_output_dir()

    try:
        # Get or create memory
        if args.load_existing:
            video_path, index_path = load_existing_memory(args.load_existing)
        else:
            # Collect files
            if args.input_dir:
                files = collect_files_from_directory(args.input_dir, set(args.extensions))
                if not files:
                    print(f"No supported files found in {args.input_dir}")
                    return 1
                print(f"Found {len(files)} files to process")
                input_source = args.input_dir
            else:
                files = args.files
                for f in files:
                    if not Path(f).exists():
                        print(f"File not found: {f}")
                        return 1
                input_source = files

            # Generate memory name
            memory_name = args.memory_name or generate_memory_name(input_source)

            # Build config overrides from command line arguments
            config_overrides = {}
            if args.chunk_size:
                config_overrides['chunk_size'] = args.chunk_size
            if args.overlap:
                config_overrides['overlap'] = args.overlap
            if args.index_type:
                config_overrides['index_type'] = args.index_type
            if args.codec:
                config_overrides['codec'] = args.codec

            # Show what defaults are being used if no overrides provided
            if not config_overrides:
                default_config = get_default_config()
                print(f"📋 Using default configuration:")
                print(f"   Chunk size: {default_config['chunking']['chunk_size']}")
                print(f"   Overlap: {default_config['chunking']['overlap']}")
                print(f"   Index type: {default_config['index']['type']}")
                print(f"   Codec: {default_config.get('codec', 'h265')}")

            # Create memory with configuration
            video_path, index_path = create_memory_from_files(
                files, output_dir, memory_name, **config_overrides
            )

        # Start chat session
        success = start_chat_session(video_path, index_path, args.provider, args.model)
        return 0 if success else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

