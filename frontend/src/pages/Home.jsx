
import './Home.css';

function Home() {
  return (
    <div className="home">
      {/* Hero Section */}
      <section className="hero">
        <div className="hero-glow" />
        <div className="hero-content">
          <span className="hero-badge">AI • Adaptive • Interactive</span>
          <h1 className="hero-title">Autonomous Tutor</h1>
          <p className="hero-subtitle">AI-Powered Adaptive Learning System</p>
          <p className="hero-description">
            Multimodal learning, intelligent tutoring, and interactive practice
            games designed for clarity and mastery.
          </p>

          {/* Get Started Button */}
          <button className="cta-btn">
            <span>Get Started</span>
          </button>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        <h2 className="section-title">Key Features</h2>

        <div className="card-grid">
          {/* Card 1 */}
          <div className="card">
            <div className="text">
              Multimodal Ingestion
              <span className="subtitle">
                Upload PDFs, text, and images. AI structures content automatically.
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
              Adaptive Tutor
              <span className="subtitle">
                Explanations adapt to your understanding and confusion level.
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
              Practice Games
              <span className="subtitle">
                Active recall with short, engaging learning games.
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

export default Home;
