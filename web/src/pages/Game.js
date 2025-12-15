import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
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
  const location = useLocation()
  
  // Get settings from GameSetup page
  const settings = location.state || {}
  const difficulty = settings.difficulty || 4
  const playerColor = settings.playerColor || 'white'
  const showCoordinates = settings.showCoordinates !== undefined ? settings.showCoordinates : true
  const showLastMove = settings.showLastMove !== undefined ? settings.showLastMove : true
  const soundEnabled = settings.soundEnabled !== undefined ? settings.soundEnabled : true
  const boardTheme = settings.boardTheme || 'classic'
  const gameMode = settings.gameMode || 'ai'
  
  const [board, setBoard] = useState(INITIAL_BOARD)
  const [selectedSquare, setSelectedSquare] = useState(null)
  const [legalMoves, setLegalMoves] = useState([])
  const [status, setStatus] = useState('Your move!')
  const [gameId, setGameId] = useState(null)
  const [isThinking, setIsThinking] = useState(false)
  
  // Game state tracking
  const [moveHistory, setMoveHistory] = useState([])
  const [capturedPieces, setCapturedPieces] = useState({ white: [], black: [] })
  const [lastMove, setLastMove] = useState(null)
  const [evaluation, setEvaluation] = useState(0)
  const [thinkingTime, setThinkingTime] = useState(0)
  const [showHint, setShowHint] = useState(false)
  const [hintMove, setHintMove] = useState(null)
  const [promotionPending, setPromotionPending] = useState(null)
  const [currentTurn, setCurrentTurn] = useState('white')

  // Initialize a new game
  useEffect(() => {
    const initGame = async () => {
      try {
        const response = await axios.post(`${API_URL}/api/newgame`)
        setGameId('connected')
        if (gameMode === 'local') {
          setStatus('White to move')
        } else {
          setStatus('Your move!')
        }
      } catch (error) {
        console.error('Backend connection failed:', error)
        setGameId('offline-mode')
        if (gameMode === 'local') {
          setStatus('White to move (Offline mode)')
        } else {
          setStatus('Offline mode (backend unavailable)')
        }
      }
    }
    initGame()
  }, [])

  // Helper function to get piece value for captured pieces
  const getPieceValue = (piece) => {
    const values = { p: 1, n: 3, b: 3, r: 5, q: 9, k: 0 }
    return values[piece.toLowerCase()] || 0
  }

  // Helper function to play move sound
  const playMoveSound = () => {
    if (soundEnabled) {
      const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSl+zPDTiTQHGGS37OihUhELTKXh8bJiHAU2jdXvyHkpBCF0xe/glEILElyx6OyrWRQLRJzd8sFuIwUme8rx1Ik0BxdhuOzooVIRC0uf3vGxYhwFNYzU77dpKgQgcsXv35RDCxFbr+ftrFkVDECa3PG/bSMFJnrI79GJNAYWXrbs6aJTEwtJoNz');
      audio.play().catch(() => {}); // Ignore errors
    }
  }

  // Get hint from engine
  const getHint = async () => {
    if (gameId === 'offline-mode') {
      setStatus('Hints not available in offline mode')
      return
    }
    try {
      setStatus('Calculating hint...')
      const response = await axios.post(`${API_URL}/api/engine`, { depth: difficulty })
      if (response.data.best_move) {
        setHintMove(response.data.best_move)
        setShowHint(true)
        setStatus('Hint shown! Green square = from, Yellow square = to')
      }
    } catch (error) {
      console.error('Error getting hint:', error)
      setStatus('Error getting hint')
    }
  }

  // Undo last move
  const undoMove = () => {
    if (moveHistory.length === 0) return
    // Remove last 2 moves (player + AI)
    const newHistory = [...moveHistory]
    newHistory.pop()
    if (gameMode === 'ai') newHistory.pop()
    setMoveHistory(newHistory)
    // Reset board - would need to replay history or track board states
    setStatus('Undo not fully implemented yet')
  }

  // Check if a king is under attack
  const isSquareAttacked = (kingRow, kingCol, currentBoard, byWhite) => {
    // Check all opponent pieces to see if they can attack this square
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        const piece = currentBoard[row][col]
        if (!piece) continue
        
        const isPieceWhite = piece === piece.toUpperCase()
        if (isPieceWhite !== byWhite) continue
        
        const pieceType = piece.toLowerCase()
        
        // Pawn attacks
        if (pieceType === 'p') {
          const direction = byWhite ? -1 : 1
          if (row + direction === kingRow && Math.abs(col - kingCol) === 1) return true
        }
        
        // Knight attacks
        if (pieceType === 'n') {
          const dr = Math.abs(row - kingRow)
          const dc = Math.abs(col - kingCol)
          if ((dr === 2 && dc === 1) || (dr === 1 && dc === 2)) return true
        }
        
        // King attacks
        if (pieceType === 'k') {
          const dr = Math.abs(row - kingRow)
          const dc = Math.abs(col - kingCol)
          if (dr <= 1 && dc <= 1) return true
        }
        
        // Rook/Queen horizontal/vertical attacks
        if (pieceType === 'r' || pieceType === 'q') {
          if (row === kingRow || col === kingCol) {
            const rowDir = row === kingRow ? 0 : (kingRow - row) / Math.abs(kingRow - row)
            const colDir = col === kingCol ? 0 : (kingCol - col) / Math.abs(kingCol - col)
            let checkRow = row + rowDir
            let checkCol = col + colDir
            let blocked = false
            while (checkRow !== kingRow || checkCol !== kingCol) {
              if (currentBoard[checkRow][checkCol]) {
                blocked = true
                break
              }
              checkRow += rowDir
              checkCol += colDir
            }
            if (!blocked) return true
          }
        }
        
        // Bishop/Queen diagonal attacks
        if (pieceType === 'b' || pieceType === 'q') {
          const dr = Math.abs(row - kingRow)
          const dc = Math.abs(col - kingCol)
          if (dr === dc && dr > 0) {
            const rowDir = (kingRow - row) / dr
            const colDir = (kingCol - col) / dc
            let checkRow = row + rowDir
            let checkCol = col + colDir
            let blocked = false
            while (checkRow !== kingRow || checkCol !== kingCol) {
              if (currentBoard[checkRow][checkCol]) {
                blocked = true
                break
              }
              checkRow += rowDir
              checkCol += colDir
            }
            if (!blocked) return true
          }
        }
      }
    }
    return false
  }

  // Get legal moves for a selected piece
  const getLegalMoves = (row, col) => {
    try {
      const moves = calculateLegalMoves(row, col, board, lastMove)
      
      // Filter out moves that would leave king in check (only in offline/local mode)
      if (gameId === 'offline-mode' || gameMode === 'local') {
        const piece = board[row][col]
        const isWhite = piece === piece.toUpperCase()
        
        return moves.filter(move => {
          // Simulate the move
          const testBoard = board.map(r => [...r])
          testBoard[move.row][move.col] = testBoard[row][col]
          testBoard[row][col] = null
          
          // Handle en passant capture
          if (move.isEnPassant) {
            testBoard[row][move.col] = null
          }
          
          // Find king position
          let kingRow, kingCol
          for (let r = 0; r < 8; r++) {
            for (let c = 0; c < 8; c++) {
              const p = testBoard[r][c]
              if (p && p.toLowerCase() === 'k' && (p === p.toUpperCase()) === isWhite) {
                kingRow = r
                kingCol = c
                break
              }
            }
            if (kingRow !== undefined) break
          }
          
          // Check if king would be in check
          return !isSquareAttacked(kingRow, kingCol, testBoard, !isWhite)
        })
      }
      
      return moves
    } catch (error) {
      console.error('Error getting legal moves:', error)
      return []
    }
  }

  // Basic legal move calculation (simplified - shows all possible squares)
  const calculateLegalMoves = (row, col, currentBoard, lastMove) => {
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
          
          // En passant: check if we can capture a pawn that just moved 2 squares
          if (lastMove) {
            const lastMovedPiece = currentBoard[lastMove.to.row]?.[lastMove.to.col]
            const isEnemyPawn = lastMovedPiece && lastMovedPiece.toLowerCase() === 'p' && 
                                (lastMovedPiece === lastMovedPiece.toLowerCase()) !== (piece === piece.toLowerCase())
            const movedTwoSquares = Math.abs(lastMove.to.row - lastMove.from.row) === 2
            const isAdjacentPawn = lastMove.to.row === row && lastMove.to.col === targetCol
            
            if (isEnemyPawn && movedTwoSquares && isAdjacentPawn) {
              moves.push({ row: targetRow, col: targetCol, isEnPassant: true })
            }
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
      
      // Castling
      // Note: This is a simplified check - doesn't verify if king has moved or is in check
      // The backend will validate the actual legality
      if (isWhite && row === 7 && col === 4) {
        // White kingside castling (e1 to g1)
        if (currentBoard[7][5] === null && currentBoard[7][6] === null && 
            currentBoard[7][7] === 'R') {
          moves.push({ row: 7, col: 6 })
        }
        // White queenside castling (e1 to c1)
        if (currentBoard[7][1] === null && currentBoard[7][2] === null && 
            currentBoard[7][3] === null && currentBoard[7][0] === 'R') {
          moves.push({ row: 7, col: 2 })
        }
      } else if (!isWhite && row === 0 && col === 4) {
        // Black kingside castling (e8 to g8)
        if (currentBoard[0][5] === null && currentBoard[0][6] === null && 
            currentBoard[0][7] === 'r') {
          moves.push({ row: 0, col: 6 })
        }
        // Black queenside castling (e8 to c8)
        if (currentBoard[0][1] === null && currentBoard[0][2] === null && 
            currentBoard[0][3] === null && currentBoard[0][0] === 'r') {
          moves.push({ row: 0, col: 2 })
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
        // Check if this is a pawn promotion
        const piece = board[selectedSquare.row][selectedSquare.col]
        const isPromotion = (piece === 'P' && row === 0) || (piece === 'p' && row === 7)
        
        if (isPromotion) {
          // Show promotion dialog
          setPromotionPending({ fromRow: selectedSquare.row, fromCol: selectedSquare.col, toRow: row, toCol: col })
        } else {
          // Make the move normally
          await makeMove(selectedSquare.row, selectedSquare.col, row, col)
        }
      }
      
      // Deselect and clear legal moves
      setSelectedSquare(null)
      setLegalMoves([])
    } else {
      // First click - select piece
      const piece = board[row][col]
      
      if (piece) {
        // In local mode, allow selecting pieces based on turn
        // In AI mode, only allow selecting white pieces
        const isWhitePiece = piece === piece.toUpperCase()
        const canSelect = gameMode === 'local' 
          ? (currentTurn === 'white' && isWhitePiece) || (currentTurn === 'black' && !isWhitePiece)
          : isWhitePiece
        
        if (canSelect) {
          setSelectedSquare({ row, col })
          
          // Get and display legal moves
          const moves = getLegalMoves(row, col)
          setLegalMoves(moves)
        }
      }
    }
  }

  const makeMove = async (fromRow, fromCol, toRow, toCol, promotion = 'q') => {
    if (!gameId) {
      setStatus('Error: Game not initialized')
      return
    }

    // If offline mode or local multiplayer, just update the board without backend
    if (gameId === 'offline-mode' || gameMode === 'local') {
      const newBoard = [...board.map(row => [...row])]
      const piece = newBoard[fromRow][fromCol]
      const capturedPiece = newBoard[toRow][toCol]
      newBoard[toRow][toCol] = piece
      newBoard[fromRow][fromCol] = null
      
      // Handle promotion in offline mode
      const isPromotion = (piece === 'P' && toRow === 0) || (piece === 'p' && toRow === 7)
      if (isPromotion) {
        const isWhitePiece = piece === piece.toUpperCase()
        newBoard[toRow][toCol] = isWhitePiece ? promotion.toUpperCase() : promotion.toLowerCase()
      }
      
      // Handle en passant in offline mode
      if ((piece === 'P' || piece === 'p') && Math.abs(toCol - fromCol) === 1 && !capturedPiece) {
        const capturedPawnRow = fromRow
        newBoard[capturedPawnRow][toCol] = null
      }
      
      // Handle castling in offline mode
      if ((piece === 'K' || piece === 'k') && Math.abs(toCol - fromCol) === 2) {
        // Kingside castling
        if (toCol > fromCol) {
          const rookFromCol = 7
          const rookToCol = toCol - 1
          newBoard[toRow][rookToCol] = newBoard[toRow][rookFromCol]
          newBoard[toRow][rookFromCol] = null
        }
        // Queenside castling
        else {
          const rookFromCol = 0
          const rookToCol = toCol + 1
          newBoard[toRow][rookToCol] = newBoard[toRow][rookFromCol]
          newBoard[toRow][rookFromCol] = null
        }
      }
      
      setBoard(newBoard)
      setLastMove({ from: { row: fromRow, col: fromCol }, to: { row: toRow, col: toCol } })
      
      if (gameMode === 'local') {
        // Switch turns in local multiplayer
        const nextTurn = currentTurn === 'white' ? 'black' : 'white'
        setCurrentTurn(nextTurn)
        setStatus(`${nextTurn === 'white' ? 'White' : 'Black'} to move`)
      } else {
        setStatus('Your move! (Offline mode - no AI opponent)')
      }
      return
    }

    try {
      setIsThinking(true)
      setStatus('Making move...')
      setShowHint(false)
      setHintMove(null)
      
      const fromSquare = toChessNotation(fromRow, fromCol)
      const toSquare = toChessNotation(toRow, toCol)
      const piece = board[fromRow][fromCol]
      const isPromotion = (piece === 'P' && toRow === 0) || (piece === 'p' && toRow === 7)
      const moveStr = fromSquare + toSquare + (isPromotion ? promotion : '')
      
      // Send move to backend for validation
      const response = await axios.post(`${API_URL}/api/move`, {
        move: moveStr
      })
      
      // Track captured piece
      const capturedPiece = board[toRow][toCol]
      if (capturedPiece) {
        const isWhitePiece = capturedPiece === capturedPiece.toUpperCase()
        setCapturedPieces(prev => ({
          ...prev,
          [isWhitePiece ? 'white' : 'black']: [...prev[isWhitePiece ? 'white' : 'black'], capturedPiece]
        }))
      }
      
      // Update board immediately after backend confirms
      const newBoard = [...board.map(row => [...row])]
      const movingPiece = newBoard[fromRow][fromCol]
      const isWhitePiece = movingPiece === movingPiece.toUpperCase()
      const promotedPiece = isPromotion ? (isWhitePiece ? promotion.toUpperCase() : promotion.toLowerCase()) : movingPiece
      newBoard[toRow][toCol] = promotedPiece
      newBoard[fromRow][fromCol] = null
      
      // Handle en passant - remove the captured pawn
      if ((movingPiece === 'P' || movingPiece === 'p') && Math.abs(toCol - fromCol) === 1 && !capturedPiece) {
        // This is en passant (diagonal pawn move with no piece at destination)
        const capturedPawnRow = fromRow
        const capturedPawn = newBoard[capturedPawnRow][toCol]
        if (capturedPawn) {
          const isWhitePiece = capturedPawn === capturedPawn.toUpperCase()
          setCapturedPieces(prev => ({
            ...prev,
            [isWhitePiece ? 'white' : 'black']: [...prev[isWhitePiece ? 'white' : 'black'], capturedPawn]
          }))
          newBoard[capturedPawnRow][toCol] = null
        }
      }
      
      // Handle castling - move the rook as well
      if ((piece === 'K' || piece === 'k') && Math.abs(toCol - fromCol) === 2) {
        // Kingside castling
        if (toCol > fromCol) {
          const rookFromCol = 7
          const rookToCol = toCol - 1
          newBoard[toRow][rookToCol] = newBoard[toRow][rookFromCol]
          newBoard[toRow][rookFromCol] = null
        }
        // Queenside castling
        else {
          const rookFromCol = 0
          const rookToCol = toCol + 1
          newBoard[toRow][rookToCol] = newBoard[toRow][rookFromCol]
          newBoard[toRow][rookFromCol] = null
        }
      }
      
      setBoard(newBoard)
      
      // Track move history and last move
      setMoveHistory(prev => [...prev, moveStr])
      setLastMove({ from: { row: fromRow, col: fromCol }, to: { row: toRow, col: toCol } })
      playMoveSound()
      
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
      
      // Get AI move (only in AI mode)
      if (gameMode === 'ai') {
        const startTime = Date.now()
        const aiResponse = await axios.post(`${API_URL}/api/engine`, {
          depth: difficulty
        })
        const elapsed = Date.now() - startTime
        setThinkingTime(elapsed)
        
        if (aiResponse.data.best_move) {
          const aiMove = aiResponse.data.best_move
          const from = fromChessNotation(aiMove.substring(0, 2))
          const to = fromChessNotation(aiMove.substring(2, 4))
          
          // Track AI captured piece
          const aiCapturedPiece = newBoard[to.row][to.col]
          if (aiCapturedPiece) {
            const isWhitePiece = aiCapturedPiece === aiCapturedPiece.toUpperCase()
            setCapturedPieces(prev => ({
              ...prev,
              [isWhitePiece ? 'white' : 'black']: [...prev[isWhitePiece ? 'white' : 'black'], aiCapturedPiece]
            }))
          }
          
          // Apply AI move to backend first
          await axios.post(`${API_URL}/api/move`, {
            move: aiMove
          })
          
          // Update board with AI move
          const aiBoard = [...newBoard.map(row => [...row])]
          const aiPiece = aiBoard[from.row][from.col]
          // Check for AI promotion (moves like e7e8q)
          const aiPromotion = aiMove.length > 4 ? aiMove[4] : null
          const isAiPromotion = (aiPiece === 'P' && to.row === 0) || (aiPiece === 'p' && to.row === 7)
          const isWhiteAiPiece = aiPiece === aiPiece.toUpperCase()
          const promotedAiPiece = isAiPromotion && aiPromotion ? (isWhiteAiPiece ? aiPromotion.toUpperCase() : aiPromotion.toLowerCase()) : aiPiece
          aiBoard[to.row][to.col] = promotedAiPiece
          aiBoard[from.row][from.col] = null
          
          // Handle en passant for AI - remove the captured pawn
          if ((aiPiece === 'P' || aiPiece === 'p') && Math.abs(to.col - from.col) === 1 && !aiCapturedPiece) {
            const capturedPawnRow = from.row
            const capturedPawn = aiBoard[capturedPawnRow][to.col]
            if (capturedPawn) {
              const isWhitePiece = capturedPawn === capturedPawn.toUpperCase()
              setCapturedPieces(prev => ({
                ...prev,
                [isWhitePiece ? 'white' : 'black']: [...prev[isWhitePiece ? 'white' : 'black'], capturedPawn]
              }))
              aiBoard[capturedPawnRow][to.col] = null
            }
          }
          
          // Handle castling for AI - move the rook as well
          if ((aiPiece === 'K' || aiPiece === 'k') && Math.abs(to.col - from.col) === 2) {
            // Kingside castling
            if (to.col > from.col) {
              const rookFromCol = 7
              const rookToCol = to.col - 1
              aiBoard[to.row][rookToCol] = aiBoard[to.row][rookFromCol]
              aiBoard[to.row][rookFromCol] = null
            }
            // Queenside castling
            else {
              const rookFromCol = 0
              const rookToCol = to.col + 1
              aiBoard[to.row][rookToCol] = aiBoard[to.row][rookFromCol]
              aiBoard[to.row][rookFromCol] = null
            }
          }
          
          setBoard(aiBoard)
          
          // Track AI move
          setMoveHistory(prev => [...prev, aiMove])
          setLastMove({ from, to })
          playMoveSound()
          
          // Update evaluation (score from response if available)
          if (aiResponse.data.score !== undefined) {
            setEvaluation(aiResponse.data.score / 100) // Convert centipawns to pawns
          }
          
          setStatus('Your move!')
        }
      } else {
        if (gameMode === 'local') {
          // Switch turns in local multiplayer
          const nextTurn = currentTurn === 'white' ? 'black' : 'white'
          setCurrentTurn(nextTurn)
          setStatus(`${nextTurn === 'white' ? 'White' : 'Black'} to move`)
        } else {
          setStatus('Your move!')
        }
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

  const isLastMove = (row, col) => {
    if (!showLastMove || !lastMove) return false
    return (lastMove.from.row === row && lastMove.from.col === col) ||
           (lastMove.to.row === row && lastMove.to.col === col)
  }

  const isHintSquare = (row, col) => {
    if (!showHint || !hintMove) return false
    const from = fromChessNotation(hintMove.substring(0, 2))
    const to = fromChessNotation(hintMove.substring(2, 4))
    return (from.row === row && from.col === col) || (to.row === row && to.col === col)
  }

  const getThemeColors = () => {
    const themes = {
      classic: { light: '#f0d9b5', dark: '#b58863' },
      blue: { light: '#dee3e6', dark: '#8ca2ad' },
      green: { light: '#ffffdd', dark: '#86a666' },
      purple: { light: '#e8d7f1', dark: '#9f7fb8' }
    }
    return themes[boardTheme] || themes.classic
  }

  const resetGame = async () => {
    setBoard(INITIAL_BOARD)
    setSelectedSquare(null)
    setLegalMoves([])
    setMoveHistory([])
    setCapturedPieces({ white: [], black: [] })
    setLastMove(null)
    setEvaluation(0)
    setShowHint(false)
    setHintMove(null)
    setCurrentTurn('white')
    
    // Reinitialize backend
    if (gameId !== 'offline-mode') {
      try {
        await axios.post(`${API_URL}/api/newgame`)
        if (gameMode === 'local') {
          setStatus('White to move')
        } else {
          setStatus('Your move!')
        }
      } catch (error) {
        console.error('Error resetting game:', error)
      }
    } else {
      if (gameMode === 'local') {
        setStatus('White to move (Offline mode)')
      } else {
        setStatus('Your move! (Offline mode)')
      }
    }
  }

  return (
    <div className="game-page">
      <div className="game-header">
        <button className="back-button" onClick={() => navigate('/play')}>
          ← Back
        </button>
        <h1>{gameMode === 'local' ? 'Player vs Player' : gameMode === 'analysis' ? 'Analysis Mode' : 'Chess vs AI'}</h1>
        <div className="header-actions">
          <button className="action-btn hint-btn" onClick={getHint} disabled={isThinking || gameMode !== 'ai'}>
            💡 Hint
          </button>
          <button className="action-btn undo-btn" onClick={undoMove} disabled={moveHistory.length === 0}>
            ↶ Undo
          </button>
          <button className="new-game-button" onClick={resetGame}>
            New Game
          </button>
        </div>
      </div>

      <div className="game-container">
        {/* Center - Chessboard */}
        <div className="board-section">
          <div className="board-wrapper">
            {showCoordinates && (
              <>
                <div className="coordinates files">
                  {['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'].map(file => (
                    <div key={file} className="coord">{file}</div>
                  ))}
                </div>
                <div className="coordinates ranks">
                  {[8, 7, 6, 5, 4, 3, 2, 1].map(rank => (
                    <div key={rank} className="coord">{rank}</div>
                  ))}
                </div>
              </>
            )}
            
            <div 
              className={`chessboard theme-${boardTheme}`}
              style={{
                '--light-square': getThemeColors().light,
                '--dark-square': getThemeColors().dark
              }}
            >
              {board.map((row, rowIndex) => (
                row.map((piece, colIndex) => {
                  const isLight = (rowIndex + colIndex) % 2 === 0
                  const selected = isSelected(rowIndex, colIndex)
                  const isLegal = isLegalMove(rowIndex, colIndex)
                  const isLast = isLastMove(rowIndex, colIndex)
                  const isHint = isHintSquare(rowIndex, colIndex)
                  
                  const isDraggable = piece && piece === piece.toUpperCase()
                  
                  return (
                    <div
                      key={`${rowIndex}-${colIndex}`}
                      className={`square ${isLight ? 'light' : 'dark'} ${selected ? 'selected' : ''} ${isLegal ? 'legal-move' : ''} ${isLast ? 'last-move' : ''} ${isHint ? 'hint-square' : ''}`}
                      onClick={() => handleSquareClick(rowIndex, colIndex)}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, rowIndex, colIndex)}
                    >
                      {piece && (
                        <span 
                          className="piece"
                          draggable={isDraggable}
                          onDragStart={(e) => handleDragStart(e, rowIndex, colIndex)}
                          onDragEnd={handleDragEnd}
                        >
                          {PIECES[piece]}
                        </span>
                      )}
                      {isLegal && !piece && <div className="move-indicator"></div>}
                      {isLegal && piece && <div className="capture-indicator"></div>}
                    </div>
                  )
                })
              ))}
            </div>
          </div>
          
          <div className="status-bar">
            <span>{status}</span>
            {thinkingTime > 0 && gameMode === 'ai' && (
              <span className="thinking-time">⏱️ {(thinkingTime / 1000).toFixed(2)}s</span>
            )}
          </div>
        </div>

        {/* Right sidebar - Game Info */}
        <div className="info-panel">
          <div className="info-section">
            <h3>📊 Evaluation</h3>
            <div className="eval-bar-container">
              <div className="eval-bar">
                <div 
                  className="eval-fill"
                  style={{ 
                    height: `${Math.min(100, Math.max(0, 50 + (evaluation * 5)))}%`
                  }}
                ></div>
              </div>
              <div className="eval-score">
                {evaluation > 0 ? '+' : ''}{evaluation.toFixed(1)}
              </div>
            </div>
          </div>

          <div className="info-section">
            <h3>🎯 Captured Pieces</h3>
            <div className="captured-section">
              <div className="captured-group">
                <span className="captured-label">White:</span>
                <div className="captured-pieces">
                  {capturedPieces.white.map((piece, i) => (
                    <span key={i} className="captured-piece">{PIECES[piece]}</span>
                  ))}
                </div>
              </div>
              <div className="captured-group">
                <span className="captured-label">Black:</span>
                <div className="captured-pieces">
                  {capturedPieces.black.map((piece, i) => (
                    <span key={i} className="captured-piece">{PIECES[piece]}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="info-section">
            <h3>📜 Move History</h3>
            <div className="move-history">
              {moveHistory.length === 0 ? (
                <p className="no-moves">No moves yet</p>
              ) : (
                <div className="moves-list">
                  {moveHistory.reduce((acc, move, i) => {
                    if (i % 2 === 0) {
                      acc.push([move])
                    } else {
                      acc[acc.length - 1].push(move)
                    }
                    return acc
                  }, []).map((movePair, i) => (
                    <div key={i} className="move-pair">
                      <span className="move-number">{i + 1}.</span>
                      <span className="move">{movePair[0]}</span>
                      {movePair[1] && <span className="move">{movePair[1]}</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Promotion Dialog */}
      {promotionPending && (
        <div className="promotion-overlay" onClick={() => setPromotionPending(null)}>
          <div className="promotion-dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Promote Pawn</h3>
            <div className="promotion-options">
              {['q', 'r', 'b', 'n'].map(piece => {
                const isWhite = board[promotionPending.fromRow][promotionPending.fromCol] === 'P'
                const displayPiece = isWhite ? piece.toUpperCase() : piece
                return (
                  <button 
                    key={piece}
                    className="promotion-piece"
                    onClick={async () => {
                      await makeMove(
                        promotionPending.fromRow, 
                        promotionPending.fromCol, 
                        promotionPending.toRow, 
                        promotionPending.toCol,
                        piece
                      )
                      setPromotionPending(null)
                    }}
                  >
                    {PIECES[displayPiece]}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Game
