import urllib.request
import urllib.error
import json
import os
import time
import sys
import getpass

# Default Configuration
DEFAULT_API_TOKEN = "" # Input your token here
DEFAULT_SIZE = "s-2vcpu-2gb"
DEFAULT_IMAGE = "ubuntu-22-04-x64"
DEFAULT_PASSWORD = "Cuba@123Tot"

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# Target Regions (Total 10 unique regions for 10 droplets)
# We pick 10 most reliable regions from the 13 available
TARGET_REGIONS = [
    "sgp1", # Singapore
    "ams3", # Amsterdam
    "fra1", # Frankfurt
    "nyc1", # New York 1
    "nyc3", # New York 3
    "sfo3", # San Francisco
    "blr1", # Bangalore
    "lon1", # London
    "tor1", # Toronto
    "syd1"  # Sydney
]

def create_droplet(token, name, region, size, image, password):
    # Cloud-init script to set password and enable SSH password auth
    user_data = f"""#!/bin/bash
# Enable password authentication in SSH
sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Set root password
echo "root:{password}" | chpasswd
"""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": name,
        "region": region,
        "size": size,
        "image": image,
        "user_data": user_data,
        "tags": ["antigravity-deployed"]
    }

    p_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        "https://api.digitalocean.com/v2/droplets",
        data=p_bytes,
        headers=headers,
        method="POST"
    )

    print(f"{YELLOW}Creating droplet '{name}' in {region}...{RESET}")
    
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 202:
                data = json.load(resp)
                droplet_id = data['droplet']['id']
                print(f"{GREEN}✅ Initiated! ID: {droplet_id}{RESET}")
                return droplet_id
            else:
                print(f"{RED}❌ Failed. Status: {resp.status}{RESET}")
                print(resp.read().decode())
                return None
    except urllib.error.HTTPError as e:
        print(f"{RED}❌ HTTP Error: {e}{RESET}")
        print(e.read().decode())
        return None
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return None

def get_droplet_ip(token, droplet_id):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(30): # Wait up to 150 seconds
        time.sleep(5)
        try:
            req = urllib.request.Request(
                f"https://api.digitalocean.com/v2/droplets/{droplet_id}",
                headers=headers
            )
            with urllib.request.urlopen(req) as resp:
                info = json.load(resp)
                networks = info.get('droplet', {}).get('networks', {}).get('v4', [])
                for net in networks:
                    if net['type'] == 'public':
                        return net['ip_address']
        except:
            pass
    return None

def main():
    print(f"{CYAN}=== DigitalOcean Multi-Region Deployer (10 Droplets) ==={RESET}")
    print("This script will automatically deploy 10 droplets across 10 regions.")
    print(f"Regions: {YELLOW}{', '.join(TARGET_REGIONS)}{RESET}\n")

    # Get inputs
    token = os.getenv("DIGITALOCEAN_TOKEN") or DEFAULT_API_TOKEN
    if not token:
        token = getpass.getpass(f"{CYAN}Enter DigitalOcean API Token: {RESET}")
    else:
        # Mask the token for display
        masked_token = token[:5] + "..." + token[-5:] if len(token) > 10 else "***"
        print(f"{GREEN}Using API Token: {masked_token}{RESET}")
    
    if not token:
        print(f"{RED}Token required!{RESET}")
        sys.exit(1)

    print(f"\n{CYAN}Configuration (Fixed):{RESET}")
    print(f"Count: 10 droplets")
    print(f"Size: {DEFAULT_SIZE}")
    print(f"Image: {DEFAULT_IMAGE}")
    print(f"Password: {DEFAULT_PASSWORD}")

    confirm = input(f"\n{CYAN}Proceed with deployment? [Y/n]: {RESET}")
    if confirm.lower() == 'n':
        print("Cancelled.")
        sys.exit(0)

    results = []
    
    for i, region in enumerate(TARGET_REGIONS):
        name = f"worker-{int(time.time())}-{region}"
        # Small delay to prevent issues
        if i > 0: time.sleep(1) 
        
        droplet_id = create_droplet(token, name, region, DEFAULT_SIZE, DEFAULT_IMAGE, DEFAULT_PASSWORD)
        if droplet_id:
            results.append({"name": name, "id": droplet_id, "region": region})
    
    print(f"\n{YELLOW}Waiting for IP addresses...{RESET}")
    
    final_output = []
    for item in results:
        ip = get_droplet_ip(token, item['id'])
        if ip:
            print(f"{GREEN}✔ {item['name']} ({item['region']}) is READY! IP: {ip}{RESET}")
            final_output.append(f"{ip} | {item['name']} | {item['region']}")
        else:
            print(f"{RED}⚠ {item['name']} ({item['region']}) timed out waiting for IP.{RESET}")

    # Save to file
    if final_output:
        with open("deployed_servers.txt", "a") as f:
            f.write("\n".join(final_output) + "\n")
        print(f"\n{GREEN}Saved IP list to 'deployed_servers.txt'{RESET}")
        
    print(f"\n{CYAN}Done!{RESET}")

if __name__ == "__main__":
    main()
