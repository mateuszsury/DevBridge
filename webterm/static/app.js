/**
 * DevShell - AI Terminal Launcher
 * Mobile-first, gesture-enabled, Claude Code ready
 */

// ============================================
// State Management
// ============================================

const state = {
  // Terminals
  tabs: new Map(),
  activeTabId: null,
  sessions: [],

  // Views
  currentView: 'terminals',

  // Projects
  projectsPath: localStorage.getItem('projectsPath') || '',
  projects: [],
  filteredProjects: [],

  // Settings
  settings: null,
  principal: null,

  // UI State
  sidebarOpen: false,
  commandPaletteOpen: false,

  // Gestures
  touchStartX: 0,
  touchStartY: 0,
  isSwiping: false,

  // AI CLI Commands
  claudeCommand: localStorage.getItem('claudeCommand') || 'claude',
  codexCommand: localStorage.getItem('codexCommand') || 'codex',
  geminiCommand: localStorage.getItem('geminiCommand') || 'gemini',

  // Quick Actions
  quickActions: JSON.parse(localStorage.getItem('quickActions') || '[]'),
  editingActionId: null,
};

// ============================================
// Utility Functions
// ============================================

function $(id) {
  return document.getElementById(id);
}

function $$(selector) {
  return document.querySelectorAll(selector);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }

  return res.json();
}

function showError(message) {
  console.error(message);
  // TODO: Add toast notification
}

function showSuccess(message) {
  console.log(message);
  showToast('success', 'Success', message);
}

function showToast(type, title, message) {
  const container = $('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    warning: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
  };

  toast.innerHTML = `
    <div class="toast-icon">${icons[type] || icons.info}</div>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <button class="toast-close" aria-label="Close">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  `;

  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    removeToast(toast);
  });

  container.appendChild(toast);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    removeToast(toast);
  }, 5000);
}

function removeToast(toast) {
  if (!toast || !toast.parentElement) return;

  toast.classList.add('removing');
  setTimeout(() => {
    if (toast.parentElement) {
      toast.parentElement.removeChild(toast);
    }
  }, 300);
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function showModal(modalId) {
  const modal = $(modalId);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(modalId) {
  const modal = $(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// ============================================
// Terminal Management
// ============================================

function createTerminalInstance(sessionId) {
  const term = new Terminal({
    cursorBlink: true,
    convertEol: true,
    fontSize: window.innerWidth <= 768 ? 16 : 14,
    fontFamily: "'JetBrains Mono', 'Consolas', monospace",
    theme: {
      background: '#000000',
      foreground: '#FAFAF9',
      cursor: '#FF9B4E',
      cursorAccent: '#000000',
      selection: 'rgba(255, 155, 78, 0.3)',
      black: '#000000',
      red: '#EF4444',
      green: '#FCD34D',
      yellow: '#FBBF24',
      blue: '#00d9ff',
      magenta: '#ff00a0',
      cyan: '#00d9ff',
      white: '#E7E5E4',
      brightBlack: '#78716C',
      brightRed: '#ff0080',
      brightGreen: '#00ff80',
      brightYellow: '#ffcc00',
      brightBlue: '#00e5ff',
      brightMagenta: '#ff00ff',
      brightCyan: '#00ffff',
      brightWhite: '#ffffff'
    }
  });

  const fitAddon = new FitAddon.FitAddon();
  term.loadAddon(fitAddon);

  return { term, fitAddon };
}

function createTerminalPanel(sessionId) {
  const panel = document.createElement('div');
  panel.className = 'terminal-panel';
  panel.id = `panel-${sessionId}`;

  const container = document.createElement('div');
  container.className = 'terminal-container-inner';
  container.id = `terminal-${sessionId}`;

  panel.appendChild(container);
  $('terminalPanels').appendChild(panel);

  return container;
}

function connectWebSocket(sessionId, term, fitAddon) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${proto}://${location.host}/ws/terminal/${sessionId}`);

  ws.onopen = () => {
    console.log(`WebSocket connected for session ${sessionId}`);
    setTimeout(() => {
      fitAddon.fit();
      sendResize(ws, term);
    }, 100);
  };

  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === 'replay' || msg.type === 'output') {
      term.write(msg.data);
    }
  };

  ws.onclose = () => {
    term.write('\r\n\x1b[31m[Connection closed]\x1b[0m\r\n');
  };

  ws.onerror = (err) => {
    console.error('WebSocket error:', err);
    term.write('\r\n\x1b[31m[Connection error]\x1b[0m\r\n');
  };

  term.onData((data) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'input', data }));
    }
  });

  return ws;
}

function sendResize(ws, term) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'resize',
      cols: term.cols || 120,
      rows: term.rows || 30
    }));
  }
}

