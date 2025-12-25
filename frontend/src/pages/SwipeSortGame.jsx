import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import './SwipeSortGame.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const SESSION_STORAGE_KEY = 'autonomousTutorSessionId';

const SWIPE_THRESHOLD_PX = 110;

function SwipeSortGame() {
  const [sessionId, setSessionId] = useState(null);
  const [gameState, setGameState] = useState('loading'); // loading, ready, playing, checking, error
  const [currentGame, setCurrentGame] = useState(null);
  const [queuedGames, setQueuedGames] = useState([]);

  const [remainingCards, setRemainingCards] = useState([]);
  const [bucketLeft, setBucketLeft] = useState([]);
  const [bucketRight, setBucketRight] = useState([]);
  const [userAnswers, setUserAnswers] = useState({}); // cardText -> left|right
  const [checkReport, setCheckReport] = useState(null); // { allCorrect: bool, perCard: { [cardText]: { correct, expectedSide, userSide, why } } }

  const [streak, setStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  const [score, setScore] = useState({ points: 0, rounds: 0 });

  const [message, setMessage] = useState('');
  const [resultStatus, setResultStatus] = useState(null); // true|false|null

  useEffect(() => {
    const existingSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!existingSessionId) {
      setSessionId(null);
      setGameState('error');
      setMessage('No session found. Go to Chat, ingest content, and get the concept marked understood first.');
      return;
    }

    setSessionId(existingSessionId);
    setGameState('ready');
    setMessage('Swipe cards left/right into the correct category.');
  }, []);

  const activeCard = remainingCards.length > 0 ? remainingCards[0] : null;

  const leftLabel = currentGame?.left_category || 'Left';
  const rightLabel = currentGame?.right_category || 'Right';

  const allSwiped = useMemo(() => currentGame && remainingCards.length === 0, [currentGame, remainingCards.length]);

  const getAccuracy = () => {
    if (score.rounds === 0) return 0;
    return Math.round((score.points / score.rounds) * 100);
  };

  const resetRoundState = (game) => {
    const cards = Array.isArray(game?.cards) ? [...game.cards] : [];
    setRemainingCards(cards);
    setBucketLeft([]);
    setBucketRight([]);
    setUserAnswers({});
    setCheckReport(null);
    setResultStatus(null);
    setMessage('Swipe cards into the correct category.');
  };

  const startGame = async () => {
    if (!sessionId) {
      setMessage('Error: No session found. Please refresh the page.');
      return;
    }

    setGameState('loading');
    setMessage('Generating game...');

    try {
      const response = await fetch(`${API_BASE}/api/game/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          game_type: 'swipe_sort',
          nuances: [],
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to generate game');
      }

      const data = await response.json();
      const batch = data?.response;
      const games = Array.isArray(batch?.games) ? batch.games : [];
      if (games.length === 0) throw new Error('No games returned from server');

      const first = games[0];
      setCurrentGame(first);
      setQueuedGames(games.slice(1));

      resetRoundState(first);
      setGameState('playing');
    } catch (error) {
      console.error('Error starting swipe-sort:', error);
      setMessage(`Error: ${error.message}`);
      setGameState('error');
    }
  };

  const resetStats = () => {
    setStreak(0);
    setBestStreak(0);
    setScore({ points: 0, rounds: 0 });
    setMessage('Stats reset! Ready for a fresh start.');
  };

  const recordSwipe = (cardText, side) => {
    setUserAnswers((prev) => ({ ...prev, [cardText]: side }));
    if (side === 'left') {
      setBucketLeft((prev) => [...prev, cardText]);
    } else {
      setBucketRight((prev) => [...prev, cardText]);
    }
    setRemainingCards((prev) => prev.slice(1));
    setResultStatus(null);
    setCheckReport(null);
  };

  const onDragEnd = (_evt, info) => {
    if (!activeCard) return;
    if (gameState !== 'playing') return;

    const offsetX = info?.offset?.x ?? 0;

    if (offsetX <= -SWIPE_THRESHOLD_PX) {
      recordSwipe(activeCard, 'left');
      return;
    }

    if (offsetX >= SWIPE_THRESHOLD_PX) {
      recordSwipe(activeCard, 'right');
    }
  };

  const handleCheck = () => {
    if (!currentGame) return;
    if (!allSwiped) {
      setMessage('Swipe all cards first, then click Check.');
      return;
    }

    setGameState('checking');

    const answerKey = currentGame.answer_key || {};
    const cards = Array.isArray(currentGame.cards) ? currentGame.cards : [];

    const perCard = {};
    for (const cardText of cards) {
      const expectedSide = answerKey[cardText];
      const userSide = userAnswers[cardText];
      const correct = userSide === expectedSide;
      const why = typeof currentGame?.why?.[cardText] === 'string' ? currentGame.why[cardText] : '';

      perCard[cardText] = {
        correct,
        expectedSide,
        userSide,
        why,
      };
    }

    const allCorrect = cards.every((c) => perCard[c]?.correct === true);
    setCheckReport({ allCorrect, perCard });

    setScore((prev) => ({
      points: prev.points + (allCorrect ? 1 : 0),
      rounds: prev.rounds + 1,
    }));

    setResultStatus(allCorrect);

    if (allCorrect) {
      const nextStreak = streak + 1;
      setStreak(nextStreak);
      if (nextStreak > bestStreak) setBestStreak(nextStreak);
      setMessage('✅ Perfect! All cards are in the correct category. +1 point');
    } else {
      setStreak(0);
      setMessage('❌ Not quite. Some cards are in the wrong category.');
    }

    // Best-effort persistence
    if (sessionId) {
      fetch(`${API_BASE}/api/game/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          game_type: 'swipe_sort',
          is_correct: allCorrect,
          selected: userAnswers,
        }),
      }).catch(() => {});
    }

    setGameState('playing');
  };

  const playNext = () => {
    if (queuedGames.length > 0) {
      const [next, ...rest] = queuedGames;
      setCurrentGame(next);
      setQueuedGames(rest);
      resetRoundState(next);
      setGameState('playing');
      return;
    }

    startGame();
  };

  const retry = () => {
    const existingSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (!existingSessionId) {
      setSessionId(null);
      setGameState('error');
      setMessage('No session found. Go to Chat, ingest content, and get the concept marked understood first.');
      return;
    }

    setSessionId(existingSessionId);
    setGameState('ready');
    setMessage('Swipe cards left/right into the correct category.');
  };

  return (
    <div className="swipe-sort-game">
      <div className="container">
        <motion.div
          className="game-header"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="game-title-section">
            <h1 className="game-title">
              Swipe <span className="accent">Sort</span>
            </h1>
            <p className="game-subtitle">Swipe left/right to sort cards into categories.</p>
          </div>

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
              <div className="stat-value">{score.points}/{score.rounds}</div>
            </div>
          </div>
        </motion.div>

        <AnimatePresence mode="wait">
          {message && (
            <motion.div
              className={`message ${resultStatus === true ? 'success' : resultStatus === false ? 'error' : 'info'}`}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
            >
              {message}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="game-area">
          {gameState === 'loading' && (
            <motion.div className="loading-state" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="loader"></div>
              <p>Generating your game...</p>
            </motion.div>
          )}

          {gameState === 'ready' && (
            <motion.div className="ready-state" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <button className="btn btn-primary btn-large" onClick={startGame}>
                🎮 Start Game
              </button>
              {score.rounds > 0 && (
                <button className="btn btn-secondary" onClick={resetStats}>
                  Reset Stats
                </button>
              )}
            </motion.div>
          )}

          {gameState === 'playing' && currentGame && (
            <div className="swipe-layout">
              <div className="bucket">
                <div className="bucket-title">{leftLabel}</div>
                <div className="bucket-list" aria-label="Left bucket">
                  {bucketLeft.map((t, idx) => (
                    <div
                      key={`${t}-${idx}`}
                      className={`bucket-item ${checkReport?.perCard?.[t]?.correct === true ? 'correct' : checkReport?.perCard?.[t]?.correct === false ? 'wrong' : ''}`}
                    >
                      {t}
                    </div>
                  ))}
                </div>
              </div>

              <div className="swipe-center">
                <div className="swipe-stack" aria-label="Swipe cards">
                  {activeCard ? (
                    <motion.div
                      key={activeCard}
                      className="swipe-card"
                      drag="x"
                      dragConstraints={{ left: 0, right: 0 }}
                      dragElastic={0.2}
                      onDragEnd={onDragEnd}
                      whileDrag={{ rotate: 6 }}
                    >
                      <div className="swipe-card-text">{activeCard}</div>
                      <div className="swipe-card-hint">Swipe ← for left, → for right</div>
                    </motion.div>
                  ) : (
                    <div className="empty-stack">
                      <div className="empty-title">All cards swiped</div>
                      <div className="empty-subtitle">Click Check to score this round.</div>
                    </div>
                  )}
                </div>

                <div className="swipe-actions">
                  <button className="btn btn-primary" onClick={handleCheck} disabled={!allSwiped}>
                    Check
                  </button>
                  <button className="btn btn-secondary" onClick={playNext} disabled={!checkReport}>
                    ▶ Next
                  </button>
                </div>

                {checkReport && (
                  <div className="review-panel" aria-live="polite">
                    <div className="review-title">Review</div>
                    <div className="review-list">
                      {Array.isArray(currentGame.cards) &&
                        currentGame.cards.map((cardText) => {
                          const r = checkReport.perCard?.[cardText];
                          if (!r) return null;

                          const expectedLabel = r.expectedSide === 'left' ? leftLabel : rightLabel;
                          const chosenLabel = r.userSide === 'left' ? leftLabel : rightLabel;

                          return (
                            <div key={cardText} className={`review-item ${r.correct ? 'correct' : 'wrong'}`}>
                              <div className="review-item-head">
                                <div className="review-item-status">{r.correct ? '✅ Correct' : '❌ Wrong'}</div>
                                {!r.correct && (
                                  <div className="review-item-meta">
                                    You chose: <span className="review-pill">{chosenLabel}</span> · Expected:{' '}
                                    <span className="review-pill">{expectedLabel}</span>
                                  </div>
                                )}
                              </div>
                              <div className="review-card-text">{cardText}</div>
                              {r.why && r.why.trim().length > 0 && <div className="review-why">{r.why}</div>}
                            </div>
                          );
                        })}
                    </div>
                  </div>
                )}
              </div>

              <div className="bucket">
                <div className="bucket-title">{rightLabel}</div>
                <div className="bucket-list" aria-label="Right bucket">
                  {bucketRight.map((t, idx) => (
                    <div
                      key={`${t}-${idx}`}
                      className={`bucket-item ${checkReport?.perCard?.[t]?.correct === true ? 'correct' : checkReport?.perCard?.[t]?.correct === false ? 'wrong' : ''}`}
                    >
                      {t}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {gameState === 'error' && (
            <motion.div className="error-state" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="error-icon">⚠️</div>
              <p>{message}</p>
              <button className="btn btn-secondary" onClick={retry}>
                Retry
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SwipeSortGame;
