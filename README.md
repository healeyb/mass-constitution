# mass-constitution

create: /etc/systemd/system/macon_api.service

pip3 install openai requests markdown2 markdown-it-py python-dotenv pymysql flask

# reload

sudo systemctl daemon-reload

sudo systemctl stop macon_api.service

sudo systemctl start macon_api.service

journalctl -u macon_api.service -b -e