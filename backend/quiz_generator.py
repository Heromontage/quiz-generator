from typing import List, Dict
import random
import json
import re

class QuizGenerator:
    """Generate quiz questions using simple NLP techniques"""
    
    def __init__(self):
        """Initialize quiz generator"""
        print("Quiz Generator initialized (using lightweight approach)")
    
    def generate(
        self,
        text: str,
        num_questions: int = 10,
        difficulty: str = "medium",
        question_types: List[str] = None,
        include_explanations: bool = True
    ) -> List[Dict]:
        """
        Generate quiz questions from text
        
        Args:
            text: Source text for quiz
            num_questions: Number of questions to generate
            difficulty: Difficulty level
            question_types: Types of questions to generate
            include_explanations: Include explanations
        
        Returns:
            List of quiz questions
        """
        if question_types is None:
            question_types = ["mcq", "truefalse", "shortanswer", "fillintheblank"]
        
        # Clean and prepare text
        text = self._preprocess_text(text)
        
        # Split text into chunks for question generation
        chunks = self._split_into_chunks(text, chunk_size=500)
        
        quiz = []
        question_count = 0
        
        for chunk in chunks:
            if question_count >= num_questions:
                break
            
            # Determine question type
            question_type = random.choice(question_types)
            
            # Generate question based on type
            if question_type in ["mcq", "multiple_choice"]:
                question = self._generate_mcq(chunk, difficulty, include_explanations)
            elif question_type in ["truefalse", "true_false"]:
                question = self._generate_truefalse(chunk, difficulty, include_explanations)
            elif question_type in ["shortanswer", "short_answer"]:
                question = self._generate_shortanswer(chunk, difficulty, include_explanations)
            elif question_type in ["fillintheblank", "fill_in_the_blank"]:
                question = self._generate_fillintheblank(chunk, difficulty, include_explanations)
            else:
                continue
            
            if question:
                quiz.append(question)
                question_count += 1
        
        return quiz
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better question generation"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        return text.strip()
    
    def _split_into_chunks(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_mcq(self, text: str, difficulty: str, include_explanations: bool) -> Dict:
        """Generate multiple choice question"""
        try:
            # Extract sentences
            sentences = text.split('. ')
            if len(sentences) < 2:
                return None
            
            # Pick a sentence to base question on
            sentence = sentences[0]
            words = sentence.split()
            
            if len(words) < 5:
                return None
            
            # Select a key word
            key_word_index = random.randint(1, len(words) - 2)
            key_word = words[key_word_index]
            
            # Create question
            question_text = f"Which word best relates to '{key_word}' in the context: {sentence[:100]}...?"
            
            # Generate options
            options = [key_word, "Unknown", "Not mentioned", "Different concept"]
            random.shuffle(options)
            
            correct_index = options.index(key_word)
            
            return {
                "type": "multiple_choice",
                "question": question_text,
                "options": options,
                "correct_answer": key_word,
                "explanation": sentence[:150] if include_explanations else None
            }
        except Exception as e:
            print(f"Error generating MCQ: {str(e)}")
            return None
    
    def _generate_truefalse(self, text: str, difficulty: str, include_explanations: bool) -> Dict:
        """Generate true/false question"""
        try:
            sentences = text.split('. ')
            if not sentences[0]:
                return None
            
            sentence = sentences[0]
            
            # Create a statement and decide if true or false
            correct_answer = random.choice(['true', 'false'])
            
            if correct_answer == 'true':
                question_text = f"True or False: {sentence}"
            else:
                # Modify sentence slightly to make it false
                words = sentence.split()
                if len(words) > 3:
                    words[0] = "NOT " + words[0]
                question_text = f"True or False: {' '.join(words)}"
            
            return {
                "type": "true_false",
                "question": question_text,
                "correct_answer": correct_answer,
                "explanation": sentence[:150] if include_explanations else None
            }
        except Exception as e:
            print(f"Error generating True/False: {str(e)}")
            return None
    
    def _generate_shortanswer(self, text: str, difficulty: str, include_explanations: bool) -> Dict:
        """Generate short answer question"""
        try:
            sentences = text.split('. ')
            if not sentences:
                return None
            
            sentence = sentences[0]
            
            # Extract key word as answer
            words = [w for w in sentence.split() if len(w) > 4]
            if not words:
                return None
            
            correct_answer = random.choice(words)
            question_text = f"What is a key term mentioned in: '{sentence[:80]}...'?"
            
            return {
                "type": "short_answer",
                "question": question_text,
                "correct_answer": correct_answer,
                "explanation": sentence[:150] if include_explanations else None
            }
        except Exception as e:
            print(f"Error generating Short Answer: {str(e)}")
            return None
    
    def _generate_fillintheblank(self, text: str, difficulty: str, include_explanations: bool) -> Dict:
        """Generate fill in the blank question"""
        try:
            sentences = text.split('. ')
            if not sentences:
                return None
            
            sentence = sentences[0]
            words = sentence.split()
            
            if len(words) < 5:
                return None
            
            # Select a word to blank out
            blank_index = random.randint(1, len(words) - 2)
            blank_word = words[blank_index]
            
            # Create sentence with blank
            question_words = words[:blank_index] + ['_____'] + words[blank_index + 1:]
            question_text = ' '.join(question_words)
            
            # Generate options
            options = [blank_word, "Nothing", "Something", "Anything"]
            random.shuffle(options)
            
            return {
                "type": "fill_in_the_blank",
                "question": question_text,
                "options": options,
                "correct_answer": blank_word,
                "explanation": sentence[:150] if include_explanations else None
            }
        except Exception as e:
            print(f"Error generating Fill in the Blank: {str(e)}")
            return None