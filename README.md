# mass-constitution

create: /etc/systemd/system/macon_api.service

```
[Unit]
Description=MA Constitution API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/app
ExecStart=sudo /app/venv/bin/python /app/mass-constitution/api.py
Restart=always

[Install]
WantedBy=multi-user.target
```

# install packages

/app/venv/bin/python -m pip install openai requests markdown2 markdown-it-py python-dotenv pymysql flask

# reload

sudo systemctl daemon-reload

sudo systemctl stop macon_api.service

sudo systemctl start macon_api.service

journalctl -u macon_api.service -b -e