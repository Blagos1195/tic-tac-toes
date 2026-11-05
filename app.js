const cells = [...document.querySelectorAll(".cell")];
const modeButtons = [...document.querySelectorAll(".mode-button")];
const statusHeading = document.querySelector("#game-status");
const roundLabel = document.querySelector("#round-label");
const turnPill = document.querySelector("#turn-pill");
const turnSymbol = document.querySelector(".turn-symbol");
const turnLabel = document.querySelector("#turn-label");
const modelStatus = document.querySelector("#model-status");
const nextTitle = document.querySelector("#next-title");
const nextCopy = document.querySelector("#next-copy");
const scoreX = document.querySelector("#score-x");
const scoreO = document.querySelector("#score-o");
const scoreDraw = document.querySelector("#score-draw");
const scoreXName = document.querySelector("#score-x-name");
const scoreOName = document.querySelector("#score-o-name");
const opponentName = document.querySelector("#opponent-name");

const wins = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6]
];

let board = Array(9).fill("");
let currentPlayer = "X";
let aiPlayer = "O";
let mode = "ai";
let gameOver = false;
let aiBusy = false;
let pyodide = null;
let aiReady = false;
let aiLoading = null;
const scoreStorageKey = "tic-tac-toe-scores-v1";
const scoresByMode = loadScores();
let scores = scoresByMode[mode];

function loadScores() {
  const empty = () => ({ X: 0, O: 0, draw: 0 });
  try {
    const saved = JSON.parse(localStorage.getItem(scoreStorageKey));
    return {
      ai: { ...empty(), ...(saved?.ai || {}) },
      pvp: { ...empty(), ...(saved?.pvp || {}) }
    };
  } catch {
    return { ai: empty(), pvp: empty() };
  }
}

function saveScores() {
  try {
    localStorage.setItem(scoreStorageKey, JSON.stringify(scoresByMode));
  } catch (error) {
    console.warn("Could not save scores in this browser.", error);
  }
}

function winnerFor(position) {
  for (const line of wins) {
    const [a, b, c] = line;
    if (position[a] && position[a] === position[b] && position[a] === position[c]) {
      return { player: position[a], line };
    }
  }
  return null;
}

function setModelStatus(message, ready = false) {
  modelStatus.innerHTML = '<span class="status-dot"></span>';
  modelStatus.append(document.createTextNode(" " + message));
  if (ready) modelStatus.querySelector(".status-dot").style.background = "#83b99c";
}

function render() {
  cells.forEach((cell, index) => {
    const value = board[index];
    cell.textContent = value;
    cell.classList.toggle("o", value === "O");
    cell.classList.toggle("winning", false);
    cell.disabled = Boolean(value) || gameOver || aiBusy || (mode === "ai" && currentPlayer === aiPlayer);
    cell.setAttribute("aria-label", `${["Top left", "Top middle", "Top right", "Middle left", "Centre", "Middle right", "Bottom left", "Bottom middle", "Bottom right"][index]}, ${value || "empty"}`);
  });

  const result = winnerFor(board);
  if (result) result.line.forEach(index => cells[index].classList.add("winning"));

  if (gameOver) {
    turnPill.style.visibility = "hidden";
  } else {
    turnPill.style.visibility = "visible";
    turnSymbol.textContent = currentPlayer;
    turnLabel.textContent = mode === "ai" && currentPlayer === aiPlayer ? "AI THINKING" : mode === "ai" ? "YOUR MOVE" : `PLAYER ${currentPlayer === "X" ? "1" : "2"}`;
  }
  scoreX.textContent = scores.X;
  scoreO.textContent = scores.O;
  scoreDraw.textContent = scores.draw;
}

function updateModeLabels() {
  const aiMode = mode === "ai";
  scoreXName.textContent = aiMode ? aiPlayer === "X" ? "AI" : "YOU" : "PLAYER 1";
  scoreOName.textContent = aiMode ? aiPlayer === "O" ? "AI" : "YOU" : "PLAYER 2";
  opponentName.textContent = aiMode ? "Trained AI" : "Player 2";
  const humanPlayer = aiMode ? aiPlayer === "X" ? "O" : "X" : "X";
  const opponentPlayer = aiMode ? aiPlayer : "O";
  const humanSymbol = document.querySelector("#score-you-symbol");
  const aiSymbol = document.querySelector("#score-opponent-symbol");
  humanSymbol.textContent = humanPlayer;
  humanSymbol.className = `score-symbol ${humanPlayer === "O" ? "o-text" : "x-text"}`;
  aiSymbol.textContent = opponentPlayer;
  aiSymbol.className = `score-symbol ${opponentPlayer === "O" ? "o-text" : "x-text"}`;
  if (aiMode) {
    roundLabel.textContent = currentPlayer === aiPlayer ? "THE AI IS THINKING" : "YOUR TURN";
    nextTitle.textContent = currentPlayer === aiPlayer ? "AI turn" : "Your move";
    nextCopy.textContent = `You play as ${aiPlayer === "X" ? "O" : "X"}. The trained AI plays as ${aiPlayer}.`;
  } else {
    roundLabel.textContent = "PLAYER 1'S TURN";
    nextTitle.textContent = "Player 1 starts";
    nextCopy.textContent = "Take turns placing X and O on the board.";
  }
}

