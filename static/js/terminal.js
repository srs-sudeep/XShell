/* ── XShell Web Terminal ───────────────────────────────────────────────── */

'use strict';

// ── Constants ─────────────────────────────────────────────────────────────
const MAX_FONT = 24;
const MIN_FONT = 8;
const URL_PATTERN = /https?:\/\/[^\s<>"]+/g;

// ── Global state ──────────────────────────────────────────────────────────
let fontSize     = 13;
let activePaneId = 0;
let paneCount    = 1;
let splitMode    = null;   // null | 'v' | 'h'
let searchMatches = [];
let searchCurrent = 0;

// Per-pane state
const panes = {
  0: {
    history: [],
    historyIndex: -1,
    currentInput: '',
    sessionId: null,
    connected: false,
    socket: null,
    cwd: '',
  }
};

// Theme state (global)
const themeState = {
  current: 'default',
  colors: {},
};

// ── ANSI name → CSS hex ───────────────────────────────────────────────────
const ANSI_HEX = {
  'black':          '#3d3d3d',
  'red':            '#e06c75',
  'green':          '#4ec94e',
  'yellow':         '#e5c07b',
  'blue':           '#61afef',
  'magenta':        '#c678dd',
  'cyan':           '#56b6c2',
  'white':          '#abb2bf',
  'bright_black':   '#5c6370',
  'bright_red':     '#ff6b6b',
  'bright_green':   '#7ec850',
  'bright_yellow':  '#ffcb6b',
  'bright_blue':    '#82aaff',
  'bright_magenta': '#c792ea',
  'bright_cyan':    '#89ddff',
  'bright_white':   '#eeffff',
};

function colorToHex(val) {
  if (!val) return null;
  if (val.startsWith('#')) return val;
  return ANSI_HEX[val.toLowerCase()] || null;
}

function applyThemeColors(colors) {
  if (!colors) return;
  const root = document.documentElement.style;
  const set = (cssVar, key) => {
    const hex = colorToHex(colors[key]);
    if (hex) root.setProperty(cssVar, hex);
  };
  set('--bg',      'background');
  set('--fg',      'foreground');
  set('--green',   'success');
  set('--red',     'error');
  set('--blue',    'info');
  set('--yellow',  'warning');
  set('--cyan',    'prompt_cwd');

  const userColor = colorToHex(colors['prompt_user']);
  if (userColor) {
    document.querySelectorAll('.prompt-display').forEach(el => el.style.color = userColor);
  }
  const cwdColor = colorToHex(colors['prompt_cwd']);
  if (cwdColor) {
    const sbCwd = document.getElementById('sb-cwd');
    if (sbCwd) sbCwd.style.color = cwdColor;
  }
}

// ── DOM helpers ───────────────────────────────────────────────────────────
function $pane(id) { return document.getElementById(`pane-${id}`); }
function $output(id) { return document.getElementById(`output-${id}`); }
function $input(id)  { return document.getElementById(`cmd-input-${id}`); }
function $ghost(id)  { return document.getElementById(`ghost-${id}`); }
function $prompt(id) { return document.getElementById(`prompt-${id}`); }

// ── Socket management ─────────────────────────────────────────────────────
function createSocket(paneId) {
  const socket = io({ transports: ['websocket', 'polling'] });
  panes[paneId].socket = socket;

  socket.on('connect', () => {
    panes[paneId].connected = true;
    if (paneId === activePaneId) {
      document.getElementById('sb-status').textContent = '● Connected';
      document.getElementById('sb-status').className = 'status-ok';
    }
  });

  socket.on('disconnect', () => {
    panes[paneId].connected = false;
    if (paneId === activePaneId) {
      document.getElementById('sb-status').textContent = '● Disconnected';
      document.getElementById('sb-status').className = 'status-err';
    }
    appendLine(paneId, 'Connection lost. Reload to reconnect.\n', 'line-stderr');
  });

  socket.on('output', (data) => {
    const text = data.data || '';
    const type = data.type || 'stdout';
    const cwd  = data.cwd;
    const code = data.code;

    if (text) appendAnsi(paneId, text, `line-${type}`);

    if (cwd !== undefined) {
      panes[paneId].cwd = cwd;
      if (paneId === activePaneId) {
        document.getElementById('tb-cwd').textContent = shorten(cwd);
        document.getElementById('sb-cwd').textContent = cwd;
      }
    }
    if (code !== undefined && paneId === activePaneId) {
      updateExitCode(code);
    }
    scrollToBottom(paneId);
  });

  socket.on('completions', (data) => {
    if (paneId === activePaneId) {
      showCompletions(data.completions || [], paneId);
    }
  });

  socket.on('themes', (data) => {
    if (data.colors) themeState.colors = data.colors;
    populateThemes(data.themes || []);
  });

  socket.on('theme_changed', (data) => {
    themeState.current = data.theme;
    document.getElementById('sb-theme').textContent = `Theme: ${data.theme}`;
    document.querySelectorAll('.theme-item').forEach(el => {
      el.classList.toggle('active', el.dataset.theme === data.theme);
    });
    if (data.colors) applyThemeColors(data.colors);
    appendLine(paneId, `Theme changed to '${data.theme}'\n`, 'line-info');
  });

  socket.on('file_download', (data) => {
    if (!data.filename || !data.content) return;
    const blob = new Blob([atob(data.content)], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = data.filename;
    a.click();
    URL.revokeObjectURL(url);
  });

  return socket;
}

// ── Input handling ────────────────────────────────────────────────────────
function setupInputHandlers(paneId) {
  const inp = $input(paneId);
  if (!inp) return;

  inp.addEventListener('keydown', (e) => {
    const pane = panes[paneId];

    // Tab completion
    if (e.key === 'Tab') {
      e.preventDefault();
      const partial = inp.value;
      if (pane.socket) {
        pane.socket.emit('complete', { partial });
      }
      return;
    }

    // Hide completion popup on Escape
    if (e.key === 'Escape') {
      hideCompletions();
      if (document.getElementById('search-bar').classList.contains('') === false) {
        toggleSearch();
      }
    }

    switch (e.key) {
      case 'Enter':
        hideCompletions();
        submitCommand(paneId);
        break;
      case 'ArrowUp':
        e.preventDefault();
        historyBack(paneId);
        break;
      case 'ArrowDown':
        e.preventDefault();
        historyForward(paneId);
        break;
      case 'l':
        if (e.ctrlKey) { e.preventDefault(); clearTerminal(); }
        break;
      case 'c':
        if (e.ctrlKey) {
          e.preventDefault();
          appendLine(paneId, '^C\n', 'line-stderr');
          inp.value = '';
          updateGhost(paneId);
        }
        break;
      case '=':
      case '+':
        if (e.ctrlKey) { e.preventDefault(); changeFontSize(1); }
        break;
      case '-':
        if (e.ctrlKey) { e.preventDefault(); changeFontSize(-1); }
        break;
      case 'f':
        if (e.ctrlKey) { e.preventDefault(); toggleSearch(); }
        break;
    }
  });

  inp.addEventListener('input', () => updateGhost(paneId));
}

function submitCommand(paneId) {
  const inp = $input(paneId);
  if (!inp) return;
  const cmd = inp.value.trim();

  if (!cmd) {
    appendLine(paneId, '\n', 'line-stdout');
    return;
  }

  appendLine(paneId, `$ ${escHtml(cmd)}\n`, 'line-cmd');

  if (cmd === 'clear' || cmd === 'cls') {
    clearTerminal(paneId);
    inp.value = '';
    updateGhost(paneId);
    return;
  }

  const pane = panes[paneId];
  if (pane.history[pane.history.length - 1] !== cmd) {
    pane.history.push(cmd);
  }
  pane.historyIndex = pane.history.length;
  pane.currentInput = '';

  if (pane.socket) {
    pane.socket.emit('command', { data: cmd });
  }
  inp.value = '';
  updateGhost(paneId);
}

// ── History ───────────────────────────────────────────────────────────────
function historyBack(paneId) {
  const pane = panes[paneId];
  const inp = $input(paneId);
  if (pane.historyIndex > 0) {
    if (pane.historyIndex === pane.history.length) {
      pane.currentInput = inp.value;
    }
    pane.historyIndex--;
    inp.value = pane.history[pane.historyIndex];
    moveCursorToEnd(paneId);
  }
}

function historyForward(paneId) {
  const pane = panes[paneId];
  const inp = $input(paneId);
  if (pane.historyIndex < pane.history.length) {
    pane.historyIndex++;
    inp.value = pane.historyIndex < pane.history.length
      ? pane.history[pane.historyIndex]
      : pane.currentInput;
    moveCursorToEnd(paneId);
  }
}

function moveCursorToEnd(paneId) {
  requestAnimationFrame(() => {
    const inp = $input(paneId);
    if (inp) inp.selectionStart = inp.selectionEnd = inp.value.length;
  });
}

// ── Ghost text ────────────────────────────────────────────────────────────
function updateGhost(paneId) {
  const inp = $input(paneId);
  const ghost = $ghost(paneId);
  if (!inp || !ghost) return;
  const val = inp.value;
  if (!val) { ghost.textContent = ''; return; }
  const pane = panes[paneId];
  const match = pane.history.slice().reverse().find(h => h.startsWith(val) && h !== val);
  ghost.textContent = match ? match.slice(val.length) : '';
}

// ── Tab completion popup ──────────────────────────────────────────────────
let _completionPopup = null;

function showCompletions(items, paneId) {
  if (!items || items.length === 0) {
    hideCompletions();
    return;
  }
  if (items.length === 1) {
    // Auto-complete single match
    const inp = $input(paneId);
    if (inp) {
      const words = inp.value.split(' ');
      words[words.length - 1] = items[0];
      inp.value = words.join(' ');
      updateGhost(paneId);
    }
    hideCompletions();
    return;
  }

  if (!_completionPopup) {
    _completionPopup = document.createElement('div');
    _completionPopup.id = 'completion-popup';
    document.body.appendChild(_completionPopup);
  }
  _completionPopup.innerHTML = '';
  _completionPopup.className = '';

  items.slice(0, 20).forEach((item, i) => {
    const div = document.createElement('div');
    div.className = 'completion-item' + (i === 0 ? ' active' : '');
    div.textContent = item;
    div.onclick = () => {
      const inp = $input(paneId);
      if (inp) {
        const words = inp.value.split(' ');
        words[words.length - 1] = item;
        inp.value = words.join(' ');
        updateGhost(paneId);
        focusInput(paneId);
      }
      hideCompletions();
    };
    _completionPopup.appendChild(div);
  });

  // Position near the input
  const inp = $input(paneId);
  if (inp) {
    const rect = inp.getBoundingClientRect();
    _completionPopup.style.left = rect.left + 'px';
    _completionPopup.style.bottom = (window.innerHeight - rect.top + 4) + 'px';
    _completionPopup.style.position = 'fixed';
  }
}

function hideCompletions() {
  if (_completionPopup) {
    _completionPopup.className = 'hidden';
  }
}

// ── Output rendering ──────────────────────────────────────────────────────
function appendLine(paneId, html, cls = 'line-stdout') {
  const out = $output(paneId);
  if (!out) return;
  const div = document.createElement('div');
  div.className = cls;
  div.innerHTML = typeof html === 'string' ? html : escHtml(html);
  out.appendChild(div);
}

function appendAnsi(paneId, text, cls = 'line-stdout') {
  const out = $output(paneId);
  if (!out) return;
  const div = document.createElement('div');
  div.className = cls;
  const processed = linkify(ansiToHtml(escHtml(text)));
  div.innerHTML = processed;
  out.appendChild(div);
}

function linkify(html) {
  return html.replace(
    /(https?:\/\/[^\s<>"&]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
  );
}

// ANSI → HTML
function ansiToHtml(text) {
  text = text.replace(/\x1b\[\d*[ABCDEFGJKST]/g, '');
  text = text.replace(/\x1b\[2J/g, '');
  text = text.replace(/\x1b\[\d*;\d*H/g, '');

  const map = {
    0: '</span>',
    1: '<span class="ansi-bold">',
    2: '<span class="ansi-dim">',
    30:'<span class="ansi-30">',31:'<span class="ansi-31">',32:'<span class="ansi-32">',
    33:'<span class="ansi-33">',34:'<span class="ansi-34">',35:'<span class="ansi-35">',
    36:'<span class="ansi-36">',37:'<span class="ansi-37">',
    90:'<span class="ansi-90">',91:'<span class="ansi-91">',92:'<span class="ansi-92">',
    93:'<span class="ansi-93">',94:'<span class="ansi-94">',95:'<span class="ansi-95">',
    96:'<span class="ansi-96">',97:'<span class="ansi-97">',
  };

  let openSpans = 0;
  text = text.replace(/\x1b\[([0-9;]*)m/g, (_, codes) => {
    const parts = codes.split(';').map(Number);
    let out = '';
    for (const code of parts) {
      if (code === 0) {
        out += '</span>'.repeat(openSpans);
        openSpans = 0;
      } else if (map[code]) {
        if (map[code].startsWith('<span')) {
          out += map[code];
          openSpans++;
        }
      }
    }
    return out;
  });
  text += '</span>'.repeat(openSpans);
  return text;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function scrollToBottom(paneId) {
  const out = $output(paneId);
  if (out) out.scrollTop = out.scrollHeight;
}

// ── Search ────────────────────────────────────────────────────────────────
function toggleSearch() {
  const bar = document.getElementById('search-bar');
  bar.classList.toggle('hidden');
  if (!bar.classList.contains('hidden')) {
    document.getElementById('search-input').focus();
  } else {
    clearSearchHighlights();
  }
}

function searchOutput(query) {
  clearSearchHighlights();
  if (!query) {
    document.getElementById('search-count').textContent = '';
    searchMatches = [];
    return;
  }

  const out = $output(activePaneId);
  if (!out) return;
  searchMatches = [];
  searchCurrent = 0;

  const walker = document.createTreeWalker(out, NodeFilter.SHOW_TEXT);
  const nodes = [];
  let node;
  while (node = walker.nextNode()) {
    nodes.push(node);
  }

  const q = query.toLowerCase();
  nodes.forEach(textNode => {
    const text = textNode.textContent;
    const lower = text.toLowerCase();
    let idx = 0;
    while ((idx = lower.indexOf(q, idx)) !== -1) {
      searchMatches.push({ node: textNode, start: idx, length: query.length });
      idx += query.length;
    }
  });

  highlightSearchMatches(query);
  document.getElementById('search-count').textContent =
    searchMatches.length ? `1/${searchMatches.length}` : '0';
}

function highlightSearchMatches(query) {
  const out = $output(activePaneId);
  if (!out) return;
  // Simple text-based highlighting via innerHTML manipulation
  const divs = out.querySelectorAll('div');
  divs.forEach(div => {
    const text = div.textContent;
    if (!text.toLowerCase().includes(query.toLowerCase())) return;
    // Re-render with highlights
    const escaped = escHtml(text);
    const rx = new RegExp('(' + escRegex(escHtml(query)) + ')', 'gi');
    div.innerHTML = escaped.replace(rx, '<mark class="search-highlight">$1</mark>');
  });

  // Scroll first match into view
  const first = out.querySelector('.search-highlight');
  if (first) first.scrollIntoView({ block: 'center' });
}

function escRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function clearSearchHighlights() {
  const out = $output(activePaneId);
  if (!out) return;
  out.querySelectorAll('mark.search-highlight').forEach(m => {
    m.replaceWith(document.createTextNode(m.textContent));
  });
}

function searchNav(dir) {
  if (!searchMatches.length) return;
  const out = $output(activePaneId);
  if (!out) return;
  const marks = out.querySelectorAll('.search-highlight');
  if (!marks.length) return;
  marks[searchCurrent]?.classList.remove('search-highlight-current');
  searchCurrent = (searchCurrent + dir + marks.length) % marks.length;
  marks[searchCurrent]?.classList.add('search-highlight-current');
  marks[searchCurrent]?.scrollIntoView({ block: 'center' });
  document.getElementById('search-count').textContent = `${searchCurrent + 1}/${marks.length}`;
}

// ── Font size ─────────────────────────────────────────────────────────────
function changeFontSize(delta) {
  fontSize = Math.max(MIN_FONT, Math.min(MAX_FONT, fontSize + delta));
  document.documentElement.style.setProperty('--font-size', fontSize + 'px');
  const sbFont = document.getElementById('sb-font');
  if (sbFont) sbFont.textContent = fontSize + 'px';
}

// ── Split panes ───────────────────────────────────────────────────────────
function splitPane(direction) {
  if (paneCount >= 4) {
    appendLine(activePaneId, 'Maximum 4 panes supported.\n', 'line-stderr');
    return;
  }

  const container = document.getElementById('pane-container');
  const newId = paneCount;
  paneCount++;

  // Update CSS split class
  container.className = `split-${direction}`;
  splitMode = direction;

  // Create new pane DOM
  const paneDiv = document.createElement('div');
  paneDiv.className = 'pane';
  paneDiv.id = `pane-${newId}`;
  paneDiv.innerHTML = `
    <div class="terminal" id="terminal-${newId}" onclick="focusInput(${newId})">
      <div class="output" id="output-${newId}"></div>
      <div class="input-row" id="input-row-${newId}">
        <span class="prompt-display" id="prompt-${newId}">$ </span>
        <div class="input-wrapper">
          <span class="input-ghost" id="ghost-${newId}"></span>
          <input class="cmd-input" id="cmd-input-${newId}" data-pane="${newId}"
            type="text" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false"/>
        </div>
      </div>
    </div>`;
  container.appendChild(paneDiv);

  // Init pane state + socket
  panes[newId] = {
    history: [], historyIndex: -1, currentInput: '',
    sessionId: null, connected: false, socket: null, cwd: '',
  };
  createSocket(newId);
  setupInputHandlers(newId);
  addTab(newId);
  setActivePane(newId);
  focusInput(newId);
}

// ── Tab management ────────────────────────────────────────────────────────
const tabPaneMap = {};

function addTab(paneId) {
  const tabs = document.getElementById('tabs');
  const id = paneId !== undefined ? paneId : activePaneId;
  const tabEl = document.createElement('div');
  tabEl.className = 'tab' + (id === activePaneId ? ' active' : '');
  tabEl.id = `tab-${id}`;
  tabEl.dataset.pane = id;
  tabEl.innerHTML = `<span>Shell ${id + 1}</span>
    <button class="tab-close" onclick="closeTab(${id})" title="Close">×</button>`;
  tabEl.addEventListener('click', (e) => {
    if (e.target.classList.contains('tab-close')) return;
    setActivePane(id);
  });
  tabs.appendChild(tabEl);
  tabPaneMap[id] = tabEl;
}

function setActivePane(paneId) {
  activePaneId = paneId;
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', parseInt(t.dataset.pane) === paneId);
  });
  document.querySelectorAll('.pane').forEach(p => {
    p.classList.toggle('pane-active', p.id === `pane-${paneId}`);
  });

  const pane = panes[paneId];
  if (pane) {
    const sbCwd = document.getElementById('sb-cwd');
    const tbCwd = document.getElementById('tb-cwd');
    if (sbCwd) sbCwd.textContent = pane.cwd;
    if (tbCwd) tbCwd.textContent = shorten(pane.cwd);
  }
  focusInput(paneId);
}

function closeTab(paneId) {
  if (Object.keys(panes).length <= 1) return;
  const tabEl = tabPaneMap[paneId];
  if (tabEl) tabEl.remove();
  const paneEl = document.getElementById(`pane-${paneId}`);
  if (paneEl) paneEl.remove();
  if (panes[paneId]?.socket) panes[paneId].socket.disconnect();
  delete panes[paneId];
  delete tabPaneMap[paneId];

  const remaining = Object.keys(panes).map(Number);
  if (remaining.length > 0) setActivePane(remaining[0]);

  if (Object.keys(panes).length <= 1) {
    document.getElementById('pane-container').className = '';
    splitMode = null;
  }
}

// ── Misc UI ───────────────────────────────────────────────────────────────
function clearTerminal(paneId) {
  const id = paneId !== undefined ? paneId : activePaneId;
  const out = $output(id);
  if (out) out.innerHTML = '';
}

function focusInput(paneId) {
  const id = paneId !== undefined ? paneId : activePaneId;
  const inp = $input(id);
  if (inp) inp.focus();
}

function updateExitCode(code) {
  const $sbExit = document.getElementById('sb-exit');
  if (!$sbExit) return;
  if (code === 0) {
    $sbExit.textContent = '✓ 0';
    $sbExit.className = 'exit-ok';
  } else {
    $sbExit.textContent = `✗ ${code}`;
    $sbExit.className = 'exit-fail';
  }
}

function shorten(path) {
  if (!path) return '';
  const parts = path.replace(/\\/g, '/').split('/');
  if (parts.length > 3) return '…/' + parts.slice(-2).join('/');
  return path;
}

// ── Theme panel ───────────────────────────────────────────────────────────
function toggleThemePanel() {
  const panel = document.getElementById('theme-panel');
  panel.classList.toggle('hidden');
  if (!panel.classList.contains('hidden')) {
    const themeList = document.getElementById('theme-list');
    if (themeList.children.length === 0) {
      panes[activePaneId].socket?.emit('get_themes');
    }
  }
}

function populateThemes(themes) {
  const list = document.getElementById('theme-list');
  list.innerHTML = '';
  themes.forEach(t => {
    const btn = document.createElement('button');
    btn.className = 'theme-item' + (t === themeState.current ? ' active' : '');
    btn.dataset.theme = t;

    const colors = themeState.colors[t] || {};
    const swatchKeys = ['background', 'prompt_user', 'prompt_cwd', 'prompt_git'];
    const swatchHtml = swatchKeys.map(k => {
      const hex = colorToHex(colors[k]);
      return hex ? `<span class="swatch" style="background:${hex}" title="${k}"></span>` : '';
    }).join('');

    btn.innerHTML = `<span class="theme-swatches">${swatchHtml}</span>${t}`;
    btn.onclick = () => {
      panes[activePaneId].socket?.emit('set_theme', { theme: t });
      document.getElementById('theme-panel').classList.add('hidden');
    };
    list.appendChild(btn);
  });
}

// ── Window controls ───────────────────────────────────────────────────────
let _minimized = false;
function toggleMinimize() {
  _minimized = !_minimized;
  document.getElementById(`terminal-${activePaneId}`).style.display = _minimized ? 'none' : 'flex';
}

let _maximized = false;
function toggleMaximize() {
  _maximized = !_maximized;
  document.getElementById('app').style.borderRadius = _maximized ? '0' : 'var(--radius)';
}

// ── File upload ───────────────────────────────────────────────────────────
function triggerUpload() {
  document.getElementById('file-upload-input').click();
}

function uploadFiles(files) {
  if (!files || !files.length) return;
  Array.from(files).forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = btoa(e.target.result);
      panes[activePaneId].socket?.emit('file_upload', {
        filename: file.name,
        content: content,
        size: file.size,
      });
      appendLine(activePaneId, `Uploading '${escHtml(file.name)}' (${(file.size/1024).toFixed(1)} KB)...\n`, 'line-info');
    };
    reader.readAsBinaryString(file);
  });
}

// Drag-and-drop upload
function setupDragDrop() {
  const container = document.getElementById('pane-container');
  container.addEventListener('dragover', (e) => {
    e.preventDefault();
    container.classList.add('drop-active');
  });
  container.addEventListener('dragleave', () => {
    container.classList.remove('drop-active');
  });
  container.addEventListener('drop', (e) => {
    e.preventDefault();
    container.classList.remove('drop-active');
    uploadFiles(e.dataTransfer.files);
  });
}

// ── Context menu ──────────────────────────────────────────────────────────
function setupContextMenu() {
  const menu = document.getElementById('ctx-menu');
  document.getElementById('pane-container').addEventListener('contextmenu', (e) => {
    e.preventDefault();
    menu.style.left = e.clientX + 'px';
    menu.style.top  = e.clientY + 'px';
    menu.classList.remove('hidden');
  });
  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target)) menu.classList.add('hidden');
  });
}

