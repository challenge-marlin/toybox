(function () {
  "use strict";

  // DOM references
  const canvas = document.getElementById("gameCanvas");
  const ctx = canvas.getContext("2d");
  const scoreEl = document.getElementById("score");
  const livesEl = document.getElementById("lives");
  const levelEl = document.getElementById("level");
  const overlayEl = document.getElementById("overlay");
  const startBtn = document.getElementById("startBtn");
  const pauseBtn = document.getElementById("pauseBtn");
  const resumeBtn = document.getElementById("resumeBtn");
  const restartBtn = document.getElementById("restartBtn");

  // Logical game size (coordinate system)
  const GAME_WIDTH = 800;
  const GAME_HEIGHT = 600;

  // Paddle properties
  const PADDLE_HEIGHT = 14;
  const PADDLE_WIDTH_START = 110;
  const PADDLE_Y = GAME_HEIGHT - 40;
  const PADDLE_SPEED = 8;

  // Ball properties
  const BALL_RADIUS = 8;

  // Brick layout
  const BRICK_COLS = 10;
  const BRICK_ROWS_START = 5;
  const BRICK_GAP = 6; // gap between bricks
  const BRICK_TOP_MARGIN = 70;
  const BRICK_SIDE_MARGIN = 32;

  // Game state
  let isRunning = false;
  let isPaused = false;
  let level = 1;
  let score = 0;
  let lives = 3;

  // Entities
  let paddleX = (GAME_WIDTH - PADDLE_WIDTH_START) / 2;
  let paddleWidth = PADDLE_WIDTH_START;
  let ballX = GAME_WIDTH / 2;
  let ballY = PADDLE_Y - BALL_RADIUS - 2;
  let ballSpeed = 5;
  let ballDX = ballSpeed * (Math.random() > 0.5 ? 1 : -1);
  let ballDY = -ballSpeed;

  // Input state
  const input = { left: false, right: false };

  // Bricks grid
  let bricks = [];
  let brickWidth = 0;
  let brickHeight = 24;

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function resetBallAndPaddle(centerToPaddle = true) {
    paddleWidth = Math.max(70, PADDLE_WIDTH_START - (level - 1) * 6);
    paddleX = (GAME_WIDTH - paddleWidth) / 2;
    ballSpeed = 5 + (level - 1) * 0.5;
    if (centerToPaddle) {
      ballX = GAME_WIDTH / 2;
      ballY = PADDLE_Y - BALL_RADIUS - 2;
    }
    ballDX = ballSpeed * (Math.random() > 0.5 ? 1 : -1);
    ballDY = -ballSpeed;
  }

  function computeBrickWidth() {
    const totalGap = BRICK_GAP * (BRICK_COLS - 1);
    const usableWidth = GAME_WIDTH - BRICK_SIDE_MARGIN * 2 - totalGap;
    return usableWidth / BRICK_COLS;
  }

  function createBricks(rows) {
    brickWidth = computeBrickWidth();
    brickHeight = clamp(28 - rows, 16, 28);
    bricks = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < BRICK_COLS; c++) {
        const x = BRICK_SIDE_MARGIN + c * (brickWidth + BRICK_GAP);
        const y = BRICK_TOP_MARGIN + r * (brickHeight + BRICK_GAP);
        const hue = 200 + ((r / Math.max(1, rows - 1)) * 140);
        bricks.push({ x, y, w: brickWidth, h: brickHeight, alive: true, hue });
      }
    }
  }

  function allBricksCleared() {
    for (const b of bricks) {
      if (b.alive) return false;
    }
    return true;
  }

  function updateHUD() {
    scoreEl.textContent = String(score);
    livesEl.textContent = String(lives);
    levelEl.textContent = String(level);
  }

  function showOverlay(message) {
    overlayEl.textContent = message;
    overlayEl.classList.remove("hidden");
  }
  function hideOverlay() {
    overlayEl.classList.add("hidden");
    overlayEl.textContent = "";
  }

  function drawPaddle() {
    ctx.fillStyle = "#4f8cff";
    ctx.shadowColor = "#4f8cff";
    ctx.shadowBlur = 10;
    ctx.fillRect(paddleX, PADDLE_Y, paddleWidth, PADDLE_HEIGHT);
    ctx.shadowBlur = 0;
  }

  function drawBall() {
    ctx.beginPath();
    ctx.arc(ballX, ballY, BALL_RADIUS, 0, Math.PI * 2);
    ctx.closePath();
    const gradient = ctx.createRadialGradient(ballX - 3, ballY - 3, 2, ballX, ballY, BALL_RADIUS);
    gradient.addColorStop(0, "#ffffff");
    gradient.addColorStop(1, "#39d98a");
    ctx.fillStyle = gradient;
    ctx.shadowColor = "#39d98a";
    ctx.shadowBlur = 12;
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  function drawBricks() {
    for (const b of bricks) {
      if (!b.alive) continue;
      ctx.fillStyle = `hsl(${b.hue} 70% 55% / 1)`;
      ctx.fillRect(b.x, b.y, b.w, b.h);
      ctx.fillStyle = `hsl(${b.hue} 80% 80% / 0.3)`;
      ctx.fillRect(b.x, b.y, b.w, 6);
    }
  }

  function drawWalls() {
    ctx.strokeStyle = "#1f2545";
    ctx.lineWidth = 2;
    ctx.strokeRect(2, 2, GAME_WIDTH - 4, GAME_HEIGHT - 4);
  }

  function clear() {
    ctx.clearRect(0, 0, GAME_WIDTH, GAME_HEIGHT);
  }

  function update() {
    if (!isRunning || isPaused) return;

    // Move paddle
    if (input.left) paddleX -= PADDLE_SPEED;
    if (input.right) paddleX += PADDLE_SPEED;
    paddleX = clamp(paddleX, 2, GAME_WIDTH - paddleWidth - 2);

    // Move ball
    ballX += ballDX;
    ballY += ballDY;

    // Collide with walls
    if (ballX - BALL_RADIUS <= 2) { ballX = 2 + BALL_RADIUS; ballDX *= -1; }
    if (ballX + BALL_RADIUS >= GAME_WIDTH - 2) { ballX = GAME_WIDTH - 2 - BALL_RADIUS; ballDX *= -1; }
    if (ballY - BALL_RADIUS <= 2) { ballY = 2 + BALL_RADIUS; ballDY *= -1; }

    // Bottom out => lose life
    if (ballY - BALL_RADIUS > GAME_HEIGHT) {
      lives -= 1;
      updateHUD();
      if (lives <= 0) {
        isRunning = false;
        showOverlay(`ゲームオーバー\nスコア: ${score}  レベル: ${level}\n[リスタート]を押してください`);
        return;
      } else {
        resetBallAndPaddle();
        isPaused = true;
        showOverlay("ライフを消費しました。スペース/再開で続行");
        return;
      }
    }

    // Paddle collision (AABB-circle approx)
    if (
      ballY + BALL_RADIUS >= PADDLE_Y &&
      ballY - BALL_RADIUS <= PADDLE_Y + PADDLE_HEIGHT &&
      ballX >= paddleX &&
      ballX <= paddleX + paddleWidth &&
      ballDY > 0
    ) {
      // Reflect with angle based on hit position
      const hitPos = (ballX - (paddleX + paddleWidth / 2)) / (paddleWidth / 2); // -1..1
      const maxBounceAngle = Math.PI / 3; // 60deg
      const angle = hitPos * maxBounceAngle;
      const speed = Math.hypot(ballDX, ballDY);
      ballDX = speed * Math.sin(angle);
      ballDY = -Math.abs(speed * Math.cos(angle));

      // Nudge out to avoid sticking
      ballY = PADDLE_Y - BALL_RADIUS - 0.1;
    }

    // Bricks collision
    for (const b of bricks) {
      if (!b.alive) continue;
      // AABB-circle collision
      const closestX = clamp(ballX, b.x, b.x + b.w);
      const closestY = clamp(ballY, b.y, b.y + b.h);
      const dx = ballX - closestX;
      const dy = ballY - closestY;
      if (dx * dx + dy * dy <= BALL_RADIUS * BALL_RADIUS) {
        b.alive = false;
        score += 10;
        updateHUD();

        // Reflect based on side hit
        const overlapLeft = Math.abs((ballX + BALL_RADIUS) - b.x);
        const overlapRight = Math.abs((b.x + b.w) - (ballX - BALL_RADIUS));
        const overlapTop = Math.abs((ballY + BALL_RADIUS) - b.y);
        const overlapBottom = Math.abs((b.y + b.h) - (ballY - BALL_RADIUS));
        const minOverlap = Math.min(overlapLeft, overlapRight, overlapTop, overlapBottom);
        if (minOverlap === overlapLeft || minOverlap === overlapRight) {
          ballDX *= -1;
        } else {
          ballDY *= -1;
        }
        break; // handle one brick per frame to avoid tunneling
      }
    }

    if (allBricksCleared()) {
      level += 1;
      // Give small bonus and next layout
      score += 100;
      const rows = BRICK_ROWS_START + level - 1;
      createBricks(Math.min(9, rows));
      resetBallAndPaddle();
      isPaused = true;
      updateHUD();
      showOverlay(`レベル ${level} 開始！スペース/再開で続行`);
      return;
    }
  }

  function render() {
    clear();
    drawWalls();
    drawBricks();
    drawPaddle();
    drawBall();
  }

  function loop() {
    update();
    render();
    requestAnimationFrame(loop);
  }

  // Controls
  function onKeyDown(e) {
    if (e.code === "ArrowLeft" || e.code === "KeyA") input.left = true;
    if (e.code === "ArrowRight" || e.code === "KeyD") input.right = true;
    if (e.code === "Space") {
      e.preventDefault();
      if (!isRunning) return;
      if (isPaused) resume(); else pause();
    }
    if (e.code === "Enter") {
      e.preventDefault();
      if (!isRunning) start();
    }
  }
  function onKeyUp(e) {
    if (e.code === "ArrowLeft" || e.code === "KeyA") input.left = false;
    if (e.code === "ArrowRight" || e.code === "KeyD") input.right = false;
  }

  // Pointer/touch move control
  function onPointerMove(e) {
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX ?? (e.touches && e.touches[0]?.clientX)) || 0;
    const normX = clamp(x - rect.left, 0, rect.width);
    const ratio = normX / rect.width;
    paddleX = clamp(ratio * GAME_WIDTH - paddleWidth / 2, 2, GAME_WIDTH - paddleWidth - 2);
  }

  function start() {
    isRunning = true;
    isPaused = false;
    level = 1;
    score = 0;
    lives = 3;
    createBricks(BRICK_ROWS_START);
    resetBallAndPaddle();
    updateHUD();
    hideOverlay();
  }

  function pause() {
    if (!isRunning) return;
    isPaused = true;
    showOverlay("一時停止中 - スペース/再開");
  }

  function resume() {
    if (!isRunning) return;
    hideOverlay();
    isPaused = false;
  }

  function restart() {
    start();
  }

  // Wire events
  window.addEventListener("keydown", onKeyDown);
  window.addEventListener("keyup", onKeyUp);
  canvas.addEventListener("pointermove", onPointerMove, { passive: true });
  canvas.addEventListener("touchmove", onPointerMove, { passive: true });

  // Buttons
  startBtn.addEventListener("click", start);
  pauseBtn.addEventListener("click", pause);
  resumeBtn.addEventListener("click", resume);
  restartBtn.addEventListener("click", restart);

  // Keep canvas aspect responsive in wrapper via CSS, logical size remains fixed
  function fitCanvasHeight() {
    const rect = canvas.getBoundingClientRect();
    // Ensure wrapper isn't too tall on very narrow screens: nothing needed, CSS handles width
  }
  window.addEventListener("resize", fitCanvasHeight);
  fitCanvasHeight();

  // Start render loop immediately; game waits for start
  loop();

  // Show initial overlay/help
  showOverlay("エンターまたは[開始]でスタート！\n←/→ で移動、スペースで一時停止/再開");
  updateHUD();
})();


