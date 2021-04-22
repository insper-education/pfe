source ~/pfe/env/bin/activate
#sudo systemctl start postgresql.service
#sudo systemctl enable postgresql.service
touch pfe.log
sudo chown ubuntu.ubuntu pfe.log
sudo chmod a+w pfe.log
celery -A pfe worker -l info &
celery -A pfe beat -l info &
sudo python3 manage.py makemigrations
sudo python3 manage.py migrate
sudo python3 manage.py collectstatic --no-input
#sudo python3 manage.py runserver 0.0.0.0:80 &
sudo systemctl start apache2
#tail -f /var/log/apache2/error.log
#tail -f /var/log/apache2/access.log
