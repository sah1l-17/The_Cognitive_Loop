import { motion } from 'framer-motion';
import './Footer.css';

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-main">
          <div className="footer-brand">
            <div className="footer-logo">
              <span className="footer-logo-icon">🎓</span>
              <span className="footer-logo-text">Autonomous Tutor</span>
            </div>
            <p className="footer-tagline">
              AI-powered adaptive learning that turns students into experts.
            </p>
            <div className="footer-stats">
              <div className="footer-stat">
                <span className="stat-value">50+</span>
                <span className="stat-label">Students</span>
              </div>
              <div className="footer-stat">
                <span className="stat-value">6</span>
                <span className="stat-label">Countries</span>
              </div>
              <div className="footer-stat">
                <span className="stat-value">Founded</span>
                <span className="stat-label">2024</span>
              </div>
            </div>
          </div>

          <div className="footer-links">
            <div className="footer-column">
              <h4 className="footer-heading">Services</h4>
              <ul className="footer-list">
                <li><a href="#branding">Multimodal Ingestion</a></li>
                <li><a href="#design">Adaptive Tutoring</a></li>
                <li><a href="#development">Practice Games</a></li>
                <li><a href="#3d">AI Insights</a></li>
              </ul>
            </div>

            <div className="footer-column">
              <h4 className="footer-heading">Technology</h4>
              <ul className="footer-list">
                <li><a href="#tech">FastAPI Backend</a></li>
                <li><a href="#tech">React Frontend</a></li>
                <li><a href="#tech">Google Gemini AI</a></li>
                <li><a href="#tech">Framer Motion</a></li>
              </ul>
            </div>

            <div className="footer-column">
              <h4 className="footer-heading">Contact</h4>
              <ul className="footer-list">
                <li><a href="#contact">Get Started</a></li>
                <li><a href="#about">About Us</a></li>
                <li><a href="#support">Support</a></li>
                <li><a href="#faq">FAQ</a></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="footer-bottom-content">
            <p className="footer-copyright">
              © {currentYear} Autonomous Tutor. All rights reserved.
            </p>
            <div className="footer-legal">
              <a href="#privacy">Privacy Policy</a>
              <a href="#cookies">Cookie Policy</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
