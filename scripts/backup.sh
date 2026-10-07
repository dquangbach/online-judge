#!/usr/bin/env bash
# ==============================================================================
# Script Sao lưu Dữ liệu Toàn diện cho DMOJ / DUTOJ Production
# Đặt tại: /opt/online-judge/scripts/backup.sh
# Cronjob khuyến nghị: 0 2 * * * /opt/online-judge/scripts/backup.sh >> /var/log/oj_backup.log 2>&1
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_ROOT="${BACKUP_DEST_DIR:-/backup/online-judge}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
CURRENT_BACKUP_DIR="$BACKUP_ROOT/$TIMESTAMP"

echo "=========================================================="
echo " BẮT ĐẦU QUY TRÌNH SAO LƯU HỆ THỐNG: $TIMESTAMP"
echo "=========================================================="

# 1. Đọc biến môi trường từ .env.production an toàn
ENV_FILE="$ROOT_DIR/.env.production"
if [ ! -f "$ENV_FILE" ]; then
    echo "LỖI: Không tìm thấy file $ENV_FILE!"
    exit 1
fi

# Nạp các biến cấu hình cần thiết
MYSQL_DATABASE=$(grep '^MYSQL_DATABASE=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"'\''')
MYSQL_USER=$(grep '^MYSQL_USER=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"'\''')
MYSQL_PASSWORD=$(grep '^MYSQL_PASSWORD=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"'\''')

mkdir -p "$CURRENT_BACKUP_DIR"

# 2. Sao lưu Cơ sở dữ liệu MariaDB
# LƯU Ý BẢO MẬT: Sử dụng biến MYSQL_PWD bên trong container để KHÔNG làm lộ mật khẩu ra 'ps aux'
echo "==> Đang sao lưu Database MariaDB ($MYSQL_DATABASE)..."
DB_CONTAINER=$(docker compose -f "$ROOT_DIR/docker-compose.prod.yml" ps -q db 2>/dev/null || echo "")

if [ -z "$DB_CONTAINER" ]; then
    echo "LỖI: Container database không đang chạy!"
    exit 1
fi

DB_DUMP_FILE="$CURRENT_BACKUP_DIR/database_${MYSQL_DATABASE}_${TIMESTAMP}.sql.gz"

docker exec -i -e MYSQL_PWD="$MYSQL_PASSWORD" "$DB_CONTAINER" \
    mysqldump -u"$MYSQL_USER" \
    --single-transaction \
    --quick \
    --routines \
    --triggers \
    --default-character-set=utf8mb4 \
    "$MYSQL_DATABASE" | gzip -9 > "$DB_DUMP_FILE"

# Kiểm tra tính toàn vẹn của file dump
if [ ! -s "$DB_DUMP_FILE" ] || ! gzip -t "$DB_DUMP_FILE"; then
    echo "LỖI NGHIÊM TRỌNG: File dump database bị rỗng hoặc lỗi nén!"
    exit 1
fi
echo "    Database dump thành công: $(du -h "$DB_DUMP_FILE" | cut -f1)"

# 3. Sao lưu Dữ liệu Media (Upload của thí sinh / bài nộp)
echo "==> Đang sao lưu thư mục Media uploads..."
MEDIA_BACKUP_FILE="$CURRENT_BACKUP_DIR/media_${TIMESTAMP}.tar.gz"
# Sao lưu từ volume docker media_data
docker run --rm \
    -v dutoj-prod_media_data:/source:ro \
    -v "$CURRENT_BACKUP_DIR":/backup \
    alpine tar -czf "/backup/media_${TIMESTAMP}.tar.gz" -C /source .
echo "    Media backup thành công: $(du -h "$MEDIA_BACKUP_FILE" | cut -f1)"

# 4. Sao lưu Đề bài và Bộ Testcases (Problem Data)
echo "==> Đang sao lưu Problem data (Testcases)..."
PROBLEMS_BACKUP_FILE="$CURRENT_BACKUP_DIR/problem_data_${TIMESTAMP}.tar.gz"
docker run --rm \
    -v dutoj-prod_problem_data:/source:ro \
    -v "$CURRENT_BACKUP_DIR":/backup \
    alpine tar -czf "/backup/problem_data_${TIMESTAMP}.tar.gz" -C /source .
echo "    Problem data backup thành công: $(du -h "$PROBLEMS_BACKUP_FILE" | cut -f1)"

# 5. Tạo file checksum xác thực tính toàn vẹn SHA256
echo "==> Tạo checksum SHA-256..."
cd "$CURRENT_BACKUP_DIR"
sha256sum *.tar.gz *.sql.gz > "SHA256SUMS"

# 6. Dọn dẹp các bản backup cũ hơn số ngày quy định
echo "==> Dọn dẹp bản sao lưu cũ hơn $RETENTION_DAYS ngày..."
find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -exec rm -rf {} +

echo "=========================================================="
echo " SAO LƯU THÀNH CÔNG TẠI: $CURRENT_BACKUP_DIR"
echo "=========================================================="
