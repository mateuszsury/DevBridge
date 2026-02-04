# Security Policy

## ⚠️ Important Security Notice

**DevBridge provides direct terminal access to your system. It should NEVER be exposed directly to the public internet without proper security measures.**

## Recommended Security Setup

### 1. VPN Access (Strongly Recommended)
```bash
# Use Tailscale for secure remote access
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up

# Access DevBridge only via Tailscale IP
# http://100.x.x.x:8000
```

### 2. Reverse Proxy with Authentication
Use Authelia, Authentik, or similar authentication proxy in front of DevBridge.

### 3. Firewall Rules
```bash
# Only allow access from VPN or specific IPs
ufw allow from 100.0.0.0/8 to any port 8000  # Tailscale
ufw deny 8000
```

### 4. SSL/TLS Encryption
Always use HTTPS in production with a reverse proxy like Nginx or Caddy.

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in DevBridge, please report it responsibly.

### How to Report

**DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email: **mateuszsury25@gmail.com**

**Subject:** [SECURITY] Brief description of the vulnerability

### What to Include

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact assessment
4. Suggested fix (if any)
5. Your contact information for follow-up

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Initial Assessment | Within 7 days |
| Fix Development | Depends on severity |
| Public Disclosure | After fix is released |

### What to Expect

1. We will acknowledge receipt of your report
2. We will investigate and validate the vulnerability
3. We will work on a fix
4. We will release a security patch
5. We will credit you in the release notes (unless you prefer anonymity)

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| **Critical** | Remote code execution, authentication bypass | 24-48 hours |
| **High** | Privilege escalation, data exposure | 3-5 days |
| **Medium** | Limited impact vulnerabilities | 1-2 weeks |
| **Low** | Minor issues, hardening suggestions | Next release |

---

## Security Best Practices for Users

### Authentication
- **Change default credentials immediately** after first run
- Use strong, unique passwords
- Consider enabling authentication even for local deployments

### Network Security
- Never expose DevBridge directly to the internet
- Use VPN (Tailscale, WireGuard) for remote access
- Use reverse proxy with SSL for HTTPS
- Implement IP whitelisting where possible

### Session Management
- Set reasonable idle timeouts for terminal sessions
- Limit maximum concurrent sessions
- Regularly review active sessions

### Updates
- Keep DevBridge updated to the latest version
- Monitor release notes for security patches
- Subscribe to GitHub releases for notifications

---

## Known Security Considerations

### Terminal Access
DevBridge provides full terminal access with the permissions of the user running the server. This means:
- Commands run with server user's privileges
- File system access matches server user's permissions
- Network access from the server's perspective

### WebSocket Connections
- WebSocket connections maintain persistent terminal sessions
- Ensure WebSocket traffic is encrypted (WSS) in production

### Session Storage
- Session data is stored in SQLite database
- Terminal scrollback is stored in memory and database
- Ensure proper file permissions on the data directory

---

## Contact

For security concerns: **mateuszsury25@gmail.com**

For general questions: Open a GitHub issue
