import { motion } from 'framer-motion';
import './Navbar.css';

function Navbar({ currentPage, onNavigate, theme, onToggleTheme }) {
  return (
    <motion.nav 
      className="navbar"
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
    >
      <div className="navbar-container">
        <motion.div 
          className="navbar-brand" 
          onClick={() => onNavigate('home')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <span className="brand-text">The Cognitive loop</span>
        </motion.div>

        <div className="navbar-links">
          <motion.button
            className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => onNavigate('home')}
            whileTap={{ scale: 0.98 }}
          >
            Home
          </motion.button>
          <motion.button
            className={`nav-link ${currentPage === 'games' ? 'active' : ''}`}
            onClick={() => onNavigate('games')}
            whileTap={{ scale: 0.98 }}
          >
            Games
          </motion.button>
          <motion.button
            className={`nav-link ${currentPage === 'chat' ? 'active' : ''}`}
            onClick={() => onNavigate('chat')}
            whileTap={{ scale: 0.98 }}
          >
            Chat
          </motion.button>
          <motion.button
            className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
            onClick={() => onNavigate('about')}
            whileTap={{ scale: 0.98 }}
          >
            About
          </motion.button>
        </div>

        <div className="navbar-cta">
          <label className="switch theme-switch">
            <span className="sr-only">Toggle dark mode</span>
            <input
              className="input"
              type="checkbox"
              checked={theme === 'dark'}
              onChange={onToggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            />
            <span className="slider round" aria-hidden="true">
              <span className="stars" aria-hidden="true">
                <svg className="star" id="star-1" viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                  <path d="M12 2l1.8 5.6H20l-4.9 3.6 1.9 5.8L12 13.6 7 17l1.9-5.8L4 7.6h6.2L12 2z" />
                </svg>
                <svg className="star" id="star-2" viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                  <path d="M12 3l1.2 3.7H17l-3 2.2 1.2 3.7-3.2-2.3-3.2 2.3 1.2-3.7-3-2.2h3.8L12 3z" />
                </svg>
                <svg className="star" id="star-3" viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                  <path d="M12 4l1 3h3.2l-2.6 1.9 1 3.1-2.6-1.9-2.6 1.9 1-3.1L7.8 7H11L12 4z" />
                </svg>
                <svg className="star" id="star-4" viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                  <path d="M12 2.5l1.4 4.3h4.5l-3.6 2.6 1.4 4.3-3.7-2.7-3.7 2.7 1.4-4.3-3.6-2.6h4.5L12 2.5z" />
                </svg>
              </span>

              <svg className="cloud-light" id="cloud-1" viewBox="0 0 64 32" focusable="false" aria-hidden="true">
                <path d="M22 26h28a10 10 0 0 0 0-20 13 13 0 0 0-25-2A9 9 0 0 0 22 26z" />
              </svg>
              <svg className="cloud-light" id="cloud-2" viewBox="0 0 64 32" focusable="false" aria-hidden="true">
                <path d="M18 24h20a7 7 0 0 0 0-14 9 9 0 0 0-17-2A6 6 0 0 0 18 24z" />
              </svg>

              <svg className="cloud-dark" id="cloud-4" viewBox="0 0 64 32" focusable="false" aria-hidden="true">
                <path d="M22 26h28a10 10 0 0 0 0-20 13 13 0 0 0-25-2A9 9 0 0 0 22 26z" />
              </svg>
              <svg className="cloud-dark" id="cloud-5" viewBox="0 0 64 32" focusable="false" aria-hidden="true">
                <path d="M18 24h20a7 7 0 0 0 0-14 9 9 0 0 0-17-2A6 6 0 0 0 18 24z" />
              </svg>

              <span className="sun-moon" aria-hidden="true">
                <span className="moon-dot" id="moon-dot-1" />
                <span className="moon-dot" id="moon-dot-2" />
                <span className="moon-dot" id="moon-dot-3" />

                <svg className="light-ray" id="light-ray-1" viewBox="0 0 40 40" focusable="false" aria-hidden="true">
                  <circle cx="20" cy="20" r="18" />
                </svg>
                <svg className="light-ray" id="light-ray-2" viewBox="0 0 50 50" focusable="false" aria-hidden="true">
                  <circle cx="25" cy="25" r="22" />
                </svg>
                <svg className="light-ray" id="light-ray-3" viewBox="0 0 56 56" focusable="false" aria-hidden="true">
                  <circle cx="28" cy="28" r="26" />
                </svg>
              </span>
            </span>
          </label>
          <motion.button
            className="nav-link"
            onClick={() => onNavigate('chat')}
            whileTap={{ scale: 0.98 }}
          >
            Get Started
          </motion.button>
        </div>
      </div>
    </motion.nav>
  );
}

export default Navbar;
