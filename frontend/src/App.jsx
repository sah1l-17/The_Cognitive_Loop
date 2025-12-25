import { useEffect, useState } from 'react';
import './App.css';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import About from './pages/About';
import Chat from './pages/Chat';
import Games from './pages/Games';
import ImpostorGame from './pages/ImpostorGame';
import MatchPairsGame from './pages/MatchPairsGame';
import SwipeSortGame from './pages/SwipeSortGame';

const CURRENT_PAGE_STORAGE_KEY = 'autonomousTutorCurrentPage';

function App() {
  const [currentPage, setCurrentPage] = useState(() => {
    const saved = localStorage.getItem(CURRENT_PAGE_STORAGE_KEY);
    const allowed = new Set(['home', 'chat', 'games', 'impostor-game', 'match-pairs-game', 'swipe-sort-game', 'about']);
    return allowed.has(saved) ? saved : 'home';
  });
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
    const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)')?.matches;
    return prefersDark ? 'dark' : 'light';
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem(CURRENT_PAGE_STORAGE_KEY, currentPage);
  }, [currentPage]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <Home />;
      case 'games':
        return <Games onNavigate={setCurrentPage} />;
      case 'impostor-game':
        return <ImpostorGame />;
      case 'match-pairs-game':
        return <MatchPairsGame />;
      case 'swipe-sort-game':
        return <SwipeSortGame />;
      case 'about':
        return <About />;
      case 'chat':
        return <Chat />;
      default:
        return <Home />;
    }
  };

  return (
    <div className="app">
      <Navbar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        theme={theme}
        onToggleTheme={toggleTheme}
      />
      
      <main className="main-content">
        {renderPage()}
        {currentPage !== 'chat' && currentPage !== 'impostor-game' && currentPage !== 'match-pairs-game' && currentPage !== 'swipe-sort-game' && <Footer />}
      </main>
    </div>
  );
}

export default App;