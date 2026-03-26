let jobs = [];
let currentJobIndex = 0;
let cvFile = null;

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
    switchScreen(screenSwipe);
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
        const data = await res.json();
        jobs = data.jobs;
        // Shuffle jobs for tinder effect
        jobs.sort(() => Math.random() - 0.5);
    } catch (e) {
        alert("Error loading local job board");
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
    swipeAction('left');
});

document.getElementById('btn-apply').addEventListener('click', () => {
    swipeAction('right');
});

// Swipe Animation
function swipeAction(direction) {
    if (currentJobIndex >= jobs.length) return;
    const card = document.querySelector('.tinder-card');
    if (!card) return;
    
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

// Logic to communicate with Llama3 via FastAPI
async function applyToJob(job) {
    switchScreen(screenResult);
    document.getElementById('applied-job-title').textContent = job.title;
    document.getElementById('loader').style.display = 'block';
    document.getElementById('optimized-cv-container').style.display = 'none';
    
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    formData.append('job_title', job.title);
    formData.append('job_description', job.description);
    
    try {
        const res = await fetch('/api/apply', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        document.getElementById('loader').style.display = 'none';
        
        if (data.success) {
            document.getElementById('optimized-cv-container').style.display = 'flex';
            document.getElementById('optimized-cv-container').style.flexDirection = 'column';
            document.getElementById('optimized-cv-text').value = data.optimized_cv;
        } else {
            alert("AI error optimizing CV: " + data.error);
            switchScreen(screenSwipe);
            renderCurrentCard();
        }
    } catch (e) {
        alert("Connection error to application server.");
        switchScreen(screenSwipe);
        renderCurrentCard();
    }
}

// Go back to continue viewing cards
document.getElementById('back-to-swipe-btn').addEventListener('click', () => {
    switchScreen(screenSwipe);
    renderCurrentCard();
});