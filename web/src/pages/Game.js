import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import './Game.css'

const API_URL = process.env.REACT_APP_API_URL || 'https://chess-ai-production.up.railway.app'

// Initial chess board setup (white on bottom, black on top)
const INITIAL_BOARD = [
  ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],  // Black back rank (row 0 = rank 8)
  ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],  // Black pawns (row 1 = rank 7)
  [null, null, null, null, null, null, null, null],  // Empty (row 2 = rank 6)
  [null, null, null, null, null, null, null, null],  // Empty (row 3 = rank 5)
  [null, null, null, null, null, null, null, null],  // Empty (row 4 = rank 4)
  [null, null, null, null, null, null, null, null],  // Empty (row 5 = rank 3)
  ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],  // White pawns (row 6 = rank 2)
  ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']   // White back rank (row 7 = rank 1)
]

// Unicode chess pieces
const PIECES = {
  'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
  'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
}

// Convert row/col to chess notation (e.g., [6,0] -> "a2")
const toChessNotation = (row, col) => {
  const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
  const rank = 8 - row
  return files[col] + rank
}

// Convert chess notation to row/col (e.g., "a2" -> [6,0])
const fromChessNotation = (notation) => {
  const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
  const col = files.indexOf(notation[0])
  const row = 8 - parseInt(notation[1])
  return { row, col }
}

