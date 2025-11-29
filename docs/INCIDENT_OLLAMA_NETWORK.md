# Incident Report: Ollama API Monitor Unreachable

**Date**: 2024-11-29
**Severity**: Medium
**Status**: Resolved
**Affected Service**: Uptime Kuma - Ollama API Monitor

---

## Summary

The Ollama API monitor in Uptime Kuma was reporting "offline" status despite the Ollama service running correctly on the VPS. The issue was caused by Docker network isolation preventing Uptime Kuma from reaching the Ollama container.

---

## Root Cause Analysis

### Problem Description
- Uptime Kuma container was deployed on the `auto-repare-network` (172.25.0.0/16)
- Ollama container was running on the default `bridge` network (172.17.0.0/16)
- The monitor was configured with URL `http://137.74.44.64:11434/api/tags` (public IP)
- Docker's iptables rules blocked inter-network traffic, preventing Uptime Kuma from accessing Ollama

### Network Topology (Before Fix)
```
┌─────────────────────────────────────────────────────────────┐
│                         VPS Host                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  auto-repare-network (172.25.0.0/16)                       │
│  ┌─────────────────┐                                       │
│  │  Uptime Kuma    │ ──── X ────┐                          │
│  │  172.25.0.2     │            │ BLOCKED                  │
│  └─────────────────┘            │                          │
│                                 ▼                          │
│  bridge network (172.17.0.0/16)                            │
│  ┌─────────────────┐                                       │
│  │  Ollama         │                                       │
│  │  172.17.0.3     │                                       │
│  └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Why Public IP Didn't Work
Even though Ollama was exposed on `0.0.0.0:11434`, Docker's internal routing and iptables `DROP` rules prevented containers on different networks from communicating via the host's public IP.

---

## Resolution

### Step 1: Connect Networks
Connected Uptime Kuma container to the `bridge` network where Ollama resides:

```bash
docker network connect bridge uptime-kuma
```

### Step 2: Update Monitor URL
Changed the monitor URL from public IP to container internal IP:

- **Before**: `http://137.74.44.64:11434/api/tags`
- **After**: `http://172.17.0.3:11434/api/tags`

Alternatively, if using container names with DNS:
- `http://ollama:11434/api/tags` (requires same network)

### Network Topology (After Fix)
```
┌─────────────────────────────────────────────────────────────┐
│                         VPS Host                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  auto-repare-network (172.25.0.0/16)                       │
│  ┌─────────────────┐                                       │
│  │  Uptime Kuma    │                                       │
│  │  172.25.0.2     │                                       │
│  └────────┬────────┘                                       │
│           │                                                │
│  bridge network (172.17.0.0/16)                            │
│  ┌────────┴────────┐     ┌─────────────────┐               │
│  │  Uptime Kuma    │ ──► │  Ollama         │  ✓ CONNECTED  │
│  │  (2nd interface)│     │  172.17.0.3     │               │
│  └─────────────────┘     └─────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Prevention Measures

### 1. Docker Compose Configuration
When deploying services that need to communicate, ensure they share a network:

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    networks:
      - monitoring
      - bridge  # Connect to Ollama's network

  ollama:
    image: ollama/ollama
    networks:
      - bridge

networks:
  monitoring:
  bridge:
    external: true
```

### 2. Use Container Names Instead of IPs
Container IPs can change after restart. Use Docker DNS:
- `http://ollama:11434` instead of `http://172.17.0.3:11434`

### 3. Dedicated Monitoring Network
Create a shared network for all monitored services:

```bash
docker network create monitoring-net
docker network connect monitoring-net uptime-kuma
docker network connect monitoring-net ollama
docker network connect monitoring-net n8n-main-prod
```

---

## Verification Commands

```bash
# Check container networks
docker inspect uptime-kuma --format '{{range .NetworkSettings.Networks}}{{.NetworkID}}: {{.IPAddress}}{{"\n"}}{{end}}'

# Test connectivity from Uptime Kuma
docker exec uptime-kuma curl -s http://ollama:11434/api/tags

# List all networks
docker network ls

# Inspect network members
docker network inspect bridge --format '{{range .Containers}}{{.Name}}: {{.IPv4Address}}{{"\n"}}{{end}}'
```

---

## Lessons Learned

1. **Docker network isolation is strict by default** - Containers on different networks cannot communicate, even via host's public IP
2. **Always verify network topology** when monitoring containerized services
3. **Use Docker DNS** instead of hardcoded IPs for inter-container communication
4. **Document network requirements** for each service in docker-compose files

---

## Related Files

- `/opt/auto-repare/docker-compose.yml` - Uptime Kuma deployment
- `/config/monitors.json` - Monitor configurations
- Uptime Kuma Dashboard: http://137.74.44.64:3001

---

*Incident resolved by connecting Uptime Kuma to the bridge network and updating the monitor URL to use Ollama's internal IP.*
