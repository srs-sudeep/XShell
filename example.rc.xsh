# ~/.xshell/rc.xsh  —  XShell startup file
# Copy to %APPDATA%\XShell\rc.xsh (Windows) or ~/.xshell/rc.xsh (Linux/macOS)
# This file is sourced every time XShell starts.

# ── Theme ──────────────────────────────────────────────────────────────────
# theme set dracula

# ── Environment variables ──────────────────────────────────────────────────
export EDITOR=code
export PAGER=less

# ── Aliases ────────────────────────────────────────────────────────────────
alias ll="ls -l"
alias la="ls -a"
alias lla="ls -la"
alias ..="cd .."
alias ...="cd ../.."
alias gs="gst"
alias gc="gcommit"
alias gp="gpush"
alias gl="glog"

# ── Auto-load plugins ──────────────────────────────────────────────────────
# plugin load z
# plugin load bookmark
# plugin load json
# plugin load npm

# ── Per-project rc example (.xshellrc) ────────────────────────────────────
# Place a .xshellrc file in any project directory.
# XShell will source it automatically when you enter that directory.
# Example .xshellrc:
#   envload .env
#   plugin load npm
#   export NODE_ENV=development

# ── Welcome message ────────────────────────────────────────────────────────
echo "Welcome to XShell! Type 'help' for commands."
