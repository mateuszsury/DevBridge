# Contributing to DevBridge 🌉

Thank you for your interest in contributing to DevBridge! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)
- [Architecture Overview](#architecture-overview)

---

## 📜 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

---

## 🚀 Getting Started

### Prerequisites

- Python 3.13 or higher
- Git
- Code editor (VS Code, PyCharm, etc.)
- Basic knowledge of:
  - Python (FastAPI, asyncio)
  - JavaScript (ES6+, WebSockets)
  - HTML/CSS
  - Terminal/PTY concepts

### Development Setup

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/devbridge.git
   cd devbridge
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv

   # Activate
   # Windows
   .venv\Scripts\activate
   # Unix/Linux/macOS
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt

   # Install development dependencies
   pip install pytest pytest-asyncio black flake8 mypy
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Run in development mode**
   ```bash
   uvicorn webterm.main:app --reload --host 127.0.0.1 --port 8000
   ```

6. **Access the application**
   ```
   http://localhost:8000
   Default credentials: admin / admin
   ```

---

## 🛠️ Making Changes

### Branch Naming

Use descriptive branch names:

```
feature/add-terminal-themes
fix/websocket-reconnection
docs/update-installation-guide
refactor/terminal-manager-cleanup
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add terminal theme support
fix: resolve WebSocket reconnection issue
docs: update installation instructions
refactor: simplify terminal manager code
chore: update dependencies
test: add tests for Quick Actions
style: format code with Black
```

**Examples:**
```bash
git commit -m "feat: add dark/light theme toggle"
git commit -m "fix: terminal not resizing on mobile Safari"
git commit -m "docs: add Tailscale setup instructions"
```

---

## 🧪 Testing

### Manual Testing Checklist

Before submitting a PR, test on:

**Desktop:**
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (if on macOS)
- [ ] Multiple terminal sessions
- [ ] WebSocket reconnection
- [ ] Quick Actions execution

**Mobile:**
- [ ] iOS Safari
- [ ] Android Chrome
- [ ] Swipe gestures
- [ ] Virtual keyboard
- [ ] Bottom navigation
- [ ] PWA installation

**Features:**
- [ ] Create/delete terminals
- [ ] Terminal input/output
- [ ] Session persistence
- [ ] Quick Actions
- [ ] Projects browser
- [ ] User authentication
- [ ] Settings changes

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_terminal.py

# Run with coverage
pytest --cov=webterm
```

### Code Quality

```bash
# Format code
black webterm/

# Lint code
flake8 webterm/

# Type checking
mypy webterm/
```

---

## 📤 Submitting Changes

### Pull Request Process

1. **Update your fork**
   ```bash
   git remote add upstream https://github.com/original/devbridge.git
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, readable code
   - Add comments for complex logic
   - Update documentation if needed
   - Add tests for new features

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Go to GitHub and click "New Pull Request"
   - Fill in the PR template
   - Link related issues
   - Request review

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested on desktop
- [ ] Tested on mobile
- [ ] Added/updated tests

## Screenshots (if UI changes)
[Add screenshots here]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

---

## 🎨 Style Guidelines

### Python

Follow [PEP 8](https://pep8.org/):

```python
# Good
async def create_terminal_session(
    cwd: str | None,
    shell: str | None,
    cols: int = 120,
    rows: int = 30
) -> dict:
    """Create a new terminal session.

    Args:
        cwd: Working directory (optional)
        shell: Shell command (optional)
        cols: Terminal columns
        rows: Terminal rows

    Returns:
        dict: Session info with id
    """
    # Implementation...
    pass

# Bad
def createTerminalSession(cwd,shell,cols=120,rows=30):
    # Missing types, docstring, not snake_case
    pass
```

### JavaScript

Use ES6+ features:

```javascript
// Good
async function executeQuickAction(actionId) {
  const action = state.quickActions.find(a => a.id === actionId);
  if (!action) return;

  try {
    const result = await api('/api/quick-action/execute', {
      method: 'POST',
      body: JSON.stringify({ command: action.command })
    });

    showToast('success', 'Completed', result.message);
  } catch (err) {
    showToast('error', 'Failed', err.message);
  }
}

// Bad
function executeQuickAction(actionId) {
  var action;
  for (var i = 0; i < state.quickActions.length; i++) {
    if (state.quickActions[i].id === actionId) {
      action = state.quickActions[i];
      break;
    }
  }
  // Old-style, harder to read
}
```

### CSS

Use BEM-like naming:

```css
/* Good */
.quick-action-card {
  background: var(--color-bg-secondary);
}

.quick-action-card__icon {
  font-size: 32px;
}

.quick-action-card--running {
  opacity: 0.7;
}

/* Bad */
.quickActionCard { }
.icon { }  /* Too generic */
#qa-card-1 { }  /* Avoid IDs in CSS */
```

### HTML

Use semantic HTML:

```html
<!-- Good -->
<nav class="sidebar-nav">
  <button class="nav-item" data-view="terminals">
    <svg>...</svg>
    <span>Terminals</span>
  </button>
</nav>

<!-- Bad -->
<div class="sidebar-nav">
  <div onclick="switchView('terminals')">
    <img src="icon.png">
    <div>Terminals</div>
  </div>
</div>
```

---

## 🏗️ Architecture Overview

### Backend Structure

```
webterm/
├── main.py              # FastAPI app, routes
├── terminal_manager.py  # Terminal session management
├── pty_windows.py       # Windows PTY implementation
├── pty_unix.py          # Unix/Linux PTY implementation
├── db.py                # SQLite database operations
├── security.py          # Authentication, authorization
└── settings.py          # Configuration
```

### Frontend Structure

```
static/
├── app.js       # Main application logic
├── styles.css   # UI styles
├── xterm.js     # Terminal emulator (third-party)
└── sw.js        # Service worker (PWA)

webterm_templates/
└── index.html   # Main HTML template
```

### Data Flow

```
Browser (xterm.js)
  ↕ WebSocket
FastAPI (main.py)
  ↕
TerminalManager (terminal_manager.py)
  ↕
PTY (pty_windows.py / pty_unix.py)
  ↕
Shell Process (bash, powershell, etc.)
```

### Key Components

**Terminal Session:**
- Created via POST `/api/sessions`
- WebSocket connection via `/ws/terminal/{sid}`
- Managed by `TerminalManager` class
- Output pumped via async task
- Scrollback stored in memory + DB

**Quick Actions:**
- Stored in localStorage (frontend)
- Executed via POST `/api/quick-action/execute`
- Runs in background with subprocess
- Returns success/error + output
- 60s timeout with cleanup

**Authentication:**
- Session-based with HTTP-only cookies
- Password hashing with bcrypt
- Admin vs regular user roles
- Optional anonymous mode

---

## 💡 Areas for Contribution

### High Priority

- [ ] Terminal themes (Dracula, Solarized, etc.)
- [ ] Session recording/playback
- [ ] File upload/download
- [ ] Better mobile keyboard support
- [ ] Performance optimization for 100+ sessions

### Medium Priority

- [ ] SSH integration
- [ ] Docker container exec
- [ ] Kubernetes pod exec
- [ ] Split terminal view
- [ ] Command history search

### Nice to Have

- [ ] Collaborative sessions (multi-user)
- [ ] AI assistant sidebar
- [ ] Terminal tabs (instead of panels)
- [ ] Custom terminal fonts
- [ ] Emoji support in terminal

### Documentation

- [ ] Video tutorials
- [ ] Architecture diagrams
- [ ] API documentation
- [ ] Deployment guides (Docker, K8s, etc.)
- [ ] Troubleshooting guide

---

## ❓ Questions?

- **GitHub Discussions**: [Ask a question](https://github.com/yourusername/devbridge/discussions)
- **Issues**: [Report a bug](https://github.com/yourusername/devbridge/issues)
- **Discord**: [Join our community](#) *(coming soon)*

---

## 📝 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to DevBridge!** 🙏

Every contribution, no matter how small, helps make DevBridge better for everyone.
