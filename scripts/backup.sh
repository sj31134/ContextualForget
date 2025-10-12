#!/bin/bash

# ContextualForget 백업 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# 설정
BACKUP_DIR="/var/backups/contextualforget"
APP_DIR="/opt/contextualforget"
DATA_DIR="/opt/contextualforget/data"
LOG_DIR="/var/log/contextualforget"
CONFIG_DIR="/etc/contextualforget"
SERVICE_USER="contextualforget"
RETENTION_DAYS=30

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 타임스탬프 생성
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="contextualforget_backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

log_info "Starting backup: $BACKUP_NAME"

# 1. 애플리케이션 코드 백업
log_info "Backing up application code..."
tar -czf "$BACKUP_PATH/app.tar.gz" -C /opt contextualforget --exclude="venv" --exclude="__pycache__" --exclude="*.pyc"

# 2. 데이터 백업
log_info "Backing up data..."
if [ -d "$DATA_DIR" ]; then
    tar -czf "$BACKUP_PATH/data.tar.gz" -C /opt contextualforget/data
else
    log_warn "Data directory not found: $DATA_DIR"
fi

# 3. 설정 파일 백업
log_info "Backing up configuration..."
if [ -d "$CONFIG_DIR" ]; then
    tar -czf "$BACKUP_PATH/config.tar.gz" -C /etc contextualforget
else
    log_warn "Config directory not found: $CONFIG_DIR"
fi

# 4. 로그 백업 (최근 7일)
log_info "Backing up recent logs..."
if [ -d "$LOG_DIR" ]; then
    find $LOG_DIR -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_PATH/logs.tar.gz" {} +
else
    log_warn "Log directory not found: $LOG_DIR"
fi

# 5. 시스템 서비스 설정 백업
log_info "Backing up system service configuration..."
if [ -f "/etc/systemd/system/contextualforget.service" ]; then
    cp /etc/systemd/system/contextualforget.service "$BACKUP_PATH/"
fi

# 6. 데이터베이스 백업 (PostgreSQL이 있는 경우)
if command -v pg_dump &> /dev/null; then
    log_info "Backing up database..."
    DB_NAME=$(grep -o '"database": "[^"]*"' /etc/contextualforget/config.json | cut -d'"' -f4)
    if [ ! -z "$DB_NAME" ]; then
        sudo -u postgres pg_dump $DB_NAME > "$BACKUP_PATH/database.sql"
    else
        log_warn "Database name not found in config"
    fi
fi

# 7. 메타데이터 생성
log_info "Creating backup metadata..."
cat > "$BACKUP_PATH/metadata.txt" <<EOF
Backup Information
==================
Backup Name: $BACKUP_NAME
Backup Date: $(date)
Backup Size: $(du -sh $BACKUP_PATH | cut -f1)
System: $(uname -a)
ContextualForget Version: $(cd $APP_DIR && git rev-parse HEAD 2>/dev/null || echo "unknown")
Python Version: $(python3 --version)
Disk Usage: $(df -h / | tail -1)

Backup Contents:
- app.tar.gz: Application code
- data.tar.gz: Data files
- config.tar.gz: Configuration files
- logs.tar.gz: Recent log files
- contextualforget.service: System service configuration
- database.sql: Database dump (if available)
- metadata.txt: This file
EOF

# 8. 백업 압축
log_info "Compressing backup..."
cd $BACKUP_DIR
tar -czf "${BACKUP_NAME}.tar.gz" $BACKUP_NAME
rm -rf $BACKUP_NAME

# 9. 백업 검증
log_info "Verifying backup..."
if [ -f "${BACKUP_NAME}.tar.gz" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log_info "Backup created successfully: ${BACKUP_NAME}.tar.gz ($BACKUP_SIZE)"
else
    log_error "Backup verification failed"
    exit 1
fi

# 10. 오래된 백업 정리
log_info "Cleaning up old backups..."
find $BACKUP_DIR -name "contextualforget_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
REMAINING_BACKUPS=$(ls -1 $BACKUP_DIR/contextualforget_backup_*.tar.gz 2>/dev/null | wc -l)
log_info "Remaining backups: $REMAINING_BACKUPS"

# 11. 백업 목록 출력
log_info "Current backups:"
ls -lh $BACKUP_DIR/contextualforget_backup_*.tar.gz 2>/dev/null || log_warn "No backups found"

log_info "Backup completed successfully!"

# 12. 복원 명령어 안내
echo ""
log_info "To restore from this backup:"
echo "  1. Stop the service: sudo systemctl stop contextualforget"
echo "  2. Extract backup: cd /tmp && tar -xzf $BACKUP_DIR/${BACKUP_NAME}.tar.gz"
echo "  3. Restore files: sudo cp -r $BACKUP_NAME/* /"
echo "  4. Restart service: sudo systemctl start contextualforget"
