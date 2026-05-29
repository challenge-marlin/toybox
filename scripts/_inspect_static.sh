#!/bin/bash
echo '=== toybox-caddy-1 mounts ==='
docker inspect toybox-caddy-1 --format '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}} (rw={{.RW}})
{{end}}'
echo
echo '=== toybox-web-1 static mount ==='
docker inspect toybox-web-1 --format '{{range .Mounts}}{{.Type}} {{.Name}} -> {{.Destination}}
{{end}}'
echo
echo '=== backend_static_volume contents (top) ==='
docker run --rm -v backend_static_volume:/d alpine sh -lc 'ls -la /d | head -20; echo "---count---"; find /d -type f | wc -l'
echo
echo '=== toybox_static_volume contents (top) ==='
docker run --rm -v toybox_static_volume:/d alpine sh -lc 'ls -la /d | head -20; echo "---count---"; find /d -type f | wc -l'
echo
echo '=== Caddyfile (volume / static references) ==='
grep -niE 'static|root|file_server|reverse_proxy|web|uploads' /var/www/toybox/Caddyfile 2>/dev/null || echo '(Caddyfile not found at /var/www/toybox/Caddyfile)'
echo
echo '=== docker-compose.yml caddy service volume refs ==='
grep -niE 'caddy|static|volume|:/' /var/www/toybox/backend/docker-compose.yml 2>/dev/null | head -60
