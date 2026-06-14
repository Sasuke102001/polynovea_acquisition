# M2 Nginx Config — EC2 Deployment

Deploy to: `/etc/nginx/sites-available/polynovea` on the EC2 instance (43.205.229.130)

```nginx
# Rate limiting zones — defined in http block (before server block)
limit_req_zone $binary_remote_addr zone=api_general:10m   rate=60r/m;
limit_req_zone $binary_remote_addr zone=api_chat:10m      rate=10r/m;
limit_req_zone $binary_remote_addr zone=api_demo:10m      rate=20r/m;

server {
    listen 80;
    server_name acquisition.polynovearecords.in;

    # Redirect all HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name acquisition.polynovearecords.in;

    ssl_certificate     /etc/letsencrypt/live/acquisition.polynovearecords.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/acquisition.polynovearecords.in/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Security headers (belt-and-suspenders alongside FastAPI middleware)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options    nosniff                                always;
    add_header X-Frame-Options           DENY                                   always;
    add_header Referrer-Policy           strict-origin-when-cross-origin        always;

    # Chat endpoints — strictest limit (10 RPM)
    location ~ ^/api/venues/[0-9]+/chat {
        limit_req zone=api_chat burst=3 nodelay;
        limit_req_status 429;
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    # Demo chat — 20 RPM
    location ~ ^/api/demo/.+/chat {
        limit_req zone=api_demo burst=5 nodelay;
        limit_req_status 429;
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 120s;
    }

    # All other API routes — 60 RPM
    location /api/ {
        limit_req zone=api_general burst=20 nodelay;
        limit_req_status 429;
        proxy_pass       http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }

    # Health check — no rate limit (for UptimeRobot)
    location = /api/health {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

## Deploy steps

```bash
sudo cp polynovea /etc/nginx/sites-available/polynovea
sudo ln -sf /etc/nginx/sites-available/polynovea /etc/nginx/sites-enabled/polynovea
sudo nginx -t
sudo systemctl reload nginx
```

## EC2 security group (AWS console — sg-0b6a8ad443531abf5)

Port 8000 (FastAPI direct) should be **removed** from inbound rules once Nginx is verified working.
Only ports 80 and 443 should be open to 0.0.0.0/0.
Port 22 (SSH) stays as-is.
