import re
import string
from typing import List, Dict, Tuple
import json
from datetime import datetime

class TextUtils:
    """Utility functions for text processing"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text to clean
        
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\"]', '', text)
        return text.strip()
    
    @staticmethod
    def remove_urls(text: str) -> str:
        """Remove URLs from text"""
        return re.sub(r'http\S+|www\S+', '', text)
    
    @staticmethod
    def remove_emails(text: str) -> str:
        """Remove email addresses from text"""
        return re.sub(r'\S+@\S+', '', text)
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """
        Extract sentences from text
        
        Args:
            text: Source text
        
        Returns:
            List of sentences
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def extract_key_phrases(text: str, num_phrases: int = 5) -> List[str]:
        """
        Extract key phrases from text
        
        Args:
            text: Source text
            num_phrases: Number of phrases to extract
        
        Returns:
            List of key phrases
        """
        # Split into words and filter by length
        words = text.split()
        # Simple heuristic: longer words are often key terms
        words = [w for w in words if len(w) > 4 and w not in TextUtils.get_stopwords()]
        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in words:
            if word.lower() not in seen:
                unique_words.append(word)
                seen.add(word.lower())
        
        return unique_words[:num_phrases]
    
    @staticmethod
    def get_stopwords() -> set:
        """Get common stopwords"""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'it', 'its', 'that', 'this', 'these', 'those', 'as', 'if', 'which'
        }
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 500) -> str:
        """
        Truncate text to maximum length
        
        Args:
            text: Text to truncate
            max_length: Maximum length
        
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'


class QuestionUtils:
    """Utility functions for question generation"""
    
    @staticmethod
    def validate_question(question: Dict) -> Tuple[bool, List[str]]:
        """
        Validate a generated question
        
        Args:
            question: Question dictionary
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if 'type' not in question:
            errors.append("Question missing 'type' field")
        if 'question' not in question:
            errors.append("Question missing 'question' field")
        
        # Validate question text
        if not question.get('question', '').strip():
            errors.append("Question text is empty")
        
        # Validate based on type
        question_type = question.get('type', '')
        
        if question_type == 'multiple_choice':
            if 'options' not in question or len(question['options']) < 2:
                errors.append("MCQ must have at least 2 options")
            if 'correct_answer' not in question:
                errors.append("MCQ must have correct_answer")
        
        elif question_type == 'true_false':
            if question.get('correct_answer') not in ['true', 'false']:
                errors.append("True/False question must have correct_answer as 'true' or 'false'")
        
        elif question_type == 'short_answer':
            if not question.get('correct_answer', '').strip():
                errors.append("Short answer must have correct_answer")
        
        elif question_type == 'fill_in_the_blank':
            if 'options' not in question or len(question['options']) < 2:
                errors.append("Fill in the blank must have at least 2 options")
            if 'correct_answer' not in question:
                errors.append("Fill in the blank must have correct_answer")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def format_question(question: Dict) -> Dict:
        """
        Format and clean a question dictionary
        
        Args:
            question: Raw question
        
        Returns:
            Formatted question
        """
        formatted = {
            'type': question.get('type', '').lower(),
            'question': TextUtils.clean_text(question.get('question', '')),
            'correct_answer': question.get('correct_answer', ''),
        }
        
        # Add optional fields
        if 'options' in question:
            formatted['options'] = [TextUtils.clean_text(opt) for opt in question['options']]
        
        if 'explanation' in question:
            formatted['explanation'] = TextUtils.truncate_text(question.get('explanation', ''), 200)
        
        return formatted
    
    @staticmethod
    def calculate_difficulty_score(question: Dict) -> float:
        """
        Calculate difficulty score (0-1) for a question
        
        Args:
            question: Question dictionary
        
        Returns:
            Difficulty score
        """
        score = 0.0
        
        # Length of question affects difficulty
        question_length = len(question.get('question', '').split())
        if question_length < 10:
            score += 0.1
        elif question_length > 30:
            score += 0.3
        else:
            score += 0.2
        
        # Type affects difficulty
        question_type = question.get('type', '')
        type_difficulty = {
            'true_false': 0.1,
            'fill_in_the_blank': 0.2,
            'short_answer': 0.3,
            'multiple_choice': 0.2
        }
        score += type_difficulty.get(question_type, 0.2)
        
        # Number of options affects difficulty
        num_options = len(question.get('options', []))
        score += min(num_options * 0.1, 0.3)
        
        return min(score / 3, 1.0)
    
    @staticmethod
    def shuffle_options(question: Dict) -> Dict:
        """
        Shuffle options while tracking correct answer
        
        Args:
            question: Question with options
        
        Returns:
            Question with shuffled options
        """
        if 'options' not in question:
            return question
        
        import random
        
        correct_answer = question.get('correct_answer', '')
        options = question.get('options', [])
        
        # Create mapping of original positions
        indexed_options = list(enumerate(options))
        random.shuffle(indexed_options)
        
        shuffled_options = [opt for _, opt in indexed_options]
        new_correct_index = shuffled_options.index(correct_answer)
        
        question['options'] = shuffled_options
        question['correct_answer_index'] = new_correct_index
        
        return question


