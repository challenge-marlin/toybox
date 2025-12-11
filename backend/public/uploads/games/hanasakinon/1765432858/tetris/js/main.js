(function(){
  "use strict";

  // ===== DOM refs =====
  const boardCanvas = document.getElementById("boardCanvas");
  const boardCtx = boardCanvas.getContext("2d");
  const nextCanvas = document.getElementById("nextCanvas");
  const nextCtx = nextCanvas.getContext("2d");
  const holdCanvas = document.getElementById("holdCanvas");
  const holdCtx = holdCanvas.getContext("2d");
  const overlay = document.getElementById("overlay");
  const scoreEl = document.getElementById("score");
  const levelEl = document.getElementById("level");
  const linesEl = document.getElementById("lines");
  const startBtn = document.getElementById("startBtn");
  const pauseBtn = document.getElementById("pauseBtn");
  const resumeBtn = document.getElementById("resumeBtn");
  const resetBtn = document.getElementById("resetBtn");

  // ===== Game constants =====
  const COLS = 10;
  const ROWS = 20;
  const BLOCK_SIZE = 30; // canvas already 300x600

  // Colors per piece type
  const COLORS = {
    I: "#5fd0ff",
    J: "#4f8cff",
    L: "#ffa84f",
    O: "#ffd34f",
    S: "#39d98a",
    T: "#b67dff",
    Z: "#ff6a8a"
  };

  // Piece definitions (rotation states as matrices)
  const SHAPES = {
    I: [
      [ [0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0] ],
      [ [0,0,1,0], [0,0,1,0], [0,0,1,0], [0,0,1,0] ]
    ],
    J: [
      [ [1,0,0], [1,1,1], [0,0,0] ],
      [ [1,1,0], [1,0,0], [1,0,0] ],
      [ [0,0,0], [1,1,1], [0,0,1] ],
      [ [0,0,1], [0,0,1], [0,1,1] ]
    ],
    L: [
      [ [0,0,1], [1,1,1], [0,0,0] ],
      [ [1,0,0], [1,0,0], [1,1,0] ],
      [ [0,0,0], [1,1,1], [1,0,0] ],
      [ [0,1,1], [0,0,1], [0,0,1] ]
    ],
    O: [
      [ [1,1], [1,1] ]
    ],
    S: [
      [ [0,1,1], [1,1,0], [0,0,0] ],
      [ [1,0,0], [1,1,0], [0,1,0] ]
    ],
    T: [
      [ [0,1,0], [1,1,1], [0,0,0] ],
      [ [1,0,0], [1,1,0], [1,0,0] ],
      [ [0,0,0], [1,1,1], [0,1,0] ],
      [ [0,1,0], [0,1,1], [0,1,0] ]
    ],
    Z: [
      [ [1,1,0], [0,1,1], [0,0,0] ],
      [ [0,0,1], [0,1,1], [0,1,0] ]
    ]
  };

  const PIECE_TYPES = Object.keys(SHAPES);

  // ===== Game state =====
  let board = createBoard();
  let currentPiece = null; // {type, rotationIndex, matrix, x, y}
  let nextType = randomType();
  let holdType = null;
  let holdUsedOnThisDrop = false;
  let isRunning = false;
  let isPaused = false;
  let score = 0;
  let level = 1;
  let totalLines = 0;

  // Drop timing
  let dropIntervalMs = intervalForLevel(level);
  let lastTime = 0;
  let dropAccumulator = 0;

  // ===== Utilities =====
  function createBoard(){
    return new Array(ROWS).fill(0).map(()=> new Array(COLS).fill(null));
  }
  function randomType(){
    return PIECE_TYPES[Math.floor(Math.random()*PIECE_TYPES.length)];
  }
  function intervalForLevel(lv){
    return Math.max(90, 1000 - (lv-1)*80);
  }
  function setOverlay(msg){
    overlay.textContent = msg;
    overlay.classList.remove("hidden");
  }
  function hideOverlay(){
    overlay.classList.add("hidden");
    overlay.textContent = "";
  }
  function updateHUD(){
    scoreEl.textContent = String(score);
    levelEl.textContent = String(level);
    linesEl.textContent = String(totalLines);
  }

  // ===== Piece helpers =====
  function spawnPiece(){
    const type = nextType; // take queued next
    nextType = randomType();
    const rotationIndex = 0;
    const shapeList = SHAPES[type];
    const matrix = cloneMatrix(shapeList[rotationIndex]);
    const startX = Math.floor(COLS/2) - Math.ceil(matrix[0].length/2);
    const startY = -1; // start above board
    currentPiece = {type, rotationIndex, matrix, x:startX, y:startY};
    holdUsedOnThisDrop = false;
    if(collides(currentPiece, board, currentPiece.x, currentPiece.y+1)){
      // immediate collision -> game over
      isRunning = false; isPaused = false;
      setOverlay(`ゲームオーバー\nスコア: ${score}`);
    }
    drawNext();
    drawHold();
  }
  function cloneMatrix(m){ return m.map(row=>row.slice()); }
  function rotateCW(piece){
    const shapeList = SHAPES[piece.type];
    const nextIndex = (piece.rotationIndex + 1) % shapeList.length;
    return cloneMatrix(shapeList[nextIndex]);
  }
  function rotateCCW(piece){
    const shapeList = SHAPES[piece.type];
    const nextIndex = (piece.rotationIndex - 1 + shapeList.length) % shapeList.length;
    return cloneMatrix(shapeList[nextIndex]);
  }

  function collides(piece, boardState, offsetX, offsetY, testMatrix){
    const mat = testMatrix || piece.matrix;
    for(let y=0; y<mat.length; y++){
      for(let x=0; x<mat[y].length; x++){
        if(!mat[y][x]) continue;
        const bx = piece.x + x + (offsetX - piece.x);
        const by = piece.y + y + (offsetY - piece.y);
        if(by < 0) continue; // allow above top
        if(bx<0 || bx>=COLS || by>=ROWS) return true;
        if(boardState[by][bx]) return true;
      }
    }
    return false;
  }

  function mergePiece(){
    const color = COLORS[currentPiece.type];
    for(let y=0; y<currentPiece.matrix.length; y++){
      for(let x=0; x<currentPiece.matrix[y].length; x++){
        if(!currentPiece.matrix[y][x]) continue;
        const bx = currentPiece.x + x;
        const by = currentPiece.y + y;
        if(by>=0) board[by][bx] = color;
      }
    }
  }

  function clearLines(){
    let cleared = 0;
    for(let y=ROWS-1; y>=0; ){
      if(board[y].every(cell=>cell)){ // full row
        board.splice(y,1);
        board.unshift(new Array(COLS).fill(null));
        cleared++;
      } else y--;
    }
    if(cleared>0){
      totalLines += cleared;
      // Scoring: 1/2/3/4 lines
      const lineScores = [0, 100, 300, 500, 800];
      score += lineScores[cleared] * level;
      // Level up every 10 lines
      const newLevel = Math.floor(totalLines/10) + 1;
      if(newLevel!==level){
        level = newLevel;
        dropIntervalMs = intervalForLevel(level);
      }
      updateHUD();
    }
  }

  function hardDrop(){
    let dropDistance = 0;
    while(!collides(currentPiece, board, currentPiece.x, currentPiece.y+1)){
      currentPiece.y++;
      dropDistance++;
    }
    if(dropDistance>0){ score += dropDistance*2; updateHUD(); }
    lockPiece();
  }

  function softDrop(){
    if(!collides(currentPiece, board, currentPiece.x, currentPiece.y+1)){
      currentPiece.y++;
      score += 1; updateHUD();
    } else {
      lockPiece();
    }
  }

  function lockPiece(){
    mergePiece();
    clearLines();
    spawnPiece();
  }

  function tryMove(dx, dy){
    if(!currentPiece) return;
    const nx = currentPiece.x + dx;
    const ny = currentPiece.y + dy;
    if(!collides(currentPiece, board, nx, ny)){
      currentPiece.x = nx; currentPiece.y = ny;
    } else if(dy>0){
      // touched down
      lockPiece();
    }
  }

  function tryRotate(dir){
    if(!currentPiece) return;
    const rotated = dir>0 ? rotateCW(currentPiece) : rotateCCW(currentPiece);
    const oldMatrix = currentPiece.matrix;
    const oldIndex = currentPiece.rotationIndex;
    // Super simple wall kick: try offsets
    const kicks = [0, -1, 1, -2, 2];
    for(const k of kicks){
      const nx = currentPiece.x + k;
      const ny = currentPiece.y;
      if(!collides(currentPiece, board, nx, ny, rotated)){
        currentPiece.matrix = rotated;
        const shapeList = SHAPES[currentPiece.type];
        currentPiece.rotationIndex = (oldIndex + (dir>0?1:-1) + shapeList.length)%shapeList.length;
        currentPiece.x = nx; currentPiece.y = ny;
        return;
      }
    }
    // if all fail, keep original
    currentPiece.matrix = oldMatrix;
    currentPiece.rotationIndex = oldIndex;
  }

  function hold(){
    if(holdUsedOnThisDrop) return;
    const saved = holdType;
    holdType = currentPiece.type;
    holdUsedOnThisDrop = true;
    if(saved){
      // swap in held piece
      const type = saved;
      const shapeList = SHAPES[type];
      const matrix = cloneMatrix(shapeList[0]);
      const startX = Math.floor(COLS/2) - Math.ceil(matrix[0].length/2);
      currentPiece = {type, rotationIndex:0, matrix, x:startX, y:-1};
    } else {
      spawnPiece();
    }
    drawHold();
  }

  // ===== Rendering =====
  function drawCell(ctx, x, y, color){
    ctx.fillStyle = color;
    ctx.fillRect(x*BLOCK_SIZE, y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
    ctx.strokeStyle = "rgba(255,255,255,.08)";
    ctx.strokeRect(x*BLOCK_SIZE, y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
  }
  function drawBoard(){
    boardCtx.clearRect(0,0,boardCanvas.width,boardCanvas.height);
    // background grid
    boardCtx.fillStyle = "#0a0d16";
    boardCtx.fillRect(0,0,boardCanvas.width,boardCanvas.height);
    for(let y=0;y<ROWS;y++){
      for(let x=0;x<COLS;x++){
        const cell = board[y][x];
        if(cell){ drawCell(boardCtx, x, y, cell); }
        else {
          boardCtx.strokeStyle = "rgba(255,255,255,.03)";
          boardCtx.strokeRect(x*BLOCK_SIZE, y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE);
        }
      }
    }
    // draw current piece
    if(currentPiece){
      const color = COLORS[currentPiece.type];
      for(let y=0; y<currentPiece.matrix.length; y++){
        for(let x=0; x<currentPiece.matrix[y].length; x++){
          if(!currentPiece.matrix[y][x]) continue;
          const by = currentPiece.y + y;
          const bx = currentPiece.x + x;
          if(by>=0) drawCell(boardCtx, bx, by, color);
        }
      }
    }
  }
  function drawPreview(ctx, type){
    ctx.clearRect(0,0,ctx.canvas.width, ctx.canvas.height);
    ctx.fillStyle = "#0a0d16"; ctx.fillRect(0,0,ctx.canvas.width, ctx.canvas.height);
    if(!type) return;
    const mat = SHAPES[type][0];
    const color = COLORS[type];
    const cell = 24;
    // center
    const matW = mat[0].length*cell;
    const matH = mat.length*cell;
    const offsetX = Math.floor((ctx.canvas.width - matW)/2);
    const offsetY = Math.floor((ctx.canvas.height - matH)/2);
    for(let y=0;y<mat.length;y++){
      for(let x=0;x<mat[y].length;x++){
        if(!mat[y][x]) continue;
        ctx.fillStyle = color;
        ctx.fillRect(offsetX + x*cell, offsetY + y*cell, cell, cell);
        ctx.strokeStyle = "rgba(255,255,255,.08)";
        ctx.strokeRect(offsetX + x*cell, offsetY + y*cell, cell, cell);
      }
    }
  }
  function drawNext(){ drawPreview(nextCtx, nextType); }
  function drawHold(){ drawPreview(holdCtx, holdType); }

  // ===== Game loop =====
  function update(time){
    if(!isRunning || isPaused){ requestAnimationFrame(update); return; }
    if(!lastTime) lastTime = time;
    const delta = time - lastTime; lastTime = time;
    dropAccumulator += delta;
    if(dropAccumulator >= dropIntervalMs){
      dropAccumulator = 0;
      tryMove(0,1);
    }
    drawBoard();
    requestAnimationFrame(update);
  }

  // ===== Controls =====
  function onKeyDown(e){
    if(!isRunning) return;
    if(isPaused && !(e.code==="KeyP")) return;
    if(e.code==="ArrowLeft"||e.code==="KeyA"){ tryMove(-1,0); }
    else if(e.code==="ArrowRight"||e.code==="KeyD"){ tryMove(1,0); }
    else if(e.code==="ArrowDown"||e.code==="KeyS"){ softDrop(); }
    else if(e.code==="ArrowUp"||e.code==="KeyX"){ tryRotate(1); }
    else if(e.code==="KeyZ"){ tryRotate(-1); }
    else if(e.code==="Space"){ e.preventDefault(); hardDrop(); }
    else if(e.code==="KeyC"){ hold(); }
    else if(e.code==="KeyP"){ togglePause(); }
    else if(e.code==="KeyR"){ reset(); }
    drawBoard();
  }

  function start(){
    isRunning = true; isPaused = false; score=0; level=1; totalLines=0; updateHUD();
    board = createBoard();
    holdType = null; nextType = randomType();
    dropIntervalMs = intervalForLevel(level);
    lastTime = 0; dropAccumulator = 0;
    hideOverlay();
    spawnPiece();
  }
  function togglePause(){
    if(!isRunning) return;
    isPaused = !isPaused;
    if(isPaused) setOverlay("一時停止中 - Pで再開"); else hideOverlay();
  }
  function reset(){
    start();
  }

  startBtn.addEventListener("click", start);
  pauseBtn.addEventListener("click", ()=>{ if(isRunning && !isPaused) togglePause(); });
  resumeBtn.addEventListener("click", ()=>{ if(isRunning && isPaused) togglePause(); });
  resetBtn.addEventListener("click", reset);
  window.addEventListener("keydown", onKeyDown);

  // Initial
  updateHUD();
  drawBoard();
  drawNext();
  drawHold();
  setOverlay("[開始] でスタート。スペースで即落下、Z/↑/Xで回転。");
  requestAnimationFrame(update);
})();



