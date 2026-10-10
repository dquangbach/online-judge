#!/usr/bin/env bash
# Copy existing named Docker volumes into the host directories used by Nginx.
# Run once before deploying the bind-mount layout. This never deletes source data.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env.production"

if [ ! -f "$ENV_FILE" ]; then
    echo "LỖI: Không tìm thấy $ENV_FILE"
    exit 1
fi

read_env() {
    local key="$1"
    sed -n "s/^${key}=//p" "$ENV_FILE" | head -n 1 | tr -d '"'
}

STATIC_DIR="$(read_env STATIC_DIR)"
MEDIA_DIR="$(read_env MEDIA_DIR)"
PROBLEM_DIR="$(read_env PROBLEM_DIR)"
if [ -z "$STATIC_DIR" ] || [ -z "$MEDIA_DIR" ] || [ -z "$PROBLEM_DIR" ]; then
    echo "LỖI: STATIC_DIR, MEDIA_DIR và PROBLEM_DIR phải có trong .env.production"
    exit 1
fi

copy_volume() {
    local volume="$1"
    local target="$2"

    if ! docker volume inspect "$volume" >/dev/null 2>&1; then
        echo "Bỏ qua $volume (không tồn tại)."
        return
    fi

    mkdir -p "$target"
    if [ -n "$(find "$target" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
        echo "LỖI: $target không rỗng; không ghi đè dữ liệu đích."
        exit 1
    fi

    echo "Đang sao chép $volume sang $target (dữ liệu nguồn được giữ nguyên)..."
    docker run --rm \
        -v "$volume":/source:ro \
        -v "$target":/target \
        alpine sh -ec 'cp -a /source/. /target/'
}

copy_volume dutoj-prod_static_data "$STATIC_DIR"
copy_volume dutoj-prod_media_data "$MEDIA_DIR"
copy_volume dutoj-prod_problem_data "$PROBLEM_DIR"

echo "Sao chép hoàn tất. Xác minh các thư mục đích trước khi deploy."
