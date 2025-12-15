import { useNavigate } from 'react-router-dom'
import './GameSetup.css'

function GameSetup() {
  const navigate = useNavigate()

  return (
    <div className="game-setup-page">
      <div className="setup-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <h1 className="setup-title">⚔️ Play vs AI</h1>
        <p className="setup-subtitle">Configure your game settings</p>

        <div className="options-panel">
          <h2>Game Options</h2>
          <p className="coming-soon">Configuration options coming soon...</p>
          
          <button 
            className="start-button"
            onClick={() => navigate('/game')}
          >
            Start Game
          </button>
        </div>
      </div>
    </div>
  )
}

export default GameSetup
