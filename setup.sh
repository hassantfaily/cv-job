#!/usr/bin/env bash
set -e

echo "🤖 JobBot Setup"
echo "═══════════════"

# Check .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✅ Created .env from template — EDIT IT before continuing"
  echo "   Required: ANTHROPIC_API_KEY, EMAIL_ADDRESS, EMAIL_PASSWORD"
  exit 1
fi

echo "📦 Building Docker images..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d postgres redis
sleep 5

echo "🗄️  Database ready"
docker compose up -d api worker browser frontend

echo ""
echo "✅ JobBot is running!"
echo "   Frontend : http://localhost:3000"
echo "   API docs : http://localhost:8000/docs"
echo "   Browser  : http://localhost:8001/docs"
echo ""
echo "📖 Logs: docker compose logs -f"