async function openTerminalTab(sessionId, autoCommand = null) {
  if (state.tabs.has(sessionId)) {
    switchToTab(sessionId);
    return;
  }

  const { term, fitAddon } = createTerminalInstance(sessionId);
  const container = createTerminalPanel(sessionId);
  term.open(container);

  const ws = connectWebSocket(sessionId, term, fitAddon);
  const sessionData = state.sessions.find(s => s.id === sessionId);

  state.tabs.set(sessionId, {
    term,
    fitAddon,
    ws,
    sessionData
  });

  createTabUI(sessionId, sessionData);
  switchToTab(sessionId);

  setTimeout(() => {
    fitAddon.fit();
    term.focus();

    // Auto-execute command if provided (for AI CLI quick launch)
    if (autoCommand) {
      setTimeout(() => {
        term.write(autoCommand + '\r');
        ws.send(JSON.stringify({ type: 'input', data: autoCommand + '\r' }));
      }, 500);
    }
  }, 150);
}

function createTabUI(sessionId, sessionData) {
  const tab = document.createElement('div');
  tab.className = 'tab';
  tab.dataset.sessionId = sessionId;

  const label = document.createElement('span');
  label.className = 'tab-label';
  label.textContent = sessionData ?
    `${sessionData.id.substring(0, 8)}... • ${sessionData.shell || 'shell'}` :
    sessionId;
  label.title = sessionData ?
    `${sessionData.id}\n${sessionData.cwd}\n${sessionData.shell}` :
    sessionId;

  const closeBtn = document.createElement('button');
  closeBtn.className = 'tab-close';
  closeBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
  closeBtn.onclick = (e) => {
    e.stopPropagation();
    closeTab(sessionId);
  };

  tab.appendChild(label);
  tab.appendChild(closeBtn);
  tab.onclick = () => switchToTab(sessionId);

  const placeholder = $('tabPlaceholder');
  if (placeholder) {
    placeholder.remove();
  }

  $('tabsScroll').appendChild(tab);
}

function switchToTab(sessionId) {
  if (!state.tabs.has(sessionId)) return;

  state.activeTabId = sessionId;

  $$('.tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.sessionId === sessionId);
  });

  $$('.terminal-panel').forEach(panel => {
    panel.classList.toggle('active', panel.id === `panel-${sessionId}`);
  });

  updateSessionListUI();

  const tabData = state.tabs.get(sessionId);
  if (tabData) {
    setTimeout(() => {
      tabData.fitAddon.fit();
      tabData.term.focus();
    }, 50);
  }
}

