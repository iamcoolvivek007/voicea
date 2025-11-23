# Deployment Guide (Coolify)

This guide explains how to deploy the Voice Assistant to a VPS using Coolify.

## Prerequisites

1.  **VPS** with Coolify installed.
2.  **Domain Name** pointed to your VPS IP.
3.  **Firewall** configured to allow required ports (see below).

## Step 1: Firewall Configuration

Before deploying, ensure the following ports are open on your VPS firewall (e.g., UFW, AWS Security Group):

*   **TCP 7880**: LiveKit Signaling (Coolify might proxy this, but for internal comms or direct access it's good to know).
*   **TCP 7881**: LiveKit WebRTC (TCP).
*   **UDP 7882**: LiveKit WebRTC (UDP).
*   **UDP 50000-50200**: LiveKit Media (RTP).

## Step 2: Configure Coolify

1.  **Create a New Service**:
    *   Go to your Project in Coolify.
    *   Select **Docker Compose**.
    *   Source: **Git Repository**.
    *   Repository URL: `<your-repo-url>`
    *   Branch: `main` (or your branch name).
    *   Docker Compose File: `docker-compose.yml` (Default).

2.  **Environment Variables**:
    You must set the following variables in Coolify for the service:

    | Variable | Description | Example |
    | :--- | :--- | :--- |
    | `LIVEKIT_KEYS` | API Key and Secret pair for LiveKit Server. | `devkey: secret` |
    | `LIVEKIT_API_KEY` | The API Key for the Agent/Frontend to use. | `devkey` |
    | `LIVEKIT_API_SECRET` | The Secret for the Agent/Frontend to use. | `secret` |
    | `GOOGLE_API_KEY` | Google Gemini API Key. | `AIzaSy...` |
    | `NEXT_PUBLIC_LIVEKIT_URL` | **Public** URL of your LiveKit server (wss). | `wss://livekit.yourdomain.com` |
    | `NEXT_PUBLIC_LIVEKIT_API_KEY`| Same as `LIVEKIT_API_KEY` (for frontend). | `devkey` |

    *   **Build Variables**: Ensure `NEXT_PUBLIC_LIVEKIT_URL` is available during the **Build** phase (Coolify allows setting Build Args/Envs). This is required for the Next.js frontend to know where to connect.

3.  **Domains**:
    *   **Frontend**: Configure a domain (e.g., `app.yourdomain.com`) pointing to port `3000`.
    *   **LiveKit**: Configure a domain (e.g., `livekit.yourdomain.com`) pointing to port `7880`. Ensure HTTPS is enabled.

## Step 3: Deploy

Click **Deploy** in Coolify.

## Troubleshooting

*   **Connection Issues (ICE Failures)**:
    *   If you see connection errors in the browser console related to ICE or WebRTC, it likely means the UDP ports (`7882`, `50000-50200`) are blocked.
    *   Ensure your VPS provider allows UDP traffic on these ports.
    *   If your server has a private IP behind 1:1 NAT (like AWS EC2), LiveKit usually detects the public IP. If not, you may need to set `rtc.external_ips` in `livekit.yaml` manually or via an environment variable override if supported.

*   **Frontend cannot connect**:
    *   Check `NEXT_PUBLIC_LIVEKIT_URL`. It must be `wss://livekit.yourdomain.com` (Secure WebSocket) if your site is HTTPS.
