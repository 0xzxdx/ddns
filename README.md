# ddns

```bash
mkdir script
cd script/
wget https://raw.githubusercontent.com/anshengme/ddns/master/godaddy_for_python.py
crontab -e
*/5 * * * * /usr/bin/python3 /root/script/godaddy_for_python.py >> /var/log/godaddy_for_python.py.log
```
