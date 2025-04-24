import pandas as pd
import json
import os
import docx
import csv
import io
import logging

logger = logging.getLogger(__name__)

def process_file(file_path):
    """
    Process uploaded files of various formats and extract content
    Returns a tuple of (content, file_type)
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        # Process based on file extension
        if file_extension in ['.csv']:
            return process_csv(file_path), 'csv'
        
        elif file_extension in ['.xlsx', '.xls']:
            return process_excel(file_path), 'excel'
        
        elif file_extension in ['.json']:
            return process_json(file_path), 'json'
        
        elif file_extension in ['.docx']:
            return process_docx(file_path), 'docx'
        
        elif file_extension in ['.txt']:
            return process_text(file_path), 'text'
        
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
            
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        raise ValueError(f"Error processing file: {str(e)}")

def process_csv(file_path):
    """Process CSV file and return a list of records"""
    try:
        # Try to read with pandas first
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except Exception as e:
        # Fallback to manual CSV processing if pandas fails
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            headers = next(csv_reader, None)
            
            if not headers:
                return []
            
            for row in csv_reader:
                if len(row) == len(headers):
                    record = {headers[i]: row[i] for i in range(len(headers))}
                    records.append(record)
        
        return records

def process_excel(file_path):
    """Process Excel file and return a list of records"""
    # Read the first sheet
    df = pd.read_excel(file_path)
    return df.to_dict('records')

def process_json(file_path):
    """Process JSON file and return its content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # If it's a simple JSON object, convert to list for consistent handling
    if isinstance(data, dict):
        return [data]
    return data

def process_docx(file_path):
    """Process DOCX file and extract text content"""
    doc = docx.Document(file_path)
    content = []
    
    for para in doc.paragraphs:
        if para.text.strip():  # Skip empty paragraphs
            content.append(para.text)
    
    # Handle as a single document
    return [{'text': '\n'.join(content)}]

def process_text(file_path):
    """Process plain text file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by lines and create records
    lines = content.strip().split('\n')
    
    # If content seems to be CSV format, try to parse it
    if ',' in lines[0]:
        try:
            reader = csv.reader(lines)
            headers = next(reader)
            records = []
            
            for row in reader:
                if len(row) == len(headers):
                    record = {headers[i]: row[i] for i in range(len(headers))}
                    records.append(record)
            
            return records
        except:
            pass  # If CSV parsing fails, continue with text processing
    
    # Handle as a single document
    return [{'text': content}]

def extract_text_from_records(records):
    """Extract text content from a list of records for analysis"""
    texts = []
    
    for record in records:
        # Look for known text fields with different naming conventions
        text_fields = ['text', 'content', 'message', 'feedback', 'description', 'comments']
        
        for field in text_fields:
            if field in record and record[field]:
                texts.append(str(record[field]))
                break
        else:
            # If no text field found, use all values concatenated
            texts.append(' '.join(str(value) for value in record.values() if value))
    
    return texts