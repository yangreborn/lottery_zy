# 后端部署到阿里云 ECS 指南

把 `lottery_backend`（Django 5.2 + DRF + PostgreSQL）部署到阿里云 ECS，
对外提供 HTTPS API，供微信小程序体验版/正式版调用。

> 命令以 **Ubuntu 22.04/24.04** 为例（root 或 sudo 用户）。CentOS 把 `apt` 换成 `yum/dnf` 即可。
> 域名 `api.example.com` 替换成你自己的；数据库密码等按需替换。

## 架构

```
微信小程序 → HTTPS(api.example.com) → nginx(443) → gunicorn(127.0.0.1:8000) → Django
                                         └── /static/ 直接由 nginx 托管
                                    PostgreSQL(本机 127.0.0.1:5432 或阿里云 RDS)
```

## 0. 前置准备

- 买好 ECS（2核2G 起步够用），系统选 Ubuntu 22.04/24.04。
- **域名必须 ICP 备案**（阿里云域名在阿里云备案），否则微信不允许作为合法域名、HTTPS 证书也签不了国内可信。
- 域名解析：在阿里云 DNS 把 `api.example.com` A 记录指向 ECS 公网 IP。
- ECS **安全组**放行入方向端口：`80`（HTTP）、`443`（HTTPS）、`22`（SSH）。数据库端口 5432 **不要**对公网开放。

## 1. 安装系统依赖

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git nginx postgresql postgresql-contrib
python3 --version   # 需 >= 3.11（项目在 3.12 开发）
```

## 2. 建数据库（本机 PostgreSQL）

```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE lottery;
CREATE USER lottery_user WITH PASSWORD '改成强密码';
ALTER ROLE lottery_user SET client_encoding TO 'utf8';
ALTER ROLE lottery_user SET timezone TO 'Asia/Shanghai';
GRANT ALL PRIVILEGES ON DATABASE lottery TO lottery_user;
SQL
# PG15+ 还需把 public schema 权限给到用户：
sudo -u postgres psql -d lottery -c "GRANT ALL ON SCHEMA public TO lottery_user;"
```

> 若用**阿里云 RDS PostgreSQL**：跳过本机安装，直接在 RDS 控制台建库建账号，把内网地址/端口/账号填进下面的 `.env`，并把 ECS 加入 RDS 白名单。

## 3. 拉代码 + 虚拟环境 + 依赖

```bash
mkdir -p /opt && cd /opt
git clone git@github.com:yangreborn/lottery_zy.git lottery   # 或 https 方式
cd /opt/lottery/lottery_backend
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## 4. 配置 .env

后端 `settings.py` 会自动读取 `lottery_backend/.env`。新建该文件：

```bash
cat > /opt/lottery/lottery_backend/.env <<'ENV'
SECRET_KEY=用一段足够长的随机字符串
DEBUG=False
ALLOWED_HOSTS=api.example.com

DB_NAME=lottery
DB_USER=lottery_user
DB_PASSWORD=改成强密码
DB_HOST=127.0.0.1
DB_PORT=5432

# 微信小程序（在微信公众平台-开发设置里拿）
WECHAT_APPID=wx3b0f890a8af52a9c
WECHAT_SECRET=你的小程序密钥
ENV
```

> 生成 SECRET_KEY 可执行：`python -c "import secrets;print(secrets.token_urlsafe(50))"`
> 注意：`DEBUG=False` 后跨域默认关闭（同域 nginx 转发，无需 CORS）。

## 5. 初始化数据

```bash
cd /opt/lottery/lottery_backend && . .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput      # 收集到 staticfiles/
python manage.py createsuperuser               # 建后台管理员
python manage.py seed_lotteries                # 写入彩种基础数据
python manage.py crawl_draw                    # 抓一次开奖（草稿）
```

抓取后到后台「开奖结果」里勾选→「发布选中开奖记录」才会对外可见（见 `docs/admin-manual-setup.md`）。

## 6. gunicorn 跑起来（先手测）

```bash
cd /opt/lottery/lottery_backend && . .venv/bin/activate
gunicorn config.wsgi:application --bind 127.0.0.1:8000
# 浏览器/另开终端 curl 本机 8000 验证后退出
```

### 配成 systemd 服务（开机自启、崩溃重启）

```bash
cat > /etc/systemd/system/lottery.service <<'UNIT'
[Unit]
Description=lottery gunicorn
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/lottery/lottery_backend
ExecStart=/opt/lottery/lottery_backend/.venv/bin/gunicorn config.wsgi:application \
  --workers 3 --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

# 目录授权给运行用户
chown -R www-data:www-data /opt/lottery/lottery_backend
systemctl daemon-reload
systemctl enable --now lottery
systemctl status lottery   # 看是否 active(running)
```

## 7. nginx 反向代理 + 静态托管

```bash
cat > /etc/nginx/sites-available/lottery <<'NGINX'
server {
    listen 80;
    server_name api.example.com;

    location /static/ {
        alias /opt/lottery/lottery_backend/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/lottery /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

此时 `http://api.example.com/api/openapi/lottery/list` 应能返回 JSON。

## 8. 开启 HTTPS（微信强制要求）

**方式 A：Let's Encrypt（免费，自动续期）**
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d api.example.com
# 按提示填邮箱、同意条款，certbot 会自动改好 nginx 443 配置
```

**方式 B：阿里云 SSL 证书**
在阿里云申请免费证书，下载 nginx 版，上传证书到 ECS，手动在 nginx 配置里加 `listen 443 ssl;` 与证书路径，再 `systemctl reload nginx`。

完成后 `https://api.example.com/...` 可访问。

## 9. 微信公众平台配置合法域名

mp.weixin.qq.com → 开发管理 → 开发设置 → 服务器域名 →
**request 合法域名** 添加：`https://api.example.com`（必须 HTTPS、必须备案）。

## 10. 前端指向生产后端并构建上传

本地 `lottery_frontend/` 新建 `.env.production`：
```
VITE_API_BASE=https://api.example.com
```
然后：
```bash
cd lottery_frontend
npm run build:mp-weixin
```
用微信开发者工具导入 `dist/build/mp-weixin` → 上传 → 公众平台「版本管理」选为体验版（详见上一步说明）。

## 11. 日常更新流程

```bash
cd /opt/lottery && git pull
cd lottery_backend && . .venv/bin/activate
pip install -r requirements.txt        # 依赖有变动时
python manage.py migrate               # 有新迁移时
python manage.py collectstatic --noinput
systemctl restart lottery
```

开奖更新：定期 `python manage.py crawl_draw` 后到后台发布（调度未做，可自行加 crontab，见 note40）。

## 备忘
- DB 密码、SECRET_KEY、WECHAT_SECRET 只放在服务器 `.env`，**不要提交到 git**。
- 安全组别对公网开 5432；数据库只走本机/内网。
- 备份：定期 `pg_dump lottery > backup.sql`。
```
