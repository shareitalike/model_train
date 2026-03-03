.PHONY: up down build logs test train shell backup health clean

# ── Development ─────────────────────────────────────────────────────────────
up:
	docker compose up --build -d
	@echo ""
	@echo "  ✓ System started"
	@echo "  Frontend:  http://localhost"
	@echo "  API Docs:  http://localhost/api/docs"
	@echo "  MinIO:     http://localhost:9001"
	@echo "  Flower:    http://localhost:5555"

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f --tail=100

logs-backend:
	docker compose logs -f --tail=100 backend

# ── Testing ──────────────────────────────────────────────────────────────────
test:
	docker compose exec backend pytest tests/ -v --tb=short

test-trans:
	docker compose exec backend pytest tests/test_transliterator.py -v

test-api:
	docker compose exec backend pytest tests/test_api.py -v

# ── ML Training ──────────────────────────────────────────────────────────────
synth-data:
	docker compose exec backend python training/synthetic_data_gen.py \
		--output_dir ./kaithi_dataset --num_samples 10000

train:
	docker compose exec backend python training/train_trocr.py \
		--dataset_path ./kaithi_dataset/hf_dataset \
		--output_dir   /app/models/kaithi-trocr-v1 \
		--epochs       30

eval:
	docker compose exec backend python training/evaluate.py \
		/app/models/kaithi-trocr-v1 \
		./kaithi_dataset/test.json

# ── Operations ───────────────────────────────────────────────────────────────
shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec postgres psql -U kaithi -d kaithi_db

backup:
	@DATE=$$(date +%Y%m%d_%H%M%S) && \
	mkdir -p backups && \
	docker compose exec -T postgres pg_dump -U kaithi kaithi_db \
		| gzip > backups/kaithi_db_$${DATE}.sql.gz && \
	echo "Backup: backups/kaithi_db_$${DATE}.sql.gz"

health:
	@bash scripts/health_check.sh

# ── Production ───────────────────────────────────────────────────────────────
prod-gpu:
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build

# ── Cleanup ──────────────────────────────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans
	docker system prune -f

reset-db:
	docker compose exec postgres psql -U kaithi -c \
		"DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker compose restart backend celery_worker
