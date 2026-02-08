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

def input_default(prompt, default_value):
    value = input(f"{CYAN}{prompt} [{default_value}]: {RESET}")
    return value.strip() if value.strip() else str(default_value)

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
    print(f"{CYAN}=== DigitalOcean Droplet Deployer ==={RESET}")
    print("Leaving a field empty uses the default value shown in brackets.\n")

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

    count_str = input_default("Number of droplets to create", DEFAULT_COUNT)
    try:
        count = int(count_str)
    except ValueError:
        print(f"{RED}Invalid number.{RESET}")
        sys.exit(1)

    # Region Selection Menu
    regions = {
        "1": "sgp1 (Singapore)",
        "2": "ams3 (Amsterdam)",
        "3": "fra1 (Frankfurt)",
        "4": "nyc1 (New York 1)",
        "5": "nyc3 (New York 3)",
        "6": "sfo3 (San Francisco)",
        "7": "blr1 (Bangalore)",
        "8": "lon1 (London)",
        "9": "tor1 (Toronto)",
        "10": "syd1 (Sydney)"
    }
    
    print(f"\n{CYAN}Select Region:{RESET}")
    for k, v in regions.items():
        print(f" {k}. {v}")
    
    region_choice = input(f"{CYAN}Enter choice [1 for sgp1]: {RESET}").strip()
    if not region_choice:
        region = "sgp1"
    elif region_choice in regions:
        region = regions[region_choice].split(" ")[0]
    else:
        region = region_choice # Allow manual slug entry if not in list

    size = input_default("Size", DEFAULT_SIZE)
    image = input_default("Image", DEFAULT_IMAGE)
    password = input_default("Root Password", DEFAULT_PASSWORD)

    print(f"\n{YELLOW}Summary:{RESET}")
    print(f"Creating {count} droplet(s)")
    print(f"Region: {region} | Size: {size}")
    print(f"OS: {image}")
    
    confirm = input(f"\n{CYAN}Proceed? [Y/n]: {RESET}")
    if confirm.lower() == 'n':
        sys.exit(0)

    results = []
    
    for i in range(count):
        name = f"worker-{int(time.time())}-{i+1}"
        droplet_id = create_droplet(token, name, region, size, image, password)
        if droplet_id:
            results.append({"name": name, "id": droplet_id})
    
    print(f"\n{YELLOW}Waiting for IP addresses (this takes a moment)...{RESET}")
    
    final_output = []
    for item in results:
        ip = get_droplet_ip(token, item['id'])
        if ip:
            print(f"{GREEN}✔ {item['name']} is READY! IP: {ip}{RESET}")
            final_output.append(f"{ip} | {item['name']}")
        else:
            print(f"{RED}⚠ {item['name']} timed out waiting for IP.{RESET}")

    # Save to file
    if final_output:
        with open("deployed_servers.txt", "a") as f:
            f.write("\n".join(final_output) + "\n")
        print(f"\n{GREEN}Saved IP list to 'deployed_servers.txt'{RESET}")
        
    print(f"\n{CYAN}Done!{RESET}")

if __name__ == "__main__":
    main()
