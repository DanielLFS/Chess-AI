// Game state
let gameState = {
    gameId: null,
    board: null,
    selectedSquare: null,
    legalMoves: [],
    playerColor: 'white',
    isPlayerTurn: false,
    gameOver: false,
    pendingPromotion: null,
    inCheck: false,
    currentTurn: 'white'
};

// Piece Unicode symbols
const PIECE_SYMBOLS = {
    'white': {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔'
    },
    'black': {
        'P': '♟', 'N': '♞', 'B': '♝', 'R': '♜', 'Q': '♛', 'K': '♚'
    }
};

// Initialize board
function initializeBoard() {
    const chessboard = document.getElementById('chessboard');
    chessboard.innerHTML = '';

    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const square = document.createElement('div');
            const squareNotation = getSquareNotation(row, col);
            
            square.className = 'square ' + ((row + col) % 2 === 0 ? 'light' : 'dark');
            square.dataset.row = row;
            square.dataset.col = col;
            square.dataset.notation = squareNotation;
            
            square.addEventListener('click', handleSquareClick);
            square.addEventListener('dragover', handleDragOver);
            square.addEventListener('drop', handleDrop);
            
            chessboard.appendChild(square);
        }
    }
}

// Convert row/col to algebraic notation
function getSquareNotation(row, col) {
    const files = 'abcdefgh';
    return files[col] + (8 - row);
}

// Convert algebraic notation to row/col
function notationToRowCol(notation) {
    const files = 'abcdefgh';
    const col = files.indexOf(notation[0]);
    const row = 8 - parseInt(notation[1]);
    return { row, col };
}

// Render board state
function renderBoard() {
    if (!gameState.board) return;

    const squares = document.querySelectorAll('.square');
    
    squares.forEach(square => {
        const row = parseInt(square.dataset.row);
        const col = parseInt(square.dataset.col);
        const piece = gameState.board[row][col];
        
        // Clear square
        square.innerHTML = '';
        square.classList.remove('selected', 'legal-move', 'has-piece', 'last-move', 'king-in-check');
        
        // Add piece if present
        if (piece) {
            const color = piece === piece.toUpperCase() ? 'white' : 'black';
            const pieceType = piece.toUpperCase();
            const pieceElement = document.createElement('span');
            pieceElement.className = 'piece';
            pieceElement.textContent = PIECE_SYMBOLS[color][pieceType];
            pieceElement.draggable = color === gameState.playerColor && gameState.isPlayerTurn;
            
            pieceElement.addEventListener('dragstart', handleDragStart);
            pieceElement.addEventListener('dragend', handleDragEnd);
            
            square.appendChild(pieceElement);
            
            // Highlight king if in check
            if (pieceType === 'K' && gameState.inCheck) {
                const currentTurn = gameState.currentTurn || 'white';
                if ((color === 'white' && currentTurn === 'white') || 
                    (color === 'black' && currentTurn === 'black')) {
                    square.classList.add('king-in-check');
                }
            }
        }
    });

    // Highlight selected square
    if (gameState.selectedSquare) {
        const { row, col } = notationToRowCol(gameState.selectedSquare);
        const selectedElement = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        if (selectedElement) {
            selectedElement.classList.add('selected');
        }
    }

    // Highlight legal moves
    gameState.legalMoves.forEach(move => {
        const { row, col } = notationToRowCol(move);
        const square = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
        if (square) {
            square.classList.add('legal-move');
            if (square.querySelector('.piece')) {
                square.classList.add('has-piece');
            }
        }
    });
}

