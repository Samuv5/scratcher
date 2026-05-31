let jobs = [];
let currentJobIndex = 0;
let cvFile = null;
let isProcessing = false;

// DOM Elements
const uploadInput = document.getElementById('cv-upload');
const fileNameDisplay = document.getElementById('file-name');
const startBtn = document.getElementById('start-btn');
const queryInput = document.getElementById('query-input');
const locationInput = document.getElementById('location-input');
const languageInput = document.getElementById('language-input');

const btnLinkedin = document.getElementById('btn-linkedin');
const btnGithub = document.getElementById('btn-github');

const screenUpload = document.getElementById('upload-screen');
const screenSwipe = document.getElementById('swipe-screen');
const screenResult = document.getElementById('result-screen');
const cardContainer = document.getElementById('card-container');
const loaderEl = document.getElementById('loader');
const optimizedContainer = document.getElementById('optimized-cv-container');
const optimizedText = document.getElementById('optimized-cv-text');

// CV Upload Event
uploadInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        cvFile = e.target.files[0];
        fileNameDisplay.textContent = `PDF Loaded: ${cvFile.name}`;
        checkStartReady();
    }
});

function checkStartReady() {
    if (cvFile && queryInput.value.trim() !== '') {
        startBtn.disabled = false;
    } else {
        startBtn.disabled = true;
    }
}

queryInput.addEventListener('input', checkStartReady);

// Account Mocks
btnLinkedin.addEventListener('click', () => {
    btnLinkedin.textContent = "✅ LinkedIn Connected (Trust: High)";
    btnLinkedin.style.background = "#0e76a8";
    btnLinkedin.disabled = true;
});

btnGithub.addEventListener('click', () => {
    btnGithub.textContent = "✅ GitHub Connected (Trust: High)";
    btnGithub.style.background = "#333";
    btnGithub.disabled = true;
});

// Start matching
startBtn.addEventListener('click', async () => {
    const statusMsg = document.getElementById('status-message');
    switchScreen(screenSwipe);
    cardContainer.innerHTML = '<div class="tinder-card" style="justify-content:center;align-items:center;text-align:center;"><div class="loader" style="margin:20px auto;"></div><p style="color:#666;">Loading jobs...</p></div>';
    await fetchJobs();
    renderCurrentCard();
});

// Switch screens
function switchScreen(screen) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    screen.classList.add('active');
}

// Fetch to local FastAPI API with filters
async function fetchJobs() {
    try {
        const query = encodeURIComponent(queryInput.value);
        const loc = encodeURIComponent(locationInput.value);
        const lang = encodeURIComponent(languageInput.value);
        
        const url = `/api/jobs?query=${query}&location=${loc}&language=${lang}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        jobs = data.jobs || [];
        // Shuffle jobs for tinder effect
        jobs.sort(() => Math.random() - 0.5);
        if (jobs.length === 0) {
            alert("No jobs found. Try different filters.");
            switchScreen(screenUpload);
        }
    } catch (e) {
        alert("Error loading jobs: " + e.message);
        switchScreen(screenUpload);
    }
}

// Render individual card
function renderCurrentCard() {
    cardContainer.innerHTML = '';
    if (currentJobIndex >= jobs.length) {
        cardContainer.innerHTML = `
            <div class="tinder-card empty-card" style="justify-content:center; align-items:center; text-align:center;">
                <h2 style="color:#000;">You're up to date!</h2>
                <p style="color:#666;">No more offers. Change the region or language.</p>
                <button onclick="window.location.reload()" style="padding:10px 20px; background:#e0e0e0; border:none; border-radius:10px; margin-top:20px; cursor:pointer;">Back to Filters</button>
            </div>`;
        return;
    }
    const job = jobs[currentJobIndex];
    const card = document.createElement('div');
    card.className = 'tinder-card';
    card.innerHTML = `
        <div class="job-title">${job.title}</div>
        <div class="job-company">${job.company} 📍 Zone: ${job.location} | 🗣 Language: ${job.language}</div>
        <div class="job-desc">${job.description}</div>
    `;
    cardContainer.appendChild(card);
}

// Pass / Apply Button Controls
document.getElementById('btn-pass').addEventListener('click', () => {
    if (!isProcessing) swipeAction('left');
});

document.getElementById('btn-apply').addEventListener('click', () => {
    if (!isProcessing) swipeAction('right');
});

// Swipe Animation
function swipeAction(direction) {
    if (currentJobIndex >= jobs.length) return;
    const card = document.querySelector('.tinder-card');
    if (!card) return;
    
    if (direction === 'right') isProcessing = true;
    
    // Visual exit animation
    card.style.transform = `translateX(${direction === 'left' ? '-150%' : '150%'}) rotate(${direction === 'left' ? '-20deg' : '20deg'})`;
    card.style.opacity = '0';
    
    // After animation ends
    setTimeout(() => {
        if (direction === 'right') {
            applyToJob(jobs[currentJobIndex]);
        }
        currentJobIndex++;
        if(direction === 'left') {
            renderCurrentCard();
        }
    }, 400); // match transition css duration
}

// Logic to communicate with FastAPI backend
async function applyToJob(job) {
    switchScreen(screenResult);
    document.getElementById('applied-job-title').textContent = job.title;
    loaderEl.style.display = 'block';
    optimizedContainer.style.display = 'none';
    
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    formData.append('job_title', job.title);
    formData.append('job_text', job.description);
    
    try {
        const res = await fetch('/api/optimize', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        loaderEl.style.display = 'none';
        
        if (data.success && data.optimized_cv) {
            optimizedContainer.style.display = 'flex';
            optimizedContainer.style.flexDirection = 'column';
            optimizedText.value = data.optimized_cv;
        } else {
            alert("Could not optimize CV: " + (data.error || 'Unknown error'));
            goBackToSwipe();
        }
    } catch (e) {
        alert("Connection error. Make sure the server is running.");
        goBackToSwipe();
    } finally {
        isProcessing = false;
    }
}

function goBackToSwipe() {
    switchScreen(screenSwipe);
    renderCurrentCard();
}

// Go back to continue viewing cards
document.getElementById('back-to-swipe-btn').addEventListener('click', () => {
    goBackToSwipe();
});