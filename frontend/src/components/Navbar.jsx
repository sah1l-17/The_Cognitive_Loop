import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import './Navbar.css';

function Navbar({ currentPage, onNavigate }) {
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > 80) {
        setIsVisible(false);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav 
      className="navbar"
      initial={{ y: -100 }}
      animate={{ y: isVisible ? 0 : -100 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <div className="navbar-container">
        <motion.div 
          className="navbar-brand" 
          onClick={() => onNavigate('home')}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          <span className="brand-text">Autonomous Tutor</span>
        </motion.div>
        
        <div className="navbar-right">
          <div className="navbar-links">
            <motion.button 
              className={`nav-link ${currentPage === 'home' ? 'active' : ''}`}
              onClick={() => onNavigate('home')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Home
            </motion.button>
            <motion.button 
              className={`nav-link ${currentPage === 'about' ? 'active' : ''}`}
              onClick={() => onNavigate('about')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              About
            </motion.button>
          </div>
          
          <motion.button 
            className="cta-button"
            whileTap={{ scale: 0.95 }}
          >
            <span>Get Started</span>
          </motion.button>
        </div>
      </div>
    </motion.nav>
  );
}

export default Navbar;
