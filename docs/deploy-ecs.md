# 后端部署到阿里云 ECS 指南

把 `lottery_backend`（Django 5.2 + DRF + PostgreSQL）部署到阿里云 ECS，
对外提供 HTTPS API，供微信小程序体验版/正式版调用。

> 命令以 **Ubuntu 22.04/24.04** 为例（root 或 sudo 用户）。CentOS 把 `apt` 换成 `yum/dnf` 即可。
> 域名 `api.example.com` 替换成你自己的；数据库密码等按需替换。

## 架构

```
微信小程序 → HTTPS(api.example.com) → nginx(443) → gunicorn(127.0.0.1:8000) → Django
H5 网页    →                          ├── /            H5 静态站点 /var/www/lottery/h5
                                       ├── /api/ /admin/ 反代 gunicorn
                                       └── /static/     nginx 托管 /var/www/lottery/static
                                    PostgreSQL(本机 127.0.0.1:5432 或阿里云 RDS)
```

> 本项目当前实际部署:公网 IP `47.100.161.8`,代码在 `/root/lottery_zy`,
> 尚未备案域名 / HTTPS,故小程序只能用开发者工具开发版联调(见第 8、10 节)。

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

> ⚠️ 坑:若曾用 `postgres` 超级用户建过表,后续用 `lottery_user` 执行 `migrate`
> 会报 `must be owner of table ...`。把库内所有表/序列 owner 改给 `lottery_user`：
> ```bash
> sudo -u postgres psql -d lottery <<'SQL'
> DO $$ DECLARE r RECORD; BEGIN
>   FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='public' LOOP
>     EXECUTE format('ALTER TABLE public.%I OWNER TO lottery_user', r.tablename); END LOOP;
>   FOR r IN SELECT sequencename FROM pg_sequences WHERE schemaname='public' LOOP
>     EXECUTE format('ALTER SEQUENCE public.%I OWNER TO lottery_user', r.sequencename); END LOOP;
> END $$; SQL
> ```

> 若用**阿里云 RDS PostgreSQL**：跳过本机安装，直接在 RDS 控制台建库建账号，把内网地址/端口/账号填进下面的 `.env`，并把 ECS 加入 RDS 白名单。

## 3. 拉代码 + 虚拟环境 + 依赖

```bash
cd /root
git clone git@github.com:yangreborn/lottery_zy.git   # 或 https 方式 → /root/lottery_zy
cd /root/lottery_zy/lottery_backend
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

> 本项目实际把代码放在 `/root/lottery_zy`(故 systemd 以 root 运行)。
> 若想用 `www-data` 运行更安全,改 clone 到 `/opt/lottery` 并把下文所有
> `/root/lottery_zy` 路径、`User=root` 相应替换即可。

## 4. 配置 .env

后端 `settings.py` 会自动读取 `lottery_backend/.env`。新建该文件：

```bash
cat > /root/lottery_zy/lottery_backend/.env <<'ENV'
SECRET_KEY=用一段足够长的随机字符串
DEBUG=False
# 未备案域名前用公网 IP；备案后改成 api.example.com
ALLOWED_HOSTS=47.100.161.8,api.example.com

DB_NAME=lottery
DB_USER=lottery_user
DB_PASSWORD=改成强密码
DB_HOST=127.0.0.1
DB_PORT=5432

# collectstatic 收集到 nginx 可读目录（见 settings.py STATIC_ROOT）
STATIC_ROOT=/var/www/lottery/static

