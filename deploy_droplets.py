import urllib.request
import urllib.error
import json
import os
import time
import sys
import getpass

# Default Configuration
DEFAULT_API_TOKEN = "" # Input your token here
DEFAULT_COUNT = 1
DEFAULT_REGION = "sgp1"
DEFAULT_SIZE = "s-2vcpu-2gb"
DEFAULT_IMAGE = "ubuntu-22-04-x64"
DEFAULT_PASSWORD = "Cuba@123Tot"

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

def input_default(prompt, default_value):
    value = input(f"{CYAN}{prompt} [{default_value}]: {RESET}")
    return value.strip() if value.strip() else str(default_value)

# ... (create_droplet and get_droplet_ip functions remain unchanged) ...

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

    region = input_default("Region", DEFAULT_REGION)
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
