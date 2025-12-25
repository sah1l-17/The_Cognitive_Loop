import './Games.css';

function Games({ onNavigate }) {
  const games = [
    {
      id: 'swipe-sort',
      eyebrow: 'Game 01',
      title: 'Swipe-Sort',
      description:
        'Stop relying on slow, rote memorization and start building true muscle memory. Swipe-Sort turns your study material into a rapid-fire decision game where you swipe left or right to categorize facts, formulas, and concepts instantly. It’s the fastest, most addictive way to test your reflexes and ensure you know your material inside out.',
      imageSrc: './public/swipe-sort.png',
      imageAlt: 'Swipe-Sort game preview',
    },
    {
      id: 'imposter',
      eyebrow: 'Game 02',
      title: 'The Imposter',
      description:
        "True mastery isn't just about knowing the right answer—it's about spotting the wrong one. In this game, our AI generates a group of related concepts hiding a single, clever \"imposter\" that doesn't belong. You’ll need to use deep critical thinking to catch the subtle traps and analyze the nuances that separate similar ideas.",
      imageSrc: './public/imposter.png',
      imageAlt: 'Imposter game preview',
    },
    {
      id: 'pair',
      eyebrow: 'Game 03',
      title: 'Pair Match',
      description:
        'Knowledge is all about making connections. Pair Match challenges you to link terms to definitions, causes to effects, or problems to solutions in a grid of hidden cards. It’s a reimagined classic that moves beyond simple recall to test how well you understand the underlying relationships between the complex topics you are learning.',
      imageSrc: './public/pair.png',
      imageAlt: 'Pair game preview',
    },
  ];

  return (
    <div className="games">
      <section className="games-hero">
        <div className="container">
          <div className="eyebrow">Games</div>
          <h1 className="games-title">Practice that feels like play</h1>
          <p className="games-subtitle">
            Short, focused mini-games designed around active recall. Pick a mode, hit play, and build mastery.
          </p>
        </div>
      </section>

      {games.map((game, idx) => {
        const isReversed = idx % 2 === 1;
        const sectionClass = idx % 2 === 1 ? 'section section-muted' : 'section';

        return (
          <section key={game.id} className={sectionClass}>
            <div className="container">
              <div className={`game-grid ${isReversed ? 'reverse' : ''}`}>
                <div className="game-copy">
                  <div className="eyebrow">{game.eyebrow}</div>
                  <h2 className="section-title">{game.title}</h2>
                  <p className="section-subtitle">{game.description}</p>

                  <div className="game-actions">
                    <button 
                      className="btn btn-primary" 
                      type="button"
                      onClick={() => {
                        if (game.id === 'swipe-sort') onNavigate('swipe-sort-game');
                        if (game.id === 'imposter') onNavigate('impostor-game');
                        if (game.id === 'pair') onNavigate('match-pairs-game');
                      }}
                    >
                      Play
                    </button>
                  </div>
                </div>

                <div className="game-media">
                  <div className="game-card">
                    <img
                      className="game-image"
                      src={game.imageSrc}
                      alt={game.imageAlt}
                      loading="lazy"
                      onError={(e) => {
                        e.currentTarget.src = '/image1.png';
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}

export default Games;
