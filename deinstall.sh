sudo rm /etc/supervisor/conf.d/agents_call.conf
sudo rm /etc/nginx/sites-enabled/agents_call_nginx.conf
sudo supervisorctl update
sudo systemctl restart nginx
