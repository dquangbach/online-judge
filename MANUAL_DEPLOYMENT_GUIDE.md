# Hướng dẫn deploy thủ công DUTOJ

## Trạng thái hiện tại

Các lỗi cấu hình production đã được sửa trong workspace. Docker Compose, Ruff, Black, cú pháp shell và cú pháp Python đã qua kiểm tra. Tuy nhiên, **chưa thể coi hệ thống đã sẵn sàng chạy production** cho đến khi:

- Các sửa đổi được commit và push lên GitHub.
- Máy chủ có `.env.production` chứa secret thật và `SITE_DOMAIN` đã cấu hình.
- Nginx/TLS và firewall được xác nhận trên máy chủ.
- Nếu có Docker volumes cũ, dữ liệu được sao chép sang thư mục host trước khi chuyển Compose.
- Docker images được build và toàn bộ stack được kiểm tra trên máy chủ.

Không gửi mật khẩu SSH hoặc các secret qua chat. Không commit `.env.production`.

## 1. Đẩy mã nguồn đã sửa lên GitHub

Chạy trên máy có workspace của dự án:

```bash
cd "/Users/bach/Downloads/AI Projects/online-judge"
git status --short
```

Nếu các file hiện ra đúng là những thay đổi cần deploy, commit và push:

```bash
git add -A
git commit -m "fix: prepare production deployment"
git push origin master
```

Nếu `master` bị khóa, push lên branch riêng, tạo PR và deploy sau khi PR đã được merge.

## 2. Đăng nhập và kiểm tra máy chủ

Các bước cài đặt dưới đây giả định máy chủ chạy Ubuntu. SSH từ máy của bạn:

```bash
ssh your-user@your-server-ip
```

Chạy các lệnh chỉ đọc trước khi thay đổi server:

```bash
cat /etc/os-release
df -h /
free -h
sudo docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
sudo docker volume ls
sudo nginx -t
sudo nginx -T 2>/dev/null | grep -E 'server_name|listen '
```

Nếu server đang chạy website, Docker containers hoặc có volumes dữ liệu, hãy sao lưu trước khi deploy. Không xóa container/volume cũ và không thay Nginx site đang hoạt động cho đến khi xác định rõ cách chuyển dữ liệu.

Firewall của nhà cung cấp cần cho phép inbound cổng `22`, `80`, `443`. Không mở `3306`, `6379`, `11211`, `8001`, `9998`, `9999` hoặc `15100` ra Internet.

## 3. Cài Docker, Compose, Git và Nginx

