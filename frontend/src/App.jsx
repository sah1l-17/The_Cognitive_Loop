import { useState } from 'react';
import './App.css';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import About from './pages/About';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  const renderPage = () => {
    switch (currentPage) {
      case 'home':
        return <Home />;
      case 'about':
        return <About />;
      default:
        return <Home />;
    }
  };

  return (
    <div className="app">
      <Navbar currentPage={currentPage} onNavigate={setCurrentPage} />
      
      <main className="main-content">
        {renderPage()}
        <Footer />
      </main>
    </div>
  );
}

export default App;