function Game() {
  const navigate = useNavigate()
  const [board, setBoard] = useState(INITIAL_BOARD)
  const [selectedSquare, setSelectedSquare] = useState(null)
  const [legalMoves, setLegalMoves] = useState([])
  const [status, setStatus] = useState('Your move!')
  const [gameId, setGameId] = useState(null)
  const [isThinking, setIsThinking] = useState(false)

  // Initialize a new game
  useEffect(() => {
    const initGame = async () => {
      try {
        const response = await axios.post(`${API_URL}/api/newgame`)
        setGameId('connected')
        setStatus('Your move!')
      } catch (error) {
        console.error('Backend connection failed:', error)
        setGameId('offline-mode')
        setStatus('Offline mode (backend unavailable)')
      }
    }
    initGame()
  }, [])

  // Get legal moves for a selected piece
  const getLegalMoves = (row, col) => {
    try {
      const moves = calculateLegalMoves(row, col, board)
      return moves
    } catch (error) {
      console.error('Error getting legal moves:', error)
      return []
    }
  }

  // Basic legal move calculation (simplified - shows all possible squares)
  const calculateLegalMoves = (row, col, currentBoard) => {
    const piece = currentBoard[row][col]
    if (!piece) return []
    
    const moves = []
    const pieceType = piece.toLowerCase()
    const isWhite = piece === piece.toUpperCase()
    
    // Pawn moves
    if (pieceType === 'p') {
      const direction = isWhite ? -1 : 1
      
      // One square forward
      if (currentBoard[row + direction]?.[col] === null) {
        moves.push({ row: row + direction, col })
        
        // Two squares forward from starting position
        const startRow = isWhite ? 6 : 1
        if (row === startRow && currentBoard[row + 2 * direction]?.[col] === null) {
          moves.push({ row: row + 2 * direction, col })
        }
      }
      
      // Captures
      for (const dc of [-1, 1]) {
        const targetRow = row + direction
        const targetCol = col + dc
        if (targetRow >= 0 && targetRow < 8 && targetCol >= 0 && targetCol < 8) {
          const targetPiece = currentBoard[targetRow][targetCol]
          if (targetPiece && (targetPiece === targetPiece.toLowerCase()) !== (piece === piece.toLowerCase())) {
            moves.push({ row: targetRow, col: targetCol })
          }
        }
      }
    }
    
    // Knight moves
    if (pieceType === 'n') {
      const knightMoves = [
        [-2, -1], [-2, 1], [-1, -2], [-1, 2],
        [1, -2], [1, 2], [2, -1], [2, 1]
      ]
      for (const [dr, dc] of knightMoves) {
        const newRow = row + dr
        const newCol = col + dc
        if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
          const targetPiece = currentBoard[newRow][newCol]
          if (!targetPiece || (targetPiece === targetPiece.toLowerCase()) !== (piece === piece.toLowerCase())) {
            moves.push({ row: newRow, col: newCol })
          }
        }
      }
    }
    
    // Rook moves
    if (pieceType === 'r') {
      const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]]
      for (const [dr, dc] of directions) {
        for (let i = 1; i < 8; i++) {
          const newRow = row + dr * i
          const newCol = col + dc * i
          if (newRow < 0 || newRow >= 8 || newCol < 0 || newCol >= 8) break
          
          const targetPiece = currentBoard[newRow][newCol]
          if (!targetPiece) {
            moves.push({ row: newRow, col: newCol })
          } else {
            if ((targetPiece === targetPiece.toLowerCase()) !== (piece === piece.toLowerCase())) {
              moves.push({ row: newRow, col: newCol })
            }
            break
          }
        }
      }
    }
    
    // Bishop moves
    if (pieceType === 'b') {
      const directions = [[1, 1], [1, -1], [-1, 1], [-1, -1]]
      for (const [dr, dc] of directions) {
        for (let i = 1; i < 8; i++) {
          const newRow = row + dr * i
          const newCol = col + dc * i
          if (newRow < 0 || newRow >= 8 || newCol < 0 || newCol >= 8) break
          
          const targetPiece = currentBoard[newRow][newCol]
          if (!targetPiece) {
            moves.push({ row: newRow, col: newCol })
          } else {
            if ((targetPiece === targetPiece.toLowerCase()) !== (piece === piece.toLowerCase())) {
              moves.push({ row: newRow, col: newCol })
            }
            break
          }
        }
      }
    }
    
    // Queen moves (combination of rook and bishop)
    if (pieceType === 'q') {
      const directions = [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [1, -1], [-1, 1], [-1, -1]]
      for (const [dr, dc] of directions) {
        for (let i = 1; i < 8; i++) {
          const newRow = row + dr * i
          const newCol = col + dc * i
          if (newRow < 0 || newRow >= 8 || newCol < 0 || newCol >= 8) break
          
          const targetPiece = currentBoard[newRow][newCol]
          if (!targetPiece) {
            moves.push({ row: newRow, col: newCol })
          } else {
            if ((targetPiece === targetPiece.toLowerCase()) !== (piece === piece.toLowerCase())) {
              moves.push({ row: newRow, col: newCol })
            }
            break
          }
        }
      }
    }
    
    // King moves
    if (pieceType === 'k') {
      const kingMoves = [
        [-1, -1], [-1, 0], [-1, 1],
        [0, -1], [0, 1],
        [1, -1], [1, 0], [1, 1]
      ]
      for (const [dr, dc] of kingMoves) {
        const newRow = row + dr
        const newCol = col + dc
        if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
          const targetPiece = currentBoard[newRow][newCol]
          if (!targetPiece || (targetPiece === targetPiece.toLowerCase()) !== (piece === piece.toLowerCase())) {
            moves.push({ row: newRow, col: newCol })
          }
        }
      }
    }
    
    return moves
  }

  const handleDragStart = (e, row, col) => {
    const piece = board[row][col]
    // Allow dragging white pieces (uppercase) since we play as white
    if (piece && piece === piece.toUpperCase()) {
      e.dataTransfer.effectAllowed = 'move'
      e.dataTransfer.setData('text/plain', JSON.stringify({ row, col }))
      
      // Set selected square and show legal moves
      setSelectedSquare({ row, col })
      const moves = getLegalMoves(row, col)
      setLegalMoves(moves)
    } else {
      e.preventDefault()
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = async (e, toRow, toCol) => {
    e.preventDefault()
    
    try {
      const data = e.dataTransfer.getData('text/plain')
      const { row: fromRow, col: fromCol } = JSON.parse(data)
      
      // Check if it's a legal move
      const isLegalMove = legalMoves.some(move => move.row === toRow && move.col === toCol)
      
      if (isLegalMove) {
        await makeMove(fromRow, fromCol, toRow, toCol)
      }
    } catch (error) {
      console.error('Drop error:', error)
    }
    
    // Clear selection
    setSelectedSquare(null)
    setLegalMoves([])
  }

  const handleDragEnd = () => {
    // Clear selection if drag is cancelled
    setSelectedSquare(null)
    setLegalMoves([])
  }

  const handleSquareClick = async (row, col) => {
    if (selectedSquare) {
      // Check if clicked square is a legal move
      const isLegalMove = legalMoves.some(move => move.row === row && move.col === col)
      
      if (isLegalMove) {
        // Make the move
        await makeMove(selectedSquare.row, selectedSquare.col, row, col)
      }
      
      // Deselect and clear legal moves
      setSelectedSquare(null)
      setLegalMoves([])
    } else {
      // First click - select piece
      const piece = board[row][col]
      
      if (piece && piece === piece.toUpperCase()) {
        // Only select white pieces (uppercase) since we play as white
        setSelectedSquare({ row, col })
        
        // Get and display legal moves
        const moves = getLegalMoves(row, col)
        setLegalMoves(moves)
      }
    }
  }

  const makeMove = async (fromRow, fromCol, toRow, toCol) => {
    if (!gameId) {
      setStatus('Error: Game not initialized')
      return
    }

    // If offline mode, just update the board
    if (gameId === 'offline-mode') {
      const newBoard = [...board.map(row => [...row])]
      const piece = newBoard[fromRow][fromCol]
      newBoard[toRow][toCol] = piece
      newBoard[fromRow][fromCol] = null
      setBoard(newBoard)
      setStatus('Your move! (Offline mode - no AI opponent)')
      return
    }

    try {
      setIsThinking(true)
      setStatus('Making move...')
      
      const fromSquare = toChessNotation(fromRow, fromCol)
      const toSquare = toChessNotation(toRow, toCol)
      const moveStr = fromSquare + toSquare
      
      // Send move to backend for validation
      const response = await axios.post(`${API_URL}/api/move`, {
        move: moveStr
      })
      
      // Update board immediately after backend confirms
      const newBoard = [...board.map(row => [...row])]
      const piece = newBoard[fromRow][fromCol]
      newBoard[toRow][toCol] = piece
      newBoard[fromRow][fromCol] = null
      setBoard(newBoard)
      
      // Check for game over
      if (response.data.is_checkmate) {
        setStatus('Checkmate! You win!')
        setIsThinking(false)
        return
      }
      if (response.data.is_stalemate) {
        setStatus('Stalemate - Draw!')
        setIsThinking(false)
        return
      }
      
      setStatus('AI is thinking...')
      
      // Get AI move
      const aiResponse = await axios.post(`${API_URL}/api/engine`, {
        depth: 4
      })
      
      if (aiResponse.data.best_move) {
        const aiMove = aiResponse.data.best_move
        const from = fromChessNotation(aiMove.substring(0, 2))
        const to = fromChessNotation(aiMove.substring(2, 4))
        
        // Apply AI move to backend first
        await axios.post(`${API_URL}/api/move`, {
          move: aiMove
        })
        
        // Update board with AI move
        const aiBoard = [...newBoard.map(row => [...row])]
        const aiPiece = aiBoard[from.row][from.col]
        aiBoard[to.row][to.col] = aiPiece
        aiBoard[from.row][from.col] = null
        setBoard(aiBoard)
        
        setStatus('Your move!')
      }
    } catch (error) {
      console.error('Error making move:', error)
      const errorMsg = error.response?.data?.detail || error.message
      setStatus('Error: ' + errorMsg)
    } finally {
      setIsThinking(false)
    }
  }

  const isSelected = (row, col) => {
    return selectedSquare && selectedSquare.row === row && selectedSquare.col === col
  }

  const isLegalMove = (row, col) => {
    return legalMoves.some(move => move.row === row && move.col === col)
  }

  return (
    <div className="game-page">
      <div className="game-header">
        <button className="back-button" onClick={() => navigate('/play')}>
          ← Back
        </button>
        <h1>Chess vs AI</h1>
        <button className="new-game-button" onClick={() => {
          setBoard(INITIAL_BOARD)
          setSelectedSquare(null)
          setLegalMoves([])
        }}>
          New Game
        </button>
      </div>

      <div className="game-container">
        <div className="board-section">
          <div className="chessboard">
            {board.map((row, rowIndex) => (
              row.map((piece, colIndex) => {
                const isLight = (rowIndex + colIndex) % 2 === 0
                const selected = isSelected(rowIndex, colIndex)
                const isLegal = isLegalMove(rowIndex, colIndex)
                
                // Allow dragging white pieces since we play as white
                const isDraggable = piece && piece === piece.toUpperCase()
                
                return (
                  <div
                    key={`${rowIndex}-${colIndex}`}
                    className={`square ${isLight ? 'light' : 'dark'} ${selected ? 'selected' : ''} ${isLegal ? 'legal-move' : ''}`}
                    onClick={() => {
                      handleSquareClick(rowIndex, colIndex)
                    }}
                    onDragOver={handleDragOver}
                    onDrop={(e) => handleDrop(e, rowIndex, colIndex)}
                    style={{ cursor: 'pointer' }}
                  >
                    {piece && (
                      <span 
                        className="piece"
                        draggable={isDraggable}
                        onDragStart={(e) => handleDragStart(e, rowIndex, colIndex)}
                        onDragEnd={handleDragEnd}
                        style={{ cursor: isDraggable ? 'grab' : 'default' }}
                      >
                        {PIECES[piece]}
                      </span>
                    )}
                    {isLegal && !piece && (
                      <div className="move-indicator"></div>
                    )}
                    {isLegal && piece && (
                      <div className="capture-indicator"></div>
                    )}
                  </div>
                )
              })
            ))}
          </div>
          
          <div className="status-bar">
            <span>{status}</span>
          </div>
        </div>

        <div className="side-panel">
          <div className="info-section">
            <h3>Game Info</h3>
            <p>Click a piece to select it, then click where to move it.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Game
