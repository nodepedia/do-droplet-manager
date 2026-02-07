import urllib.request
import urllib.error
import json
import os
import time
import sys

# Configuration
API_TOKEN = os.getenv("DIGITALOCEAN_TOKEN")
REGION = "sgp1"
SIZE = "s-2vcpu-2gb"
IMAGE = "ubuntu-22-04-x64"
ROOT_PASSWORD = "Cuba@123Tot"

# Cloud-init script to set password and enable SSH password auth
USER_DATA = f"""#!/bin/bash
# Enable password authentication in SSH
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Set root password
echo "root:{ROOT_PASSWORD}" | chpasswd
"""

def create_droplet():
    if not API_TOKEN:
        print("Error: DIGITALOCEAN_TOKEN environment variable is not set.")
        print("Usage: export DIGITALOCEAN_TOKEN=your_token_here && python3 create_droplet.py")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Generate a name based on timestamp to avoid collisions
    droplet_name = f"sg-worker-{int(time.time())}"

    payload = {
        "name": droplet_name,
        "region": REGION,
        "size": SIZE,
        "image": IMAGE,
        "user_data": USER_DATA,
        "tags": ["antigravity-created"]
    }

    p_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        "https://api.digitalocean.com/v2/droplets",
        data=p_bytes,
        headers=headers,
        method="POST"
    )

    print(f"Creating droplet '{droplet_name}' in {REGION}...")
    print(f"Spec: {SIZE}, Image: {IMAGE}")
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 202:
                data = json.load(resp)
                droplet_id = data['droplet']['id']
                print(f"✅ Droplet creation initiated! ID: {droplet_id}")
                print("Waiting for IP address assignment...")
                
                # Wait for IP
                for _ in range(20):
                    time.sleep(5)
                    req_get = urllib.request.Request(
                        f"https://api.digitalocean.com/v2/droplets/{droplet_id}",
                        headers=headers
                    )
                    with urllib.request.urlopen(req_get) as resp_get:
                        droplet_info = json.load(resp_get)
                        networks = droplet_info.get('droplet', {}).get('networks', {}).get('v4', [])
                        if networks:
                            for net in networks:
                                if net['type'] == 'public':
                                    print(f"\n🎉 Droplet Ready!")
                                    print(f"IP Address: {net['ip_address']}")
                                    print(f"Login: ssh root@{net['ip_address']}")
                                    print(f"Password: {ROOT_PASSWORD}")
                                    return
                print("\n⚠️ Droplet created but timed out waiting for IP. Please check dashboard.")
            else:
                print(f"❌ Failed to create droplet. Status: {resp.status}")
                print(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to create droplet: {e}")
        print(e.read().decode())
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    create_droplet()
