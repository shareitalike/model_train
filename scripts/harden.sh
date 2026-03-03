#!/bin/bash
# Security hardening script for production Ubuntu server
# Run once on a fresh EC2 instance: sudo bash harden.sh

set -euo pipefail

echo "═══ Kaithi OCR — Security Hardening ═══"

# SSH hardening
echo "Hardening SSH..."
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
echo "MaxAuthTries 3" >> /etc/ssh/sshd_config
systemctl reload sshd

# UFW firewall
echo "Configuring UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Fail2ban
echo "Installing Fail2ban..."
apt-get install -y fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = ssh
logpath = %(sshd_log)s
backend = %(syslog_backend)s
EOF
systemctl enable fail2ban
systemctl restart fail2ban

# Unattended security upgrades
echo "Enabling unattended upgrades..."
apt-get install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades

# Kernel hardening
echo "Applying sysctl hardening..."
cat >> /etc/sysctl.d/99-kaithi-hardening.conf << 'EOF'
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
kernel.randomize_va_space = 2
fs.suid_dumpable = 0
EOF
sysctl -p /etc/sysctl.d/99-kaithi-hardening.conf

echo ""
echo "═══════════════════════════════════"
echo "Security hardening complete ✓"
echo ""
echo "Next steps:"
echo "  1. Copy SSH public key: ssh-copy-id user@server"
echo "  2. Test SSH key auth before closing session"
echo "  3. Install certbot for SSL: apt install certbot"
echo "  4. Generate SSL cert: certbot certonly --standalone -d kaithi.gov.in"
