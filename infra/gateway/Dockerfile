FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY includes /etc/nginx/conf.d

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=6 \
  CMD wget -q -O - http://127.0.0.1:80/health >/dev/null || exit 1