async function closeTab(sessionId, killSession = false) {
  const tabData = state.tabs.get(sessionId);
  if (!tabData) return;

  if (tabData.ws) {
    tabData.ws.close();
  }

  tabData.term.dispose();

  const panel = $(`panel-${sessionId}`);
  if (panel) {
    panel.remove();
  }

  const tabEl = document.querySelector(`.tab[data-session-id="${sessionId}"]`);
  if (tabEl) {
    tabEl.remove();
  }

  state.tabs.delete(sessionId);

  if (state.activeTabId === sessionId) {
    const remainingTabs = Array.from(state.tabs.keys());
    if (remainingTabs.length > 0) {
      switchToTab(remainingTabs[0]);
    } else {
      state.activeTabId = null;
      showTabPlaceholder();
    }
  }

  if (killSession) {
    try {
      await api(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      await refreshSessions();
    } catch (err) {
      console.error('Failed to kill session:', err);
    }
  }
}

function showTabPlaceholder() {
  const placeholder = document.createElement('div');
  placeholder.className = 'tab-placeholder';
  placeholder.id = 'tabPlaceholder';
  placeholder.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <path d="M4 17l6-6-6-6M12 19h8"/>
    </svg>
    <p>No terminals open</p>
    <p class="hint">Tap the + button to create a session</p>
  `;
  $('tabsScroll').appendChild(placeholder);
}

// ============================================
// Session Management
// ============================================

async function refreshSessions() {
  try {
    const data = await api('/api/sessions');
    state.sessions = data.sessions;
    renderSessionsList();
  } catch (err) {
    showError('Failed to load sessions: ' + err.message);
  }
}

function renderSessionsList() {
  const container = $('sessionsList');
  container.innerHTML = '';

  if (state.sessions.length === 0) {
    container.innerHTML = '<div style="padding: 1rem; text-align: center; font-size: 12px; color: var(--color-text-muted);">No active sessions</div>';
    return;
  }

  state.sessions.forEach(session => {
    if (session.status !== 'running') return;

    const card = document.createElement('div');
    card.className = 'session-card';
    if (session.id === state.activeTabId) {
      card.classList.add('active');
    }

    const pidDisplay = session.pid ? `PID: ${session.pid}` : 'PID: N/A';
    const shortId = session.id.substring(0, 8) + '...';

    card.innerHTML = `
      <div class="session-info">
        <div class="session-id">${shortId}</div>
        <div class="session-details">${session.shell || 'shell'}</div>
        <div class="session-details">${session.cwd || '~'}</div>
        <div class="session-details">${session.status} • ${pidDisplay}</div>
      </div>
      <div class="session-actions">
        <button class="btn btn-sm btn-primary">Open</button>
        <button class="btn btn-sm btn-danger">Kill</button>
      </div>
    `;

    card.querySelector('.btn-primary').onclick = () => openTerminalTab(session.id);
    card.querySelector('.btn-danger').onclick = async () => {
      if (confirm(`Kill terminal ${shortId}?`)) {
        await killSession(session.id);
      }
    };

    container.appendChild(card);
  });
}

function updateSessionListUI() {
  $$('.session-card').forEach(card => {
    const sessionId = card.querySelector('.session-id').textContent.replace('...', '');
    const fullId = state.sessions.find(s => s.id.startsWith(sessionId))?.id;
    card.classList.toggle('active', fullId === state.activeTabId);
  });
}

async function createSession(cwd = null, shell = null, autoCommand = null) {
  try {
    const created = await api('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({
        cwd: cwd || null,
        shell: shell || null,
        cols: 120,
        rows: 30
      })
    });

    await refreshSessions();
    await openTerminalTab(created.id, autoCommand);
  } catch (err) {
    showError('Failed to create session: ' + err.message);
  }
}

async function killSession(sessionId) {
  await closeTab(sessionId, true);
}

// ============================================
// Projects Browser
// ============================================

async function loadProjects() {
  const path = $('projectsPathInput').value.trim();
  if (!path) {
    showError('Please enter a projects directory path');
    return;
  }

  state.projectsPath = path;
  localStorage.setItem('projectsPath', path);

  try {
    // Call the backend API to get real project list
    const data = await api(`/api/projects?path=${encodeURIComponent(path)}`);

    state.projects = data.projects || [];
    state.filteredProjects = [...state.projects];
    renderProjects();

    if (state.projects.length > 0) {
      showSuccess(`Loaded ${state.projects.length} project(s)`);
    }
  } catch (err) {
    showError('Failed to load projects: ' + err.message);
    state.projects = [];
    state.filteredProjects = [];
    renderProjects();
  }
}

function renderProjects() {
  const container = $('projectsGrid');

  const empty = container.querySelector('.projects-empty');
  if (state.filteredProjects.length === 0) {
    if (!empty) {
      container.innerHTML = `
        <div class="projects-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
          </svg>
          <p>No projects found</p>
          <p class="hint">Try loading a different directory</p>
        </div>
      `;
    }
    return;
  }

  if (empty) {
    empty.remove();
  }

  container.innerHTML = '';

  state.filteredProjects.forEach(project => {
    const card = document.createElement('div');
    card.className = 'project-card';

    card.innerHTML = `
      <div class="project-header">
        <div class="project-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
          </svg>
        </div>
      </div>
      <div class="project-name">${project.name}</div>
      <div class="project-path">${project.path}</div>
      <div class="project-actions">
        <button class="btn-primary project-action claude-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 17l6-6-6-6M12 19h8"/>
          </svg>
          Claude
        </button>
        <button class="btn-ghost project-action codex-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 17l6-6-6-6M12 19h8"/>
          </svg>
          Codex
        </button>
        <button class="btn-ghost project-action gemini-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 17l6-6-6-6M12 19h8"/>
          </svg>
          Gemini
        </button>
        <button class="btn-ghost project-action terminal-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
          </svg>
          Terminal
        </button>
      </div>
    `;

    // Quick launch handlers
    card.querySelector('.claude-btn').onclick = () => {
      quickLaunchAI(project.path, state.claudeCommand);
    };

    card.querySelector('.codex-btn').onclick = () => {
      quickLaunchAI(project.path, state.codexCommand);
    };

    card.querySelector('.gemini-btn').onclick = () => {
      quickLaunchAI(project.path, state.geminiCommand);
    };

    card.querySelector('.terminal-btn').onclick = () => {
      quickLaunchAI(project.path, null);
    };

    container.appendChild(card);
  });
}

async function quickLaunchAI(projectPath, command) {
  // Switch to terminals view
  switchView('terminals');

  // Create session with project path and auto-run command
  // PowerShell uses `;` instead of `&&` for command chaining
  const isWindows = navigator.platform.toLowerCase().includes('win');
  const separator = isWindows ? '; ' : ' && ';
  const autoCommand = command ? `cd "${projectPath}"${separator}${command}` : `cd "${projectPath}"`;
  await createSession(projectPath, null, autoCommand);
}

function filterProjects() {
  const search = $('projectsSearch').value.toLowerCase();
  const filter = $('projectsFilter').value;

  state.filteredProjects = state.projects.filter(project => {
    const matchesSearch = project.name.toLowerCase().includes(search);

    let matchesFilter = true;
    if (filter === 'favorites') {
      // TODO: Implement favorites
      matchesFilter = false;
    } else if (filter === 'recent') {
      // TODO: Implement recent
      matchesFilter = false;
    }

    return matchesSearch && matchesFilter;
  });

  renderProjects();
}

// ============================================
// View Navigation
// ============================================

function switchView(viewName) {
  state.currentView = viewName;

  $$('.view').forEach(view => {
    view.classList.remove('active');
  });
  $(`${viewName}View`).classList.add('active');

  $$('.nav-item, .bottom-nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.view === viewName);
  });

  const titles = {
    terminals: 'Terminals',
    projects: 'Projects',
    settings: 'Settings'
  };
  $('viewTitle').textContent = titles[viewName] || viewName;

  // Auto-load projects when switching to projects view
  if (viewName === 'projects' && state.projectsPath && state.projects.length === 0) {
    loadProjects();
  }
}

// ============================================
// Quick Actions Management
// ============================================

function loadQuickActions() {
  state.quickActions = JSON.parse(localStorage.getItem('quickActions') || '[]');
  renderQuickActions();
}

function saveQuickActionsToStorage() {
  localStorage.setItem('quickActions', JSON.stringify(state.quickActions));
}

function renderSidebarQuickActions() {
  const container = $('sidebarQuickActionsList');
  if (!container) return;

  if (state.quickActions.length === 0) {
    container.innerHTML = `
      <div class="quick-actions-empty">
        <p>No actions yet</p>
      </div>
    `;
    return;
  }

  container.innerHTML = '';

  const colors = {
    primary: { color: '#FF9B4E' },
    success: { color: '#10B981' },
    warning: { color: '#F59E0B' },
    danger: { color: '#EF4444' },
    info: { color: '#3B82F6' }
  };

  state.quickActions.forEach((action) => {
    const item = document.createElement('div');
    item.className = 'sidebar-quick-action-item';
    item.dataset.id = action.id;

    const colorSet = colors[action.color] || colors.primary;
    item.style.setProperty('--action-color', colorSet.color);

    item.innerHTML = `
      <div class="sidebar-quick-action-item-icon">${action.icon || '⚡'}</div>
      <div class="sidebar-quick-action-item-content">
        <div class="sidebar-quick-action-item-name">${action.name}</div>
        <div class="sidebar-quick-action-item-command">${action.command}</div>
      </div>
    `;

    item.addEventListener('click', () => {
      executeQuickAction(action.id);
    });

    container.appendChild(item);
  });
}

function renderQuickActions() {
  const container = $('quickActionsGrid');
  if (!container) return;

  const empty = container.querySelector('.quick-actions-empty');

  if (state.quickActions.length === 0) {
    if (!empty) {
      container.innerHTML = `
        <div class="quick-actions-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
          <p>No quick actions configured</p>
          <p class="hint">Click "Add Quick Action" to create your first action</p>
        </div>
      `;
    }
    return;
  }

  if (empty) {
    empty.remove();
  }

  container.innerHTML = '';

  state.quickActions.forEach((action) => {
    const card = document.createElement('div');
    card.className = 'quick-action-card';
    card.dataset.color = action.color || 'primary';
    card.dataset.id = action.id;

    card.innerHTML = `
      <div class="quick-action-header">
        <div class="quick-action-icon">${action.icon || '⚡'}</div>
        <div class="quick-action-menu">
          <button class="btn-icon edit-action-btn" aria-label="Edit">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="btn-icon delete-action-btn" aria-label="Delete">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="quick-action-name">${action.name}</div>
      <div class="quick-action-command">${action.command}</div>
      <div class="quick-action-path">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
        </svg>
        ${action.cwd}
      </div>
    `;

    // Execute action on click (not on menu buttons)
    card.addEventListener('click', (e) => {
      if (!e.target.closest('.quick-action-menu')) {
        executeQuickAction(action.id);
      }
    });

    // Edit button
    card.querySelector('.edit-action-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      openEditQuickActionModal(action.id);
    });

    // Delete button
    card.querySelector('.delete-action-btn').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteQuickAction(action.id);
    });

    container.appendChild(card);
  });
}

function openAddQuickActionModal() {
  state.editingActionId = null;

  $('quickActionModalTitle').textContent = 'Add Quick Action';
  $('quickActionName').value = '';
  $('quickActionCommand').value = '';
  $('quickActionCwd').value = '';
  $('quickActionIcon').value = '';
  $('quickActionColor').value = 'primary';

  showModal('quickActionModal');
}

function openEditQuickActionModal(actionId) {
  const action = state.quickActions.find(a => a.id === actionId);
  if (!action) return;

  state.editingActionId = actionId;

  $('quickActionModalTitle').textContent = 'Edit Quick Action';
  $('quickActionName').value = action.name;
  $('quickActionCommand').value = action.command;
  $('quickActionCwd').value = action.cwd;
  $('quickActionIcon').value = action.icon || '';
  $('quickActionColor').value = action.color || 'primary';

  showModal('quickActionModal');
}

function saveQuickAction() {
  const name = $('quickActionName').value.trim();
  const command = $('quickActionCommand').value.trim();
  const cwd = $('quickActionCwd').value.trim();
  const icon = $('quickActionIcon').value.trim();
  const color = $('quickActionColor').value;

  if (!name || !command || !cwd) {
    showError('Please fill in all required fields');
    return;
  }

  const actionData = {
    name,
    command,
    cwd,
    icon: icon || '⚡',
    color: color || 'primary'
  };

  if (state.editingActionId) {
    // Update existing action
    const index = state.quickActions.findIndex(a => a.id === state.editingActionId);
    if (index !== -1) {
      state.quickActions[index] = {
        ...state.quickActions[index],
        ...actionData
      };
    }
  } else {
    // Create new action
    const newAction = {
      id: Date.now().toString(),
      ...actionData
    };
    state.quickActions.push(newAction);
  }

  saveQuickActionsToStorage();
  renderSidebarQuickActions();
  closeModal('quickActionModal');
  showSuccess('Quick action saved successfully');
}

function deleteQuickAction(actionId) {
  if (!confirm('Are you sure you want to delete this quick action?')) {
    return;
  }

  state.quickActions = state.quickActions.filter(a => a.id !== actionId);
  saveQuickActionsToStorage();
  renderSidebarQuickActions();
  showSuccess('Quick action deleted');
}

async function executeQuickAction(actionId) {
  const action = state.quickActions.find(a => a.id === actionId);
  if (!action) return;

  // Show starting toast
  showToast('info', 'Running Action', `Executing ${action.name}...`);

  try {
    const result = await api('/api/quick-action/execute', {
      method: 'POST',
      body: JSON.stringify({
        command: action.command,
        cwd: action.cwd
      })
    });

    if (result.success) {
      showToast('success', 'Action Completed', `${action.name} completed successfully`);

      if (result.output) {
        console.log(`Quick Action "${action.name}" output:`, result.output);
      }
    } else {
      const errorMsg = result.error || 'Unknown error';
      showToast('error', 'Action Failed', `${action.name}: ${errorMsg}`);

      if (result.output) {
        console.error(`Quick Action "${action.name}" error:`, result.output);
      }
    }
  } catch (err) {
    showToast('error', 'Execution Error', `Failed to execute ${action.name}: ${err.message}`);
  }
}

// ============================================
// Settings Management
// ============================================

async function loadSettings() {
  try {
    const data = await api('/api/settings');
    state.settings = data.settings;
    state.principal = data.principal;

    const who = state.principal.username
      ? `${state.principal.username}`
      : 'Anonymous';
    $('userName').textContent = who;

    $('authRequired').checked = !!state.settings.auth_required;
    $('allowAnonymousTerminal').checked = !!state.settings.allow_anonymous_terminal;
    $('maxSessions').value = state.settings.max_sessions || 50;
    $('idleTtl').value = state.settings.idle_ttl_seconds || 0;
    $('scrollbackLimit').value = state.settings.scrollback_limit_chars || 200000;
    $('defaultUnixShell').value = state.settings.default_unix_shell || '/bin/bash';
    $('defaultWindowsShell').value = state.settings.default_windows_shell || 'powershell.exe';

    // AI CLI commands
    if ($('claudeCommand')) {
      $('claudeCommand').value = state.claudeCommand;
      $('codexCommand').value = state.codexCommand;
      $('geminiCommand').value = state.geminiCommand;
    }
  } catch (err) {
    showError('Failed to load settings: ' + err.message);
    $('userName').textContent = 'Not logged in';
  }
}

async function saveSettings() {
  const settings = {
    auth_required: $('authRequired').checked,
    allow_anonymous_terminal: $('allowAnonymousTerminal').checked,
    max_sessions: parseInt($('maxSessions').value, 10),
    idle_ttl_seconds: parseInt($('idleTtl').value, 10),
    scrollback_limit_chars: parseInt($('scrollbackLimit').value, 10),
    default_unix_shell: $('defaultUnixShell').value.trim(),
    default_windows_shell: $('defaultWindowsShell').value.trim()
  };

  // Save AI CLI commands to localStorage
  if ($('claudeCommand')) {
    state.claudeCommand = $('claudeCommand').value.trim();
    state.codexCommand = $('codexCommand').value.trim();
    state.geminiCommand = $('geminiCommand').value.trim();

    localStorage.setItem('claudeCommand', state.claudeCommand);
    localStorage.setItem('codexCommand', state.codexCommand);
    localStorage.setItem('geminiCommand', state.geminiCommand);
  }

  try {
    await api('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings)
    });
    await loadSettings();
    alert('Settings saved successfully');
  } catch (err) {
    showError('Failed to save settings: ' + err.message);
  }
}

// ============================================
// User Management
// ============================================

async function loadUsers() {
  try {
    const data = await api('/api/users');
    renderUsers(data.users);
  } catch (err) {
    $('usersList').innerHTML = '<div style="padding: 1rem; font-size: 12px; color: var(--color-text-muted);">No permission</div>';
  }
}

function renderUsers(users) {
  const container = $('usersList');
  container.innerHTML = '';

  if (users.length === 0) {
    container.innerHTML = '<div style="padding: 1rem; text-align: center; font-size: 12px; color: var(--color-text-muted);">No users</div>';
    return;
  }

  users.forEach(user => {
    const card = document.createElement('div');
    card.className = 'user-card';

    card.innerHTML = `
      <div>
        <h4>${user.username}</h4>
        <p>ID: ${user.id} • ${user.is_admin ? 'Admin' : 'User'}</p>
      </div>
      <div class="user-actions">
        <label class="checkbox-label">
          <input type="checkbox" ${user.is_admin ? 'checked' : ''}>
          <span>Admin</span>
        </label>
        <button class="btn btn-sm btn-danger">Delete</button>
      </div>
    `;

    card.querySelector('input[type="checkbox"]').addEventListener('change', async (e) => {
      try {
        await api(`/api/users/${user.id}`, {
          method: 'PUT',
          body: JSON.stringify({ is_admin: e.target.checked })
        });
      } catch (err) {
        showError('Failed to update user: ' + err.message);
        e.target.checked = !e.target.checked;
      }
    });

    card.querySelector('.btn-danger').onclick = async () => {
      if (!confirm(`Delete user "${user.username}"?`)) return;
      try {
        await api(`/api/users/${user.id}`, { method: 'DELETE' });
        await loadUsers();
      } catch (err) {
        showError('Failed to delete user: ' + err.message);
      }
    };

    container.appendChild(card);
  });
}

async function createUser() {
  const username = $('newUsername').value.trim();
  const password = $('newPassword').value;
  const is_admin = $('newIsAdmin').checked;

  if (!username || !password) {
    alert('Username and password are required');
    return;
  }

  try {
    await api('/api/users', {
      method: 'POST',
      body: JSON.stringify({ username, password, is_admin })
    });

    $('newUsername').value = '';
    $('newPassword').value = '';
    $('newIsAdmin').checked = false;

    await loadUsers();
  } catch (err) {
    showError('Failed to create user: ' + err.message);
  }
}

// ============================================
// Gesture Navigation
// ============================================

function setupGestures() {
  const terminalPanels = $('terminalPanels');

  terminalPanels.addEventListener('touchstart', (e) => {
    state.touchStartX = e.touches[0].clientX;
    state.touchStartY = e.touches[0].clientY;
    state.isSwiping = false;
  }, { passive: true });

  terminalPanels.addEventListener('touchmove', (e) => {
    if (!state.touchStartX || !state.touchStartY) return;

    const diffX = e.touches[0].clientX - state.touchStartX;
    const diffY = e.touches[0].clientY - state.touchStartY;

    if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
      state.isSwiping = true;
    }
  }, { passive: true });

  terminalPanels.addEventListener('touchend', (e) => {
    if (!state.isSwiping) return;

    const diffX = e.changedTouches[0].clientX - state.touchStartX;

    if (Math.abs(diffX) > 100) {
      const tabs = Array.from(state.tabs.keys());
      const currentIndex = tabs.indexOf(state.activeTabId);

      if (diffX > 0 && currentIndex > 0) {
        // Swipe right - previous tab
        switchToTab(tabs[currentIndex - 1]);
      } else if (diffX < 0 && currentIndex < tabs.length - 1) {
        // Swipe left - next tab
        switchToTab(tabs[currentIndex + 1]);
      }
    }

    state.touchStartX = 0;
    state.touchStartY = 0;
    state.isSwiping = false;
  }, { passive: true });
}

// ============================================
// Virtual Keyboard
// ============================================

function setupVirtualKeyboard() {
  $$('.vk-key').forEach(key => {
    key.addEventListener('click', () => {
      const keyName = key.dataset.key;
      const tabData = state.tabs.get(state.activeTabId);

      if (!tabData) return;

      let keyData = '';
      switch (keyName) {
        case 'Tab':
          keyData = '\t';
          break;
        case 'Escape':
          keyData = '\x1b';
          break;
        case 'Control':
          // TODO: Implement Ctrl modifier
          return;
        case 'ArrowUp':
          keyData = '\x1b[A';
          break;
        case 'ArrowDown':
          keyData = '\x1b[B';
          break;
        case 'ArrowRight':
          keyData = '\x1b[C';
          break;
        case 'ArrowLeft':
          keyData = '\x1b[D';
          break;
      }

      if (keyData && tabData.ws.readyState === WebSocket.OPEN) {
        tabData.ws.send(JSON.stringify({ type: 'input', data: keyData }));
      }
    });
  });
}

// ============================================
// Modals
// ============================================

function openNewSessionModal() {
  $('newSessionModal').classList.add('active');
  $('newSessionCwd').focus();
}

function closeNewSessionModal() {
  $('newSessionModal').classList.remove('active');
  $('newSessionCwd').value = '';
  $('newSessionShell').value = '';
}

function openCommandPalette() {
  state.commandPaletteOpen = true;
  $('commandPalette').classList.add('active');
  $('commandPaletteInput').focus();
}

function closeCommandPalette() {
  state.commandPaletteOpen = false;
  $('commandPalette').classList.remove('active');
  $('commandPaletteInput').value = '';
}

// ============================================
// Window Resize Handler
// ============================================

let resizeTimeout;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    if (state.activeTabId && state.tabs.has(state.activeTabId)) {
      const tabData = state.tabs.get(state.activeTabId);
      try {
        tabData.fitAddon.fit();
        sendResize(tabData.ws, tabData.term);
      } catch (err) {
        console.error('Error resizing terminal:', err);
      }
    }
  }, 250);
});

// ============================================
// Keyboard Shortcuts
// ============================================

document.addEventListener('keydown', (e) => {
  // Command Palette: Ctrl+K or Cmd+K
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    if (state.commandPaletteOpen) {
      closeCommandPalette();
    } else {
      openCommandPalette();
    }
  }

  // Close modal: Escape
  if (e.key === 'Escape') {
    if (state.commandPaletteOpen) {
      closeCommandPalette();
    }
    if ($('newSessionModal').classList.contains('active')) {
      closeNewSessionModal();
    }
  }

  // Next/Previous tab: Ctrl+Tab / Ctrl+Shift+Tab
  if (e.ctrlKey && e.key === 'Tab') {
    e.preventDefault();
    const tabs = Array.from(state.tabs.keys());
    const currentIndex = tabs.indexOf(state.activeTabId);

    if (e.shiftKey) {
      // Previous tab
      if (currentIndex > 0) {
        switchToTab(tabs[currentIndex - 1]);
      }
    } else {
      // Next tab
      if (currentIndex < tabs.length - 1) {
        switchToTab(tabs[currentIndex + 1]);
      }
    }
  }
});

// ============================================
// Event Listeners
// ============================================

function setupEventListeners() {
  // View navigation
  $$('.nav-item, .bottom-nav-item').forEach(item => {
    item.addEventListener('click', () => {
      switchView(item.dataset.view);
      if (window.innerWidth <= 768) {
        $('desktopSidebar').classList.remove('open');
      }
    });
  });

  // Mobile menu toggle
  if ($('mobileMenuBtn')) {
    $('mobileMenuBtn').addEventListener('click', () => {
      $('desktopSidebar').classList.add('open');
      $('sidebarOverlay').classList.add('active');
    });
  }

  // Desktop menu button (shows when sidebar collapsed)
  if ($('desktopMenuBtn')) {
    $('desktopMenuBtn').addEventListener('click', () => {
      $('desktopSidebar').classList.remove('collapsed');
    });
  }

  // Sidebar toggle
  if ($('toggleSidebarBtn')) {
    $('toggleSidebarBtn').addEventListener('click', () => {
      $('desktopSidebar').classList.toggle('collapsed');
    });
  }

  // Close sidebar button (mobile)
  if ($('closeSidebarBtn')) {
    $('closeSidebarBtn').addEventListener('click', () => {
      $('desktopSidebar').classList.remove('open');
      $('sidebarOverlay').classList.remove('active');
    });
  }

  // Sidebar overlay (mobile)
  if ($('sidebarOverlay')) {
    $('sidebarOverlay').addEventListener('click', () => {
      $('desktopSidebar').classList.remove('open');
      $('sidebarOverlay').classList.remove('active');
    });
  }

  // New terminal button (desktop)
  if ($('newTerminalBtn')) {
    $('newTerminalBtn').addEventListener('click', openNewSessionModal);
  }

  // FAB button
  if ($('fabBtn')) {
    $('fabBtn').addEventListener('click', () => {
      openNewSessionModal();
    });
  }

  // Refresh button
  if ($('refreshBtn')) {
    $('refreshBtn').addEventListener('click', () => {
      if (state.currentView === 'terminals') {
        refreshSessions();
      } else if (state.currentView === 'projects') {
        loadProjects();
      }
    });
  }

  // Command palette
  if ($('commandPaletteBtn')) {
    $('commandPaletteBtn').addEventListener('click', openCommandPalette);
  }

  if ($('commandPaletteOverlay')) {
    $('commandPaletteOverlay').addEventListener('click', closeCommandPalette);
  }

  // New session modal
  if ($('newSessionBtnDrawer')) {
    $('newSessionBtnDrawer').addEventListener('click', openNewSessionModal);
  }

  if ($('closeNewSessionBtn')) {
    $('closeNewSessionBtn').addEventListener('click', closeNewSessionModal);
  }

  if ($('cancelNewSessionBtn')) {
    $('cancelNewSessionBtn').addEventListener('click', closeNewSessionModal);
  }

  if ($('newSessionModalOverlay')) {
    $('newSessionModalOverlay').addEventListener('click', closeNewSessionModal);
  }

  if ($('createNewSessionBtn')) {
    $('createNewSessionBtn').addEventListener('click', async () => {
      const cwd = $('newSessionCwd').value.trim() || null;
      const shell = $('newSessionShell').value.trim() || null;
      await createSession(cwd, shell);
      closeNewSessionModal();
    });
  }

  // Projects
  if ($('loadProjectsBtn')) {
    $('loadProjectsBtn').addEventListener('click', loadProjects);
  }

  if ($('projectsSearch')) {
    $('projectsSearch').addEventListener('input', debounce(filterProjects, 300));
  }

  if ($('projectsFilter')) {
    $('projectsFilter').addEventListener('change', filterProjects);
  }

  // Load projects path from localStorage
  if (state.projectsPath) {
    $('projectsPathInput').value = state.projectsPath;
  }

  // Settings
  if ($('saveSettingsBtn')) {
    $('saveSettingsBtn').addEventListener('click', saveSettings);
  }

  if ($('refreshUsersBtn')) {
    $('refreshUsersBtn').addEventListener('click', loadUsers);
  }

  if ($('createUserBtn')) {
    $('createUserBtn').addEventListener('click', createUser);
  }

  // Quick Actions
  if ($('quickActionsToggle')) {
    $('quickActionsToggle').addEventListener('click', () => {
      const toggle = $('quickActionsToggle');
      const list = $('sidebarQuickActionsList');

      toggle.classList.toggle('expanded');
      list.classList.toggle('expanded');
    });
  }

  if ($('addQuickActionSidebarBtn')) {
    $('addQuickActionSidebarBtn').addEventListener('click', openAddQuickActionModal);
  }

  if ($('closeQuickActionBtn')) {
    $('closeQuickActionBtn').addEventListener('click', () => closeModal('quickActionModal'));
  }

  if ($('cancelQuickActionBtn')) {
    $('cancelQuickActionBtn').addEventListener('click', () => closeModal('quickActionModal'));
  }

  if ($('quickActionModalOverlay')) {
    $('quickActionModalOverlay').addEventListener('click', () => closeModal('quickActionModal'));
  }

  if ($('saveQuickActionBtn')) {
    $('saveQuickActionBtn').addEventListener('click', saveQuickAction);
  }

  // Virtual keyboard
  setupVirtualKeyboard();

  // Gestures
  setupGestures();
}

// ============================================
// Initialization
// ============================================

async function init() {
  console.log('Initializing DevBridge...');

  setupEventListeners();

  await loadSettings();
  await refreshSessions();

  if (state.tabs.size === 0) {
    showTabPlaceholder();
  }

  // Load projects if path is set
  if (state.projectsPath && $('projectsPathInput')) {
    $('projectsPathInput').value = state.projectsPath;
  }

  // Render quick actions in sidebar
  renderSidebarQuickActions();

  console.log('DevBridge initialized successfully');
}

// Start the application
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
