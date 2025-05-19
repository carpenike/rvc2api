
# Setup Dev Environment

## Colima Environment

1. Follow the install process for colima and start the VM.
2. Ensure the linux headers are installed so vcan shows up:

```bash
sudo apt install -y build-essential linux-headers-$(uname - r)  linux-modules-extra-$(uname -r)
```
3. Ensure the vcan interfaces are loaded at boot:

```bash
sudo tee /etc/modules-load.d/vcan.conf <<EOF
vcan
can_dev
EOF
```

4. Ensure the vcan interface starts at boot:

```bash
sudo tee /etc/systemd/system/vcan0.service <<'EOF'
[Unit]
Description=Create and bring up vcan0
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/sbin/ip link add dev vcan0 type vcan
ExecStart=/usr/sbin/ip link set up vcan0
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable vcan0.service
```
