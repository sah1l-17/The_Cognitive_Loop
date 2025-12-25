import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './ImpostorGame.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const SESSION_STORAGE_KEY = 'autonomousTutorSessionId';

function ImpostorGame() {
  const [sessionId, setSessionId] = useState(null);
  const [gameState, setGameState] = useState('loading'); // loading, ready, playing, result
  const [currentGame, setCurrentGame] = useState(null);
  const [queuedGames, setQueuedGames] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [flippedCards, setFlippedCards] = useState([]);
  const [streak, setStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  const [score, setScore] = useState({ correct: 0, total: 0 });
  const [isCorrect, setIsCorrect] = useState(null);
  const [message, setMessage] = useState('');

  // After a selection, flip cards back automatically (but keep selection locked
  // so the user can't re-score by clicking again).
  useEffect(() => {
    if (gameState !== 'result') return;
    const t = window.setTimeout(() => {
      setFlippedCards([]);
    }, 900);
    return () => window.clearTimeout(t);
  }, [gameState]);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    const existingSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!existingSessionId) {
      setSessionId(null);
      setGameState('error');
      setMessage('No session found. Go to Chat, ingest content, and get the concept marked understood first.');
      return;
    }

    setSessionId(existingSessionId);
    setGameState('ready');
    setMessage('Click "Start Game" to play Find the Impostor!');
  };

  const startGame = async () => {
    if (!sessionId) {
      setMessage('Error: No session found. Please refresh the page.');
      return;
    }

    setGameState('loading');
    setMessage('Generating game...');

    try {
      // Request a batch of games from the backend
      const response = await fetch(`${API_BASE}/api/game/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          game_type: 'impostor',
          nuances: []
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate game');
      }

      const data = await response.json();

      const batch = data?.response;
      const games = Array.isArray(batch?.games) ? batch.games : [];
      if (games.length === 0) {
        throw new Error('No games returned from server');
      }

      setCurrentGame(games[0]);
      setQueuedGames(games.slice(1));
      setGameState('playing');
      setSelectedCard(null);
      setFlippedCards([]);
      setIsCorrect(null);
      setMessage('Find the impostor! Click on a card to reveal.');
    } catch (error) {
      console.error('Error starting game:', error);
      setMessage(`Error: ${error.message}`);
      setGameState('error');
    }
  };

  const handleCardClick = (option, index) => {
    if (flippedCards.includes(index) || selectedCard !== null) return;

    // Flip the card
    setFlippedCards([...flippedCards, index]);
    setSelectedCard(option);

    // Check if it's the impostor
    const correct = option === currentGame.impostor;
    setIsCorrect(correct);

    // Persist stats to backend (best effort)
    if (sessionId) {
      fetch(`${API_BASE}/api/game/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          game_type: 'impostor',
          is_correct: correct,
          selected: option,
        }),
      }).catch(() => {
        // ignore network errors; UI still works locally
      });
    }

    // Update streak and score
    if (correct) {
      const newStreak = streak + 1;
      setStreak(newStreak);
      if (newStreak > bestStreak) {
        setBestStreak(newStreak);
      }
      setScore({ correct: score.correct + 1, total: score.total + 1 });
      setMessage('🎉 Correct! You found the impostor!');
    } else {
      setStreak(0);
      setScore({ correct: score.correct, total: score.total + 1 });
      setMessage('❌ Wrong! That was not the impostor.');
    }

    setGameState('result');
  };

  const playNext = () => {
    if (queuedGames.length > 0) {
      const [next, ...rest] = queuedGames;
      setCurrentGame(next);
      setQueuedGames(rest);
      setGameState('playing');
      setSelectedCard(null);
      setFlippedCards([]);
      setIsCorrect(null);
      setMessage('Find the impostor! Click on a card to reveal.');
      return;
    }

    // No queued games left; fetch a new batch.
    startGame();
  };

  const resetStats = () => {
    setStreak(0);
    setBestStreak(0);
    setScore({ correct: 0, total: 0 });
    setMessage('Stats reset! Ready for a fresh start.');
  };

  const getAccuracy = () => {
    if (score.total === 0) return 0;
    return Math.round((score.correct / score.total) * 100);
  };

  return (
    <div className="impostor-game">
      <div className="container">
        {/* Header */}
        <motion.div
          className="game-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="game-title-section">
            <h1 className="game-title">
               Find the <span className="accent">Impostor</span>
            </h1>
            <p className="game-subtitle">
              One of these options doesn't belong. Can you spot it?
            </p>
          </div>

          {/* Stats Bar */}
          <div className="stats-bar">
            <div className="stat-card">
              <div className="stat-label">Current Streak</div>
              <div className="stat-value streak-value">{streak} 🔥</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Best Streak</div>
              <div className="stat-value">{bestStreak}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Accuracy</div>
              <div className="stat-value">{getAccuracy()}%</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Score</div>
              <div className="stat-value">{score.correct}/{score.total}</div>
            </div>
          </div>
        </motion.div>

        {/* Message Area */}
        <AnimatePresence mode="wait">
          {message && (
            <motion.div
              className={`message ${isCorrect === true ? 'success' : isCorrect === false ? 'error' : 'info'}`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
            >
              {message}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Game Area */}
        <div className="game-area">
          {gameState === 'loading' && (
            <motion.div
              className="loading-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="loader"></div>
              <p>Generating your game...</p>
            </motion.div>
          )}

          {gameState === 'ready' && (
            <motion.div
              className="ready-state"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <button className="btn btn-primary btn-large" onClick={startGame}>
                🎮 Start Game
              </button>
              {score.total > 0 && (
                <button className="btn btn-secondary" onClick={resetStats}>
                  Reset Stats
                </button>
              )}
            </motion.div>
          )}

          {(gameState === 'playing' || gameState === 'result') && currentGame && (
            <motion.div
              className="game-board"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4 }}
            >
              <div className="cards-grid">
                {currentGame.options.map((option, index) => (
                  <motion.div
                    key={index}
                    className="card-wrapper"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div
                      className={`flip-card-game ${selectedCard !== null ? 'disabled' : ''} ${flippedCards.includes(index) ? 'flipped' : ''} ${
                        selectedCard === option && option === currentGame.impostor ? 'impostor' : ''
                      } ${
                        selectedCard === option && option !== currentGame.impostor ? 'not-impostor' : ''
                      }`}
                      onClick={() => handleCardClick(option, index)}
                      role="button"
                      tabIndex={0}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          handleCardClick(option, index);
                        }
                      }}
                    >
                      <div className="flip-card-game-inner">
                        {/* Front of card */}
                        <div className="flip-card-game-front">
                          <div className="card-number">Option {index + 1}</div>
                          <p className="card-text">{option}</p>
                          <div className="card-hint">Click to reveal</div>
                        </div>

                        {/* Back of card */}
                        <div className="flip-card-game-back">
                          <div className="reveal-content">
                            {option === currentGame.impostor ? (
                              <>
                                <div className="reveal-icon impostor-icon">🚨</div>
                                <div className="reveal-title">IMPOSTOR!</div>
                                <p className="reveal-text">This is the odd one out</p>
                              </>
                            ) : (
                              <>
                                <div className="reveal-icon genuine-icon">✓</div>
                                <div className="reveal-title">Genuine</div>
                                <p className="reveal-text">This belongs to the group</p>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {gameState === 'result' && typeof currentGame.why === 'string' && currentGame.why.trim().length > 0 && (
                <div className="why-panel" aria-live="polite">
                  <div className="why-title">Why</div>
                  <p className="why-text">
                    {isCorrect === true
                      ? currentGame.why
                      : `Correct impostor: ${currentGame.impostor}. ${currentGame.why}`}
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              {gameState === 'result' && (
                <motion.div
                  className="game-actions"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <button className="btn btn-primary" onClick={playNext}>
                    ▶ Next Game
                  </button>
                  <button className="btn btn-secondary" onClick={() => setGameState('ready')}>
                    Reset Score
                  </button>
                </motion.div>
              )}
            </motion.div>
          )}

          {gameState === 'error' && (
            <motion.div
              className="error-state"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="error-icon">⚠️</div>
              <p>{message}</p>
              <button className="btn btn-secondary" onClick={initializeSession}>
                Retry
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ImpostorGame;
