#!/usr/bin/env python3
"""
Persona-Driven Document Intelligence for Round 1B
Extracts and prioritizes relevant sections from documents based on persona and job-to-be-done
"""

import os
import json
import re
import datetime
from pathlib import Path
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
import logging
from collections import defaultdict
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentIntelligenceExtractor:
    def __init__(self):
        # Keywords for different domains and personas
        self.persona_keywords = {
            'researcher': ['research', 'methodology', 'analysis', 'study', 'experiment', 'data', 'results', 'conclusion'],
            'student': ['learn', 'understand', 'concept', 'definition', 'example', 'practice', 'exam', 'study'],
            'analyst': ['analysis', 'trend', 'performance', 'metrics', 'revenue', 'growth', 'market', 'financial'],
            'journalist': ['news', 'event', 'report', 'source', 'fact', 'interview', 'story', 'investigation'],
            'entrepreneur': ['business', 'opportunity', 'market', 'strategy', 'innovation', 'profit', 'customer'],
            'salesperson': ['sales', 'customer', 'product', 'benefit', 'price', 'deal', 'revenue', 'target']
        }
        
        self.job_keywords = {
            'literature_review': ['literature', 'review', 'survey', 'overview', 'comparison', 'methodology'],
            'financial_analysis': ['financial', 'revenue', 'profit', 'cost', 'investment', 'ROI', 'budget'],
            'exam_preparation': ['key', 'important', 'concept', 'definition', 'formula', 'example', 'practice'],
            'market_analysis': ['market', 'competition', 'trend', 'analysis', 'share', 'position', 'strategy'],
            'technical_review': ['technical', 'implementation', 'algorithm', 'method', 'approach', 'performance']
        }
        
    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract structured text from PDF with page and section information"""
        doc_data = {
            'title': '',
            'sections': [],
            'full_text': '',
            'page_count': 0
        }
        
        try:
            doc = fitz.open(pdf_path)
            doc_data['page_count'] = len(doc)
            
            # Extract title (similar to Round 1A)
            if len(doc) > 0:
                first_page = doc[0]
                text = first_page.get_text()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                
                for line in lines[:5]:
                    if len(line) > 10 and len(line) < 100:
                        if not re.match(r'^\d+$', line) and not line.lower().startswith('page'):
                            doc_data['title'] = line
                            break
                
                if not doc_data['title']:
                    doc_data['title'] = Path(pdf_path).stem
            
            # Extract sections with content
            current_section = None
            section_content = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Split into paragraphs
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                
                for paragraph in paragraphs:
                    # Check if this looks like a heading
                    if self._is_heading(paragraph):
                        # Save previous section
                        if current_section and section_content:
                            doc_data['sections'].append({
                                'title': current_section,
                                'content': ' '.join(section_content),
                                'page': page_num + 1,
                                'word_count': len(' '.join(section_content).split())
                            })
                        
                        # Start new section
                        current_section = paragraph[:200]  # Limit heading length
                        section_content = []
                    else:
                        # Add to current section content
                        if len(paragraph) > 20:  # Ignore very short paragraphs
                            section_content.append(paragraph)
                            doc_data['full_text'] += paragraph + ' '
            
            # Add final section
            if current_section and section_content:
                doc_data['sections'].append({
                    'title': current_section,
                    'content': ' '.join(section_content),
                    'page': len(doc),
                    'word_count': len(' '.join(section_content).split())
                })
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting from {pdf_path}: {e}")
        
        return doc_data
    
    def _is_heading(self, text: str) -> bool:
        """Determine if text looks like a heading"""
        # Common heading patterns
        heading_patterns = [
            r'^\d+\.?\s+[A-Z]',  # "1. Introduction"
            r'^[A-Z][A-Z\s]{5,}$',  # "INTRODUCTION"
            r'^Chapter\s+\d+',  # "Chapter 1"
            r'^Section\s+\d+',  # "Section 1"
            r'^\d+\.\d+\.?\s+[A-Z]',  # "1.1 Background"
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, text):
                return True
        
        # Check if it's short and looks like a title
        if (len(text) < 100 and 
            not text.endswith('.') and 
            len(text.split()) < 15 and
            text[0].isupper()):
            return True
        
        return False
    
    def calculate_relevance_score(self, text: str, persona: str, job: str) -> float:
        """Calculate relevance score based on persona and job keywords"""
        text_lower = text.lower()
        score = 0.0
        
        # Extract persona type from description
        persona_type = self._extract_persona_type(persona.lower())
        job_type = self._extract_job_type(job.lower())
        
        # Score based on persona keywords
        if persona_type in self.persona_keywords:
            for keyword in self.persona_keywords[persona_type]:
                count = text_lower.count(keyword)
                score += count * 1.0
        
        # Score based on job keywords
        if job_type in self.job_keywords:
            for keyword in self.job_keywords[job_type]:
                count = text_lower.count(keyword)
                score += count * 1.5  # Job keywords weighted higher
        
        # Additional scoring based on specific job requirements
        job_specific_score = self._calculate_job_specific_score(text_lower, job.lower())
        score += job_specific_score
        
        # Normalize by text length (prevent bias toward longer texts)
        word_count = len(text.split())
        if word_count > 0:
            score = score / math.log(word_count + 1)
        
        return score
    
    def _extract_persona_type(self, persona: str) -> str:
        """Extract persona type from description"""
        for persona_type in self.persona_keywords.keys():
            if persona_type in persona:
                return persona_type
        
        # Fallback mappings
        if 'phd' in persona or 'research' in persona:
            return 'researcher'
        elif 'student' in persona or 'undergraduate' in persona:
            return 'student'
        elif 'analyst' in persona or 'investment' in persona:
            return 'analyst'
        elif 'journalist' in persona or 'reporter' in persona:
            return 'journalist'
        elif 'entrepreneur' in persona or 'business' in persona:
            return 'entrepreneur'
        elif 'sales' in persona:
            return 'salesperson'
        
        return 'researcher'  # Default
    
    def _extract_job_type(self, job: str) -> str:
        """Extract job type from description"""
        if 'literature review' in job or 'survey' in job:
            return 'literature_review'
        elif 'financial' in job or 'revenue' in job or 'investment' in job:
            return 'financial_analysis'
        elif 'exam' in job or 'study' in job or 'preparation' in job:
            return 'exam_preparation'
        elif 'market' in job or 'competition' in job:
            return 'market_analysis'
        elif 'technical' in job or 'algorithm' in job or 'method' in job:
            return 'technical_review'
        
        return 'literature_review'  # Default
    
    def _calculate_job_specific_score(self, text: str, job: str) -> float:
        """Calculate additional score based on specific job requirements"""
        score = 0.0
        
        # Look for specific terms mentioned in the job description
        job_words = job.split()
        for word in job_words:
            if len(word) > 3 and word not in ['the', 'and', 'for', 'with', 'from']:
                count = text.count(word)
                score += count * 0.5
        
        return score
    
    def extract_subsections(self, section_content: str, max_subsections: int = 3) -> List[Dict[str, Any]]:
        """Extract important subsections from section content"""
        # Split content into sentences
        sentences = re.split(r'[.!?]+', section_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Group sentences into subsections (every 2-3 sentences)
        subsections = []
        current_subsection = []
        
        for i, sentence in enumerate(sentences):
            current_subsection.append(sentence)
            
            if len(current_subsection) >= 2 or i == len(sentences) - 1:
                if current_subsection:
                    subsection_text = '. '.join(current_subsection) + '.'
                    subsections.append({
                        'refined_text': subsection_text,
                        'sentence_count': len(current_subsection),
                        'word_count': len(subsection_text.split())
                    })
                current_subsection = []
        
        # Return top subsections (limit to max_subsections)
        return subsections[:max_subsections]
    
    def process_documents(self, input_dir: Path, persona: str, job: str) -> Dict[str, Any]:
        """Process all documents and extract relevant sections"""
        logger.info(f"🔍 Processing documents for persona: {persona}")
        logger.info(f"🎯 Job to be done: {job}")
        
        # Extract text from all PDFs
        documents_data = []
        pdf_files = list(input_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            logger.info(f"📄 Extracting from {pdf_file.name}")
            doc_data = self.extract_text_from_pdf(str(pdf_file))
            doc_data['filename'] = pdf_file.name
            documents_data.append(doc_data)
        
        # Score and rank sections
        all_sections = []
        
        for doc_data in documents_data:
            for section in doc_data['sections']:
                relevance_score = self.calculate_relevance_score(
                    section['content'], persona, job
                )
                
                section_info = {
                    'document': doc_data['filename'],
                    'page_number': section['page'],
                    'section_title': section['title'],
                    'content': section['content'],
                    'relevance_score': relevance_score,
                    'word_count': section['word_count']
                }
                
                all_sections.append(section_info)
        
        # Sort by relevance score
        all_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Take top sections and add importance rank
        top_sections = all_sections[:10]  # Top 10 sections
        
        extracted_sections = []
        for i, section in enumerate(top_sections):
            # Extract subsections
            subsections = self.extract_subsections(section['content'])
            
            section_result = {
                'document': section['document'],
                'page_number': section['page_number'],
                'section_title': section['section_title'],
                'importance_rank': i + 1,
                'relevance_score': round(section['relevance_score'], 3),
                'subsections': []
            }
            
            # Add subsection analysis
            for j, subsection in enumerate(subsections):
                subsection_result = {
                    'document': section['document'],
                    'refined_text': subsection['refined_text'],
                    'page_number': section['page_number'],
                    'subsection_rank': j + 1
                }
                section_result['subsections'].append(subsection_result)
            
            extracted_sections.append(section_result)
        
        # Prepare final result
        result = {
            'metadata': {
                'input_documents': [doc['filename'] for doc in documents_data],
                'persona': persona,
                'job_to_be_done': job,
                'processing_timestamp': datetime.datetime.now().isoformat(),
                'total_documents': len(documents_data),
                'total_sections_analyzed': len(all_sections)
            },
            'extracted_sections': extracted_sections,
            'subsection_analysis': []
        }
        
        # Flatten subsections for the required format
        for section in extracted_sections:
            for subsection in section['subsections']:
                result['subsection_analysis'].append(subsection)
        
        return result

def main():
    """Main function to process documents based on persona and job"""
    logger.info("🚀 Starting Persona-Driven Document Intelligence")
    
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read persona and job from input files
    persona_file = input_dir / "persona.txt"
    job_file = input_dir / "job.txt"
    
    if not persona_file.exists() or not job_file.exists():
        logger.error("❌ Missing persona.txt or job.txt in input directory")
        logger.info("💡 Required files: persona.txt, job.txt, and PDF documents")
        return
    
    persona = persona_file.read_text(encoding='utf-8').strip()
    job = job_file.read_text(encoding='utf-8').strip()
    
    # Initialize extractor
    extractor = DocumentIntelligenceExtractor()
    
    # Process documents
    result = extractor.process_documents(input_dir, persona, job)
    
    # Save result
    output_file = output_dir / "analysis_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Analysis complete! Results saved to {output_file}")
    logger.info(f"📊 Processed {result['metadata']['total_documents']} documents")
    logger.info(f"📋 Found {len(result['extracted_sections'])} relevant sections")
    logger.info("🎉 Processing complete!")

if __name__ == "__main__":
    main()
