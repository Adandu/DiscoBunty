# Discord Ubuntu Manager - TODO List

Project: Create a Discord bot in a Docker container for managing Ubuntu servers via SSH and Discord Slash commands.

## Phase 1: Planning & Setup
- [x] Initial Architecture Brainstorming (Central Bot + SSH selected)
- [x] Create project directory
- [x] Create `TODO.md`
- [x] Initialize GitHub Repository: `discord-ubuntu-manager-bot-antigravity`
- [x] Create initial `requirements.txt`
- [x] Scaffold `main.py` with basic Discord Slash Command support
- [x] Create basic `Dockerfile`
- [x] Implement `ssh_manager.py` (Multi-server & Multi-auth support)

## Phase 2: Core Bot Development
- [x] Implement SSH client wrapper for remote command execution (`ssh_manager.py`)
- [x] Implement Autocomplete logic for server selection
- [x] Implement `/update` command
- [x] Implement `/process` search/display command
- [x] Implement `/service` search/control command
- [x] Implement `/logs` check command
- [x] Implement `/disk` space check command (Proof-of-concept)
- [x] Implement `/docker` command group for container management (ps, control, logs, details)
- [x] Implement Autocomplete for container names based on selected server

## Phase 3: Dockerization & Generic Configuration
- [x] Create `docker-compose.yml` for local testing
- [x] Create `.env.example` template for user configuration
- [x] Ensure all sensitive data is handled via Environment Variables (no hardcoding)

## Phase 4: CI/CD & GitHub Integration
- [ ] Setup GitHub Actions for building and pushing Docker images to GHCR
- [ ] Create `README.md` with detailed setup instructions for public use
- [ ] Push all initial files to GitHub repository

## Phase 5: Testing & Validation
- [ ] Test bot with a local Ubuntu VM
- [ ] Verify Slash Commands are working correctly in Discord
- [ ] Verify multi-server management works

---
*Last Updated: 2026-03-17*
