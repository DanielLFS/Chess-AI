import { useNavigate } from 'react-router-dom'
import './HomePage.css'

function HomePage() {
  const navigate = useNavigate()

  return (
    <div className="home-page">
      <div className="home-container">
        <div className="hero-section">
          <h1 className="title">♟️ Chess AI</h1>
          <p className="subtitle">Challenge a powerful chess engine</p>
        </div>

        <div className="game-modes">
          <button 
            className="mode-card primary"
            onClick={() => navigate('/play')}
          >
            <div className="mode-icon">⚔️</div>
            <h2>Play vs AI</h2>
            <p>Challenge the engine</p>
          </button>

          <div className="mode-card secondary disabled">
            <div className="mode-icon">👥</div>
            <h2>Multiplayer</h2>
            <p className="coming-soon">Coming soon...</p>
          </div>

          <div className="mode-card secondary disabled">
            <div className="mode-icon">🔍</div>
            <h2>Analysis</h2>
            <p className="coming-soon">Coming soon...</p>
          </div>
        </div>

        <div className="features">
          <div className="feature-item">
            <span className="feature-icon">🧠</span>
            <span>Advanced AI Engine</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">⚡</span>
            <span>Fast Response</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🎯</span>
            <span>Multiple Difficulty Levels</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
