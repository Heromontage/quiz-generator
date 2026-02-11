// State Management
const appState = {
    files: [],
    quiz: null,
    currentQuestionIndex: 0,
    answers: {},
    isGenerating: false
};

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const fileList = document.getElementById('fileList');
const filesContainer = document.getElementById('filesContainer');
const clearFilesBtn = document.getElementById('clearFilesBtn');
const generateBtn = document.getElementById('generateBtn');
const settingsSection = document.getElementById('settingsSection');
const quizSection = document.getElementById('quizSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const errorMessage = document.getElementById('errorMessage');
const successMessage = document.getElementById('successMessage');
const quizContent = document.getElementById('quizContent');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const downloadBtn = document.getElementById('downloadBtn');
const retakeBtn = document.getElementById('retakeBtn');

const API_BASE_URL = 'http://localhost:8000/api';

// Event Listeners
browseBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
uploadArea.addEventListener('dragover', handleDragOver);
uploadArea.addEventListener('dragleave', handleDragLeave);
uploadArea.addEventListener('drop', handleDrop);
clearFilesBtn.addEventListener('click', clearFiles);
generateBtn.addEventListener('click', handleGenerateQuiz);
prevBtn.addEventListener('click', previousQuestion);
nextBtn.addEventListener('click', nextQuestion);
downloadBtn.addEventListener('click', downloadQuiz);
retakeBtn.addEventListener('click', retakeQuiz);

// File Upload Handlers
function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFiles(files);
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    uploadArea.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
}

function addFiles(files) {
    const validFiles = files.filter(file => {
        const validExtensions = ['pdf', 'docx', 'txt', 'doc'];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        return validExtensions.includes(fileExtension) && file.size <= 10 * 1024 * 1024; // 10MB limit
    });

    if (validFiles.length === 0) {
        showError('Please select valid files (PDF, DOCX, TXT, DOC) under 10MB');
        return;
    }

    appState.files = [...appState.files, ...validFiles];
    displayFiles();
}

function displayFiles() {
    if (appState.files.length === 0) {
        fileList.style.display = 'none';
        uploadArea.style.display = 'block';
        return;
    }

    fileList.style.display = 'block';
    uploadArea.style.display = 'none';

    filesContainer.innerHTML = appState.files.map((file, index) => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${formatFileSize(file.size)}</div>
            </div>
            <button class="file-remove" onclick="removeFile(${index})">×</button>
        </div>
    `).join('');
}

function removeFile(index) {
    appState.files.splice(index, 1);
    displayFiles();
}

function clearFiles() {
    appState.files = [];
    fileInput.value = '';
    displayFiles();
    settingsSection.style.display = 'none';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Quiz Generation
async function handleGenerateQuiz() {
    if (appState.files.length === 0) {
        showError('Please select at least one file');
        return;
    }

    settingsSection.style.display = 'block';
    settingsSection.scrollIntoView({ behavior: 'smooth' });
}

async function generateQuiz() {
    try {
        showLoading(true);
        quizSection.style.display = 'none';

        const formData = new FormData();
        appState.files.forEach(file => {
            formData.append('files', file);
        });

        formData.append('question_count', document.getElementById('questionCount').value);
        formData.append('difficulty', document.getElementById('difficulty').value);
        
        const questionTypes = Array.from(document.querySelectorAll('#questionTypes input:checked'))
            .map(input => input.value);
        formData.append('question_types', JSON.stringify(questionTypes));
        formData.append('include_explanations', document.getElementById('includeExplanations').checked);

        const response = await fetch(`${API_BASE_URL}/generate-quiz`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to generate quiz');
        }

        const data = await response.json();
        appState.quiz = data.quiz;
        appState.currentQuestionIndex = 0;
        appState.answers = {};

        displayQuiz();
        showSuccess('Quiz generated successfully!');
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

function displayQuiz() {
    quizSection.style.display = 'block';
    quizSection.scrollIntoView({ behavior: 'smooth' });
    displayQuestion();
    updateNavigation();
}

function displayQuestion() {
    if (!appState.quiz || appState.quiz.length === 0) {
        showError('No questions generated');
        return;
    }

    const question = appState.quiz[appState.currentQuestionIndex];
    const questionNumber = appState.currentQuestionIndex + 1;
    const totalQuestions = appState.quiz.length;

    document.getElementById('currentQuestion').textContent = questionNumber;
    document.getElementById('totalQuestions').textContent = totalQuestions;

    let questionHTML = `
        <div class="question-card">
            <div class="question-number">Question ${questionNumber}</div>
            <div class="question-type">${question.type}</div>
            <div class="question-text">${question.question}</div>
    `;

    const savedAnswer = appState.answers[appState.currentQuestionIndex];

    switch (question.type) {
        case 'multiple_choice':
            questionHTML += `
                <div class="options">
                    ${question.options.map((option, index) => `
                        <label class="option">
                            <input type="radio" name="answer" value="${index}" 
                                ${savedAnswer === index ? 'checked' : ''}>
                            ${option}
                        </label>
                    `).join('')}
                </div>
            `;
            break;

        case 'true_false':
            questionHTML += `
                <div class="options">
                    <label class="option">
                        <input type="radio" name="answer" value="true" 
                            ${savedAnswer === 'true' ? 'checked' : ''}>
                        True
                    </label>
                    <label class="option">
                        <input type="radio" name="answer" value="false" 
                            ${savedAnswer === 'false' ? 'checked' : ''}>
                        False
                    </label>
                </div>
            `;
            break;

        case 'short_answer':
            questionHTML += `
                <input type="text" class="short-answer-input" placeholder="Enter your answer" 
                    value="${savedAnswer || ''}" id="shortAnswerInput">
            `;
            break;

        case 'fill_in_the_blank':
            questionHTML += `
                <div class="options">
                    ${question.options.map((option, index) => `
                        <label class="option">
                            <input type="radio" name="answer" value="${index}" 
                                ${savedAnswer === index ? 'checked' : ''}>
                            ${option}
                        </label>
                    `).join('')}
                </div>
            `;
            break;
    }

    if (question.explanation) {
        questionHTML += `
            <div class="explanation">
                <div class="explanation-title">Explanation</div>
                <div class="explanation-text">${question.explanation}</div>
            </div>
        `;
    }

    questionHTML += '</div>';
    quizContent.innerHTML = questionHTML;

    // Add event listeners for answer saving
    const radios = quizContent.querySelectorAll('input[type="radio"]');
    const shortAnswerInput = document.getElementById('shortAnswerInput');

    radios.forEach(radio => {
        radio.addEventListener('change', saveAnswer);
    });

    if (shortAnswerInput) {
        shortAnswerInput.addEventListener('input', saveAnswer);
    }
}

function saveAnswer() {
    const radios = quizContent.querySelectorAll('input[type="radio"]:checked');
    const shortAnswerInput = document.getElementById('shortAnswerInput');

    if (radios.length > 0) {
        appState.answers[appState.currentQuestionIndex] = radios[0].value;
    } else if (shortAnswerInput) {
        appState.answers[appState.currentQuestionIndex] = shortAnswerInput.value;
    }
}

function previousQuestion() {
    if (appState.currentQuestionIndex > 0) {
        saveAnswer();
        appState.currentQuestionIndex--;
        displayQuestion();
        updateNavigation();
    }
}

function nextQuestion() {
    if (appState.currentQuestionIndex < appState.quiz.length - 1) {
        saveAnswer();
        appState.currentQuestionIndex++;
        displayQuestion();
        updateNavigation();
    }
}

function updateNavigation() {
    prevBtn.disabled = appState.currentQuestionIndex === 0;
    nextBtn.disabled = appState.currentQuestionIndex === appState.quiz.length - 1;
}

function downloadQuiz() {
    const quizData = {
        questions: appState.quiz,
        answers: appState.answers,
        timestamp: new Date().toISOString()
    };

    const dataStr = JSON.stringify(quizData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `quiz-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);

    showSuccess('Quiz downloaded successfully!');
}

function retakeQuiz() {
    appState.currentQuestionIndex = 0;
    appState.answers = {};
    displayQuestion();
    updateNavigation();
}

// UI Helper Functions
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    setTimeout(() => {
        successMessage.style.display = 'none';
    }, 5000);
}

// Initialize on page load
window.addEventListener('load', () => {
    console.log('Quiz Generator loaded successfully');
});