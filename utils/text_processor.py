import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import logging

# Setup NLTK resources on first run
def download_nltk_resources():
    """Download required NLTK resources if not already available"""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('punkt')
        nltk.download('stopwords')

# Download resources when module is imported
download_nltk_resources()

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """
    Handles text preprocessing including:
    - Cleaning and normalization
    - Stopword removal
    - Batching large datasets
    """
    
    def __init__(self):
        """
        Initialize the text preprocessor
        
        Args:
            stopwords: remove stopwords and to keep keywords
            batch_size: batch_size to process the text
        """
        self.batch_size = 200
        self.stop_words = set(stopwords.words("english"))
        
    def clean_text(self, text):
        """
        Clean and normalize text
        
        Args:
            text: Text string to clean
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
            
        # Convert to string if not already
        text = str(text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove special characters and numbers (keep letters, spaces, and basic punctuation)
        text = re.sub(r'[^\w\s.,!?]', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def remove_stop_words(self, text):
        """
        Remove stopwords from text
        
        Args:
            text: Text string to process
            
        Returns:
            Text string with stopwords removed
        """
        # Tokenize text
        word_tokens = word_tokenize(text)
        
        # Remove stopwords
        filtered_text = [word for word in word_tokens if word.lower() not in self.stop_words]
        
        # Join tokens back into string
        return ' '.join(filtered_text)
    
    def preprocess_text(self, text):
        """
        Apply full preprocessing pipeline to text
        
        Args:
            text: Text string to process
            
        Returns:
            Preprocessed text string
        """
        # Clean text
        cleaned_text = self.clean_text(text)
        
        # Remove stopwords if enabled
        cleaned_text = self.remove_stop_words(cleaned_text)
            
        return cleaned_text
    
    def preprocess_record(self, record):
        """
        Preprocess text fields in a record
        
        Args:
            record: Dictionary containing record data
            
        Returns:
            Record with preprocessed text fields
        """
        # Make a copy to avoid modifying original
        processed_record = record.copy()
        
        # Common text fields to process
        text_fields = ['text', 'content', 'message', 'feedback', 'description', 'comments']
        
        for field in text_fields:
            if field in processed_record and processed_record[field]:
                processed_record[field] = self.preprocess_text(processed_record[field])
                
        return processed_record
    
    def batch_records(self, records):
        """
        Split records into batches for processing
        
        Args:
            records: List of records to batch
            
        Returns:
            Generator yielding batches of records
        """
        for i in range(0, len(records), self.batch_size):
            yield records[i:i + self.batch_size]
    
    def preprocess_batch(self, records):
        """
        Preprocess a batch of records
        
        Args:
            records: List of records to preprocess
            
        Returns:
            List of preprocessed records
        """
        return [self.preprocess_record(record) for record in records]