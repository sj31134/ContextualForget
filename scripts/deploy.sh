#!/bin/bash

# ContextualForget 프로덕션 배포 스크립트

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경 변수 설정
ENVIRONMENT=${1:-production}
APP_NAME="contextualforget"
APP_DIR="/opt/contextualforget"
SERVICE_USER="contextualforget"
LOG_DIR="/var/log/contextualforget"
CONFIG_DIR="/etc/contextualforget"

log_info "Starting deployment for environment: $ENVIRONMENT"

# 1. 시스템 의존성 확인
log_info "Checking system dependencies..."

# Python 3.11+ 확인
if ! command -v python3.11 &> /dev/null; then
    log_error "Python 3.11+ is required but not installed"
    exit 1
fi

# 필수 패키지 확인
REQUIRED_PACKAGES=("git" "curl" "wget" "unzip")
for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! command -v $package &> /dev/null; then
        log_error "$package is required but not installed"
        exit 1
    fi
done

log_info "System dependencies check passed"

# 2. 사용자 및 디렉토리 생성
log_info "Setting up user and directories..."

if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -r -s /bin/false -d $APP_DIR $SERVICE_USER
    log_info "Created service user: $SERVICE_USER"
fi

sudo mkdir -p $APP_DIR $LOG_DIR $CONFIG_DIR
sudo chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR $LOG_DIR $CONFIG_DIR

log_info "User and directories setup completed"

# 3. 애플리케이션 코드 배포
log_info "Deploying application code..."

if [ -d "$APP_DIR/.git" ]; then
    cd $APP_DIR
    sudo -u $SERVICE_USER git pull origin main
else
    sudo -u $SERVICE_USER git clone https://github.com/sj31134/ContextualForget.git $APP_DIR
fi

cd $APP_DIR
sudo -u $SERVICE_USER git checkout main

log_info "Application code deployed"

# 4. Python 가상환경 설정
log_info "Setting up Python virtual environment..."

if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u $SERVICE_USER python3.11 -m venv $APP_DIR/venv
fi

sudo -u $SERVICE_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $SERVICE_USER $APP_DIR/venv/bin/pip install -e ".[dev]"

log_info "Python virtual environment setup completed"

# 5. 설정 파일 배포
log_info "Deploying configuration files..."

sudo cp $APP_DIR/config/$ENVIRONMENT.json $CONFIG_DIR/config.json
sudo chown $SERVICE_USER:$SERVICE_USER $CONFIG_DIR/config.json
sudo chmod 600 $CONFIG_DIR/config.json

log_info "Configuration files deployed"

# 6. 시스템 서비스 설정
log_info "Setting up system service..."

sudo tee /etc/systemd/system/contextualforget.service > /dev/null <<EOF
[Unit]
Description=ContextualForget Digital Twin Graph-RAG Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR/src
Environment=ENVIRONMENT=$ENVIRONMENT
Environment=CONFIG_FILE=$CONFIG_DIR/config.json
ExecStart=$APP_DIR/venv/bin/python -m contextualforget.cli.cli start-monitor
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=contextualforget

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable contextualforget

log_info "System service configured"

# 7. 로그 로테이션 설정
log_info "Setting up log rotation..."

sudo tee /etc/logrotate.d/contextualforget > /dev/null <<EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload contextualforget
    endscript
}
EOF

log_info "Log rotation configured"

# 8. 방화벽 설정 (선택사항)
if command -v ufw &> /dev/null; then
    log_info "Configuring firewall..."
    sudo ufw allow 8000/tcp comment "ContextualForget API"
    log_info "Firewall configured"
fi

# 9. 서비스 시작
log_info "Starting service..."

sudo systemctl start contextualforget
sleep 5

if sudo systemctl is-active --quiet contextualforget; then
    log_info "Service started successfully"
else
    log_error "Failed to start service"
    sudo systemctl status contextualforget
    exit 1
fi

# 10. 상태 확인
log_info "Checking service status..."

sudo systemctl status contextualforget --no-pager

# 11. 헬스 체크
log_info "Performing health check..."

sleep 10
if sudo -u $SERVICE_USER $APP_DIR/venv/bin/ctxf health > /dev/null 2>&1; then
    log_info "Health check passed"
else
    log_warn "Health check failed - service may still be starting"
fi

# 12. 배포 완료
log_info "Deployment completed successfully!"
log_info "Service status: $(sudo systemctl is-active contextualforget)"
log_info "Service logs: sudo journalctl -u contextualforget -f"
log_info "Application logs: tail -f $LOG_DIR/app.log"

# 13. 유용한 명령어 출력
echo ""
log_info "Useful commands:"
echo "  Service control:"
echo "    sudo systemctl start contextualforget"
echo "    sudo systemctl stop contextualforget"
echo "    sudo systemctl restart contextualforget"
echo "    sudo systemctl status contextualforget"
echo ""
echo "  Logs:"
echo "    sudo journalctl -u contextualforget -f"
echo "    tail -f $LOG_DIR/app.log"
echo ""
echo "  CLI:"
echo "    sudo -u $SERVICE_USER $APP_DIR/venv/bin/ctxf --help"
echo "    sudo -u $SERVICE_USER $APP_DIR/venv/bin/ctxf health"
echo "    sudo -u $SERVICE_USER $APP_DIR/venv/bin/ctxf metrics"
