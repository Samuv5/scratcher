import { useState, useEffect, useRef } from 'react'
import { jsPDF } from 'jspdf'
import './App.css'

function App() {
  const [step, setStep] = useState(1)
  const [theme, setTheme] = useState('dark')
  const [cvFile, setCvFile] = useState(null)
  const [cvText, setCvText] = useState('')
  const [cvSkills, setCvSkills] = useState([])
  const [location, setLocation] = useState(null)
  const [locationName, setLocationName] = useState('')
  const [coords, setCoords] = useState({ lat: 40.4168, lng: -3.7038 }) // Default: Madrid
  const [jobUrl, setJobUrl] = useState('')
  const [jobText, setJobText] = useState('')
  const [inputMode, setInputMode] = useState('url')
  const [jobTitle, setJobTitle] = useState('')
  const [jobRequirements, setJobRequirements] = useState(null)
  const [optimizedCV, setOptimizedCV] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState('')
  const [error, setError] = useState('')
  const [showContactForm, setShowContactForm] = useState(false)
  const [contactData, setContactData] = useState({ linkedin: '', phone: '', email: '' })
  const fileInputRef = useRef(null)
  const mapRef = useRef(null)
  const mapInstanceRef = useRef(null)

  useEffect(() => {
    getLocation()
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark')
  }

  useEffect(() => {
    if (mapRef.current && !mapInstanceRef.current && window.L) {
      mapInstanceRef.current = window.L.map(mapRef.current).setView([coords.lat, coords.lng], 10)
      window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap'
      }).addTo(mapInstanceRef.current)
      
      window.L.marker([coords.lat, coords.lng]).addTo(mapInstanceRef.current)
    }
  }, [])

  useEffect(() => {
    if (mapInstanceRef.current && coords.lat && coords.lng) {
      mapInstanceRef.current.setView([coords.lat, coords.lng], 10)
      mapInstanceRef.current.eachLayer((layer) => {
        if (layer instanceof window.L.Marker) {
          mapInstanceRef.current.removeLayer(layer)
        }
      })
      window.L.marker([coords.lat, coords.lng]).addTo(mapInstanceRef.current)
    }
  }, [coords])

  const getLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords
          setCoords({ lat: latitude, lng: longitude })
          try {
            const response = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
            )
            const data = await response.json()
            const city = data.address?.city || data.address?.town || data.address?.village || ''
            const country = data.address?.country_code?.toUpperCase() || ''
            setLocation({ city, country, lat: latitude, lng: longitude })
            setLocationName(city ? `${city}, ${country}` : country)
          } catch {
            setLocationName('Location detected')
          }
        },
        () => setLocationName('Location unavailable')
      )
    } else {
      setLocationName('Geolocation not supported')
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    
    setCvFile(file)
    setLoading(true)
    setLoadingStep('Extracting skills from your CV...')
    setError('')
    
    const formData = new FormData()
    formData.append('cv_file', file)
    
    try {
      const response = await fetch('http://localhost:8000/api/upload-cv', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      
      if (data.success) {
        setCvText(data.cv_text)
        setCvSkills(data.skills || [])
        // Check if contact data is missing
        const hasLinkedIn = data.cv_text.toLowerCase().includes('linkedin')
        const hasEmail = data.cv_text.match(/\S+@\S+\.\S+/)
        const hasPhone = data.cv_text.match(/[\+]?[\d\s\-\(\)]{9,}/)
        
        if (!hasLinkedIn || !hasEmail || !hasPhone) {
          setShowContactForm(true)
        } else {
          setStep(2)
        }
      } else {
        setError(data.error || 'Error processing CV')
      }
    } catch (err) {
      setError('Connection error')
    }
    setLoading(false)
  }

  const continueAfterContactForm = () => {
    // Add contact data to CV text if provided
    let contactInfo = ''
    if (contactData.email) contactInfo += `Email: ${contactData.email}\n`
    if (contactData.phone) contactInfo += `Phone: ${contactData.phone}\n`
    if (contactData.linkedin) contactInfo += `LinkedIn: ${contactData.linkedin}\n`
    
    if (contactInfo) {
      setCvText(contactInfo + '\n' + cvText)
    }
    
    setShowContactForm(false)
    setStep(2)
  }

  const analyzeJob = async () => {
    if (!jobUrl.trim()) {
      setError('Paste the job link')
      return
    }
    
    setLoading(true)
    setLoadingStep('Analyzing job requirements...')
    setError('')
    
    try {
      const formData = new FormData()
      formData.append('url', jobUrl)
      
      const response = await fetch('http://localhost:8000/api/analyze-job', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      
      if (data.success) {
        const req = data.requirements || {}
        setJobRequirements({
          title: req.title || 'Position',
          requirements: req.requirements || [],
          experience: req.experience || 'Not specified',
          languages: req.languages || [],
          responsibilities: req.responsibilities || []
        })
        setJobTitle(req.title || 'Position')
        setStep(3)
      } else {
        // Continue with default data if it fails
        setJobRequirements({title: 'Position', requirements: [], experience: 'Not specified', languages: [], responsibilities: []})
        setJobTitle('Position')
        setStep(3)
      }
    } catch (err) {
      // Continuar con datos por defecto si hay error
      setJobRequirements({titulo: 'Puesto', requisitos: [], experiencia: 'No especificada', idiomas: [], responsabilidades: []})
      setJobTitle('Puesto')
      setStep(3)
    }
    setLoading(false)
  }

  const analyzeJobText = async () => {
    if (!jobText.trim()) {
      setError('Paste the job description')
      return
    }
    
    setLoading(true)
    setLoadingStep('Analyzing job requirements...')
    setError('')
    
    try {
      const formData = new FormData()
      formData.append('job_text', jobText)
      
      const response = await fetch('http://localhost:8000/api/analyze-job-text', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      
      if (data.success) {
        const req = data.requirements || {}
        setJobRequirements({
          titulo: req.titulo || 'Puesto',
          requisitos: req.requisitos || [],
          experiencia: req.experiencia || 'No especificada',
          languages: req.languages || [],
          responsibilities: req.responsibilities || []
        })
        setJobTitle(req.title || 'Position')
        setStep(3)
      } else {
        // Continue with default data
        setJobRequirements({title: 'Position', requirements: [], experience: 'Not specified', languages: [], responsibilities: []})
        setJobTitle('Position')
        setStep(3)
      }
    } catch (err) {
      // Continue with default data
      setJobRequirements({title: 'Position', requirements: [], experience: 'Not specified', languages: [], responsibilities: []})
      setJobTitle('Position')
      setStep(3)
    }
    setLoading(false)
  }

  const optimizeCV = async () => {
    setLoading(true)
    setLoadingStep('Optimizing your CV for this position...')
    setError('')
    
    try {
      const formData = new FormData()
      formData.append('cv_file', cvFile)
      formData.append('job_title', jobTitle)
      
      // Send text if available, otherwise URL
      if (inputMode === 'text' && jobText) {
        formData.append('job_text', jobText)
      } else {
        formData.append('job_url', jobUrl)
      }
      
      const response = await fetch('http://localhost:8000/api/optimize', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      
      if (data.success) {
        setOptimizedCV(data.optimized_cv)
        setStep(4)
      } else {
        setError(data.error || 'Error optimizing')
      }
    } catch (err) {
      setError('Connection error')
    }
    setLoading(false)
  }

  const downloadPDF = () => {
    const doc = new jsPDF('p', 'mm', 'a4')
    const pageWidth = doc.internal.pageSize.getWidth()
    const pageHeight = doc.internal.pageSize.getHeight()
    const margin = 15
    const contentWidth = pageWidth - (margin * 2)
    let y = 20
    
    // Colores
    const primaryColor = [0, 113, 227]  // Azul
    const darkColor = [30, 30, 30]
    const grayColor = [100, 100, 100]
    
    // Parsear el contenido
    const lines = optimizedCV.split('\n')
    
    lines.forEach((line) => {
      // Check if we need a new page
      if (y > pageHeight - 20) {
        doc.addPage()
        y = 20
      }
      
      const cleanLine = line.replace(/\*\*/g, '').replace(/\*/g, '').trim()
      if (!cleanLine) {
        y += 4
        return
      }
      
      // Main title (Name)
      if (line.includes('# ') && !line.includes('## ')) {
        doc.setFontSize(24)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(...primaryColor)
        doc.text(cleanLine.replace('# ', ''), margin, y)
        y += 4
        
        // Línea separadora
        doc.setDrawColor(...primaryColor)
        doc.setLineWidth(0.5)
        doc.line(margin, y, pageWidth - margin, y)
        y += 8
      }
      // Subtítulos
      else if (line.includes('## ') || line.includes('### ')) {
        doc.setFontSize(13)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(...primaryColor)
        const subtitle = cleanLine.replace(/##?#?\s*/g, '')
        doc.text(subtitle.toUpperCase(), margin, y)
        y += 2
        
        // Línea debajo del subtítulo
        doc.setDrawColor(...primaryColor)
        doc.setLineWidth(0.3)
        doc.line(margin, y, margin + 50, y)
        y += 6
      }
      // Items con viñetas
      else if (line.includes('- ') || line.includes('• ') || line.includes('✔')) {
        doc.setFontSize(10)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(...darkColor)
        const itemText = cleanLine.replace(/^[-•✔]\s*/, '').replace(/\*\*/g, '')
        const bullet = '•'
        
        // Texto con sangría
        doc.text(bullet, margin + 2, y)
        const splitText = doc.splitTextToSize(itemText, contentWidth - 8)
        doc.text(splitText, margin + 8, y)
        y += splitText.length * 5
      }
      // Separadores
      else if (line.includes('---')) {
        y += 2
        doc.setDrawColor(200, 200, 200)
        doc.setLineWidth(0.2)
        doc.line(margin, y, pageWidth - margin, y)
        y += 6
      }
      // Notas y texto normal
      else if (line.includes('**Nota**') || line.includes('Nota:')) {
        doc.setFontSize(9)
        doc.setFont('helvetica', 'italic')
        doc.setTextColor(...grayColor)
        const noteText = cleanLine.replace(/\*\*/g, '').replace(/\*/g, '')
        const splitNote = doc.splitTextToSize(noteText, contentWidth)
        doc.text(splitNote, margin, y)
        y += splitNote.length * 4 + 2
      }
      // Texto normal (experiencia, educación, etc.)
      else {
        doc.setFontSize(11)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(...darkColor)
        const splitText = doc.splitTextToSize(cleanLine, contentWidth)
        doc.text(splitText, margin, y)
        y += splitText.length * 5
      }
    })
    
    doc.save(`CV_${jobTitle.replace(/\s+/g, '_')}_${Date.now()}.pdf`)
  }

  return (
    <div className="app">
      <nav className="navbar">
        <div className="logo">Scratcher</div>
        <div className="nav-right">
          <button className="theme-toggle" onClick={toggleTheme} title={theme === 'dark' ? 'Light mode' : 'Dark mode'}>
            {theme === 'dark' ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
          {locationName && (
            <span className="location-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                <circle cx="12" cy="10" r="3"/>
              </svg>
              {locationName}
            </span>
          )}
        </div>
      </nav>

      <main className="main-content">
        {step === 1 && !showContactForm && (
          <div className="step-container fade-in">
            <div className="hero-section">
              <div className="hero-icons">
                <div className="hero-icon icon-1">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                </div>
                <div className="hero-icon icon-2">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <rect x="2" y="3" width="20" height="14" rx="2"/>
                    <path d="M8 21h8"/>
                    <path d="M12 17v4"/>
                  </svg>
                </div>
                <div className="hero-icon icon-3">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                  </svg>
                </div>
              </div>
              <h1>Your perfect CV,<br/><span className="gradient-text">without lies</span></h1>
              <p>Upload your CV and paste the job link. We adapt your real experience with the skills they're looking for.</p>
              <div className="hero-stats">
                <div className="stat">
                  <span className="stat-number">100%</span>
                  <span className="stat-label">Honest</span>
                </div>
                <div className="stat">
                  <span className="stat-number">0</span>
                  <span className="stat-label">lies</span>
                </div>
                <div className="stat">
                  <span className="stat-number">AI</span>
                  <span className="stat-label">Optimized</span>
                </div>
              </div>
            </div>
            
            <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
              <input 
                ref={fileInputRef}
                type="file" 
                accept=".pdf" 
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
              <div className="upload-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M7 18a4.6 4.4 0 0 1-.9-8.5 6 6 0 0 1 11.9 0A4.6 4.4 0 0 1 17 18"/>
                  <path d="M12 13v9"/>
                  <path d="m9 16 3-3 3 3"/>
                </svg>
              </div>
              <h3>Drag your CV here</h3>
              <p>or click to select • PDF only</p>
            </div>
          </div>
        )}

        {showContactForm && (
          <div className="step-container fade-in">
            <div className="contact-form">
              <div className="contact-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
              </div>
              <h2>Contact Information</h2>
              <p className="subtitle">We couldn't find some data in your CV. Help us complete them:</p>
              
              <div className="contact-inputs">
                <div className="input-group">
                  <label>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                      <polyline points="22,6 12,13 2,6"/>
                    </svg>
                    Email
                  </label>
                  <input
                    type="email"
                    value={contactData.email}
                    onChange={(e) => setContactData({...contactData, email: e.target.value})}
                    placeholder="tu@email.com"
                  />
                </div>
                
                <div className="input-group">
                  <label>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                    </svg>
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={contactData.phone}
                    onChange={(e) => setContactData({...contactData, phone: e.target.value})}
                    placeholder="+34 600 123 456"
                  />
                </div>
                
                <div className="input-group">
                  <label>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/>
                      <rect x="2" y="9" width="4" height="12"/>
                      <circle cx="4" cy="4" r="2"/>
                    </svg>
                    LinkedIn (optional)
                  </label>
                  <input
                    type="text"
                    value={contactData.linkedin}
                    onChange={(e) => setContactData({...contactData, linkedin: e.target.value})}
                    placeholder="linkedin.com/in/tu-perfil"
                  />
                </div>
              </div>
              
              <button className="continue-btn" onClick={continueAfterContactForm}>
                Continuar
              </button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="step-container fade-in">
            <div className="success-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              CV Cargado
            </div>
            
            <div className="skills-section">
              <h2>Your Skills</h2>
              <div className="skills-grid">
                {cvSkills.map((skill, i) => (
                  <span key={i} className="skill-tag">{skill}</span>
                ))}
                {cvSkills.length === 0 && (
                  <span className="skill-tag">Skills detected</span>
                )}
              </div>
              
              {locationName && locationName !== 'Ubicación no disponible' && (
                <div className="location-info">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                    <circle cx="12" cy="10" r="3"/>
                  </svg>
                  <span>{locationName}</span>
                  <div className="mini-map-static">
                    <img src={"https://staticmap.openstreetmap.de/staticmap.php?center=" + coords.lat + "," + coords.lng + "&zoom=10&size=200x100&markers=" + coords.lat + "," + coords.lng + ",red"} alt="Map" onError={(e) => e.target.style.display='none'} />
                  </div>
                </div>
              )}
            </div>

            <h3>Job Info</h3>
            <p className="subtitle">Paste the link OR the job description</p>
            
            <div className="mode-tabs">
              <button 
                className={"mode-tab" + (inputMode === 'url' ? ' active' : '')}
                onClick={() => setInputMode('url')}
              >
                Link
              </button>
              <button 
                className={"mode-tab" + (inputMode === 'text' ? ' active' : '')}
                onClick={() => setInputMode('text')}
              >
                Texto
              </button>
            </div>
            
            {inputMode === 'url' ? (
              <div className="url-input-container">
                <input
                  type="text"
                  value={jobUrl}
                  onChange={(e) => setJobUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/jobs/..."
                  className="url-input"
                />
                <button className="analyze-btn" onClick={analyzeJob}>
                  Analyze
                </button>
              </div>
            ) : (
              <div className="text-input-container">
                <textarea
                  value={jobText}
                  onChange={(e) => setJobText(e.target.value)}
                  placeholder="Paste the job description here..."
                  className="job-text-input"
                  rows={6}
                />
                <button className="analyze-btn" onClick={analyzeJobText}>
                  Analyze
                </button>
              </div>
            )}

            {error && <p className="error-text">{error}</p>}
            
            <button className="skip-btn" onClick={() => {
              setJobTitle('Position')
              setJobRequirements({title: 'Position', requirements: []})
              setStep(3)
            }}>
              Skip and continue without AI
            </button>
          </div>
        )}

        {step === 3 && jobRequirements && (
          <div className="step-container fade-in">
            <div className="success-badge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Análisis Completado
            </div>
            
            <h2>{jobRequirements.titulo}</h2>
            
            <div className="requirements-card">
              <h4>Requisitos del Puesto</h4>
              <div className="skills-grid">
                {jobRequirements.requisitos?.map((req, i) => (
                  <span key={i} className="skill-tag req">{req}</span>
                )) || <span className="skill-tag">Not specified</span>}
              </div>
              
              <h4>Experience</h4>
              <p>{jobRequirements.experience || 'Not specified'}</p>
              
              <h4>Languages</h4>
              <p>{jobRequirements.languages?.join(', ') || 'Not specified'}</p>
            </div>

            <button className="optimize-btn" onClick={optimizeCV}>
              Optimize My CV with These Skills
            </button>

            {error && <p className="error-text">{error}</p>}
          </div>
        )}

        {step === 4 && (
          <div className="step-container fade-in">
            <div className="result-section">
              <div className="success-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
                CV Optimized!
              </div>
              <h2>Ready for {jobTitle}</h2>
              <p className="subtitle">We only use your real skills</p>
              
              <div className="cv-preview-box">
                <pre>{optimizedCV}</pre>
              </div>
              
              <div className="action-buttons">
                <button className="download-btn" onClick={downloadPDF}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="7 10 12 15 17 10"/>
                    <line x1="12" y1="15" x2="12" y2="3"/>
                  </svg>
                  Download PDF
                </button>
                <button className="back-btn" onClick={() => setStep(1)}>
                  Start over
                </button>
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="loader"></div>
            <p>{loadingStep}</p>
          </div>
        )}
      </main>

      <footer className="footer">
        <div className="step-indicator">
          {[1, 2, 3, 4].map((s) => (
              <div 
              key={s} 
              className={"step-dot" + (step >= s ? ' active' : '') + (step === s ? ' current' : '')}
            />
          ))}
        </div>
      </footer>
    </div>
  )
}

export default App
