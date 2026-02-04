# Changelog

All notable changes to DevBridge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-04

### Added

- **Core Terminal Features**
  - Multi-terminal session management
  - Full xterm.js terminal emulation with PTY support
  - Session persistence across page reloads
  - Automatic session restoration on server restart
  - Real-time output via WebSockets
  - Proper terminal resizing

- **AI CLI Integration**
  - Project browser with quick launch
  - Claude Code integration
  - Codex CLI integration
  - Google Gemini CLI integration
  - Smart shell detection (PowerShell/Bash)

- **Quick Actions**
  - Custom command shortcuts
  - Background execution with notifications
  - Configurable timeout (60 seconds)
  - Visual feedback with toast notifications

- **Responsive Design**
  - Desktop: Collapsible sidebar, multi-column layouts
  - Tablet: Optimized medium screen layouts
  - Mobile: Bottom navigation, swipe gestures, virtual keyboard
  - PWA support for native-like experience

- **User Management**
  - Multi-user authentication
  - Admin and regular user roles
  - Bootstrap admin on first run
  - Anonymous mode option
  - Session-based auth with HTTP-only cookies

- **Settings & Configuration**
  - Authentication toggle
  - Session limits
  - Scrollback buffer size
  - Shell configuration
  - AI CLI command customization

### Security

- Basic authentication system
- Session management
- Configurable access controls

### Technical

- FastAPI backend
- SQLite database
- WebSocket real-time communication
- Cross-platform PTY support (Windows/Unix)

---

## Roadmap

### [1.1.0] - Planned

- [ ] Terminal themes (Dracula, Solarized, Nord, etc.)
- [ ] File upload/download via terminal
- [ ] Session recording and playback
- [ ] Command history search

### [1.2.0] - Planned

- [ ] Collaborative sessions (multi-user terminals)
- [ ] SSH integration for remote servers
- [ ] Split terminal view
- [ ] Terminal tabs

### [2.0.0] - Future

- [ ] Kubernetes pod exec integration
- [ ] Docker container attachment
- [ ] Built-in AI chat sidebar
- [ ] Plugin system for extensions

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute to DevBridge.
