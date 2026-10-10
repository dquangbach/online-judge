# Báo cáo sửa lỗi sẵn sàng triển khai

**Ngày:** 10/10/2026  
**Phạm vi:** cấu hình Django production, Docker Compose, judge, CI/CD, Nginx paths và backup/restore.

## Đã sửa trong repository

1. **Compose nạp cấu hình production nhất quán.** Tất cả lệnh CD và backup/restore dùng `--env-file .env.production`. Các biến bắt buộc như mật khẩu MariaDB, khóa WebSocket, khóa judge và đường dẫn dữ liệu giờ làm Compose dừng ngay nếu thiếu.
2. **Đồng bộ vị trí lưu dữ liệu.** Web, bridge, worker và judge cùng dùng bind mounts tại `/static`, `/media`, `/problems`; Django ghi vào đúng ba đường dẫn này. Các thư mục host mặc định trong `.env.production.example` khớp với alias trong Nginx. Backup và restore chuyển sang các thư mục bind mount.
3. **Thêm khóa xác thực cho judge.** Judge đọc `JUDGE_AUTH_KEY` từ môi trường; entrypoint tạo cấu hình tạm có trường `key` rồi khởi chạy judge. Cấu hình dùng `problem_storage_globs` và mount problem data chỉ đọc.
4. **Sửa smoke test CD.** Kiểm tra HTTPS qua Nginx với `SITE_DOMAIN` và SNI, thay vì gửi HTTP vào cổng uWSGI nhị phân. CD kiểm tra cả tám service đang chạy và xác nhận bridge có ít nhất một judge kết nối trước khi báo thành công. Input `target_ref` được chuyển tới máy chủ.
5. **Fail-fast với cấu hình production yếu hoặc thiếu.** Django không khởi động production nếu thiếu secret, dùng giá trị mẫu, bật `DEBUG`, hoặc dùng wildcard cho `ALLOWED_HOSTS`. Dockerfile chép production settings bắt buộc, không nuốt lỗi. Đã thêm `SecurityMiddleware` và các thiết lập HTTPS/HSTS khi bật `DMOJ_SSL`.
6. **Mở rộng CI.** Thêm bước build image web và WebSocket bên cạnh lint và kiểm tra Compose.
7. **Cập nhật vận hành.** Backup/restore dùng `.env.production` và host data paths. Thêm `scripts/migrate-legacy-docker-volumes.sh` để sao chép dữ liệu từ named volumes cũ sang bind mounts mà không xóa nguồn. Báo cáo cũ được đánh dấu là lịch sử vì một số nhận định đã lỗi thời.

## Cần hoàn tất trên máy chủ trước production deploy

- Tạo `.env.production` thật từ mẫu và thay **tất cả** giá trị `change-me`; đặt `SITE_DOMAIN`, domain trong `DJANGO_ALLOWED_HOSTS`, `ALLOWED_ORIGINS`, và cấu hình TLS tương ứng. Không đưa secrets vào Git.
- Nếu stack cũ đã có dữ liệu trong `dutoj-prod_static_data`, `dutoj-prod_media_data` hoặc `dutoj-prod_problem_data`, chạy `scripts/migrate-legacy-docker-volumes.sh` **trước lần deploy đầu**. Script dừng nếu thư mục đích đã có dữ liệu; kiểm tra thủ công trước khi xử lý trường hợp đó.
- Đảm bảo Nginx trên host phục vụ đúng các thư mục `STATIC_DIR` và `MEDIA_DIR`, chứng chỉ TLS tồn tại, và user Nginx có quyền đọc dữ liệu.
- Đăng ký judge trong database với cùng giá trị `JUDGE_AUTH_KEY` (ví dụ `manage.py addjudge judge1 '<key>'`).
- Cấu hình GitHub Actions secrets SSH (`SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`, tùy chọn `SERVER_SSH_PORT`) để CD có thể kết nối.

## Kiểm tra và giới hạn

- Đã chạy `git diff --check`; không phát hiện whitespace errors.
- Đã kiểm tra `docker compose ... config --quiet`, Ruff, Black, cú pháp shell (`bash -n`) và cú pháp Python (`py_compile`); tất cả đều đạt.
- Chưa chạy unit/integration tests, Docker image build, hoặc deploy lên server.
- Workspace không có `.env.production`, thông tin SSH, DNS/TLS thực tế hay Docker volumes của production; vì vậy chưa thể xác nhận các bước trên máy chủ hoặc thực hiện chuyển dữ liệu.

Sau khi hoàn tất các bước máy chủ, cần chạy CI và một lần deploy có giám sát để xác nhận kết nối database, TLS, bridge và judge hoạt động cùng nhau.
