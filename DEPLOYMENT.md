# Deployment Guide

## Pre-deployment Checklist

- [ ] All environment variables configured correctly
- [ ] PostgreSQL database created and accessible
- [ ] Migrations run: `alembic upgrade head`
- [ ] Secret key is strong and not default
- [ ] CORS origins configured for production
- [ ] Upload directory has proper permissions
- [ ] Logging configured
- [ ] HTTPS configured (if public)

## Environment Setup

### Production .env
```bash
DATABASE_URL=postgresql://user:password@dbhost:5432/proddb
SECRET_KEY=<generated-secure-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=1
UPLOAD_DIR=/var/app/uploads/
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=jpg,jpeg,png,webp
APP_NAME=TableManager Production
```

### Update CORS in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Docker Deployment

### Build and run with Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tablemanager
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/tablemanager
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "8000:8000"
    volumes:
      - uploads:/app/uploads

volumes:
  postgres_data:
  uploads:
```

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/profiles uploads/products

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy:
```bash
export DB_PASSWORD=yourpassword
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
docker-compose up -d
```

## Linux Server Deployment (Ubuntu)

### Using Systemd

Create `/etc/systemd/system/tablemanager.service`:

```ini
[Unit]
Description=TableManager API
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/tablemanager
Environment="DATABASE_URL=postgresql://..."
Environment="SECRET_KEY=..."
ExecStart=/var/www/tablemanager/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Copy files to server
sudo cp -r . /var/www/tablemanager
sudo chown -R www-data:www-data /var/www/tablemanager

# Create uploads directory
sudo mkdir -p /var/www/tablemanager/uploads
sudo chown -R www-data:www-data /var/www/tablemanager/uploads

# Enable and start service
sudo systemctl enable tablemanager
sudo systemctl start tablemanager
sudo systemctl status tablemanager
```

## Nginx作为反向代理

Create `/etc/nginx/sites-available/tablemanager`:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /uploads/ {
        alias /var/www/tablemanager/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and test:
```bash
sudo ln -s /etc/nginx/sites-available/tablemanager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL with Let's Encrypt

```bash
sudo certbot --nginx -d api.yourdomain.com
```

## Monitoring

### Health Check
```bash
curl https://api.yourdomain.com/health
```

### Logs
```bash
# Systemd
sudo journalctl -u tablemanager -f

# Docker
docker-compose logs -f api
```

## Backup Strategy

### Database Backup
```bash
# Daily cron job
0 2 * * * pg_dump tablemanager > /backups/tablemanager_$(date +\%Y\%m\%d).sql
```

### File Uploads Backup
```bash
# Sync uploads to S3 or backup server
rsync -av uploads/ backup@server:/backups/uploads/
```

## Scaling

### Horizontal Scaling (Multiple Instances)
- Use same PostgreSQL database
- Share uploads via NFS or object storage (S3)
- Load balance with Nginx/HAProxy

### Upload to S3 instead of local filesystem

Update `app/core/uploads.py`:
```python
import boto3
from botocore.exceptions import NoCredentialsError

s3_client = boto3.client('s3')

async def save_upload_file(upload_file: UploadFile, subfolder: str = "temp") -> str:
    key = f"{subfolder}/{uuid.uuid4()}_{upload_file.filename}"
    try:
        s3_client.upload_fileobj(
            upload_file.file,
            'your-bucket-name',
            key,
            ExtraArgs={'ACL': 'public-read'}
        )
        return key
    except NoCredentialsError:
        raise HTTPException(500, "S3 credentials not configured")
```

## Security Hardening

1. Change default admin password
2. Disable `/docs` in production:
   ```python
   app = FastAPI(docs_url=None, redoc_url=None)  # Disable API docs
   ```
3. Add rate limiting (Redis)
4. Enable request logging
5. Set up firewall rules
6. Regular security updates
7. Use environment-specific secrets

## Troubleshooting

### Database Migration Fails
```bash
alembic downgrade base
alembic upgrade head
```

### Permission Errors
```bash
sudo chown -R www-data:www-data /var/www/tablemanager
sudo chmod 755 uploads/
```

### Memory Issues
- Increase worker count
- Use Gunicorn with Uvicorn workers:
  ```bash
  gunicorn -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000 app.main:app
  ```
