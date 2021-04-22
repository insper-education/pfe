sudo kill -9 $(pgrep -f celery)
sudo kill -9 $(pgrep -f manage.py)
sudo systemctl stop apache2
#sudo systemctl stop postgresql.service