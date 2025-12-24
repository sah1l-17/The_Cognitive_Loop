import './About.css';

function About() {
  return (
    <div className="about">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-glow" />
        <div className="hero-content">
          <span className="hero-badge">About • Mission • Vision</span>
          <h1 className="hero-title">About Autonomous Tutor</h1>
          <p className="hero-subtitle">Revolutionizing Education Through AI</p>
          <p className="hero-description">
            Transforming the way people learn with intelligent, adaptive tutoring 
            that understands each student's unique learning pace and style.
          </p>

          {/* Get Started Button */}
          <button className="cta-btn">
            <span>Learn More</span>
          </button>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        <h2 className="section-title">Our Mission</h2>

        <div className="card-grid">
          {/* Card 1 */}
          <div className="card">
            <div className="text">
              Adaptive Learning
              <span className="subtitle">
                AI tutor detects confusion and adjusts explanations in real-time.
              </span>
            </div>

            <a className="button" style={{ '--clr': '#7c3aed' }}>
              Explore
              <span className="button__icon-wrapper">
                <svg className="button__icon-svg" viewBox="0 0 20 20" width="14">
                  <path d="M7 5l5 5-5 5" fill="currentColor" />
                </svg>
                <svg className="button__icon-svg button__icon-svg--copy" viewBox="0 0 20 20" width="14">
                  <path d="M7 5l5 5-5 5" fill="currentColor" />
                </svg>
              </span>
            </a>
          </div>

          {/* Card 2 */}
          <div className="card">
            <div className="text">
              Smart Content Processing
              <span className="subtitle">
                Upload any material - text, PDFs, or images - automatically structured.
              </span>
            </div>

            <a className="button" style={{ '--clr': '#7c3aed' }}>
              Explore
              <span className="button__icon-wrapper">
                <svg className="button__icon-svg" viewBox="0 0 20 20" width="14">
                  <path d="M7 5l5 5-5 5" fill="currentColor" />
                </svg>
                <svg className="button__icon-svg button__icon-svg--copy" viewBox="0 0 20 20" width="14">
                  <path d="M7 5l5 5-5 5" fill="currentColor" />
                </svg>
              </span>
            </a>
          </div>

          {/* Card 3 */}
          <div className="card">
            <div className="text">
              Active Recall Practice
              <span className="subtitle">
                Interactive games using proven cognitive science principles.
              </span>
            </div>

            <a className="button" style={{ '--clr': '#7c3aed' }}>
              Explore
              <span className="button__icon-wrapper">
                <svg className="button__icon-svg" viewBox="0 0 20 20" width="14">
                  <path d="M7 5l5 5-5 5" fill="currentColor" />
                </svg>
                <svg className="button__icon-svg button__icon-svg--copy" viewBox="0 0 20 20" width="14">
                  <path d="M7 5l5 5-5 5" fill="currentColor" />
                </svg>
              </span>
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

export default About;
