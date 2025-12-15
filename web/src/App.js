import { useState, useEffect } from 'react'
import { Chess } from 'chess.js'
import { Chessboard } from 'react-chessboard'
import axios from 'axios'
import './App.css'

// API URL - uses environment variable or defaults to proxy
const API_URL = process.env.REACT_APP_API_URL || ''

function App() {
  const [game, setGame] = useState(new Chess())
  const [position, setPosition] = useState(game.fen())
  const [analysis, setAnalysis] = useState(null)
  const [thinking, setThinking] = useState(false)
  const [status, setStatus] = useState('New game - Your move!')
  const [depth, setDepth] = useState(5)

  useEffect(() => {
    newGame()
  }, [])

  const newGame = async () => {
    try {
      await axios.post(`${API_URL}/api/newgame`)
      const freshGame = new Chess()
      setGame(freshGame)
      setPosition(freshGame.fen())
      setAnalysis(null)
      setStatus('New game - Your move!')
    } catch (error) {
      console.error('Error:', error)
      setStatus('Error connecting to server')
    }
  }

  const onDrop = (sourceSquare, targetSquare) => {
    if (thinking) {
      console.log('AI is thinking, cannot move')
      return false
    }

    console.log(`Attempting move: ${sourceSquare} -> ${targetSquare}`)

    // Try move in chess.js first
    const gameCopy = new Chess(game.fen())
    let move = null

    try {
      // Try the move
      move = gameCopy.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q' // Always promote to queen for now
      })
    } catch (error) {
      console.log('Move failed:', error)
      setStatus('Illegal move!')
      return false
    }

    if (move === null) {
      console.log('Move returned null')
      setStatus('Illegal move!')
      return false
    }

    console.log('Move successful:', move)

    // Update game immediately for responsiveness
    setGame(gameCopy)
    setPosition(gameCopy.fen())
    setStatus('Your move!')

    // Send to backend and get engine move
    handleMove(move, gameCopy)

    return true
  }

  const handleMove = async (move, gameCopy) => {
    try {
      // Send to backend
      const response = await axios.post(`${API_URL}/api/move`, {
        move: move.from + move.to + (move.promotion || '')
      })

      // Check game over
      if (response.data.is_checkmate) {
        setStatus('Checkmate! You win!')
        return
      }
      if (response.data.is_stalemate) {
        setStatus('Stalemate!')
        return
      }

      // AI's turn
      setStatus('AI is thinking...')
      setTimeout(() => makeEngineMove(gameCopy), 500)

    } catch (error) {
      console.error('Error:', error)
      setStatus('Error making move')
    }
  }

  const makeEngineMove = async (currentGame) => {
    setThinking(true)
    try {
      const response = await axios.post(`${API_URL}/api/engine`, { depth })

      const engineMove = response.data.best_move
      const from = engineMove.substring(0, 2)
      const to = engineMove.substring(2, 4)
      const promotion = engineMove.length > 4 ? engineMove[4] : undefined

      const gameCopy = new Chess(currentGame.fen())
      const move = gameCopy.move({ from, to, promotion })

      if (move) {
        setGame(gameCopy)
        setPosition(gameCopy.fen())
        setAnalysis(response.data)

        if (gameCopy.isCheckmate()) {
          setStatus('Checkmate! AI wins!')
        } else if (gameCopy.isStalemate()) {
          setStatus('Stalemate!')
        } else if (gameCopy.isCheck()) {
          setStatus('Check! Your move')
        } else {
          setStatus('Your move')
        }
      }
    } catch (error) {
      console.error('Error:', error)
      setStatus('AI error')
    } finally {
      setThinking(false)
    }
  }

  return (
    <div className="App">
      <h1>♟️ Chess AI</h1>
      
      <div className="container">
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
          
          <div className="status">{status}</div>

          <div className="controls">
            <button onClick={newGame} disabled={thinking}>
              New Game
            </button>
            <div className="depth-control">
              <label>Depth:</label>
              <select value={depth} onChange={(e) => setDepth(Number(e.target.value))} disabled={thinking}>
                <option value={3}>3 - Fast</option>
                <option value={5}>5 - Normal</option>
                <option value={7}>7 - Strong</option>
                <option value={8}>8 - Very Strong</option>
              </select>
            </div>
          </div>
        </div>

        <div className="info-section">
          <div className="panel">
            <h2>Engine Analysis</h2>
            {analysis ? (
              <>
                <div className="stat">
                  <span>Best Move:</span>
                  <span>{analysis.best_move}</span>
                </div>
                <div className="stat">
                  <span>Evaluation:</span>
                  <span>{(analysis.score / 100).toFixed(2)}</span>
                </div>
                <div className="stat">
                  <span>Depth:</span>
                  <span>{analysis.depth}</span>
                </div>
                <div className="stat">
                  <span>Nodes:</span>
                  <span>{analysis.nodes.toLocaleString()}</span>
                </div>
                <div className="stat">
                  <span>Time:</span>
                  <span>{analysis.time_ms}ms</span>
                </div>
                {analysis.pv && analysis.pv.length > 0 && (
                  <div className="pv">
                    <span>PV:</span>
                    <div>{analysis.pv.slice(0, 5).join(' → ')}</div>
                  </div>
                )}
              </>
            ) : (
              <p className="empty">Make a move to see analysis</p>
            )}
            {thinking && (
              <div className="thinking">
                <div className="spinner"></div>
                <span>Thinking...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
