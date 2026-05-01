#!/bin/bash
# setup_rpi_nginx.sh - Установка микросервиса User Service для Raspberry Pi с Nginx

set -e  # Остановка при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Функции для вывода
print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}==>${NC} ${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_substep() {
    echo -e "${CYAN}  →${NC} $1"
}

print_error() {
    echo -e "${RED}❌ Ошибка: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  Предупреждение: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_config() {
    echo -e "${MAGENTA}📝 $1${NC}"
}

# Проверка архитектуры Raspberry Pi
check_rpi() {
    print_step "Проверка системы Raspberry Pi"
    
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model | tr -d '\0')
        print_success "Обнаружена: $MODEL"
    else
        MODEL="Raspberry Pi (unknown)"
        print_info "Не удалось определить модель"
    fi
    
    ARCH=$(uname -m)
    print_info "Архитектура: $ARCH"
    
    if [[ "$ARCH" == "aarch64" ]]; then
        print_success "64-битная архитектура"
    elif [[ "$ARCH" == "armv7l" ]]; then
        print_info "32-битная архитектура (armv7l)"
    fi
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_info "ОС: $NAME $VERSION"
    fi
    
    # Проверка свободного места
    FREE_SPACE=$(df -BG / | tail -1 | awk '{print $4}' | sed 's/G//')
    print_info "Свободное место: ${FREE_SPACE}GB"
    
    if [ "$FREE_SPACE" -lt 2 ]; then
        print_error "Недостаточно свободного места! Требуется минимум 2GB"
        exit 1
    fi
    
    TOTAL_RAM=$(free -h | grep Mem | awk '{print $2}')
    print_info "Оперативная память: $TOTAL_RAM"
    
    # Получение IP адреса
    IP_ADDR=$(hostname -I | awk '{print $1}')
    print_info "IP адрес: $IP_ADDR"
}

# Обновление системы
update_system() {
    print_step "Обновление системы"
    
    print_substep "Обновление списка пакетов..."
    sudo apt-get update
    
    print_substep "Обновление установленных пакетов..."
    sudo apt-get upgrade -y
    
    print_success "Система обновлена"
}

# Установка системных зависимостей
install_system_deps() {
    print_step "Установка системных зависимостей"
    
    local deps=(
        "python3"
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "postgresql"
        "postgresql-contrib"
        "libpq-dev"
        "nginx"
        "gcc"
        "make"
        "git"
        "curl"
        "wget"
        "htop"
        "nano"
        "build-essential"
        "libssl-dev"
        "libffi-dev"
        "certbot"
        "python3-certbot-nginx"
    )
    
    for dep in "${deps[@]}"; do
        if ! dpkg -s "$dep" 2>/dev/null | grep -q "Status: install ok installed"; then
            print_substep "Установка: $dep"
            sudo apt-get install -y "$dep"
        else
            print_substep "$dep уже установлен"
        fi
    done
    
    print_success "Системные зависимости установлены"
}

# Настройка PostgreSQL
setup_postgresql() {
    print_step "Настройка PostgreSQL для Raspberry Pi"
    
    print_substep "Запуск PostgreSQL..."
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    
    if sudo systemctl is-active --quiet postgresql; then
        print_success "PostgreSQL запущен"
    else
        print_error "PostgreSQL не запустился"
        return 1
    fi
    
    # Создание пользователя и базы данных
    read -p "Введите пароль для пользователя PostgreSQL: " -s PG_PASSWORD
    echo
    
    sudo -u postgres psql << EOF
CREATE USER user_service WITH PASSWORD '$PG_PASSWORD';
CREATE DATABASE usersdb OWNER user_service;
GRANT ALL PRIVILEGES ON DATABASE usersdb TO user_service;
EOF
    
    print_success "Пользователь и база данных созданы"
    
    # Сохранение пароля в .env
    echo "POSTGRES_PASSWORD=$PG_PASSWORD" >> .env.tmp
}

