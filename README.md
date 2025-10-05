# EEOP-7340: SDN Network Lab

Hands-on optical network management using TransportPCE SDN controller and LightyNode simulators.

## Prerequisites
- Docker
- Python 3.x
- Jupyter Lab

## Installation and Setup

### 1. Install Jupyter Lab on Linux Server

SSH into your Linux server first, then:

```bash
# On the Linux server (not on your local PC)
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Jupyter Lab
pip install jupyterlab
```

### 2. Start Jupyter Lab on Linux Server

Still on the Linux server:

```bash
# Start Jupyter Lab without browser (for remote access)
jupyter lab --no-browser --port=8888 --ip=0.0.0.0
```

The command will output a URL with a token like:
```
http://127.0.0.1:8888/lab?token=your_token_here
```

### 3. Access from Your Local PC via SSH Tunnel

Open a new terminal on **your local PC** (Windows/Mac/Linux):

```bash
# On your local PC - create SSH tunnel to forward port 8888
ssh -L 8888:localhost:8888 username@your_linux_server_ip

# Keep this terminal open while using Jupyter Lab
```

### 4. Open in Your Local Browser

On **your local PC**, open your web browser and navigate to:
```
http://localhost:8888/lab?token=your_token_here
```

Use the token from step 2.

## Notebooks Overview

### 01_Docker_Basics_and_LightyNode_Setup.ipynb
Learn Docker container management and deploy optical network device simulators (ROADM and transponder) in isolated environments.

### 02_TransportPCE_SDN_Controller_Setup.ipynb
Deploy the TransportPCE SDN controller and explore RESTCONF APIs for network management.

### 03_Mounting_LightyNode_to_TransportPCE.ipynb
Connect simulated optical devices to the SDN controller using NETCONF protocol for centralized management.

### 04_Managing_Interfaces_via_TransportPCE.ipynb
Create and configure optical interfaces on network devices using OpenROADM data models and APIs.

### 05_Creating_Connections_Between_Nodes.ipynb
Build network topology by establishing links between devices and provision end-to-end optical services.

### 06_Cleanup_Environment.ipynb
Safely remove containers and networks to reset your learning environment.

## Usage Tips

1. **Run notebooks in order** - Each builds on the previous one
2. **Change STUDENT_ID** - Use your assigned ID for isolated environments
3. **Wait for services** - Some operations take 2-5 minutes to complete
4. **Check logs** - Use Docker logs if something doesn't work as expected

## Troubleshooting SSH Tunnel

If you can't connect:

1. **Check if Jupyter is running:**
   ```bash
   ps aux | grep jupyter
   ```

2. **Try a different port:**
   ```bash
   # On server
   jupyter lab --no-browser --port=8889

   # On local machine
   ssh -L 8889:localhost:8889 username@remote_server_ip
   ```

3. **Use specific bind address:**
   ```bash
   ssh -L 127.0.0.1:8888:127.0.0.1:8888 username@remote_server_ip
   ```

## Common Issues

- **Port already in use:** Kill existing Jupyter processes or use a different port
- **Token expired:** Restart Jupyter Lab to get a new token
- **Connection refused:** Check firewall settings and ensure Jupyter is running