Trên Ubuntu, cài Docker Engine từ [kho chính thức của Docker](https://docs.docker.com/engine/install/ubuntu/):

```bash
sudo apt update
sudo apt install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker

sudo apt install -y git nginx certbot
```

Kiểm tra Compose đã có:

```bash
sudo docker compose version
```

## 4. Chuẩn bị domain, DNS và TLS

Khuyến nghị dùng domain trỏ bản ghi A về IP server. Nếu có bản ghi AAAA thì phải trỏ đúng server IPv6. Mở cổng `80` để cấp/challenge chứng chỉ và `443` để phục vụ HTTPS.

Repo có cấu hình Nginx production sẵn tại `sample_conf/nginx/production.conf`. Cấu hình đó trỏ tới chứng chỉ ở `/etc/letsencrypt/live/<DOMAIN>/`.

Nếu server mới và chưa có Nginx site đang hoạt động, tạo thư mục challenge và cấu hình HTTP tạm cho domain:

```bash
sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
sudo tee /etc/nginx/sites-available/online-judge-acme >/dev/null <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name <DOMAIN>;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }

    location / {
        return 200 "ACME bootstrap";
    }
}
EOF
```

Thay `<DOMAIN>` bằng domain thật trong file, bật site rồi lấy chứng chỉ:

```bash
sudo ln -sfn /etc/nginx/sites-available/online-judge-acme \
  /etc/nginx/sites-enabled/online-judge-acme
sudo nginx -t && sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/www/certbot \
  -d oj.example.com --agree-tos -m you@example.com --non-interactive
```

Thay `oj.example.com` và `you@example.com` bằng domain và email của bạn.

IP-only cũng có thể dùng chứng chỉ Let’s Encrypt ngắn hạn; cần Certbot mới hỗ trợ IP và cấu hình gia hạn tự động. Với lần deploy đầu, domain thường ít phức tạp hơn. Xem [thông tin chính thức về chứng chỉ IP](https://letsencrypt.org/2026/01/15/6day-and-ip-address-certificates-are-generally-available/) và [hướng dẫn Certbot cho IP](https://letsencrypt.org/2026/03/11/shorter-certs-certbot.html).

Nếu Nginx đang phục vụ site hiện tại, không thay cấu hình đó theo mẫu trên trước khi đã chuẩn bị cutover và backup.

## 5. Clone repo và tạo `.env.production`

Clone repo sau khi các sửa đổi ở bước 1 đã được push:

```bash
sudo mkdir -p /opt/online-judge
sudo chown "$USER:$(id -gn)" /opt/online-judge
git clone https://github.com/dquangbach/online-judge.git /opt/online-judge
cd /opt/online-judge

cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production
```

Tạo **secret riêng cho từng biến** bằng lệnh dưới đây; chạy lại cho mỗi secret và không dùng chung giá trị:

```bash
openssl rand -hex 32
```

Thay toàn bộ giá trị `change-me` trong `.env.production`. Kiểm tra các mục sau:

- `DJANGO_SECRET_KEY`: secret dài ít nhất 50 ký tự.
- `MYSQL_ROOT_PASSWORD` và `MYSQL_PASSWORD`: hai mật khẩu riêng.
- `CHAT_SECRET_KEY`, `EVENT_DAEMON_KEY`, `EVENT_DAEMON_SUBMISSION_KEY`, `JUDGE_AUTH_KEY`: các secret riêng.
- `SITE_DOMAIN=<DOMAIN>` — chỉ hostname, không có `https://`.
- `DJANGO_ALLOWED_HOSTS=<SERVER_IP>,<DOMAIN>` — không dùng `*`.
- `ALLOWED_ORIGINS=https://<DOMAIN>`.
- `EVENT_DAEMON_PUBLIC_URL=wss://<DOMAIN>`.
- Giữ `EVENT_DAEMON_URL=http://wsevent:15100`, `MYSQL_HOST=db`, `BRIDGED_CONNECT_HOST=bridge`, `DMOJ_SSL=1`.
- Giữ các thư mục `STATIC_DIR`, `MEDIA_DIR`, `PROBLEM_DIR` khớp với đường dẫn Nginx mẫu: `/opt/online-judge/static`, `/opt/online-judge/media`, `/opt/online-judge/problem_data`.

Tạo thư mục host:

```bash
sudo mkdir -p /opt/online-judge/static \
  /opt/online-judge/media \
  /opt/online-judge/problem_data
```

## 6. Chuyển dữ liệu cũ nếu server đã dùng Docker volumes

Lệnh `sudo docker volume ls` ở bước 2 cho biết có các volume cũ không. Nếu có `dutoj-prod_static_data`, `dutoj-prod_media_data` hoặc `dutoj-prod_problem_data`, chạy script này **trước khi khởi động Compose mới**:

```bash
cd /opt/online-judge
sudo ./scripts/migrate-legacy-docker-volumes.sh
```

Script chỉ sao chép, không xóa nguồn. Nếu thư mục đích không rỗng, script dừng để tránh ghi đè. Khi đó hãy dừng lại và kiểm tra dữ liệu đích với nguồn trước khi tiếp tục.

## 7. Kiểm tra Compose, build và khởi tạo Django

```bash
cd /opt/online-judge
sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production config --quiet

sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production build web bridge wsevent celery_worker celery_beat

sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production up -d db redis memcached wsevent
```

Chạy migrations, collectstatic và tạo tài khoản quản trị:

```bash
sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production run --rm web \
  python3 manage.py migrate --noinput

sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production run --rm web \
  python3 manage.py collectstatic --noinput

sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production run --rm web \
  python3 manage.py createsuperuser
```

Khởi động web, bridge và Celery, tạm thời chưa bật judge:

```bash
sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production up -d \
  web bridge celery_worker celery_beat
```

## 8. Cài Nginx production và bật HTTPS

Sao chép cấu hình mẫu và thay hostname:

```bash
sudo cp /opt/online-judge/sample_conf/nginx/production.conf \
  /etc/nginx/sites-available/online-judge
sudo sed -i 's/oj.yourdomain.com/oj.example.com/g' \
  /etc/nginx/sites-available/online-judge
sudo ln -sfn /etc/nginx/sites-available/online-judge \
  /etc/nginx/sites-enabled/online-judge
```

Trong file vừa cài, xác nhận các alias trỏ tới đúng `STATIC_DIR` và `MEDIA_DIR`, và các đường dẫn chứng chỉ khớp với domain. Sau đó kiểm tra và reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo certbot renew --dry-run
```

Chỉ gỡ link `sites-enabled/default` nếu đã xác nhận site mặc định không được dùng. Cấu hình này redirect HTTP sang HTTPS, proxy uWSGI và WebSocket.

## 9. Đăng ký judge và xác nhận hoạt động

Mở `https://<DOMAIN>`, đăng nhập tài khoản quản trị, vào **Admin → Judges → Add Judge**. Tạo judge tên `judge1` và nhập đúng giá trị `JUDGE_AUTH_KEY` trong `.env.production`.

Sau đó bật judge:

```bash
sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production up -d judge

sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production ps

sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production exec -T web \
  python3 manage.py bridge_status
```

Kết quả `bridge_status` cần hiện bridge hoạt động và có ít nhất một judge kết nối. Trong admin, judge cũng cần hiện trạng thái online.

Backup dữ liệu theo script trong repo:

```bash
sudo /opt/online-judge/scripts/backup.sh
```

## 10. Deploy tự động bằng GitHub Actions (tùy chọn)

Workflow hiện dùng SSH key, không đăng nhập bằng mật khẩu. Sau khi deploy thủ công thành công, tạo SSH key riêng cho deploy, cài public key vào user trên server và cấu hình GitHub repository secrets: `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`, tùy chọn `SERVER_SSH_PORT`. Sau đó chạy workflow thủ công với `target_ref=master` hoặc tag release.

## Nếu gặp lỗi

Thu thập trạng thái và log, không gửi `.env.production`:

```bash
sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production ps

sudo docker compose -f docker-compose.prod.yml \
  --env-file .env.production logs --tail=100 web bridge judge wsevent

sudo nginx -t
```

Gửi output đã che IP/domain nếu muốn giữ riêng tư, và tuyệt đối xóa mật khẩu, secret, token, private key khỏi output trước khi chia sẻ.