# Создание виртуального окружения
setup_venv() {
    print_step "Создание виртуального окружения"
    
    cd /opt
    
    if [ -d "user_service" ]; then
        print_warning "Директория user_service уже существует"
        read -p "Пересоздать? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo rm -rf user_service
            sudo mkdir -p user_service
            sudo chown $USER:$USER user_service
        fi
    else
        sudo mkdir -p user_service
        sudo chown $USER:$USER user_service
    fi
    
    cd user_service
    
    if [ -d "venv" ]; then
        print_warning "Виртуальное окружение уже существует"
    else
        python3 -m venv venv
        print_success "Виртуальное окружение создано"
    fi
    
    source venv/bin/activate
    print_success "Виртуальное окружение активировано"
}

# Установка Python зависимостей
install_python_deps() {
    print_step "Установка Python зависимостей"
    
    source /opt/user_service/venv/bin/activate
    
    pip install --upgrade pip
    
    cat > requirements.txt << 'EOF'
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-dotenv==1.0.0
gunicorn==21.2.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
asyncpg==0.29.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
bcrypt==4.0.1

# Validation
pydantic==2.5.0
pydantic-settings==2.1.0
email-validator==2.1.0

# Utils
python-dateutil==2.8.2
EOF
    
    pip install -r requirements.txt
    print_success "Python зависимости установлены"
}

# Настройка конфигурации
setup_config() {
    print_step "Настройка конфигурации"
    
    cd /opt/user_service
    
    if [ ! -f ".env" ]; then
        # Генерация секретного ключа
        SECRET_KEY=$(openssl rand -hex 32)
        
        cat > .env << EOF
# PostgreSQL Configuration
POSTGRES_USER=user_service
POSTGRES_PASSWORD=${PG_PASSWORD}
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=usersdb

# JWT Configuration
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin
ADMIN_PASSWORD=admin123

# Environment
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://${IP_ADDR},https://your-domain.com
EOF
        
        print_success "Файл .env создан"
        print_warning "Сохраните пароли:"
        print_config "PostgreSQL пароль: $PG_PASSWORD"
        print_config "Secret Key: $SECRET_KEY"
        print_config "Admin пароль: admin123"
    else
        print_success "Файл .env уже существует"
    fi
}

# Создание systemd сервиса
create_systemd_service() {
    print_step "Создание systemd сервиса"
    
    sudo cat > /etc/systemd/system/user-service.service << EOF
[Unit]
Description=User Service Microservice
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/user_service
Environment="PATH=/opt/user_service/venv/bin"
ExecStart=/opt/user_service/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable user-service.service
    
    print_success "Systemd сервис создан"
}

# Настройка Nginx
setup_nginx() {
    print_step "Настройка Nginx как reverse proxy"
    
    read -p "Введите доменное имя (или оставьте пустым для IP): " DOMAIN_NAME
    
    if [ -z "$DOMAIN_NAME" ]; then
        DOMAIN_NAME=$IP_ADDR
        USE_SSL=false
    else
        USE_SSL=true
    fi
    
    # Создание конфигурации Nginx
    sudo cat > /etc/nginx/sites-available/user-service << EOF
# HTTP блок (перенаправление на HTTPS если есть SSL)
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME};
    
    # Перенаправление на HTTPS если есть домен
    $( [ "$USE_SSL" = true ] && echo "return 301 https://\$server_name\$request_uri;" )
    
    # Если без SSL - проксирование на HTTP
    $( [ "$USE_SSL" = false ] && cat << 'HTTP_CONFIG'
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Статика
    location /static/ {
        alias /opt/user_service/static/;
    }
HTTP_CONFIG
)
}
EOF

    # Добавление HTTPS конфигурации если есть домен
    if [ "$USE_SSL" = true ]; then
        sudo cat >> /etc/nginx/sites-available/user-service << 'HTTPS_CONFIG'