class FileUtils:
    """Utility functions for file handling"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'doc'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension"""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Check if file extension is allowed"""
        return FileUtils.get_file_extension(filename) in FileUtils.ALLOWED_EXTENSIONS
    
    @staticmethod
    def is_file_size_valid(file_size: int) -> bool:
        """Check if file size is within limits"""
        return file_size <= FileUtils.MAX_FILE_SIZE
    
    @staticmethod
    def get_file_size_mb(file_size: int) -> float:
        """Convert file size to MB"""
        return round(file_size / (1024 * 1024), 2)
    
    @staticmethod
    def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate file
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not FileUtils.is_allowed_file(filename):
            return False, f"File type not allowed. Allowed types: {', '.join(FileUtils.ALLOWED_EXTENSIONS)}"
        
        if not FileUtils.is_file_size_valid(file_size):
            return False, f"File size exceeds limit. Max size: {FileUtils.get_file_size_mb(FileUtils.MAX_FILE_SIZE)}MB"
        
        return True, ""


class ValidationUtils:
    """Utility functions for input validation"""
    
    @staticmethod
    def validate_question_count(count: int, min_count: int = 3, max_count: int = 50) -> Tuple[bool, str]:
        """
        Validate question count
        
        Args:
            count: Number of questions
            min_count: Minimum questions
            max_count: Maximum questions
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(count, int):
            return False, "Question count must be an integer"
        
        if count < min_count:
            return False, f"Question count must be at least {min_count}"
        
        if count > max_count:
            return False, f"Question count cannot exceed {max_count}"
        
        return True, ""
    
    @staticmethod
    def validate_difficulty(difficulty: str) -> Tuple[bool, str]:
        """
        Validate difficulty level
        
        Args:
            difficulty: Difficulty level
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_difficulties = {'easy', 'medium', 'hard'}
        
        if difficulty.lower() not in valid_difficulties:
            return False, f"Difficulty must be one of: {', '.join(valid_difficulties)}"
        
        return True, ""
    
    @staticmethod
    def validate_question_types(question_types: List[str]) -> Tuple[bool, str]:
        """
        Validate question types
        
        Args:
            question_types: List of question types
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_types = {'mcq', 'truefalse', 'shortanswer', 'fillintheblank', 'multiple_choice', 'true_false', 'short_answer', 'fill_in_the_blank'}
        
        if not question_types:
            return False, "At least one question type must be selected"
        
        for qtype in question_types:
            if qtype.lower() not in valid_types:
                return False, f"Invalid question type: {qtype}"
        
        return True, ""


class LoggingUtils:
    """Utility functions for logging"""
    
    @staticmethod
    def log_quiz_generation(
        num_files: int,
        num_questions: int,
        difficulty: str,
        question_types: List[str],
        duration_seconds: float
    ) -> Dict:
        """
        Create a log entry for quiz generation
        
        Args:
            num_files: Number of files processed
            num_questions: Number of questions generated
            difficulty: Difficulty level
            question_types: Types of questions
            duration_seconds: Time taken
        
        Returns:
            Log dictionary
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'num_files': num_files,
            'num_questions': num_questions,
            'difficulty': difficulty,
            'question_types': question_types,
            'duration_seconds': round(duration_seconds, 2),
            'status': 'success'
        }
    
    @staticmethod
    def log_error(error_message: str, context: Dict = None) -> Dict:
        """
        Create a log entry for errors
        
        Args:
            error_message: Error message
            context: Additional context
        
        Returns:
            Log dictionary
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': error_message
        }
        
        if context:
            log_entry['context'] = context
        
        return log_entry


class ExportUtils:
    """Utility functions for exporting quiz data"""
    
    @staticmethod
    def export_to_json(quiz: List[Dict]) -> str:
        """Export quiz to JSON format"""
        return json.dumps(quiz, indent=2)
    
    @staticmethod
    def export_to_csv(quiz: List[Dict]) -> str:
        """Export quiz to CSV format"""
        if not quiz:
            return ""
        
        import csv
        from io import StringIO
        
        output = StringIO()
        
        # Get all possible keys
        fieldnames = set()
        for question in quiz:
            fieldnames.update(question.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for question in quiz:
            # Convert lists to strings
            row = {}
            for key, value in question.items():
                if isinstance(value, list):
                    row[key] = ', '.join(str(v) for v in value)
                else:
                    row[key] = value
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_to_html(quiz: List[Dict]) -> str:
        """Export quiz to HTML format"""
        html = """
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .question { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                .question-text { font-weight: bold; margin-bottom: 10px; }
                .options { margin-left: 20px; }
                .option { margin: 5px 0; }
                .explanation { background-color: #f0f0f0; padding: 10px; margin-top: 10px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>Quiz</h1>
        """
        
        for i, question in enumerate(quiz, 1):
            html += f"""
            <div class="question">
                <div class="question-text">Question {i}: {question.get('question', '')}</div>
                <div class="type">Type: {question.get('type', '')}</div>
            """
            
            if 'options' in question:
                html += '<div class="options">'
                for option in question['options']:
                    html += f'<div class="option">- {option}</div>'
                html += '</div>'
            
            if 'explanation' in question:
                html += f'<div class="explanation"><strong>Explanation:</strong> {question["explanation"]}</div>'
            
            html += '</div>'
        
        html += """
        </body>
        </html>
        """
        
        return html