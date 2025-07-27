#!/usr/bin/env python3
"""
PDF Outline Extractor for Round 1A
Extracts structured outlines (title and headings) from PDF documents
"""

import os
import json
import re
from pathlib import Path
import fitz  # PyMuPDF
from typing import List, Dict, Any, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFOutlineExtractor:
    def __init__(self):
        self.heading_patterns = [
            # English patterns
            r'^(?:Chapter|CHAPTER)\s+\d+',
            r'^(?:Section|SECTION)\s+\d+',
            r'^\d+\.?\s+[A-Z\u00C0-\u017F][^.]*$',  # Unicode support for accented chars
            r'^\d+\.\d+\.?\s+[A-Z\u00C0-\u017F][^.]*$',
            r'^\d+\.\d+\.\d+\.?\s+[A-Z\u00C0-\u017F][^.]*$',
            r'^[A-Z\u00C0-\u017F][A-Z\s\u00C0-\u017F]{2,}$',  # ALL CAPS headers with unicode
            r'^[A-Z\u00C0-\u017F][a-z\u00C0-\u017F].*[^.]$',  # Title case without period
            # Multilingual patterns (Japanese, Chinese, etc.)
            r'^第\d+章',  # Japanese chapter
            r'^第\d+节',  # Chinese section
            r'^\d+[．.]\s*[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]+',  # CJK with numbers
        ]
        
    def extract_title(self, doc: fitz.Document) -> str:
        """Extract document title from metadata or first page"""
        # Try metadata first
        metadata = doc.metadata
        if metadata and metadata.get('title'):
            title = metadata['title'].strip()
            if title and len(title) < 200:  # Reasonable title length
                return title
        
        # Try first page content
        if len(doc) > 0:
            first_page = doc[0]
            text = first_page.get_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Look for title-like text in first few lines
            for i, line in enumerate(lines[:5]):
                if len(line) > 5 and len(line) < 100:
                    # Check if it looks like a title (not too long, meaningful)
                    if not re.match(r'^\d+$', line) and not line.lower().startswith('page'):
                        return line
        
        return "Untitled Document"
    
    def analyze_text_style(self, page: fitz.Page, text_dict: Dict) -> Dict[str, Any]:
        """Analyze text styling to determine heading levels"""
        style_info = {}
        
        # Get font size and style information
        try:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                font_size = span["size"]
                                font_flags = span["flags"]
                                
                                # Store style information
                                if text not in style_info:
                                    style_info[text] = {
                                        'font_size': font_size,
                                        'is_bold': bool(font_flags & 2**4),
                                        'is_italic': bool(font_flags & 2**1),
                                    }
        except Exception as e:
            logger.warning(f"Error analyzing text style: {e}")
        
        return style_info
    
    def classify_heading_level(self, text: str, font_size: float, is_bold: bool, 
                             avg_font_size: float, max_font_size: float) -> str:
        """Classify text as H1, H2, or H3 based on styling and patterns"""
        
        # Pattern-based classification with multilingual support
        if re.match(r'^(?:Chapter|CHAPTER|第\d+章)\s*\d*', text):
            return "H1"
        
        if re.match(r'^(?:Section|SECTION|第\d+节)\s*\d*', text):
            return "H1"
        
        if re.match(r'^\d+[．.]?\s+[A-Z\u00C0-\u017F\u4e00-\u9fff]', text):
            return "H1"
        
        if re.match(r'^\d+\.\d+[．.]?\s+[A-Z\u00C0-\u017F\u4e00-\u9fff]', text):
            return "H2"
        
        if re.match(r'^\d+\.\d+\.\d+[．.]?\s+[A-Z\u00C0-\u017F\u4e00-\u9fff]', text):
            return "H3"
        
        # Size-based classification with improved thresholds
        size_ratio = font_size / avg_font_size if avg_font_size > 0 else 1
        
        # More sophisticated size analysis
        if size_ratio >= 1.8 or font_size >= max_font_size * 0.95:
            return "H1"
        elif size_ratio >= 1.4 or (is_bold and size_ratio >= 1.2):
            return "H2"
        elif size_ratio >= 1.15 or (is_bold and size_ratio >= 1.05):
            return "H3"
        
        # Check for ALL CAPS (often headings)
        if text.isupper() and len(text) > 5 and len(text) < 60:
            if size_ratio >= 1.1:
                return "H2"
            else:
                return "H3"
        
        return None
    
    def extract_headings(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract headings from PDF document"""
        headings = []
        
        # Collect all text with styling information
        all_text_info = []
        font_sizes = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            style_info = self.analyze_text_style(page, {})
            
            # Get text blocks
            try:
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = ""
                            line_font_size = 0
                            line_is_bold = False
                            
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text:
                                    line_text += text + " "
                                    line_font_size = max(line_font_size, span["size"])
                                    line_is_bold = line_is_bold or bool(span["flags"] & 2**4)
                            
                            line_text = line_text.strip()
                            if line_text and len(line_text) > 3:
                                all_text_info.append({
                                    'text': line_text,
                                    'page': page_num + 1,
                                    'font_size': line_font_size,
                                    'is_bold': line_is_bold
                                })
                                font_sizes.append(line_font_size)
                                
            except Exception as e:
                logger.warning(f"Error processing page {page_num + 1}: {e}")
                continue
        
        if not font_sizes:
            return headings
        
        avg_font_size = sum(font_sizes) / len(font_sizes)
        max_font_size = max(font_sizes)
        
        # Classify headings
        for text_info in all_text_info:
            text = text_info['text']
            
            # Skip very long lines (likely body text)
            if len(text) > 150:
                continue
            
            # Skip lines that look like body text
            if text.endswith('.') and len(text) > 50:
                continue
            
            # Check if it matches heading patterns
            is_heading = False
            for pattern in self.heading_patterns:
                if re.match(pattern, text):
                    is_heading = True
                    break
            
            # Check styling-based heading classification
            level = self.classify_heading_level(
                text, 
                text_info['font_size'], 
                text_info['is_bold'],
                avg_font_size, 
                max_font_size
            )
            
            if is_heading or level:
                if not level:
                    # Default level if pattern matched but no style-based level
                    if re.match(r'^\d+\.?\s+', text):
                        level = "H1"
                    elif re.match(r'^\d+\.\d+\.?\s+', text):
                        level = "H2"
                    else:
                        level = "H1"
                
                # Avoid duplicates
                if not any(h['text'] == text and h['page'] == text_info['page'] for h in headings):
                    headings.append({
                        'level': level,
                        'text': text,
                        'page': text_info['page']
                    })
        
        # Sort by page number
        headings.sort(key=lambda x: x['page'])
        
        return headings
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF file and extract outline"""
        try:
            doc = fitz.open(pdf_path)
            
            # Extract title
            title = self.extract_title(doc)
            
            # Extract headings
            outline = self.extract_headings(doc)
            
            doc.close()
            
            result = {
                "title": title,
                "outline": outline
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return {
                "title": "Error Processing Document",
                "outline": []
            }

def main():
    """Main function to process PDFs from input directory"""
    logger.info("🚀 Starting PDF Outline Extractor")
    
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    logger.info(f"📁 Input directory: {input_dir}")
    logger.info(f"📁 Output directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("✅ Output directory ready")
    
    extractor = PDFOutlineExtractor()
    logger.info("✅ PDF extractor initialized")
    
    # Process all PDF files in input directory
    pdf_files = list(input_dir.glob("*.pdf"))
    logger.info(f"🔍 Found {len(pdf_files)} PDF file(s)")
    
    if not pdf_files:
        logger.warning("❌ No PDF files found in input directory")
        logger.info("💡 Place PDF files in /app/input directory")
        return
    
    for pdf_file in pdf_files:
        logger.info(f"📄 Processing {pdf_file.name}")
        
        try:
            # Extract outline
            result = extractor.process_pdf(str(pdf_file))
            
            # Save result
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved outline to {output_file}")
            logger.info(f"   📊 Title: {result['title']}")
            logger.info(f"   📋 Found {len(result['outline'])} headings")
            
        except Exception as e:
            logger.error(f"❌ Error processing {pdf_file.name}: {e}")
    
    logger.info("🎉 Processing complete!")

if __name__ == "__main__":
    main()