# HTTPS блок
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN_NAME};
    
    # SSL сертификаты (будут получены через certbot)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN_NAME}/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Проксирование на приложение
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Безопасность
        proxy_hide_header X-Powered-By;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }
    
    # Статика
    location /static/ {
        alias /opt/user_service/static/;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
HTTPS_CONFIG
    fi
    
    # Активация конфигурации
    sudo ln -sf /etc/nginx/sites-available/user-service /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Проверка конфигурации Nginx
    sudo nginx -t
    
    print_success "Nginx конфигурация создана"
    
    # Получение SSL сертификата
    if [ "$USE_SSL" = true ]; then
        print_step "Получение SSL сертификата"
        read -p "Введите email для CertBot: " CERT_EMAIL
        
        sudo certbot --nginx -d $DOMAIN_NAME --non-interactive --agree-tos -m $CERT_EMAIL
        print_success "SSL сертификат получен"
    fi
    
    # Перезапуск Nginx
    sudo systemctl restart nginx
    print_success "Nginx перезапущен"
}

# Настройка firewall
setup_firewall() {
    print_step "Настройка firewall"
    
    if command -v ufw &> /dev/null; then
        sudo ufw allow 22/tcp
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw --force enable
        print_success "Firewall настроен (порты: 22,80,443)"
    else
        print_info "UFW не установлен, пропускаем"
    fi
}

# Создание скриптов управления
create_management_scripts() {
    print_step "Создание скриптов управления"
    
    cd /opt/user_service
    
    # Скрипт запуска
    sudo cat > start.sh << 'EOF'
#!/bin/bash
sudo systemctl start user-service
sudo systemctl start nginx
echo "✅ Сервис запущен"
EOF
    
    # Скрипт остановки
    sudo cat > stop.sh << 'EOF'
#!/bin/bash
sudo systemctl stop user-service
echo "✅ Сервис остановлен"
EOF
    
    # Скрипт перезапуска
    sudo cat > restart.sh << 'EOF'
#!/bin/bash
sudo systemctl restart user-service
sudo systemctl restart nginx
echo "✅ Сервис перезапущен"
EOF
    
    # Скрипт статуса
    sudo cat > status.sh << 'EOF'
#!/bin/bash
echo "=== Статус сервиса ==="
sudo systemctl status user-service --no-pager
echo ""
echo "=== Последние логи ==="
sudo journalctl -u user-service -n 20 --no-pager
EOF
    
    # Скрипт логов
    sudo cat > logs.sh << 'EOF'
#!/bin/bash
sudo journalctl -u user-service -f
EOF
    
    sudo chmod +x *.sh
    sudo chown $USER:$USER *.sh
    
    print_success "Скрипты управления созданы"
}

# Создание скрипта резервного копирования
create_backup_script() {
    print_step "Создание скрипта резервного копирования"
    
    sudo cat > /opt/user_service/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/user_service"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Резервная копия базы данных
sudo -u postgres pg_dump usersdb > $BACKUP_DIR/db_$DATE.sql

# Резервная копия .env
cp /opt/user_service/.env $BACKUP_DIR/env_$DATE.bak

# Резервная копия кода
tar -czf $BACKUP_DIR/code_$DATE.tar.gz /opt/user_service/app

# Удаление старых копий (старше 7 дней)
find $BACKUP_DIR -type f -mtime +7 -delete

echo "✅ Резервная копия создана: $BACKUP_DIR/db_$DATE.sql"
EOF
    
    sudo chmod +x /opt/user_service/backup.sh
    
    # Добавление в cron (ежедневно в 2:00)
    (sudo crontab -l 2>/dev/null; echo "0 2 * * * /opt/user_service/backup.sh") | sudo crontab -
    
    print_success "Скрипт бэкапа создан и добавлен в cron"
}

# Мониторинг
setup_monitoring() {
    print_step "Настройка мониторинга"
    
    # Скрипт мониторинга
    sudo cat > /opt/user_service/monitor.sh << 'EOF'
#!/bin/bash

# Проверка статуса сервиса
if systemctl is-active --quiet user-service; then
    echo "✅ Сервис работает"
else
    echo "❌ Сервис не работает"
    sudo systemctl restart user-service
fi

# Проверка Nginx
if systemctl is-active --quiet nginx; then
    echo "✅ Nginx работает"
else
    echo "❌ Nginx не работает"
    sudo systemctl restart nginx
fi

# Проверка PostgreSQL
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL работает"
else
    echo "❌ PostgreSQL не работает"
    sudo systemctl restart postgresql
fi

# Проверка дискового пространства
USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $USAGE -gt 80 ]; then
    echo "⚠️  Диск заполнен на $USAGE%"
