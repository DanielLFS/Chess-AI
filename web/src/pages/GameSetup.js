import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './GameSetup.css'

function GameSetup() {
  const navigate = useNavigate()
  
  // Game options state
  const [difficulty, setDifficulty] = useState(4)
  const [playerColor, setPlayerColor] = useState('white')
  const [showCoordinates, setShowCoordinates] = useState(true)
  const [showLastMove, setShowLastMove] = useState(true)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [boardTheme, setBoardTheme] = useState('classic')
  const [gameMode, setGameMode] = useState('ai')

  const startGame = () => {
    // Pass settings via state to Game component
    navigate('/game', {
      state: {
        difficulty,
        playerColor,
        showCoordinates,
        showLastMove,
        soundEnabled,
        boardTheme,
        gameMode
      }
    })
  }

  return (
    <div className="game-setup-page">
      <div className="setup-container">
        <button className="back-button" onClick={() => navigate('/')}>
          ← Back to Home
        </button>

        <h1 className="setup-title">⚔️ Play Chess</h1>
        <p className="setup-subtitle">Configure your game settings</p>

        <div className="options-grid">
          {/* Left Column - Gameplay */}
          <div className="options-section">
            <h2>🎮 Gameplay Options</h2>
            
            <div className="option-group">
              <label>Game Mode</label>
              <select value={gameMode} onChange={(e) => setGameMode(e.target.value)}>
                <option value="ai">vs AI</option>
                <option value="local">Local 2 Player</option>
                <option value="analysis">Analysis Mode</option>
              </select>
            </div>

            {gameMode === 'ai' && (
              <div className="option-group">
                <label>Difficulty</label>
                <select value={difficulty} onChange={(e) => setDifficulty(Number(e.target.value))}>
                  <option value={1}>1 - Beginner</option>
                  <option value={2}>2 - Easy</option>
                  <option value={3}>3 - Medium</option>
                  <option value={4}>4 - Normal</option>
                  <option value={5}>5 - Hard</option>
                  <option value={6}>6 - Expert</option>
                  <option value={7}>7 - Master</option>
                  <option value={8}>8 - Grand Master</option>
                </select>
              </div>
            )}

            <div className="option-group">
              <label>Play As</label>
              <select value={playerColor} onChange={(e) => setPlayerColor(e.target.value)}>
                <option value="white">White</option>
                <option value="black">Black</option>
              </select>
            </div>
          </div>

          {/* Right Column - Visual */}
          <div className="options-section">
            <h2>🎨 Visual Options</h2>
            
            <div className="option-group">
              <label>Board Theme</label>
              <select value={boardTheme} onChange={(e) => setBoardTheme(e.target.value)}>
                <option value="classic">Classic Brown</option>
                <option value="blue">Ocean Blue</option>
                <option value="green">Forest Green</option>
                <option value="purple">Royal Purple</option>
              </select>
            </div>

            <div className="option-group checkbox-group">
              <label>
                <input 
                  type="checkbox" 
                  checked={showCoordinates} 
                  onChange={(e) => setShowCoordinates(e.target.checked)}
                />
                Show Coordinates (a-h, 1-8)
              </label>
            </div>

            <div className="option-group checkbox-group">
              <label>
                <input 
                  type="checkbox" 
                  checked={showLastMove} 
                  onChange={(e) => setShowLastMove(e.target.checked)}
                />
                Highlight Last Move
              </label>
            </div>

            <div className="option-group checkbox-group">
              <label>
                <input 
                  type="checkbox" 
                  checked={soundEnabled} 
                  onChange={(e) => setSoundEnabled(e.target.checked)}
                />
                Sound Effects
              </label>
            </div>
          </div>
        </div>

        <button 
          className="start-button"
          onClick={startGame}
        >
          Start Game →
        </button>
      </div>
    </div>
  )
}

export default GameSetup