// Handle square click
function handleSquareClick(e) {
    if (gameState.gameOver || !gameState.isPlayerTurn) return;

    const square = e.currentTarget;
    const notation = square.dataset.notation;
    const piece = square.querySelector('.piece');

    // If a square is already selected
    if (gameState.selectedSquare) {
        // Try to make a move
        if (gameState.legalMoves.includes(notation)) {
            makeMove(gameState.selectedSquare, notation);
        } else if (piece && piece.draggable) {
            // Select different piece
            selectSquare(notation);
        } else {
            // Deselect by clicking empty square or opponent piece
            gameState.selectedSquare = null;
            gameState.legalMoves = [];
            renderBoard();
        }
    } else {
        // Select square if it has a player's piece
        if (piece && piece.draggable) {
            selectSquare(notation);
        }
    }
}

// Select a square and get legal moves
async function selectSquare(notation) {
    gameState.selectedSquare = notation;
    
    try {
        const response = await fetch('/api/get_legal_moves', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                game_id: gameState.gameId,
                square: notation 
            })
        });
        
        const data = await response.json();
        gameState.legalMoves = data.legal_moves || [];
        renderBoard();
    } catch (error) {
        console.error('Error getting legal moves:', error);
        gameState.selectedSquare = null;
        gameState.legalMoves = [];
    }
}

// Make a move
async function makeMove(from, to) {
    // Check if move requires promotion
    const fromPos = notationToRowCol(from);
    const piece = gameState.board[fromPos.row][fromPos.col];
    const toRank = to[1];
    
    if (piece && piece.toUpperCase() === 'P' && (toRank === '8' || toRank === '1')) {
        // Show promotion modal
        gameState.pendingPromotion = { from, to };
        showPromotionModal();
        return;
    }

    await executeMoveAPI(from, to, null);
}

// Execute move via API
async function executeMoveAPI(from, to, promotion) {
    try {
        const response = await fetch('/api/make_move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                game_id: gameState.gameId,
                from: from,
                to: to,
                promotion: promotion
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear selection first
            gameState.selectedSquare = null;
            gameState.legalMoves = [];
            
            // Update board state immediately from response
            gameState.board = data.board;
            gameState.isPlayerTurn = data.is_player_turn;
            gameState.gameOver = data.game_over;
            gameState.inCheck = data.in_check;
            gameState.currentTurn = data.current_turn;
            
            // Render the updated board immediately
            renderBoard();
            updateStatus(data);
            updateCapturedPieces(data.captured_pieces);
            updateMoveHistory(data.move_history);
            
            if (data.player_elo) {
                updateEloDisplay(data.player_elo, data.ai_elo);
            }
            if (data.last_move_accuracy) {
                updateMoveAccuracy(data.last_move_accuracy);
            }
            if (data.evaluation !== undefined) {
                updateEvaluation(data.evaluation);
            }
            
            // Show game over notification and analysis
            if (data.game_over) {
                setTimeout(() => {
                    alert(data.status);
                    if (data.game_analysis) {
                        showGameAnalysis(data.game_analysis);
                    }
                }, 500);
            } else if (data.should_ai_move) {
                // If AI should move, request AI move after a short delay
                setTimeout(() => {
                    makeAIMove();
                }, 300);  // Small delay so user sees their move first
            }
        } else {
            alert(data.error || 'Invalid move');
            gameState.selectedSquare = null;
            gameState.legalMoves = [];
            renderBoard();
        }
    } catch (error) {
        console.error('Error making move:', error);
        alert('Error making move');
    }
}

// Show promotion modal
function showPromotionModal() {
    const modal = document.getElementById('promotion-modal');
    modal.classList.remove('hidden');
    
    // Update piece colors based on player
    const promotionBtns = document.querySelectorAll('.promotion-btn');
    promotionBtns.forEach(btn => {
        const piece = btn.dataset.piece;
        btn.textContent = PIECE_SYMBOLS[gameState.playerColor][piece];
        
        btn.onclick = async () => {
            modal.classList.add('hidden');
            const { from, to } = gameState.pendingPromotion;
            await executeMoveAPI(from, to, piece.toLowerCase());
            gameState.pendingPromotion = null;
        };
    });
}

