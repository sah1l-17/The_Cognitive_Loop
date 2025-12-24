import './Navbar.css';

function Navbar({ currentPage, onNavigate }) {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand" onClick={() => onNavigate('home')}>
          <span className="brand-icon">🎓</span>
          <span className="brand-text">Autonomous Tutor</span>
        </div>
        
        <div className="navbar-links">
          <button 
            className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => onNavigate('home')}
          >
            Home
          </button>
          <button 
            className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
            onClick={() => onNavigate('about')}
          >
            About
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
