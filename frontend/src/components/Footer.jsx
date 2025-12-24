import './Footer.css';

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <h3>Autonomous Tutor</h3>
          <p>AI-powered adaptive learning system</p>
        </div>
        
        <div className="footer-section">
          <h4>Features</h4>
          <ul>
            <li>Multimodal Content Ingestion</li>
            <li>Adaptive Tutoring</li>
            <li>Practice Games</li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4>Technology</h4>
          <ul>
            <li>FastAPI Backend</li>
            <li>React Frontend</li>
            <li>Google Gemini AI</li>
          </ul>
        </div>
        
        <div className="footer-section">
          <h4>Contact</h4>
          <p>Built with ❤️ for better learning</p>
        </div>
      </div>
      
      <div className="footer-bottom">
        <p>&copy; 2025 Autonomous Tutor. All rights reserved.</p>
      </div>
    </footer>
  );
}

export default Footer;