function ctxCopy() {
  const sel = window.getSelection()?.toString();
  if (sel) navigator.clipboard.writeText(sel);
  document.getElementById('ctx-menu').classList.add('hidden');
}

async function ctxPaste() {
  try {
    const text = await navigator.clipboard.readText();
    const inp = $input(activePaneId);
    if (inp) {
      const pos = inp.selectionStart;
      inp.value = inp.value.slice(0, pos) + text + inp.value.slice(inp.selectionEnd);
      inp.selectionStart = inp.selectionEnd = pos + text.length;
      updateGhost(activePaneId);
    }
  } catch (e) { /* clipboard access denied */ }
  document.getElementById('ctx-menu').classList.add('hidden');
}

// ── Mobile keyboard ───────────────────────────────────────────────────────
function toggleMobileKeyboard() {
  const inp = $input(activePaneId);
  if (!inp) return;
  if (document.activeElement === inp) {
    inp.blur();
  } else {
    inp.focus();
    // On iOS this triggers the virtual keyboard
    inp.click();
  }
}

// Swipe left/right for history on mobile
function setupMobileSwipe() {
  let startX = 0;
  const container = document.getElementById('pane-container');
  container.addEventListener('touchstart', (e) => {
    startX = e.touches[0].clientX;
  }, { passive: true });
  container.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 60) {
      if (dx < 0) historyBack(activePaneId);
      else historyForward(activePaneId);
    }
  }, { passive: true });
}

// ── Boot ──────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // Init primary pane socket
  createSocket(0);
  setupInputHandlers(0);

  // Add initial tab
  addTab(0);
  setActivePane(0);

  // Request themes
  panes[0].socket?.emit('get_themes');

  // Extra setup
  setupDragDrop();
  setupContextMenu();
  setupMobileSwipe();

  focusInput(0);
});
