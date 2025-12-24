import { useState } from 'react';
import './Sidebar.css';

function Sidebar({ currentPage, onNavigate }) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <>
      <button 
        className="sidebar-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle Sidebar"
      >
        {isOpen ? '✕' : '☰'}
      </button>

      <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <h2>🎓 Autonomous Tutor</h2>
        </div>
        
        <nav className="sidebar-nav">
          <ul>
            <li>
              <button 
                className={currentPage === 'home' ? 'active' : ''}
                onClick={() => onNavigate('home')}
              >
                <span className="icon">🏠</span>
                <span className="text">Home</span>
              </button>
            </li>
            <li>
              <button 
                className={currentPage === 'about' ? 'active' : ''}
                onClick={() => onNavigate('about')}
              >
                <span className="icon">ℹ️</span>
                <span className="text">About</span>
              </button>
            </li>
          </ul>
        </nav>

        <div className="sidebar-footer">
          <p>Version 1.0.0</p>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
