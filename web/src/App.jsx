import { useState, useEffect } from 'react'
import { Chess } from 'chess.js'
import { Chessboard } from 'react-chessboard'
import axios from 'axios'
import './App.css'

function App() {
  const [game, setGame] = useState(new Chess())
  const [position, setPosition] = useState(game.fen())
  const [engineAnalysis, setEngineAnalysis] = useState(null)
  const [isThinking, setIsThinking] = useState(false)
  const [moveHistory, setMoveHistory] = useState([])
  const [gameStatus, setGameStatus] = useState('')
  const [engineDepth, setEngineDepth] = useState(5)

  // Initialize game with backend
  useEffect(() => {
    initializeGame()
  }, [])

  const initializeGame = async () => {
    try {
      await axios.post('/api/newgame')
      const newGame = new Chess()
      setGame(newGame)
      setPosition(newGame.fen())
      setMoveHistory([])
      setEngineAnalysis(null)
      setGameStatus('Game started. Your move!')
    } catch (error) {
      console.error('Error initializing game:', error)
      setGameStatus('Error connecting to server')
    }
  }

  const makeMove = async (sourceSquare, targetSquare, piece) => {
    try {
      // Validate move with chess.js
      const gameCopy = new Chess(game.fen())
      let move = null
      
      // Check if it's a promotion
      if (piece[1] === 'P' && (targetSquare[1] === '8' || targetSquare[1] === '1')) {
        move = gameCopy.move({
          from: sourceSquare,
          to: targetSquare,
          promotion: 'q' // Auto-promote to queen for now
        })
      } else {
        move = gameCopy.move({
          from: sourceSquare,
          to: targetSquare
        })
      }

      if (move === null) {
        setGameStatus('Illegal move!')
        return false
      }

      // Send move to backend
      const response = await axios.post('/api/move', {
        move: move.from + move.to + (move.promotion || '')
      })

      if (response.data.success) {
        setGame(gameCopy)
        setPosition(gameCopy.fen())
        setMoveHistory([...moveHistory, move.san])
        
        // Check game status
        if (response.data.is_checkmate) {
          setGameStatus('Checkmate! You win!')
        } else if (response.data.is_stalemate) {
          setGameStatus('Stalemate!')
        } else if (gameCopy.isCheck()) {
          setGameStatus('Check! AI is thinking...')
          setTimeout(() => makeEngineMove(gameCopy), 500)
        } else {
          setGameStatus('AI is thinking...')
          setTimeout(() => makeEngineMove(gameCopy), 500)
        }
        
        return true
      }
      
      return false
    } catch (error) {
      console.error('Error making move:', error)
      setGameStatus('Error making move')
      return false
    }
  }

  const makeEngineMove = async (currentGame) => {
    setIsThinking(true)
    try {
      const response = await axios.post('/api/engine', {
        depth: engineDepth
      })

      const engineMove = response.data.best_move
      const from = engineMove.substring(0, 2)
      const to = engineMove.substring(2, 4)
      const promotion = engineMove.length > 4 ? engineMove[4] : undefined

      const gameCopy = new Chess(currentGame.fen())
      const move = gameCopy.move({
        from,
        to,
        promotion
      })

      if (move) {
        setGame(gameCopy)
        setPosition(gameCopy.fen())
        setMoveHistory([...moveHistory, move.san])
        setEngineAnalysis({
          bestMove: move.san,
          score: response.data.score,
          depth: response.data.depth,
          nodes: response.data.nodes,
          time: response.data.time_ms,
          pv: response.data.pv
        })

        // Check game status
        if (gameCopy.isCheckmate()) {
          setGameStatus('Checkmate! AI wins!')
        } else if (gameCopy.isStalemate()) {
          setGameStatus('Stalemate!')
        } else if (gameCopy.isCheck()) {
          setGameStatus('Check! Your move.')
        } else {
          setGameStatus('Your move.')
        }
      }
    } catch (error) {
      console.error('Error getting engine move:', error)
      setGameStatus('Error: AI could not move')
    } finally {
      setIsThinking(false)
    }
  }

  const onDrop = (sourceSquare, targetSquare, piece) => {
    if (isThinking) return false
    return makeMove(sourceSquare, targetSquare, piece)
  }

  const formatScore = (score) => {
    if (!score) return '0.00'
    return (score / 100).toFixed(2)
  }

  const formatTime = (ms) => {
    if (!ms) return '0s'
    return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(2)}s`
  }

  return (
    <div className="App">
      <h1>♟️ Chess AI</h1>
      
      <div className="game-container">
        <div className="board-section">
          <div className="board-wrapper">
            <Chessboard 
              position={position}
              onPieceDrop={onDrop}
              boardWidth={560}
              customBoardStyle={{
                borderRadius: '10px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
              }}
            />
          </div>
          
          <div className="game-status">
            {gameStatus}
          </div>

          <div className="controls">
            <button onClick={initializeGame} disabled={isThinking}>
              New Game
            </button>
            <div className="depth-control">
              <label>Depth:</label>
              <select 
                value={engineDepth} 
                onChange={(e) => setEngineDepth(Number(e.target.value))}
                disabled={isThinking}
              >
                <option value={3}>3 - Fast</option>
                <option value={5}>5 - Normal</option>
                <option value={7}>7 - Strong</option>
                <option value={8}>8 - Very Strong</option>
              </select>
            </div>
          </div>
        </div>

        <div className="info-section">
          <div className="analysis-panel">
            <h2>Engine Analysis</h2>
            {engineAnalysis ? (
              <>
                <div className="stat">
                  <span className="label">Best Move:</span>
                  <span className="value">{engineAnalysis.bestMove}</span>
                </div>
                <div className="stat">
                  <span className="label">Evaluation:</span>
                  <span className="value">{formatScore(engineAnalysis.score)}</span>
                </div>
                <div className="stat">
                  <span className="label">Depth:</span>
                  <span className="value">{engineAnalysis.depth}</span>
                </div>
                <div className="stat">
                  <span className="label">Nodes:</span>
                  <span className="value">{engineAnalysis.nodes.toLocaleString()}</span>
                </div>
                <div className="stat">
                  <span className="label">Time:</span>
                  <span className="value">{formatTime(engineAnalysis.time)}</span>
                </div>
                {engineAnalysis.pv && engineAnalysis.pv.length > 0 && (
                  <div className="pv">
                    <span className="label">Principal Variation:</span>
                    <div className="pv-moves">
                      {engineAnalysis.pv.slice(0, 5).join(' → ')}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <p className="no-analysis">Make a move to see engine analysis</p>
            )}
            
            {isThinking && (
              <div className="thinking">
                <div className="spinner"></div>
                <span>Thinking...</span>
              </div>
            )}
          </div>

          <div className="move-history-panel">
            <h2>Move History</h2>
            <div className="moves">
              {moveHistory.length === 0 ? (
                <p className="no-moves">No moves yet</p>
              ) : (
                moveHistory.map((move, index) => (
                  <div key={index} className="move-item">
                    <span className="move-number">{Math.floor(index / 2) + 1}.</span>
                    <span className="move-text">{move}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
