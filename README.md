CROWN CLASH LAN - 2 PLAYER

HOST: A Windows PC on the same Wi-Fi as both Chromebooks.
Requires Python 3.10+ and the websockets Python package.
On the Windows host, install once: py -m pip install websockets
Then run: py server.py
Find the Windows PC's local IPv4 address with: ipconfig
Both players open http://HOST_IP:8765 in Chrome.
Example: http://192.168.1.20:8765 (replace with actual address).
No installs required on Chromebooks, but they must be allowed to access the host URL.
The host PC must remain on. Windows Firewall may ask to allow Python on private networks.
School networks may isolate devices or block local connections; use only permitted network access.
This is a prototype with one room and two players. Restart server to reset the match.
