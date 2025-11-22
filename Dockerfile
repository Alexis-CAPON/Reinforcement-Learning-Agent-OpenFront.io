# Multi-stage build for OpenFront.io RL Training
# Stage 1: Build the game bridge
# Use AMD64 platform for consistency with GPU servers
FROM --platform=linux/amd64 node:20-bullseye AS game-builder

WORKDIR /app

# Install system dependencies for canvas (required by game engine)
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Copy game engine source
COPY base-game/package*.json ./base-game/
COPY base-game/ ./base-game/

# Build the game
WORKDIR /app/base-game
RUN npm install
RUN npm run build-dev

# Copy phase5 game bridge
WORKDIR /app
COPY phase5-implementation/game_bridge/ ./phase5-implementation/game_bridge/

# Stage 2: Python training environment with game bridge
FROM --platform=linux/amd64 pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

# Install system dependencies (including canvas dependencies for runtime)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libjpeg62-turbo \
    libgif7 \
    librsvg2-2 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x (from NodeSource)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy built game from builder stage
COPY --from=game-builder /app/base-game/dist ./base-game/dist
COPY --from=game-builder /app/base-game/resources ./base-game/resources
COPY --from=game-builder /app/base-game/node_modules ./base-game/node_modules
COPY --from=game-builder /app/base-game/package.json ./base-game/
COPY --from=game-builder /app/phase5-implementation/game_bridge ./phase5-implementation/game_bridge

# Copy base-game source files needed at runtime
COPY base-game/src ./base-game/src
COPY base-game/tests ./base-game/tests
COPY base-game/tsconfig.json ./base-game/

# Copy Python training code
COPY phase5-implementation/src ./phase5-implementation/src
COPY phase5-implementation/train_full_game.py ./phase5-implementation/
COPY phase5-implementation/requirements.txt ./phase5-implementation/

# Install Python dependencies
RUN pip install --no-cache-dir -r phase5-implementation/requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir \
    stable-baselines3 \
    sb3-contrib \
    gymnasium \
    tensorboard \
    scipy

# Set working directory to phase5
WORKDIR /workspace/phase5-implementation

# Expose TensorBoard port
EXPOSE 6006

# Default command
CMD ["python3", "train_full_game.py", "--device", "cuda", "--map", "australia_256x256", "--bots", "10", "--timesteps", "20000000"]
