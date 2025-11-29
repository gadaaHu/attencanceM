import pandas as pd
import numpy as np
from datetime import datetime
import json
import re

class ReportAnalyzer:
    def __init__(self):
        self.keywords = {
            'goals': ['goal', 'target', 'objective', 'aim', 'purpose'],
            'metrics': ['metric', 'kpi', 'measure', 'indicator', 'statistic'],
            'timeline': ['timeline', 'schedule', 'deadline', 'milestone'],
            'budget': ['budget', 'cost', 'expense', 'funding', 'financial'],
            'risk': ['risk', 'challenge', 'issue', 'problem', 'concern']
        }
    
    def analyze_document(self, file_path):
        """Analyze uploaded document for key information"""
        analysis = {
            'file_type': file_path.split('.')[-1].upper(),
            'analysis_date': datetime.now().isoformat(),
            'word_count': 0,
            'keyword_frequency': {},
            'detected_goals': [],
            'detected_metrics': [],
            'detected_timelines': [],
            'sentiment_score': 0,
            'readability_score': 0
        }
        
        try:
            if file_path.endswith('.csv'):
                content = self.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                content = self.read_excel(file_path)
            else:
                content = self.read_text_file(file_path)
            
            analysis['word_count'] = self.count_words(content)
            analysis['keyword_frequency'] = self.analyze_keywords(content)
            analysis['detected_goals'] = self.extract_goals(content)
            analysis['detected_metrics'] = self.extract_metrics(content)
            analysis['sentiment_score'] = self.analyze_sentiment(content)
            analysis['readability_score'] = self.calculate_readability(content)
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def read_csv(self, file_path):
        df = pd.read_csv(file_path)
        return df.to_string()
    
    def read_excel(self, file_path):
        df = pd.read_excel(file_path)
        return df.to_string()
    
    def read_text_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def count_words(self, text):
        words = re.findall(r'\b\w+\b', text.lower())
        return len(words)
    
    def analyze_keywords(self, text):
        keyword_freq = {}
        text_lower = text.lower()
        
        for category, words in self.keywords.items():
            freq = 0
            for word in words:
                freq += len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower))
            keyword_freq[category] = freq
        
        return keyword_freq
    
    def extract_goals(self, text):
        goals = []
        goal_patterns = [
            r'(?:goal|objective|target|aim)\s*[:\-]\s*([^.]+)',
            r'(?:achieve|accomplish|reach)\s+([^.]+)'
        ]
        
        for pattern in goal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            goals.extend(matches)
        
        return goals[:10]
    
    def extract_metrics(self, text):
        metrics = []
        metric_patterns = [
            r'(\d+%)',
            r'(\$\d+(?:,\d+)*(?:\.\d+)?)',
            r'(\d+(?:,\d+)*(?:\.\d+)?\s*(?:units|members|events|%)?)'
        ]
        
        for pattern in metric_patterns:
            matches = re.findall(pattern, text)
            metrics.extend(matches)
        
        return list(set(metrics))[:15]
    
    def analyze_sentiment(self, text):
        positive_words = ['success', 'achieve', 'growth', 'improve', 'positive', 'excellent', 'good']
        negative_words = ['challenge', 'risk', 'issue', 'problem', 'negative', 'poor', 'difficult']
        
        text_lower = text.lower()
        positive_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower)) for word in positive_words)
        negative_count = sum(len(re.findall(r'\b' + re.escape(word) + r'\b', text_lower)) for word in negative_words)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.5
        
        return positive_count / total
    
    def calculate_readability(self, text):
        sentences = re.split(r'[.!?]+', text)
        words = re.findall(r'\b\w+\b', text)
        
        if len(sentences) == 0 or len(words) == 0:
            return 0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        readability = 100 - (avg_sentence_length * 0.5 + avg_word_length * 10)
        return max(0, min(100, readability))

# Global instance
analyzer = ReportAnalyzer()

def analyze_document(file_path):
    return analyzer.analyze_document(file_path)