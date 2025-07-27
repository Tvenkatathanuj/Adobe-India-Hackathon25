# Challenge 1A - PDF Outline Extractor

## Overview
This solution extracts hierarchical outlines from PDF documents, identifying titles and heading structures with multilingual support.

## Solution Components

### Core Files
- **`main.py`** - Main PDF outline extraction implementation
- **`requirements.txt`** - Python dependencies (PyMuPDF)
- **`Dockerfile`** - Container configuration with AMD64 platform

### Key Features
- **Title Extraction**: Automatically detects document titles from first page
- **Hierarchical Heading Detection**: Identifies and classifies heading levels (1-6)
- **Multilingual Support**: Works with various language formats
- **JSON Output**: Structured output format as required
- **Error Handling**: Robust error handling and logging

## Technical Implementation

### PDF Processing
- Uses PyMuPDF (fitz) library for reliable PDF text extraction
- Analyzes text formatting and patterns to identify headings
- Supports various heading formats (numbered, lettered, mixed)

### Heading Classification
- Pattern-based detection using regular expressions
- Font size and formatting analysis
- Hierarchical level assignment (1-6 levels)
- Handles complex document structures

### Output Format
```json
{
  "title": "Document Title",
  "headings": [
    {
      "text": "Heading Text",
      "level": 1,
      "page": 1
    }
  ]
}
```

## Performance
- **Memory Efficient**: Processes documents without loading entire content
- **Fast Processing**: Optimized for quick extraction
- **Scalable**: Handles documents of various sizes

## Requirements Met
✅ PDF text extraction and processing  
✅ Hierarchical outline generation  
✅ JSON output format  
✅ Docker containerization (AMD64)  
✅ Error handling and logging  
✅ Multilingual support  
✅ Performance optimization  

## Usage
The solution is designed to run in a Docker container with input/output directories as specified in the challenge requirements.