fi
EOF
    
    sudo chmod +x /opt/user_service/monitor.sh
    
    # Добавление в cron (каждые 5 минут)
    (sudo crontab -l 2>/dev/null; echo "*/5 * * * * /opt/user_service/monitor.sh >> /var/log/user_service_monitor.log") | sudo crontab -
    
    print_success "Мониторинг настроен"
}

# Запуск сервиса
start_service() {
    print_step "Запуск сервиса"
    
    sudo systemctl start user-service
    sudo systemctl enable user-service
    
    sleep 3
    
    if sudo systemctl is-active --quiet user-service; then
        print_success "Сервис успешно запущен"
    else
        print_error "Ошибка запуска сервиса"
        sudo journalctl -u user-service -n 20 --no-pager
        exit 1
    fi
}

# Финальная информация
print_summary() {
    print_step "Установка завершена!"
    
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Микросервис успешно установлен и запущен!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    echo -e "${CYAN}📌 Доступ к сервису:${NC}"
    if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "$IP_ADDR" ]; then
        echo -e "   • https://$DOMAIN_NAME"
        echo -e "   • Документация API: https://$DOMAIN_NAME/docs"
        echo -e "   • Health check: https://$DOMAIN_NAME/health"
    fi
    echo -e "   • http://$IP_ADDR"
    echo -e "   • Документация API: http://$IP_ADDR/docs"
    echo -e "   • Health check: http://$IP_ADDR/health"
    
    echo -e "\n${CYAN}📌 Управление сервисом:${NC}"
    echo -e "   • Запуск:     sudo systemctl start user-service"
    echo -e "   • Остановка:  sudo systemctl stop user-service"
    echo -e "   • Перезапуск: sudo systemctl restart user-service"
    echo -e "   • Статус:     sudo systemctl status user-service"
    echo -e "   • Логи:       sudo journalctl -u user-service -f"
    
    echo -e "\n${CYAN}📌 Скрипты управления (/opt/user_service/):${NC}"
    echo -e "   • ./start.sh    - запуск"
    echo -e "   • ./stop.sh     - остановка"
    echo -e "   • ./restart.sh  - перезапуск"
    echo -e "   • ./status.sh   - статус"
    echo -e "   • ./logs.sh     - просмотр логов"
    echo -e "   • ./backup.sh   - резервное копирование"
    echo -e "   • ./monitor.sh  - мониторинг"
    
    echo -e "\n${CYAN}📌 Важные пароли:${NC}"
    echo -e "   • PostgreSQL: $PG_PASSWORD"
    echo -e "   • Admin panel: admin / admin123"
    
    echo -e "\n${CYAN}📌 Файлы конфигурации:${NC}"
    echo -e "   • Конфиг:      /opt/user_service/.env"
    echo -e "   • Nginx:       /etc/nginx/sites-available/user-service"
    echo -e "   • Systemd:     /etc/systemd/system/user-service.service"
    
    echo -e "\n${YELLOW}⚠️  Важно:${NC}"
    echo -e "   • Смените пароль администратора в .env"
    echo -e "   • Регулярно делайте бэкапы: ./backup.sh"
    echo -e "   • Мониторинг выполняется каждые 5 минут"
    
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Главная функция
main() {
    clear
    echo -e "${GREEN}"
    cat << "EOF"
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     User Service Microservice Setup for Raspberry Pi     ║
    ║              with PostgreSQL and Nginx                   ║
    ║                                                          ║
    ║           Установка микросервиса на Raspberry Pi         ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    check_rpi
    update_system
    install_system_deps
    setup_postgresql
    setup_venv
    install_python_deps
    setup_config
    create_systemd_service
    setup_nginx
    setup_firewall
    create_management_scripts
    create_backup_script
    setup_monitoring
    start_service
    print_summary
}

# Запуск
main "$@"
