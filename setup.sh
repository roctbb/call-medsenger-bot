sudo pip3 install -r requirements.txt
sudo cp agents_call.conf /etc/supervisor/conf.d/
sudo cp agents_call_nginx.conf /etc/nginx/sites-enabled/
sudo supervisorctl update
sudo systemctl restart nginx
sudo certbot --nginx -d call.ai.medsenger.ru
touch config.py
