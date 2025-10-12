#!/bin/bash

# ContextualForget 모니터링 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 설정
APP_DIR="/opt/contextualforget"
SERVICE_NAME="contextualforget"
SERVICE_USER="contextualforget"
LOG_DIR="/var/log/contextualforget"
CONFIG_DIR="/etc/contextualforget"
ALERT_EMAIL="admin@yourdomain.com"

# 상태 체크 함수
check_service_status() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ Service is running"
        return 0
    else
        echo "❌ Service is not running"
        return 1
    fi
}

check_service_enabled() {
    if systemctl is-enabled --quiet $SERVICE_NAME; then
        echo "✅ Service is enabled"
        return 0
    else
        echo "❌ Service is not enabled"
        return 1
    fi
}

check_disk_space() {
    local threshold=85
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $usage -gt $threshold ]; then
        echo "❌ Disk usage is high: ${usage}%"
        return 1
    else
        echo "✅ Disk usage is normal: ${usage}%"
        return 0
    fi
}

check_memory_usage() {
    local threshold=85
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ $usage -gt $threshold ]; then
        echo "❌ Memory usage is high: ${usage}%"
        return 1
    else
        echo "✅ Memory usage is normal: ${usage}%"
        return 0
    fi
}

check_cpu_usage() {
    local threshold=80
    local usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    
    if (( $(echo "$usage > $threshold" | bc -l) )); then
        echo "❌ CPU usage is high: ${usage}%"
        return 1
    else
        echo "✅ CPU usage is normal: ${usage}%"
        return 0
    fi
}

check_log_errors() {
    local error_count=$(journalctl -u $SERVICE_NAME --since "1 hour ago" | grep -i error | wc -l)
    
    if [ $error_count -gt 10 ]; then
        echo "❌ High error count in logs: $error_count errors in last hour"
        return 1
    else
        echo "✅ Log error count is normal: $error_count errors in last hour"
        return 0
    fi
}

check_application_health() {
    if [ -f "$APP_DIR/venv/bin/ctxf" ]; then
        if sudo -u $SERVICE_USER $APP_DIR/venv/bin/ctxf health > /dev/null 2>&1; then
            echo "✅ Application health check passed"
            return 0
        else
            echo "❌ Application health check failed"
            return 1
        fi
    else
        echo "❌ Application CLI not found"
        return 1
    fi
}

check_data_integrity() {
    local data_dir="$APP_DIR/data/processed"
    
    if [ -d "$data_dir" ]; then
        local graph_file="$data_dir/graph.gpickle"
        if [ -f "$graph_file" ]; then
            local file_size=$(stat -c%s "$graph_file" 2>/dev/null || echo "0")
            if [ $file_size -gt 0 ]; then
                echo "✅ Data integrity check passed"
                return 0
            else
                echo "❌ Graph file is empty or corrupted"
                return 1
            fi
        else
            echo "❌ Graph file not found"
            return 1
        fi
    else
        echo "❌ Data directory not found"
        return 1
    fi
}

# 알림 함수
send_alert() {
    local message="$1"
    local subject="ContextualForget Alert: $message"
    
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" $ALERT_EMAIL
        log_info "Alert sent to $ALERT_EMAIL"
    else
        log_warn "Mail command not available, cannot send alert"
    fi
}

# 메인 모니터링 함수
run_monitoring() {
    local overall_status=0
    local issues=()
    
    log_info "Starting ContextualForget monitoring..."
    echo "=========================================="
    
    # 서비스 상태 체크
    echo "🔧 Service Status:"
    if ! check_service_status; then
        overall_status=1
        issues+=("Service not running")
    fi
    
    if ! check_service_enabled; then
        overall_status=1
        issues+=("Service not enabled")
    fi
    
    echo ""
    
    # 시스템 리소스 체크
    echo "💻 System Resources:"
    if ! check_disk_space; then
        overall_status=1
        issues+=("High disk usage")
    fi
    
    if ! check_memory_usage; then
        overall_status=1
        issues+=("High memory usage")
    fi
    
    if ! check_cpu_usage; then
        overall_status=1
        issues+=("High CPU usage")
    fi
    
    echo ""
    
    # 애플리케이션 체크
    echo "📱 Application Health:"
    if ! check_application_health; then
        overall_status=1
        issues+=("Application health check failed")
    fi
    
    if ! check_data_integrity; then
        overall_status=1
        issues+=("Data integrity issues")
    fi
    
    echo ""
    
    # 로그 체크
    echo "📋 Log Analysis:"
    if ! check_log_errors; then
        overall_status=1
        issues+=("High error count in logs")
    fi
    
    echo ""
    echo "=========================================="
    
    # 결과 요약
    if [ $overall_status -eq 0 ]; then
        log_info "✅ All checks passed - System is healthy"
    else
        log_error "❌ Issues detected:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        
        # 알림 전송
        if [ ${#issues[@]} -gt 0 ]; then
            local alert_message="Issues detected: ${issues[*]}"
            send_alert "$alert_message"
        fi
    fi
    
    return $overall_status
}

# 상세 진단 함수
run_diagnosis() {
    log_info "Running detailed diagnosis..."
    echo "=========================================="
    
    # 서비스 상세 정보
    echo "🔧 Service Details:"
    systemctl status $SERVICE_NAME --no-pager
    echo ""
    
    # 최근 로그
    echo "📋 Recent Logs (last 20 lines):"
    journalctl -u $SERVICE_NAME --no-pager -n 20
    echo ""
    
    # 시스템 리소스 상세
    echo "💻 System Resources:"
    echo "Memory:"
    free -h
    echo ""
    echo "Disk:"
    df -h
    echo ""
    echo "CPU:"
    top -bn1 | head -5
    echo ""
    
    # 애플리케이션 메트릭
    echo "📊 Application Metrics:"
    if [ -f "$APP_DIR/venv/bin/ctxf" ]; then
        sudo -u $SERVICE_USER $APP_DIR/venv/bin/ctxf metrics 2>/dev/null || echo "Metrics not available"
    fi
    echo ""
    
    # 데이터 디렉토리 정보
    echo "📁 Data Directory:"
    if [ -d "$APP_DIR/data" ]; then
        ls -la $APP_DIR/data/
        echo ""
        if [ -d "$APP_DIR/data/processed" ]; then
            ls -la $APP_DIR/data/processed/
        fi
    else
        echo "Data directory not found"
    fi
}

# 자동 복구 함수
auto_repair() {
    log_info "Attempting auto-repair..."
    
    # 서비스 재시작
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        log_info "Restarting service..."
        systemctl restart $SERVICE_NAME
        sleep 5
        
        if systemctl is-active --quiet $SERVICE_NAME; then
            log_info "✅ Service restarted successfully"
        else
            log_error "❌ Failed to restart service"
            return 1
        fi
    fi
    
    # 로그 정리
    log_info "Cleaning up old logs..."
    journalctl --vacuum-time=7d
    
    # 임시 파일 정리
    log_info "Cleaning up temporary files..."
    find /tmp -name "*contextualforget*" -mtime +1 -delete 2>/dev/null || true
    
    log_info "Auto-repair completed"
}

# 메인 함수
main() {
    case "${1:-monitor}" in
        "monitor")
            run_monitoring
            ;;
        "diagnose")
            run_diagnosis
            ;;
        "repair")
            auto_repair
            ;;
        "help"|"-h"|"--help")
            echo "ContextualForget Monitoring Script"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  monitor   - Run health checks (default)"
            echo "  diagnose  - Run detailed diagnosis"
            echo "  repair    - Attempt auto-repair"
            echo "  help      - Show this help"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"
