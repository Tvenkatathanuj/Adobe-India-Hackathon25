# Challenge 1B - Persona-Driven Document Intelligence

## Overview
This solution performs intelligent document analysis based on user personas and job-to-be-done, extracting and prioritizing relevant sections using advanced relevance scoring.

## Solution Components

### Core Files
- **`main.py`** - Main document intelligence implementation
- **`requirements.txt`** - Python dependencies (PyMuPDF)
- **`Dockerfile`** - Container configuration with AMD64 platform
- **`approach_explanation.md`** - Detailed methodology explanation (required)

### Key Features
- **Persona-Driven Analysis**: Tailored content extraction based on user profiles
- **Relevance Scoring**: Advanced keyword-based scoring algorithm
- **Section Prioritization**: Intelligent ranking of document sections
- **Subsection Analysis**: Granular content breakdown
- **Multi-Document Processing**: Handles multiple PDF inputs simultaneously

## Technical Implementation

### Persona Recognition
- Supports multiple persona types: researcher, student, analyst, journalist, entrepreneur, salesperson
- Dynamic persona detection from text descriptions
- Keyword mapping for different professional roles

### Job-to-be-Done Mapping
- Literature review, financial analysis, exam preparation, market analysis, technical review
- Job-specific keyword weighting and scoring
- Context-aware content prioritization

### Relevance Scoring Algorithm
- **Keyword Matching**: Persona and job-specific keyword detection
- **Frequency Analysis**: Weighted term frequency scoring
- **Normalization**: Length-normalized scores to prevent bias
- **Mathematical Model**: Logarithmic scaling for optimal results

### Content Extraction
- **Section Detection**: Intelligent heading and section identification
- **Subsection Analysis**: Granular content breakdown
- **Text Refinement**: Clean, structured output generation
- **Ranking System**: Importance-based section ordering

## Output Format
```json
{
  "metadata": {
    "persona": "User persona description",
    "job_to_be_done": "Specific task description",
    "total_documents": 3,
    "processing_timestamp": "2025-01-XX"
  },
  "extracted_sections": [
    {
      "document": "filename.pdf",
      "page_number": 1,
      "section_title": "Section Title",
      "importance_rank": 1,
      "relevance_score": 8.5,
      "subsections": [...]
    }
  ],
  "subsection_analysis": [...]
}
```

## Algorithm Highlights

### Scoring Methodology
1. **Persona Keywords**: Role-specific term identification
2. **Job Keywords**: Task-specific term weighting (1.5x multiplier)
3. **Context Analysis**: Job description term extraction
4. **Length Normalization**: Logarithmic scaling to prevent bias

### Performance Optimization
- **Efficient Processing**: Batch document processing
- **Memory Management**: Streaming text extraction
- **Scalable Architecture**: Handles large document sets

## Requirements Met
✅ Persona-driven document analysis  
✅ Job-to-be-done based prioritization  
✅ Relevance scoring and ranking  
✅ Section and subsection extraction  
✅ JSON output format compliance  
✅ Multi-document processing  
✅ Docker containerization (AMD64)  
✅ Methodology documentation  
✅ Performance optimization  

## Methodology
Detailed explanation of the approach, algorithms, and decision-making process can be found in `approach_explanation.md` as required by the challenge specifications.

## Usage
The solution processes persona.txt, job.txt, and PDF documents from the input directory, generating comprehensive analysis results in the specified JSON format.
