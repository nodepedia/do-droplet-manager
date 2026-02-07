# DigitalOcean Droplet Manager

A set of Python scripts to easily create and manage DigitalOcean droplets via the API.

## Features

- **Interactive Deployment**: Use `deploy_droplets.py` to interactively create multiple droplets with custom or default configurations.
- **Easy Configuration**: Default settings for Singapore region, 2vCPU/2GB RAM, and Ubuntu 22.04.
- **Auto-Password Setup**: Automatically sets a root password and enables SSH password authentication via cloud-init.

## How to use

1. Clone this repository or copy the scripts to your server.
2. (Optional) Set your DigitalOcean API token as an environment variable:
   ```bash
   export DIGITALOCEAN_TOKEN=your_token_here
   ```
3. Run the interactive deployment script:
   ```bash
   python3 deploy_droplets.py
   ```

## Script

- `deploy_droplets.py`: The main interactive script for multi-droplet deployment.

---
Created by Antigravity AI.
