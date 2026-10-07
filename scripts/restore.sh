#!/usr/bin/env bash
# ==============================================================================
# Script Khôi phục Dữ liệu (Restore & Disaster Recovery) cho DMOJ / DUTOJ
# Cách dùng: ./scripts/restore.sh /backup/online-judge/<TIMESTAMP> [--force]
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ $# -lt 1 ]; then
    echo "Cách sử dụng: $0 <đường_dẫn_thư_mục_backup> [--force]"
    echo "Ví dụ: $0 /backup/online-judge/20261007_020000"
    exit 1
fi

TARGET_BACKUP_DIR="$1"
FORCE="${2:-}"

if [ ! -d "$TARGET_BACKUP_DIR" ]; then
    echo "LỖI: Thư mục sao lưu $TARGET_BACKUP_DIR không tồn tại!"
    exit 1
fi

echo "=========================================================="
echo " BẮT ĐẦU QUY TRÌNH KHÔI PHỤC DỮ LIỆU TỪ: $TARGET_BACKUP_DIR"
echo "=========================================================="

if [ "$FORCE" != "--force" ]; then
    echo "CẢNH BÁO NGUY HIỂM: Thao tác này sẽ GHI ĐÈ toàn bộ cơ sở dữ liệu và files hiện tại!"
    read -p "Bạn có chắc chắn muốn tiếp tục khôi phục không? (gõ 'yes' để xác nhận): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Đã hủy thao tác khôi phục."
        exit 0
    fi
fi

# 1. Kiểm tra tính toàn vẹn SHA256 trước khi giải nén
echo "==> Đang kiểm tra tính toàn vẹn các file backup..."
cd "$TARGET_BACKUP_DIR"
if [ -f "SHA256SUMS" ]; then
    sha256sum -c "SHA256SUMS"
else
    echo "Cảnh báo: Không tìm thấy file SHA256SUMS, bỏ qua bước kiểm tra checksum."
fi

# 2. Đọc file cấu hình môi trường
ENV_FILE="$ROOT_DIR/.env.production"
if [ ! -f "$ENV_FILE" ]; then
    echo "LỖI: Không tìm thấy file $ENV_FILE để lấy thông tin kết nối database!"
    exit 1
fi

MYSQL_DATABASE=$(grep '^MYSQL_DATABASE=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"'\''')
MYSQL_USER=$(grep '^MYSQL_USER=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"'\''')
MYSQL_PASSWORD=$(grep '^MYSQL_PASSWORD=' "$ENV_FILE" | cut -d '=' -f2- | tr -d '"'\''')

DB_CONTAINER=$(docker compose -f "$ROOT_DIR/docker-compose.prod.yml" ps -q db 2>/dev/null || echo "")
if [ -z "$DB_CONTAINER" ]; then
    echo "LỖI: Container MariaDB không đang chạy! Vui lòng khởi động trước: docker compose -f docker-compose.prod.yml up -d db"
    exit 1
fi

# 3. Khôi phục MariaDB Database
SQL_GZ=$(find "$TARGET_BACKUP_DIR" -name "database_*.sql.gz" | head -n 1)
if [ -n "$SQL_GZ" ]; then
    echo "==> Đang nạp cơ sở dữ liệu từ $SQL_GZ..."
    gunzip -c "$SQL_GZ" | docker exec -i -e MYSQL_PWD="$MYSQL_PASSWORD" "$DB_CONTAINER" \
        mysql -u"$MYSQL_USER" --default-character-set=utf8mb4 "$MYSQL_DATABASE"
    echo "    Khôi phục database hoàn tất."
else
    echo "Cảnh báo: Không tìm thấy file database dump trong thư mục backup."
fi

# 4. Khôi phục Media Files
MEDIA_TAR=$(find "$TARGET_BACKUP_DIR" -name "media_*.tar.gz" | head -n 1)
if [ -n "$MEDIA_TAR" ]; then
    echo "==> Đang giải nén dữ liệu Media vào volume..."
    docker run --rm \
        -v dutoj-prod_media_data:/target \
        -v "$TARGET_BACKUP_DIR":/backup:ro \
        alpine sh -c "tar -xzf /backup/$(basename "$MEDIA_TAR") -C /target"
    echo "    Khôi phục media files hoàn tất."
fi

# 5. Khôi phục Problem Data
PROBLEMS_TAR=$(find "$TARGET_BACKUP_DIR" -name "problem_data_*.tar.gz" | head -n 1)
if [ -n "$PROBLEMS_TAR" ]; then
    echo "==> Đang giải nén dữ liệu Problem data vào volume..."
    docker run --rm \
        -v dutoj-prod_problem_data:/target \
        -v "$TARGET_BACKUP_DIR":/backup:ro \
        alpine sh -c "tar -xzf /backup/$(basename "$PROBLEMS_TAR") -C /target"
    echo "    Khôi phục problem data hoàn tất."
fi

echo "=========================================================="
echo " KHÔI PHỤC HOÀN TẤT! Vui lòng chạy kiểm tra tính toàn vẹn:"
echo " docker compose -f docker-compose.prod.yml restart web bridge"
echo "=========================================================="