function updateTurnText() {
  if (gameOver) return;
  if (mode === "ai") {
    if (currentPlayer !== aiPlayer) {
      roundLabel.textContent = "YOUR TURN";
      statusHeading.textContent = "Choose your next move.";
      nextTitle.textContent = "Your move";
      nextCopy.textContent = `You're ${currentPlayer}. The AI will play as ${aiPlayer}.`;
    } else {
      roundLabel.textContent = "THE AI IS THINKING";
      statusHeading.textContent = "The model is choosing.";
      nextTitle.textContent = "AI turn";
      nextCopy.textContent = "Looking up the best learned move.";
    }
  } else {
    const player = currentPlayer === "X" ? "1" : "2";
    roundLabel.textContent = `PLAYER ${player}'S TURN`;
    statusHeading.textContent = `Player ${player}, you're up.`;
    nextTitle.textContent = `Player ${player}'s move`;
    nextCopy.textContent = `Place your ${currentPlayer} in an empty square.`;
  }
}

function finishGame(result) {
  gameOver = true;
  if (result) {
    scores[result.player] += 1;
    statusHeading.textContent = mode === "ai"
      ? result.player === aiPlayer ? "The AI takes this one." : "You beat the AI."
      : `Player ${result.player === "X" ? "1" : "2"} wins.`;
    roundLabel.textContent = "GAME OVER";
    nextTitle.textContent = mode === "ai"
      ? result.player === aiPlayer ? "AI wins" : "A win for you"
      : result.player === "X" ? "Player 1 wins" : "Player 2 wins";
    nextCopy.textContent = "Three in a row. Start another round when you're ready.";
  } else {
    scores.draw += 1;
    statusHeading.textContent = "It's a draw.";
    roundLabel.textContent = "GAME OVER";
    nextTitle.textContent = "No winner this time";
    nextCopy.textContent = "A full board and perfectly matched moves.";
  }
  saveScores();
  render();
}

function placeMove(index, player) {
  if (gameOver || board[index] || aiBusy) return false;
  board[index] = player;
  const result = winnerFor(board);
  if (result) {
    finishGame(result);
    return true;
  }
  if (board.every(Boolean)) {
    finishGame(null);
    return true;
  }
  currentPlayer = player === "X" ? "O" : "X";
  updateTurnText();
  render();
  return true;
}

async function loadAI() {
  if (aiReady) return;
  if (aiLoading) return aiLoading;

  aiLoading = (async () => {
    setModelStatus("Loading Python runtime and trained model…");
    const [runtime, pythonSource, xData, oData] = await Promise.all([
      loadPyodide(),
      fetch("ai.py").then(response => {
        if (!response.ok) throw new Error("Could not load ai.py");
        return response.text();
      }),
      fetch("aiData10.JSON").then(response => {
        if (!response.ok) throw new Error("Could not load the trained X data");
        return response.json();
      }),
      fetch("aiData9.JSON").then(response => {
        if (!response.ok) throw new Error("Could not load the trained O data");
        return response.json();
      })
    ]);

    pyodide = runtime;
    pyodide.FS.writeFile("ai.py", pythonSource);
    pyodide.FS.writeFile("aiData10.json", JSON.stringify(xData));
    pyodide.FS.writeFile("aiData9.json", JSON.stringify(oData));
    await pyodide.runPythonAsync("import ai");
    aiReady = true;
    setModelStatus("Python AI ready · trained Q-tables loaded", true);
  })().catch(error => {
    console.error(error);
    setModelStatus("AI couldn't load. Check the connection and try again.");
    aiLoading = null;
    throw error;
  });

  return aiLoading;
}

async function makeAIMove() {
  aiBusy = true;
  updateTurnText();
  render();
  try {
    await loadAI();
    const pythonBoard = board.map((value, index) => value || String(index + 1));
    pyodide.globals.set("browser_board", pyodide.toPy(pythonBoard));
    const move = pyodide.runPython(`ai.get_ai_move${aiPlayer}(browser_board, 0.01)`);
    if (Number.isInteger(move) && move >= 0 && move < 9 && !board[move]) {
      aiBusy = false;
      placeMove(move, aiPlayer);
    } else {
      throw new Error("The trained model returned an invalid move.");
    }
  } catch (error) {
    console.error(error);
    aiBusy = false;
    statusHeading.textContent = "The AI couldn't make a move.";
    nextTitle.textContent = "AI unavailable";
    nextCopy.textContent = "Refresh the page and try again.";
    render();
  }
}

function startGame(resetScores = false) {
  board = Array(9).fill("");
  currentPlayer = "X";
  aiPlayer = mode === "ai" && Math.random() < 0.5 ? "X" : "O";
  gameOver = false;
  aiBusy = false;
  scores = scoresByMode[mode];
  if (resetScores) {
    scores.X = 0;
    scores.O = 0;
    scores.draw = 0;
    saveScores();
  }
  updateModeLabels();
  updateTurnText();
  render();
  if (mode === "ai") {
    loadAI().then(() => {
      if (currentPlayer === aiPlayer && !gameOver) makeAIMove();
    }).catch(() => {});
  } else {
    setModelStatus("Python AI not needed in Player vs Player mode");
  }
}

modeButtons.forEach(button => {
  button.addEventListener("click", () => {
    const nextMode = button.dataset.mode;
    if (mode === nextMode) return;
    mode = nextMode;
    scores = scoresByMode[mode];
    modeButtons.forEach(item => {
      const active = item === button;
      item.classList.toggle("active", active);
      item.setAttribute("aria-pressed", String(active));
    });
    startGame();
  });
});

cells.forEach((cell, index) => {
  cell.addEventListener("click", async () => {
    if (mode === "ai") {
      if (currentPlayer === aiPlayer || aiBusy || gameOver) return;
      if (placeMove(index, currentPlayer) && !gameOver) await makeAIMove();
    } else {
      if (gameOver || aiBusy || board[index]) return;
      placeMove(index, currentPlayer);
    }
  });
});

document.querySelector("#new-game").addEventListener("click", () => startGame());
document.querySelector("#reset-scores").addEventListener("click", () => startGame(true));

startGame();