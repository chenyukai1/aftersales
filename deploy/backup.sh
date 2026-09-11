#!/usr/bin/env bash
# 售后平台数据库+附件每日备份脚本（容器内 bench 备份，保留 N 天自动清理）。
#
# 宿主机 crontab 示例（每天凌晨 1:30）：
#   30 1 * * * /opt/aftersales/deploy/backup.sh >> /var/log/aftersales-backup.log 2>&1
#
# 也支持 Windows 计划任务：见 docs/生产部署指南.md。
set -euo pipefail

cd "$(dirname "$0")"
source ./.env 2>/dev/null || source ./.env.example

SITE="${SITE:-aftersales.example.com}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
BACKUP_DIR_HOST="${BACKUP_DIR_HOST:-/opt/aftersales/backups}"   # 宿主机备份目录
PROJ="${COMPOSE_PROJECT_NAME:-aftersales}"

mkdir -p "${BACKUP_DIR_HOST}"

echo "[$(date '+%F %T')] 开始备份 ${SITE}"

# 1) bench 备份（含附件）——在 backend 容器内执行
docker compose --project-name "${PROJ}" -f "$(dirname "$0")/docker-compose.prod.yml" \
  exec -T backend bench --site "${SITE}" backup --with-files

# 2) 把容器内备份拷出到宿主机（sites 卷内 public/backups + private/backups）
docker cp "${PROJ}-backend-1:/home/frappe/frappe-bench/sites/${SITE}/private/backups/." \
  "${BACKUP_DIR_HOST}/private/" 2>/dev/null || mkdir -p "${BACKUP_DIR_HOST}/private"
docker cp "${PROJ}-backend-1:/home/frappe/frappe-bench/sites/${SITE}/public/backups/." \
  "${BACKUP_DIR_HOST}/public/" 2>/dev/null || mkdir -p "${BACKUP_DIR_HOST}/public"

# 3) 清理超过保留期的宿主机备份
find "${BACKUP_DIR_HOST}" -type f -mtime +"${RETENTION_DAYS}" -name "*.sql.gz" -delete
find "${BACKUP_DIR_HOST}" -type f -mtime +"${RETENTION_DAYS}" -name "*.tar" -delete
find "${BACKUP_DIR_HOST}" -type f -mtime +"${RETENTION_DAYS}" -name "*.json" -delete

echo "[$(date '+%F %T')] 备份完成，保留 ${RETENTION_DAYS} 天，目录：${BACKUP_DIR_HOST}"
