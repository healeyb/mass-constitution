# mass-constitution

sudo apt-get install python3-pymysql

sudo apt-get install python3-flask

sudo systemctl daemon-reload

sudo systemctl stop macon_api.service

sudo systemctl start macon_api.service

journalctl -u macon_api.service -b -e