# 微信小程序（在微信公众平台-开发设置里拿）
WECHAT_APPID=wx3b0f890a8af52a9c
WECHAT_SECRET=你的小程序密钥
ENV
```

> 生成 SECRET_KEY 可执行：`python -c "import secrets;print(secrets.token_urlsafe(50))"`
> 注意：`DEBUG=False` 后跨域默认关闭（同域 nginx 转发，无需 CORS）。

## 5. 初始化数据

```bash
mkdir -p /var/www/lottery/static /var/www/lottery/h5   # nginx 托管目录
cd /root/lottery_zy/lottery_backend && . .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput      # 收集到 STATIC_ROOT(/var/www/lottery/static)
python manage.py createsuperuser               # 建后台管理员
python manage.py seed_lotteries                # 写入彩种基础数据
python manage.py load_history --count 100      # 拉最近100期并自动发布
```

> `crawl_draw` 只抓最新 1 期且为**草稿**,需到后台「开奖结果」勾选→「发布选中开奖记录」才对外可见;
> `load_history --count N` 抓 N 期并**自动发布**,初始化建议用它。

抓取后到后台「开奖结果」里勾选→「发布选中开奖记录」才会对外可见（见 `docs/admin-manual-setup.md`）。

## 6. gunicorn 跑起来（先手测）

```bash
cd /root/lottery_zy/lottery_backend && . .venv/bin/activate
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
User=root
WorkingDirectory=/root/lottery_zy/lottery_backend
ExecStart=/root/lottery_zy/lottery_backend/.venv/bin/gunicorn config.wsgi:application \
  --workers 3 --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now lottery
systemctl status lottery   # 看是否 active(running)
```

## 7. nginx 反向代理 + 静态托管

同一个 server 同时托管 H5 静态站点(`/`)和后端 API(`/api/`、`/admin/`、`/static/`)：

```bash
cat > /etc/nginx/sites-available/lottery <<'NGINX'
server {
    listen 80;
    server_name 47.100.161.8 api.example.com;   # 未备案前用 IP

    # H5 网页（uni-app build:h5 产物）
    root /var/www/lottery/h5;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Django 后台静态资源
    location /static/ {
        alias /var/www/lottery/static/;
    }

    # 后端 API 与后台管理 → gunicorn
    location ~ ^/(api|admin)/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/lottery /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default   # 去掉默认站点避免抢占
nginx -t && systemctl reload nginx
```

此时 `http://47.100.161.8/api/openapi/lottery/list` 应返回 JSON,`http://47.100.161.8/` 打开 H5 页面。
> `sites-enabled/lottery` 是指向 `sites-available/lottery` 的软链接,核对实际生效配置用 `nginx -T`。

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
# 备案 + HTTPS 完成后用域名；当前阶段先用公网 IP（仅开发者工具开发版可联调）
VITE_API_BASE=https://api.example.com
```
> ⚠️ 现状是 `VITE_API_BASE=http://47.100.161.8`。小程序**体验版/正式版必须 HTTPS+已备案域名**,
> 所以 http/IP 下只能用开发者工具开发版(本地设置勾「不校验合法域名」)联调,无法上传体验版。
然后：
```bash
cd lottery_frontend
npm run build:mp-weixin
```
用微信开发者工具导入 `dist/build/mp-weixin` → 上传 → 公众平台「版本管理」选为体验版（详见上一步说明）。

## 11. 日常更新流程

**后端更新：**
```bash
cd /root/lottery_zy && git pull
cd lottery_backend && . .venv/bin/activate
pip install -r requirements.txt        # 依赖有变动时
python manage.py migrate               # 有新迁移时
python manage.py collectstatic --noinput
systemctl restart lottery
```

**H5 更新**(本地构建后上传产物,再覆盖到 nginx 目录)：
```bash
# 本地
cd lottery_frontend && npm run build:h5         # 产物在 dist/build/h5
# 上传到 ECS 后（产物放在 ~/h5）：
rm -rf /var/www/lottery/h5/* && cp -r ~/h5/. /var/www/lottery/h5/
chmod -R a+rX /var/www/lottery/h5
```
> 坑:H5 对外目录是 `/var/www/lottery/h5`,拷到别处(如 `~/lottery_frontend/h5`)不会生效。

**开奖更新**：crontab 定时跑 `crawl_draw`(草稿需后台发布)或 `load_history --count N`(自动发布)。
crontab 示例(每天 22:00,注意服务器时区 `timedatectl`)：
```cron
0 22 * * * cd /root/lottery_zy/lottery_backend && .venv/bin/python manage.py crawl_draw >> /var/log/lottery_crawl.log 2>&1
```

## 备忘
- DB 密码、SECRET_KEY、WECHAT_SECRET 只放在服务器 `.env`，**不要提交到 git**。
- 安全组别对公网开 5432；数据库只走本机/内网。
- 备份：定期 `pg_dump lottery > backup.sql`。
```
