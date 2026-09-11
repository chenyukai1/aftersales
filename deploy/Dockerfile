# 构建含售后平台应用的生产镜像。
# 用法（在 deploy/ 目录）：
#   docker build -t aftersales-prod:latest --build-arg BASE_IMAGE=frappe/erpnext:v15.68.0 \
#     --build-arg APP_REPO=https://github.com/<你的组织>/aftersales.git --build-arg APP_BRANCH=master .
# 注意：BASE_IMAGE 要与开发环境 Frappe 大版本一致（当前开发环境为 Frappe 16，需选对应 v16 tag）。
ARG BASE_IMAGE=frappe/erpnext:v16
FROM ${BASE_IMAGE}

ARG APP_REPO=https://github.com/example/aftersales.git
ARG APP_BRANCH=master

USER frappe
WORKDIR /home/frappe/frappe-bench
RUN bench get-app --branch ${APP_BRANCH} ${APP_REPO} \
    && bench build --app aftersales
USER root
