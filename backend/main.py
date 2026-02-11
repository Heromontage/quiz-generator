from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import asyncio
from typing import List
import time
from document_processor import DocumentProcessor
from quiz_generator import QuizGenerator
from config import settings
from utils import ValidationUtils, FileUtils, LoggingUtils

app = FastAPI(title="Quiz Generator API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

document_processor = DocumentProcessor()
quiz_generator = QuizGenerator()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Quiz Generator API is running",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Quiz Generator API",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/api/generate-quiz")
async def generate_quiz(
    files: List[UploadFile] = File(...),
    question_count: int = Form(10),
    difficulty: str = Form("medium"),
    question_types: str = Form('["mcq", "truefalse", "shortanswer", "fillintheblank"]'),
    include_explanations: bool = Form(True)
):
    """
    Generate a quiz from uploaded documents
    
    Args:
        files: List of uploaded files (PDF, DOCX, TXT)
        question_count: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard)
        question_types: JSON string of question types
        include_explanations: Whether to include explanations
    
    Returns:
        Generated quiz with questions
    """
    start_time = time.time()
    
    try:
        # Validate question count
        is_valid, error_msg = ValidationUtils.validate_question_count(
            question_count,
            settings.MIN_QUESTION_COUNT,
            settings.MAX_QUESTION_COUNT
        )
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": error_msg}
            )
        
        # Validate difficulty
        is_valid, error_msg = ValidationUtils.validate_difficulty(difficulty)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": error_msg}
            )
        
        # Parse question types
        try:
            question_types_list = json.loads(question_types)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid JSON format for question_types"}
            )
        
        # Validate question types
        is_valid, error_msg = ValidationUtils.validate_question_types(question_types_list)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": error_msg}
            )
        
        # Validate files
        if not files or len(files) == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "At least one file must be uploaded"}
            )
        
        # Validate each file
        for file in files:
            is_valid, error_msg = FileUtils.validate_file(
                file.filename,
                len(await file.read()) if file.file else 0
            )
            if not is_valid:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"File '{file.filename}': {error_msg}"}
                )
            # Reset file pointer after reading
            await file.seek(0)
        
        # Extract text from all documents
        extracted_text = ""
        file_count = 0
        
        for file in files:
            try:
                content = await file.read()
                if not content:
                    continue
                
                text = document_processor.extract_text(content, file.filename)
                if text and text.strip():
                    extracted_text += f"\n\n{text}"
                    file_count += 1
            except Exception as e:
                print(f"Error processing file {file.filename}: {str(e)}")
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Error processing file '{file.filename}': {str(e)}"}
                )
        
        if not extracted_text.strip():
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract text from any of the uploaded files"}
            )
        
        # Generate quiz
        try:
            quiz = quiz_generator.generate(
                text=extracted_text,
                num_questions=question_count,
                difficulty=difficulty,
                question_types=question_types_list,
                include_explanations=include_explanations
            )
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": f"Error generating quiz: {str(e)}"}
            )
        
        if not quiz or len(quiz) == 0:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to generate any questions"}
            )
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the operation
        log_entry = LoggingUtils.log_quiz_generation(
            num_files=file_count,
            num_questions=len(quiz),
            difficulty=difficulty,
            question_types=question_types_list,
            duration_seconds=duration
        )
        print(f"Quiz generation log: {json.dumps(log_entry)}")
        
        return {
            "success": True,
            "quiz": quiz,
            "metadata": {
                "num_questions": len(quiz),
                "difficulty": difficulty,
                "question_types": question_types_list,
                "files_processed": file_count,
                "generation_time_seconds": round(duration, 2)
            }
        }
    
    except Exception as e:
        duration = time.time() - start_time
        error_log = LoggingUtils.log_error(
            str(e),
            context={
                "question_count": question_count,
                "difficulty": difficulty,
                "duration_seconds": round(duration, 2)
            }
        )
        print(f"Error log: {json.dumps(error_log)}")
        
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@app.post("/api/validate-answer")
async def validate_answer(
    question_id: int = Form(...),
    user_answer: str = Form(...),
    correct_answer: str = Form(...)
):
    """
    Validate user's answer
    
    Args:
        question_id: ID of the question
        user_answer: User's provided answer
        correct_answer: Correct answer
    
    Returns:
        Validation result
    """
    try:
        # Simple string comparison (case-insensitive)
        is_correct = user_answer.lower().strip() == correct_answer.lower().strip()
        
        return {
            "success": True,
            "question_id": question_id,
            "is_correct": is_correct,
            "user_answer": user_answer,
            "correct_answer": correct_answer
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/api/batch-validate-answers")
async def batch_validate_answers(request_body: dict):
    """
    Validate multiple answers at once
    
    Args:
        request_body: Dictionary with answers list
    
    Returns:
        List of validation results
    """
    try:
        answers = request_body.get("answers", [])
        results = []
        
        for answer in answers:
            is_correct = (
                answer.get("user_answer", "").lower().strip() == 
                answer.get("correct_answer", "").lower().strip()
            )
            results.append({
                "question_id": answer.get("question_id"),
                "is_correct": is_correct
            })
        
        return {
            "success": True,
            "total_questions": len(results),
            "correct_answers": sum(1 for r in results if r["is_correct"]),
            "results": results
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "supported_formats": list(FileUtils.ALLOWED_EXTENSIONS),
        "max_file_size_mb": FileUtils.get_file_size_mb(FileUtils.MAX_FILE_SIZE)
    }


@app.get("/api/difficulty-levels")
async def get_difficulty_levels():
    """Get available difficulty levels"""
    return {
        "difficulty_levels": ["easy", "medium", "hard"]
    }


@app.get("/api/question-types")
async def get_question_types():
    """Get available question types"""
    return {
        "question_types": [
            {
                "id": "mcq",
                "name": "Multiple Choice",
                "description": "Select one correct option from multiple choices"
            },
            {
                "id": "truefalse",
                "name": "True/False",
                "description": "Determine if statement is true or false"
            },
            {
                "id": "shortanswer",
                "name": "Short Answer",
                "description": "Type a short answer response"
            },
            {
                "id": "fillintheblank",
                "name": "Fill in the Blank",
                "description": "Select the correct word to complete the sentence"
            }
        ]
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle all unhandled exceptions"""
    error_log = LoggingUtils.log_error(str(exc))
    print(f"Unhandled error: {json.dumps(error_log)}")
    
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )