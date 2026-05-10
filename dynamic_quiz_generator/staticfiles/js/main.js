/**
 * Global Utilities
 */

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = type === 'success' ? '✅' : '❌';
    toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
    
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hide');
        toast.addEventListener('animationend', () => toast.remove());
    }, 4000);
}

/**
 * Page Init Routing
 */
document.addEventListener('DOMContentLoaded', () => {
    // Determine which page we are on based on existing elements
    if (document.getElementById('generate-quiz-btn')) {
        // Processing page
        console.log("Processing page loaded.");
    } else if (document.getElementById('quiz-container')) {
        // Quiz taking page
        initQuiz();
    } else if (document.getElementById('score-percentage')) {
        // Results page
        initResults();
    }
});

/**
 * Processing Page Logic
 */

async function startQuizGeneration(url, videoId, title) {
    const btn = document.getElementById('generate-quiz-btn');
    const statusText = document.getElementById('status-text');
    const pulse = document.getElementById('status-pulse');
    const progressContainer = document.getElementById('generation-progress-container');
    const progressBar = document.getElementById('generation-progress');
    const progressDetail = document.getElementById('progress-detail');

    if (btn.disabled) return;

    // UI Loading State
    btn.classList.add('loading');
    btn.disabled = true;
    pulse.style.display = 'block';
    progressContainer.style.display = 'block';
    
    statusText.textContent = "AI is analyzing your video (this may take a few minutes)...";
    
    // Simulate some progress while waiting for long polling
    let progress = 10;
    progressBar.style.width = `${progress}%`;
    
    const interval = setInterval(() => {
        if (progress < 85) {
            progress += 5;
            progressBar.style.width = `${progress}%`;
            if (progress === 30) progressDetail.textContent = "Downloading and converting audio...";
            if (progress === 50) progressDetail.textContent = "Transcribing with Faster-Whisper...";
            if (progress === 70) progressDetail.textContent = "Extracting key concepts & generating quiz via LLM...";
        }
    }, 3000);

    try {
        const response = await fetch(window.apiUrls.generateQuiz, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            body: JSON.stringify({ url, video_id: videoId, title: title })
        });
        
        clearInterval(interval);
        progressBar.style.width = `100%`;
        progressDetail.textContent = "Quiz ready!";

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || `HTTP Error ${response.status}`);
        }

        const quizData = await response.json();
        
        // Store quiz in session storage
        sessionStorage.setItem('currentQuiz', JSON.stringify(quizData.quiz));
        sessionStorage.setItem('quizScore', '0');
        sessionStorage.setItem('quizTotal', String(quizData.quiz.length));
        sessionStorage.setItem('quizCorrect', '0');
        sessionStorage.setItem('quizIncorrect', '0');
        
        showToast("Quiz Generated Successfully!", "success");
        
        // Redirect to quiz view
        setTimeout(() => {
            window.location.href = window.apiUrls.quizView;
        }, 1000);

    } catch (error) {
        clearInterval(interval);
        progressBar.style.width = `10%`;
        progressBar.style.background = `var(--error)`;
        progressDetail.textContent = `Error: ${error.message}`;
        statusText.textContent = "Failed to generate quiz";
        pulse.style.background = `var(--error)`;
        pulse.style.boxShadow = `0 0 10px var(--error)`;
        
        showToast(error.message, "error");
        
        // Reset button
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

/**
 * Quiz Page Logic
 */
let quizData = [];
let currentQuestionIndex = 0;
let score = 0;
let correctCount = 0;
let incorrectCount = 0;

function initQuiz() {
    const rawData = sessionStorage.getItem('currentQuiz');
    if (!rawData) {
        showToast("No quiz data found. Redirecting to home...", "error");
        setTimeout(() => window.location.href = "/", 2000);
        return;
    }

    try {
        quizData = JSON.parse(rawData);
        if (!Array.isArray(quizData) || quizData.length === 0) {
            throw new Error("Invalid quiz structure");
        }
        
        document.getElementById('total-q-num').textContent = quizData.length;
        renderQuestion(currentQuestionIndex);
        
    } catch (e) {
        showToast("Failed to parse quiz data.", "error");
    }
}

function renderQuestion(index) {
    const qData = quizData[index];
    
    // Update Progress
    const progressPercent = ((index) / quizData.length) * 100;
    document.getElementById('quiz-progress-bar').style.width = `${progressPercent}%`;
    document.getElementById('current-q-num').textContent = index + 1;
    
    // Set text
    document.getElementById('question-text').textContent = qData.question;
    
    // Clear & Populate options
    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';
    
    // Shuffle options nicely but just map for now
    const shuffledOptions = [...qData.options].sort(() => Math.random() - 0.5);
    
    shuffledOptions.forEach((opt, optIndex) => {
        const btn = document.createElement('button');
        btn.className = 'option-btn fade-in-up';
        btn.style.animationDelay = `${optIndex * 0.1}s`;
        
        btn.innerHTML = `
            <span>${opt}</span>
            <span class="indicator"></span>
        `;
        
        btn.onclick = () => checkAnswer(btn, opt, qData.correct_answer, qData.explanation);
        
        optionsContainer.appendChild(btn);
    });
    
    // Hide explanation and next button
    document.getElementById('explanation-box').classList.remove('visible');
    document.getElementById('next-btn').style.display = 'none';
}

function checkAnswer(selectedBtn, selectedOpt, correctOpt, explanation) {
    const optionsContainer = document.getElementById('options-container');
    const allBtns = optionsContainer.querySelectorAll('.option-btn');
    
    // Disable all
    allBtns.forEach(b => b.disabled = true);
    
    const sOpt = String(selectedOpt).toLowerCase().trim();
    const cOpt = String(correctOpt).toLowerCase().trim();
    
    // Handle exact matches or cases where the correct answer is a substring (e.g. correct_answer: "option a", option: "option a: 42")
    const isCorrect = sOpt === cOpt || 
                      sOpt.includes(cOpt) || 
                      cOpt.includes(sOpt);
    
    if (isCorrect) {
        selectedBtn.classList.add('correct');
        selectedBtn.querySelector('.indicator').textContent = '✓';
        score += 1;
        correctCount += 1;
    } else {
        selectedBtn.classList.add('incorrect');
        selectedBtn.querySelector('.indicator').textContent = '✗';
        incorrectCount += 1;
        
        // Highlight correct
        allBtns.forEach(b => {
            const bText = b.textContent.toLowerCase().trim();
            if (bText.includes(cOpt) || cOpt.includes(bText)) {
                b.classList.add('correct');
                b.querySelector('.indicator').textContent = '✓';
            }
        });
    }
    
    // Show explanation
    const expBox = document.getElementById('explanation-box');
    document.getElementById('explanation-text').textContent = explanation;
    expBox.classList.add('visible');
    
    // Show next btn
    const nextBtn = document.getElementById('next-btn');
    if (currentQuestionIndex < quizData.length - 1) {
        nextBtn.textContent = 'Next Question ➔';
    } else {
        nextBtn.textContent = 'View Results ➔';
    }
    nextBtn.style.display = 'inline-flex';
}

function nextQuestion() {
    currentQuestionIndex++;
    if (currentQuestionIndex < quizData.length) {
        renderQuestion(currentQuestionIndex);
    } else {
        // Compute Results & Redirect
        sessionStorage.setItem('quizScore', score);
        sessionStorage.setItem('quizCorrect', correctCount);
        sessionStorage.setItem('quizIncorrect', incorrectCount);
        window.location.href = window.apiUrls.resultView;
    }
}

/**
 * Results Page Logic
 */
function initResults() {
    const total = parseInt(sessionStorage.getItem('quizTotal') || '0');
    const score = parseInt(sessionStorage.getItem('quizScore') || '0');
    const correct = parseInt(sessionStorage.getItem('quizCorrect') || '0');
    const incorrect = parseInt(sessionStorage.getItem('quizIncorrect') || '0');
    
    if (total === 0) {
        showToast("No active session.", "error");
        return;
    }
    
    const percentage = Math.round((score / total) * 100);
    
    document.getElementById('score-percentage').textContent = `${percentage}%`;
    document.getElementById('score-correct').textContent = correct;
    document.getElementById('score-incorrect').textContent = incorrect;
    document.getElementById('score-total').textContent = `${score}/${total}`;
    
    // Fun color adjustments based on score
    const circle = document.querySelector('.score-circle');
    if (percentage < 50) {
        circle.style.borderColor = 'var(--error)';
        circle.style.boxShadow = '0 0 30px rgba(239, 68, 68, 0.4)';
    } else if (percentage === 100) {
        circle.style.borderColor = 'var(--success)';
        circle.style.boxShadow = '0 0 30px rgba(16, 185, 129, 0.4)';
    }
}

function retryQuiz() {
    // Reset state but keep quiz JSON
    sessionStorage.setItem('quizScore', '0');
    sessionStorage.setItem('quizCorrect', '0');
    sessionStorage.setItem('quizIncorrect', '0');
    window.location.href = window.apiUrls.quizView;
}