// Drag and drop handlers
function handleDragStart(e) {
    const square = e.target.closest('.square');
    const notation = square.dataset.notation;
    
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', notation);
    e.target.classList.add('dragging');
    
    selectSquare(notation);
}

function handleDragEnd(e) {
    e.target.classList.remove('dragging');
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDrop(e) {
    e.preventDefault();
    const fromNotation = e.dataTransfer.getData('text/plain');
    const toSquare = e.target.closest('.square');
    
    if (!toSquare) {
        // Dropped outside valid square, cancel
        gameState.selectedSquare = null;
        gameState.legalMoves = [];
        renderBoard();
        return;
    }
    
    const toNotation = toSquare.dataset.notation;
    
    if (gameState.legalMoves.includes(toNotation)) {
        makeMove(fromNotation, toNotation);
    } else {
        gameState.selectedSquare = null;
        gameState.legalMoves = [];
        renderBoard();
    }
}

// Update game state from server
async function updateGameState() {
    try {
        const response = await fetch(`/api/get_game_state?game_id=${gameState.gameId}`);
        const data = await response.json();
        
        gameState.board = data.board;
        gameState.isPlayerTurn = data.is_player_turn;
        gameState.gameOver = data.game_over;
        
        renderBoard();
        updateStatus(data);
        updateCapturedPieces(data.captured_pieces);
        updateMoveHistory(data.move_history);
        
    } catch (error) {
        console.error('Error updating game state:', error);
    }
}

// Request AI to make a move
async function makeAIMove() {
    if (gameState.gameOver || gameState.isPlayerTurn) return;
    
    try {
        const response = await fetch('/api/ai_move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ game_id: gameState.gameId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            gameState.board = data.board;
            gameState.isPlayerTurn = data.is_player_turn;
            gameState.gameOver = data.game_over;
            gameState.inCheck = data.in_check;
            gameState.currentTurn = data.current_turn;
            
            renderBoard();
            updateStatus(data);
            updateCapturedPieces(data.captured_pieces);
            updateMoveHistory(data.move_history);
            
            if (data.evaluation !== undefined) {
                updateEvaluation(data.evaluation);
            }
            
            // Show game over notification and analysis
            if (data.game_over) {
                setTimeout(() => {
                    alert(data.status);
                    if (data.game_analysis) {
                        showGameAnalysis(data.game_analysis);
                    }
                }, 500);
            }
        }
    } catch (error) {
        console.error('Error getting AI move:', error);
    }
}

// Update status display
function updateStatus(data) {
    const statusElement = document.getElementById('status');
    const turnIndicator = document.getElementById('turn-indicator');
    
    statusElement.className = 'status';
    
    if (data.game_over) {
        statusElement.classList.add('game-over');
        statusElement.textContent = data.status;
        turnIndicator.textContent = '';
    } else {
        if (data.in_check) {
            statusElement.classList.add('check');
            statusElement.textContent = 'Check!';
        } else {
            statusElement.classList.add('in-progress');
            statusElement.textContent = 'Game in progress';
        }
        
        const currentTurn = data.current_turn;
        turnIndicator.textContent = `${currentTurn === 'white' ? 'White' : 'Black'} to move`;
        turnIndicator.className = 'turn-indicator ' + (currentTurn === 'white' ? 'white-turn' : 'black-turn');
    }
}

// Update captured pieces display
function updateCapturedPieces(capturedPieces) {
    const whiteElement = document.getElementById('captured-white');
    const blackElement = document.getElementById('captured-black');
    
    whiteElement.innerHTML = '';
    blackElement.innerHTML = '';
    
    if (capturedPieces) {
        capturedPieces.white.forEach(piece => {
            const span = document.createElement('span');
            span.textContent = PIECE_SYMBOLS.white[piece.toUpperCase()];
            whiteElement.appendChild(span);
        });
        
        capturedPieces.black.forEach(piece => {
            const span = document.createElement('span');
            span.textContent = PIECE_SYMBOLS.black[piece.toUpperCase()];
            blackElement.appendChild(span);
        });
    }
}

// Update move history display
function updateMoveHistory(moveHistory) {
    const movesListElement = document.getElementById('moves-list');
    movesListElement.innerHTML = '';
    
    if (!moveHistory || moveHistory.length === 0) return;
    
    for (let i = 0; i < moveHistory.length; i += 2) {
        const moveNumber = Math.floor(i / 2) + 1;
        const whiteMove = moveHistory[i];
        const blackMove = i + 1 < moveHistory.length ? moveHistory[i + 1] : '';
        
        const movePair = document.createElement('div');
        movePair.className = 'move-pair';
        
        movePair.innerHTML = `
            <span class="move-number">${moveNumber}.</span>
            <span class="move-notation">${whiteMove}</span>
            <span class="move-notation">${blackMove}</span>
        `;
        
        movesListElement.appendChild(movePair);
    }
    
    // Scroll to bottom
    movesListElement.scrollTop = movesListElement.scrollHeight;
}

// Update ELO display
function updateEloDisplay(playerElo, aiElo) {
    document.getElementById('player-elo').textContent = Math.round(playerElo);
    document.getElementById('ai-elo').textContent = Math.round(aiElo);
}

// Update move accuracy display
function updateMoveAccuracy(accuracy) {
    const accuracyElement = document.getElementById('move-accuracy');
    accuracyElement.textContent = accuracy;
    
    // Color code the accuracy
    accuracyElement.className = 'accuracy-' + accuracy.toLowerCase();
}

// Update evaluation bar
function updateEvaluation(evaluation) {
    const evalScore = document.getElementById('eval-score');
    const evalBarFill = document.getElementById('eval-bar-fill');
    
    // Clamp evaluation between -10 and +10 for display
    const clampedEval = Math.max(-10, Math.min(10, evaluation));
    
    // Display evaluation (from white's perspective)
    evalScore.textContent = evaluation > 0 ? `+${evaluation.toFixed(1)}` : evaluation.toFixed(1);
    
    // Calculate bar fill percentage (50% = equal, >50% = white advantage, <50% = black advantage)
    // Map -10 to 0%, 0 to 50%, +10 to 100%
    const percentage = 50 + (clampedEval / 10) * 50;
    
    evalBarFill.style.width = `${Math.abs(percentage - 50)}%`;
    
    if (evaluation > 0) {
        // White advantage - fill from center to right (white side)
        evalBarFill.style.left = '50%';
        evalBarFill.style.background = '#f5f5f5';
    } else {
        // Black advantage - fill from center to left (black side)
        evalBarFill.style.right = '50%';
        evalBarFill.style.left = 'auto';
        evalBarFill.style.background = '#333';
    }
}

// Show post-game analysis
function showGameAnalysis(analysisData) {
    const analysisPanel = document.getElementById('game-analysis-panel');
    
    // Calculate accuracy percentage
    const totalMoves = analysisData.total_moves || 1;
    const excellentCount = analysisData.excellent || 0;
    const goodCount = analysisData.good || 0;
    const inaccuracyCount = analysisData.inaccuracies || 0;
    const mistakeCount = analysisData.mistakes || 0;
    const blunderCount = analysisData.blunders || 0;
    
    // Weighted accuracy: Excellent=100%, Good=80%, Inaccuracy=50%, Mistake=20%, Blunder=0%
    const accuracyScore = (excellentCount * 100 + goodCount * 80 + inaccuracyCount * 50 + mistakeCount * 20) / totalMoves;
    const accuracy = Math.round(accuracyScore);
    
    // Update UI
    document.getElementById('player-accuracy-text').textContent = `${accuracy}%`;
    document.getElementById('player-accuracy-fill').style.width = `${accuracy}%`;
    
    document.getElementById('excellent-count').textContent = excellentCount;
    document.getElementById('good-count').textContent = goodCount;
    document.getElementById('inaccuracy-count').textContent = inaccuracyCount;
    document.getElementById('mistake-count').textContent = mistakeCount;
    document.getElementById('blunder-count').textContent = blunderCount;
    
    analysisPanel.style.display = 'block';
}

// Start new game
async function startNewGame() {
    const gameMode = document.getElementById('game-mode').value;
    
    let requestData;
    
    if (gameMode === 'ai-vs-ai') {
        // AI vs AI mode
        const whiteDifficulty = document.getElementById('white-ai-difficulty').value;
        const blackDifficulty = document.getElementById('black-ai-difficulty').value;
        
        requestData = {
            game_mode: 'ai-vs-ai',
            white_difficulty: whiteDifficulty,
            black_difficulty: blackDifficulty
        };
    } else {
        // Player vs AI mode
        const color = document.getElementById('color-select').value;
        let difficulty = document.getElementById('difficulty-select').value;
        
        if (difficulty === 'custom') {
            difficulty = document.getElementById('elo-slider').value;
        }
        
        requestData = {
            game_mode: 'player-vs-ai',
            color: color,
            difficulty: difficulty
        };
    }
    
    try {
        const response = await fetch('/api/new_game', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            gameState.gameId = data.game_id;
            gameState.playerColor = data.player_color;
            gameState.selectedSquare = null;
            gameState.legalMoves = [];
            gameState.gameOver = false;
            gameState.board = data.board;
            gameState.isPlayerTurn = data.is_player_turn;
            gameState.inCheck = data.in_check;
            gameState.currentTurn = data.current_turn;
            
            // Render the initial board state
            renderBoard();
            updateStatus(data);
            updateCapturedPieces(data.captured_pieces);
            updateMoveHistory(data.move_history);
            
            if (gameMode === 'ai-vs-ai') {
                updateEloDisplay(data.white_elo, data.black_elo);
                document.getElementById('player-elo').parentElement.querySelector('.label').textContent = 'White:';
                document.getElementById('ai-elo').parentElement.querySelector('.label').textContent = 'Black:';
                document.getElementById('move-accuracy').parentElement.style.display = 'none';
                
                // Start AI vs AI auto-play
                if (data.evaluation !== undefined) {
                    updateEvaluation(data.evaluation);
                }
                setTimeout(() => startAIvsAIMode(), 1000);
            } else {
                updateEloDisplay(data.player_elo, data.ai_elo);
                document.getElementById('player-elo').parentElement.querySelector('.label').textContent = 'Your ELO:';
                document.getElementById('ai-elo').parentElement.querySelector('.label').textContent = 'AI ELO:';
                document.getElementById('move-accuracy').parentElement.style.display = 'flex';
                updateMoveAccuracy('-');
                if (data.evaluation !== undefined) {
                    updateEvaluation(data.evaluation);
                }
            }
            
            // Hide analysis panel on new game
            document.getElementById('game-analysis-panel').style.display = 'none';
        } else {
            alert('Error starting new game');
        }
    } catch (error) {
        console.error('Error starting new game:', error);
        alert('Error starting new game');
    }
}

// AI vs AI auto-play mode
async function startAIvsAIMode() {
    if (gameState.gameOver) return;
    
    const delay = parseInt(document.getElementById('auto-play-speed').value);
    
    // Make AI move
    await makeAIMove();
    
    // Schedule next move
    if (!gameState.gameOver) {
        setTimeout(() => startAIvsAIMode(), delay);
    }
}

// Event listeners
document.getElementById('new-game-btn').addEventListener('click', startNewGame);

// Handle game mode selector
document.getElementById('game-mode').addEventListener('change', function() {
    const playerControls = document.getElementById('player-controls');
    const aiControls = document.getElementById('ai-vs-ai-controls');
    
    if (this.value === 'ai-vs-ai') {
        playerControls.style.display = 'none';
        aiControls.style.display = 'block';
    } else {
        playerControls.style.display = 'block';
        aiControls.style.display = 'none';
    }
});

// Handle difficulty selector
document.getElementById('difficulty-select').addEventListener('change', function() {
    const customEloGroup = document.getElementById('custom-elo-group');
    if (this.value === 'custom') {
        customEloGroup.style.display = 'block';
    } else {
        customEloGroup.style.display = 'none';
    }
});

// Handle ELO slider
document.getElementById('elo-slider').addEventListener('input', function() {
    document.getElementById('elo-value').textContent = this.value;
});

// Toggle evaluation visibility
document.getElementById('show-eval-toggle').addEventListener('change', function() {
    const evalContainer = document.getElementById('eval-container');
    if (this.checked) {
        evalContainer.style.display = 'block';
    } else {
        evalContainer.style.display = 'none';
    }
});

// Close analysis button
document.getElementById('close-analysis-btn').addEventListener('click', function() {
    document.getElementById('game-analysis-panel').style.display = 'none';
});

// === NEW FEATURES ===

// Sound effects
const sounds = {
    move: new Audio('/static/sounds/move.mp3'),
    capture: new Audio('/static/sounds/capture.mp3'),
    check: new Audio('/static/sounds/check.mp3')
};

function playSound(soundName) {
    if (sounds[soundName]) {
        sounds[soundName].currentTime = 0;
        sounds[soundName].play().catch(e => console.log('Sound play failed:', e));
    }
}

// Timer management
let playerTimer = 0;
let aiTimer = 0;
let timerInterval = null;
let activeTimer = null;

function startTimer(player) {
    stopTimer();
    activeTimer = player;
    
    timerInterval = setInterval(() => {
        if (activeTimer === 'player') {
            playerTimer++;
            document.getElementById('player-time').textContent = formatTime(playerTimer);
            document.querySelector('.player-timer').classList.add('active');
            document.querySelector('.ai-timer').classList.remove('active');
        } else {
            aiTimer++;
            document.getElementById('ai-time').textContent = formatTime(aiTimer);
            document.querySelector('.ai-timer').classList.add('active');
            document.querySelector('.player-timer').classList.remove('active');
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
    document.querySelector('.player-timer').classList.remove('active');
    document.querySelector('.ai-timer').classList.remove('active');
}

function resetTimers() {
    stopTimer();
    playerTimer = 0;
    aiTimer = 0;
    document.getElementById('player-time').textContent = '00:00';
    document.getElementById('ai-time').textContent = '00:00';
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// Flip board
let boardFlipped = false;
document.getElementById('flip-board-btn').addEventListener('click', function() {
    boardFlipped = !boardFlipped;
    const boardContainer = document.querySelector('.board-container');
    boardContainer.classList.toggle('flipped');
});

// Export PGN
document.getElementById('export-pgn-btn').addEventListener('click', function() {
    exportToPGN();
});

function exportToPGN() {
    if (!gameState.gameId) {
        alert('No game to export!');
        return;
    }
    
    fetch(`/api/get_game_state?game_id=${gameState.gameId}`)
        .then(res => res.json())
        .then(data => {
            const pgn = generatePGN(data);
            downloadPGN(pgn);
        })
        .catch(err => {
            console.error('Export failed:', err);
            alert('Failed to export game');
        });
}

function generatePGN(gameData) {
    const date = new Date().toISOString().split('T')[0];
    let pgn = `[Event "Chess AI Game"]\n`;
    pgn += `[Date "${date}"]\n`;
    pgn += `[White "${gameData.player_color === 'white' ? 'Player' : 'AI'}"]\n`;
    pgn += `[Black "${gameData.player_color === 'black' ? 'Player' : 'AI'}"]\n`;
    pgn += `[Result "*"]\n\n`;
    
    const moves = gameData.move_history || [];
    let moveText = '';
    for (let i = 0; i < moves.length; i += 2) {
        const moveNum = Math.floor(i / 2) + 1;
        moveText += `${moveNum}. ${moves[i]} `;
        if (i + 1 < moves.length) {
            moveText += `${moves[i + 1]} `;
        }
    }
    pgn += moveText;
    
    return pgn;
}

function downloadPGN(pgn) {
    const blob = new Blob([pgn], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chess-game-${Date.now()}.pgn`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Load from FEN
document.getElementById('load-fen-btn').addEventListener('click', function() {
    document.getElementById('fen-modal').classList.remove('hidden');
});

function closeFenModal() {
    document.getElementById('fen-modal').classList.add('hidden');
}

function loadFromFen() {
    const fen = document.getElementById('fen-input').value.trim();
    if (!fen) {
        alert('Please enter a FEN string');
        return;
    }
    
    // TODO: Add API endpoint to load from FEN
    fetch('/api/load_fen', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fen: fen })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            gameState.gameId = data.game_id;
            gameState.board = data.board;
            renderBoard();
            closeFenModal();
        } else {
            alert('Invalid FEN: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(err => {
        console.error('FEN load failed:', err);
        alert('Failed to load FEN');
    });
}

// Analysis Board
let analysisState = {
    moves: [],
    currentMoveIndex: 0,
    boards: []
};

document.getElementById('show-analysis-btn').addEventListener('click', function() {
    showAnalysisBoard();
});

function showAnalysisBoard() {
    if (!gameState.gameId) {
        alert('No game to analyze!');
        return;
    }
    
    fetch(`/api/get_game_state?game_id=${gameState.gameId}`)
        .then(res => res.json())
        .then(data => {
            analysisState.moves = data.move_history || [];
            loadAnalysisData();
            document.getElementById('analysis-modal').classList.remove('hidden');
        })
        .catch(err => {
            console.error('Analysis load failed:', err);
            alert('Failed to load analysis');
        });
}

function loadAnalysisData() {
    const movesList = document.getElementById('analysis-moves-list');
    movesList.innerHTML = '';
    
    for (let i = 0; i < analysisState.moves.length; i++) {
        const moveItem = document.createElement('div');
        moveItem.className = 'analysis-move-item';
        moveItem.textContent = `${Math.floor(i / 2) + 1}. ${analysisState.moves[i]}`;
        moveItem.onclick = () => goToMove(i);
        movesList.appendChild(moveItem);
    }
    
    analysisState.currentMoveIndex = analysisState.moves.length - 1;
    updateAnalysisBoard();
}

function updateAnalysisBoard() {
    // Highlight current move
    const items = document.querySelectorAll('.analysis-move-item');
    items.forEach((item, idx) => {
        item.classList.toggle('active', idx === analysisState.currentMoveIndex);
    });
    
    document.getElementById('analysis-move-info').textContent = 
        `Move ${analysisState.currentMoveIndex + 1} of ${analysisState.moves.length}`;
}

function goToMove(index) {
    analysisState.currentMoveIndex = index;
    updateAnalysisBoard();
}

function analysisFirst() {
    analysisState.currentMoveIndex = 0;
    updateAnalysisBoard();
}

function analysisPrev() {
    if (analysisState.currentMoveIndex > 0) {
        analysisState.currentMoveIndex--;
        updateAnalysisBoard();
    }
}

function analysisNext() {
    if (analysisState.currentMoveIndex < analysisState.moves.length - 1) {
        analysisState.currentMoveIndex++;
        updateAnalysisBoard();
    }
}

function analysisLast() {
    analysisState.currentMoveIndex = analysisState.moves.length - 1;
    updateAnalysisBoard();
}

function closeAnalysisModal() {
    document.getElementById('analysis-modal').classList.add('hidden');
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initializeBoard();
    
    // Start a default game
    startNewGame();
});


