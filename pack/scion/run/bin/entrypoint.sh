#!/bin/bash

echo "=== PREPARE SCION APP ==="
source ~/.bash_profile

# Make a pyon.local.yml config file with defaults from ENV

cd $APP_DIR

sed "s/%SYSNAME%/${SYSNAME:-scion}/g;\
s/%AMQP_HOST%/${AMQP_HOST:-rabbitmq}/g;\
s/%AMQP_PORT%/${AMQP_PORT:-5672}/g;\
s/%AMQP_USER%/${AMQP_USER:-guest}/g;\
s/%AMQP_PASSWORD%/${AMQP_PASSWORD:-guest}/g;\
s/%AMQP_MPORT%/${AMQP_MPORT:-15672}/g;\
s/%AMQP_MUSER%/${AMQP_MUSER:-guest}/g;\
s/%AMQP_MPASSWORD%/${AMQP_MPASSWORD:-guest}/g;\
s/%PG_HOST%/${PG_HOST:-postgres}/g;\
s/%PG_PORT%/${PG_PORT:-5432}/g;\
s/%PG_USER%/${PG_USER:-ion}/g;\
s/%PG_PASSWORD%/${PG_PASSWORD:-$POSTGRES_ION_PASSWORD}/g;\
s/%PG_ADMIN_USER%/${PG_ADMIN_USER:-postgres}/g;\
s/%PG_ADMIN_PASSWORD%/${PG_ADMIN_PASSWORD:-$POSTGRES_PASSWORD}/g;\
s/%DEPLOY_REGION%/${DEPLOY_REGION:-default}/g;\
s/%DEPLOY_AZ%/${DEPLOY_AZ:-default}/g;\
s/%SERVICE_GWY_PORT%/${SERVICE_GWY_PORT:-4000}/g;\
s/%WEB_UI_URL%/${WEB_UI_URL:-localhost}/g;\
s/%ADMIN_UI_PORT%/${ADMIN_UI_PORT:-8080}/g" \
defs/res/config/templates/pyon-docker.local.yml > res/config/pyon.local.yml
