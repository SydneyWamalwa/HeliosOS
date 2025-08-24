class HeliosOS {
    constructor() {
        this.apiBase = '';
        this.token = null;
        this.user = null;
        this.chatHistory = [];
        this.commandHistory = [];
        this.currentHistoryIndex = -1;
        this.maxHistorySize = 100;
        this.systemStats = {};
        this.userType = 'casual';
        this.isAuthenticated = false;

        // User experience preferences
        this.preferences = {
            theme: 'dark',
            language: 'en',
            notifications: true,
            autoSave: true,
            helpMode: true
        };

        // Mock user data for demo
        this.mockUser = {
            id: 'demo-user',
            name: 'Demo User',
            email: 'demo@heliosos.com',
            profile: {
                role: 'casual'
            }
        };

        this.init();
    }

    async init() {
        this.showLoadingScreen();
        this.setupEventListeners();
        this.loadUserPreferences();

        try {
            await this.checkAuth();
            await this.initializeUserExperience();
            this.updateStatus();
            this.startPeriodicUpdates();
            this.hideLoadingScreen();
        } catch (error) {
            console.error('Initialization failed:', error);
            this.hideLoadingScreen();
            this.showAuthRequired();
        }
    }

    showLoadingScreen() {
        const loadingScreen = document.getElementById('desktop-loading');
        if (loadingScreen) {
            loadingScreen.style.display = 'flex';
            loadingScreen.classList.remove('hidden');
        }
    }

    hideLoadingScreen() {
        const loadingScreen = document.getElementById('desktop-loading');
        if (loadingScreen) {
            setTimeout(() => {
                loadingScreen.classList.add('hidden');
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                }, 300);
            }, 1000); // Reduced from 2000ms
        }
    }

    async checkAuth() {
        try {
            const response = await fetch('/api/user/profile');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.user) {
                    this.isAuthenticated = true;
                    this.user = {
                        id: data.user.id,
                        name: data.user.username,
                        email: data.user.email,
                        profile: data.user.profile || { role: 'casual' }
                    };
                    this.updateUserInfo();
                    return true;
                }
            }
            // If not authenticated, redirect to login
            window.location.href = '/auth/login';
            return false;
        } catch (error) {
            console.error('Auth check failed:', error);
            window.location.href = '/auth/login';
            return false;
        }
    }

    updateUserInfo() {
        const userNameEl = document.getElementById('user-name');
        if (userNameEl && this.user) {
            userNameEl.textContent = this.user.name;
        }
    }

    showAuthRequired() {
        // Redirect to login page instead of using mock data
        window.location.href = '/auth/login';
    }

    async initializeUserExperience() {
        this.detectUserType();
        this.customizeInterface();
        this.showWelcomeMessage();
        this.loadQuickActions();
    }

    detectUserType() {
        const profile = this.user?.profile || {};

        if (profile.role) {
            this.userType = profile.role;
        } else if (profile.organization) {
            this.userType = 'business';
        } else if (profile.education) {
            this.userType = 'student';
        } else {
            this.userType = 'casual';
        }

        console.log(`User type detected: ${this.userType}`);
    }

    customizeInterface() {
        const body = document.body;
        body.classList.add(`user-type-${this.userType}`);
        this.updateQuickCommands();
        this.updateAssistantPersonality();
    }

    updateQuickCommands() {
        const quickSelect = document.getElementById('quick-select');
        if (!quickSelect) return;

        const commands = {
            business: [
                { value: 'df -h', label: 'df -h - Check disk space (Monitor storage usage)' },
                { value: 'ps aux | head -20', label: 'ps aux - List processes (See running applications)' },
                { value: 'free -h', label: 'free -h - Memory usage (Check RAM usage)' },
                { value: 'uptime', label: 'uptime - System uptime (Check system stability)' },
                { value: 'whoami', label: 'whoami - Current user (Verify user context)' },
                { value: 'pwd', label: 'pwd - Current directory (Show current location)' },
                { value: 'ls -la', label: 'ls -la - List files (Detailed file listing)' }
            ],
            student: [
                { value: 'whoami', label: 'whoami - Who am I? (Show current user)' },
                { value: 'pwd', label: 'pwd - Where am I? (Show current folder)' },
                { value: 'ls -la', label: 'ls -la - What\'s here? (List all files and details)' },
                { value: 'date', label: 'date - What time is it? (Show current date/time)' },
                { value: 'uptime', label: 'uptime - How long running? (System uptime)' },
                { value: 'df -h', label: 'df -h - Storage space (Check available disk space)' },
                { value: 'free -h', label: 'free -h - Memory usage (Check RAM usage)' }
            ],
            casual: [
                { value: 'whoami', label: 'whoami - See current user' },
                { value: 'ls', label: 'ls - List files in current folder' },
                { value: 'pwd', label: 'pwd - Show current folder path' },
                { value: 'date', label: 'date - Show current date and time' },
                { value: 'df -h', label: 'df -h - Check disk space' },
                { value: 'free -h', label: 'free -h - Check memory usage' }
            ]
        };

        const userCommands = commands[this.userType] || commands.casual;

        // Clear existing options except the first one
        while (quickSelect.children.length > 1) {
            quickSelect.removeChild(quickSelect.lastChild);
        }

        userCommands.forEach(cmd => {
            const option = document.createElement('option');
            option.value = cmd.value;
            option.textContent = cmd.label;
            quickSelect.appendChild(option);
        });
    }

    updateAssistantPersonality() {
        const personalities = {
            business: {
                greeting: "Hello! I'm Leo, your AI assistant. I'm here to help you manage your business tasks efficiently. I can help with system monitoring, file management, and productivity tasks.",
                style: 'professional'
            },
            student: {
                greeting: "Hi there! I'm Leo, your friendly AI tutor. I'm here to help you learn and navigate HeliosOS. Don't worry - I'll explain everything step by step!",
                style: 'educational'
            },
            casual: {
                greeting: "Hey! I'm Leo, your AI buddy. I'm here to make using HeliosOS easy and fun. Just ask me anything - I'll help you get things done!",
                style: 'friendly'
            }
        };

        this.assistantPersonality = personalities[this.userType] || personalities.casual;
    }

    showWelcomeMessage() {
        const welcomeMsg = this.getWelcomeMessage();
        setTimeout(() => {
            this.addChatMessage('assistant', welcomeMsg);
        }, 500);
    }

    getWelcomeMessage() {
        const messages = {
            business: "Welcome to HeliosOS! I'm optimized to help you with professional tasks. Try asking me to summarize documents, monitor system resources, or run diagnostic commands. What can I help you accomplish today?",
            student: "Welcome to your learning environment! I'm here to help you understand how operating systems work. You can ask me questions, run safe commands to explore the system, or request explanations. What would you like to learn about first?",
            casual: "Welcome to HeliosOS! I'm here to make your computing experience smooth and enjoyable. You can chat with me, ask me to summarize text, or run system commands. What would you like to do?"
        };

        return messages[this.userType] || messages.casual;
    }

    loadQuickActions() {
        const quickActions = this.getQuickActions();
        this.displayQuickActions(quickActions);
    }

    getQuickActions() {
        const actions = {
            business: [
                { icon: '📊', title: 'System Report', action: () => this.generateSystemReport() },
                { icon: '📁', title: 'File Management', action: () => this.showFileManager() },
                { icon: '⚙️', title: 'Process Monitor', action: () => this.showProcessMonitor() },
                { icon: '📝', title: 'Document Summary', action: () => this.focusOnSummarizer() }
            ],
            student: [
                { icon: '🎓', title: 'Learning Mode', action: () => this.enableLearningMode() },
                { icon: '❓', title: 'Help & Tutorial', action: () => this.showTutorial() },
                { icon: '🔍', title: 'Explore System', action: () => this.startExploration() },
                { icon: '📖', title: 'Command Guide', action: () => this.showCommandGuide() }
            ],
            casual: [
                { icon: '💬', title: 'Chat with Leo', action: () => this.focusOnChat() },
                { icon: '📄', title: 'Summarize Text', action: () => this.focusOnSummarizer() },
                { icon: '⚡', title: 'Quick Commands', action: () => this.showQuickCommands() },
                { icon: '🎨', title: 'Customize', action: () => this.showCustomization() }
            ]
        };

        return actions[this.userType] || actions.casual;
    }

    displayQuickActions(actions) {
        console.log('Quick actions loaded:', actions);
    }

    setupEventListeners() {
        this.setupChatListeners();
        this.setupCommandListeners();
        this.setupAuthListeners();
        this.setupKeyboardShortcuts();
        this.setupTabListeners();
    }

    setupChatListeners() {
        const chatInput = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-btn');
        const summarizeBtn = document.getElementById('summarize-btn');

        if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                } else if (e.key === 'Enter' && e.shiftKey) {
                    return;
                }
            });

            chatInput.addEventListener('input', () => {
                this.autoResizeTextarea(chatInput);
            });
        }

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendChatMessage());
        }

        if (summarizeBtn) {
            summarizeBtn.addEventListener('click', () => this.summarizeText());
        }
    }

    setupCommandListeners() {
        const cmdInput = document.getElementById('cmd-input');
        const runBtn = document.getElementById('run-btn');
        const quickSelect = document.getElementById('quick-select');

        if (cmdInput) {
            cmdInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.executeCommand();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.navigateCommandHistory(-1);
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.navigateCommandHistory(1);
                } else if (e.key === 'Tab') {
                    e.preventDefault();
                    this.autoCompleteCommand();
                }
            });
        }

        if (runBtn) {
            runBtn.addEventListener('click', () => this.executeCommand());
        }

        if (quickSelect) {
            quickSelect.addEventListener('change', (e) => {
                if (e.target.value && cmdInput) {
                    cmdInput.value = e.target.value;
                    cmdInput.focus();
                }
            });
        }
    }

    setupAuthListeners() {
        const loginBtn = document.getElementById('login-btn');
        const logoutBtn = document.getElementById('logout-btn');

        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.showLoginDialog());
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Enter to send chat message
            if (e.ctrlKey && e.key === 'Enter') {
                this.sendChatMessage();
            }

            // Ctrl+` to focus on command input
            if (e.ctrlKey && e.key === '`') {
                e.preventDefault();
                const cmdInput = document.getElementById('cmd-input');
                if (cmdInput) {
                    cmdInput.focus();
                    this.switchToTab('command');
                }
            }

            // Ctrl+/ to focus on chat input
            if (e.ctrlKey && e.key === '/') {
                e.preventDefault();
                const chatInput = document.getElementById('chat-input');
                if (chatInput) {
                    chatInput.focus();
                    this.switchToTab('chat');
                }
            }
        });
    }

    setupTabListeners() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchToTab(tab.dataset.tab);
            });
        });
    }

    switchToTab(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        // Add active class to target tab and content
        const targetTab = document.querySelector(`[data-tab="${tabName}"]`);
        const targetContent = document.getElementById(`${tabName}-tab`);

        if (targetTab && targetContent) {
            targetTab.classList.add('active');
            targetContent.classList.add('active');
        }
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    async sendChatMessage() {
        const chatInput = document.getElementById('chat-input');
        if (!chatInput || !chatInput.value.trim()) return;

        const message = chatInput.value.trim();
        chatInput.value = '';
        this.autoResizeTextarea(chatInput);

        // Add user message to chat
        this.addChatMessage('user', message);

        // Store in chat history
        this.chatHistory.push({ role: 'user', content: message, timestamp: new Date() });

        try {
            // Send to backend API
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: this.chatHistory.slice(-10).map(msg => ({
                        role: msg.role === 'assistant' ? 'assistant' : 'user',
                        content: msg.content
                    }))
                })
            });

            const data = await response.json();

            if (data.success && data.response) {
                this.addChatMessage('assistant', data.response);
                this.chatHistory.push({ role: 'assistant', content: data.response, timestamp: new Date() });
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addChatMessage('assistant', 'Sorry, I encountered an error. Please try again.');
        }
    }

    async summarizeText() {
        const chatInput = document.getElementById('chat-input');
        if (!chatInput || !chatInput.value.trim()) {
            this.addChatMessage('assistant', 'Please paste the text you\'d like me to summarize in the chat input field.');
            return;
        }

        const text = chatInput.value.trim();
        this.addChatMessage('user', 'Please summarize: ' + text.substring(0, 100) + '...');

        try {
            const response = await fetch('/api/ai/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text })
            });

            const data = await response.json();

            if (data.success && data.summary) {
                this.addChatMessage('assistant', `**Summary** (${data.original_length} → ${data.summary_length} words, ${data.compression_ratio}:1 ratio):\n\n${data.summary}`);
            } else {
                throw new Error(data.error || 'Summarization failed');
            }

            chatInput.value = '';
            this.autoResizeTextarea(chatInput);
        } catch (error) {
            console.error('Summarization error:', error);
            this.addChatMessage('assistant', 'Sorry, I couldn\'t generate a summary. Please try again.');
        }
    }

    addChatMessage(sender, content) {
        const chatContainer = document.getElementById('chat-container');
        if (!chatContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const avatar = sender === 'user' ? '👤' : '🤖';
        const time = new Date().toLocaleTimeString();

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div>
                <div class="message-content">${this.formatMessage(content)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        chatContainer.appendChild(messageDiv);

        // Auto-scroll to bottom
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 100);
    }

    formatMessage(content) {
        // Basic formatting for messages
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    async executeCommand() {
        const cmdInput = document.getElementById('cmd-input');
        if (!cmdInput || !cmdInput.value.trim()) return;

        const command = cmdInput.value.trim();

        // Add to command history
        this.commandHistory.push(command);
        if (this.commandHistory.length > this.maxHistorySize) {
            this.commandHistory.shift();
        }
        this.currentHistoryIndex = this.commandHistory.length;

        // Clear input
        cmdInput.value = '';

        try {
            const response = await fetch('/api/exec', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command })
            });

            const data = await response.json();

            if (data.success) {
                this.displayCommandResult(command, {
                    output: data.output,
                    exitCode: data.exit_code,
                    executionTime: data.execution_time
                });
            } else {
                throw new Error(data.error || 'Command execution failed');
            }
        } catch (error) {
            console.error('Command execution error:', error);
            this.displayCommandResult(command, {
                output: 'Command execution failed: ' + error.message,
                exitCode: 1,
                error: true
            });
        }
    }

    displayCommandResult(command, result) {
        const cmdOutput = document.getElementById('cmd-output');
        if (!cmdOutput) return;

        // Remove placeholder text if it exists
        if (cmdOutput.children.length === 1 && cmdOutput.children[0].style.textAlign === 'center') {
            cmdOutput.innerHTML = '';
        }

        const resultDiv = document.createElement('div');
        resultDiv.className = 'command-result';

        const timestamp = new Date().toLocaleTimeString();
        const exitCodeClass = result.exitCode === 0 ? 'success' : 'error';

        resultDiv.innerHTML = `
            <div class="command-header">
                <span class="command-text">$ ${command}</span>
                <span class="command-time">${timestamp}</span>
            </div>
            <div class="command-body">
                <pre class="command-output-text">${result.output || 'No output'}</pre>
            </div>
            <div class="command-footer">
                <span>Execution time: ${result.executionTime || 'N/A'}ms</span>
                <span class="exit-code ${exitCodeClass}">Exit code: ${result.exitCode}</span>
            </div>
        `;

        cmdOutput.insertBefore(resultDiv, cmdOutput.firstChild);

        // Limit number of displayed results
        while (cmdOutput.children.length > 10) {
            cmdOutput.removeChild(cmdOutput.lastChild);
        }
    }

    navigateCommandHistory(direction) {
        if (this.commandHistory.length === 0) return;

        const cmdInput = document.getElementById('cmd-input');
        if (!cmdInput) return;

        this.currentHistoryIndex += direction;

        if (this.currentHistoryIndex < 0) {
            this.currentHistoryIndex = 0;
        } else if (this.currentHistoryIndex >= this.commandHistory.length) {
            this.currentHistoryIndex = this.commandHistory.length;
            cmdInput.value = '';
            return;
        }

        cmdInput.value = this.commandHistory[this.currentHistoryIndex];
    }

    autoCompleteCommand() {
        const cmdInput = document.getElementById('cmd-input');
        if (!cmdInput) return;

        const currentCmd = cmdInput.value;
        const commonCommands = ['whoami', 'pwd', 'ls', 'ls -la', 'date', 'uptime', 'df -h', 'free -h', 'ps aux'];

        const matches = commonCommands.filter(cmd =>
            cmd.startsWith(currentCmd.toLowerCase())
        );

        if (matches.length === 1) {
            cmdInput.value = matches[0];
        } else if (matches.length > 1) {
            this.displayCommandResult(`tab completion for "${currentCmd}"`, {
                output: 'Possible completions:\n' + matches.join('\n'),
                exitCode: 0
            });
        }
    }

    updateStatus() {
        const statusIndicator = document.getElementById('status-indicator');
        if (statusIndicator) {
            statusIndicator.style.background = this.isAuthenticated ? '#10b981' : '#ef4444';
        }
    }

    startPeriodicUpdates() {
        // Update system stats every 5 seconds
        setInterval(() => {
            this.updateSystemStats();
        }, 5000);

        // Update session time every minute
        setInterval(() => {
            this.updateSessionTime();
        }, 60000);
    }

    updateSystemStats() {
        // Generate realistic fluctuating stats
        const cpuUsage = Math.floor(Math.random() * 30) + 20; // 20-50%
        const memoryUsage = Math.floor(Math.random() * 20) + 50; // 50-70%
        const diskUsage = Math.floor(Math.random() * 5) + 20; // 20-25%

        const cpuEl = document.getElementById('cpu-usage');
        const memEl = document.getElementById('memory-usage');
        const diskEl = document.getElementById('disk-usage');

        if (cpuEl) cpuEl.innerHTML = `${cpuUsage}<span class="system-unit">%</span>`;
        if (memEl) memEl.innerHTML = `${memoryUsage}<span class="system-unit">%</span>`;
        if (diskEl) diskEl.innerHTML = `${diskUsage}<span class="system-unit">%</span>`;

        // Store stats for API calls
        this.systemStats = { cpuUsage, memoryUsage, diskUsage };
    }

    updateSessionTime() {
        const sessionEl = document.getElementById('session-time');
        if (sessionEl) {
            const now = new Date();
            const sessionStart = this.sessionStartTime || now;
            const diff = now - sessionStart;
            const hours = Math.floor(diff / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);

            sessionEl.textContent = `${hours} hours, ${minutes} minutes`;
        }
    }

    loadUserPreferences() {
        // In production, load from server
        console.log('User preferences loaded:', this.preferences);
    }

    // Utility methods for UI interactions
    refreshDesktop() {
        const loadingOverlay = document.getElementById('desktop-loading');
        const desktopFrame = document.getElementById('desktop-frame');

        if (loadingOverlay && desktopFrame) {
            loadingOverlay.style.display = 'flex';
            desktopFrame.src = desktopFrame.src; // Reload iframe

            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 3000);
        }

        this.showNotification('Desktop refreshed successfully', 'success');
    }

    toggleFullscreen() {
        const desktopContainer = document.querySelector('.desktop-container');

        if (document.fullscreenElement) {
            document.exitFullscreen().catch(err => {
                console.error('Error exiting fullscreen:', err);
            });
        } else if (desktopContainer) {
            desktopContainer.requestFullscreen().catch(err => {
                console.error('Error entering fullscreen:', err);
                this.showNotification('Fullscreen not supported', 'warning');
            });
        }
    }

    showSettings() {
        this.addChatMessage('assistant', 'Settings panel is coming soon! You can customize themes, notifications, and other preferences.');
        this.switchToTab('chat');
    }

    logout() {
        if (confirm('Are you sure you want to logout?')) {
            this.isAuthenticated = false;
            this.user = null;
            this.token = null;
            this.chatHistory = [];
            this.commandHistory = [];

            // Reset UI
            this.updateUserInfo();
            this.updateStatus();

            // Clear chat
            const chatContainer = document.getElementById('chat-container');
            if (chatContainer) {
                chatContainer.innerHTML = '';
            }

            // Clear command output
            const cmdOutput = document.getElementById('cmd-output');
            if (cmdOutput) {
                cmdOutput.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 40px;">Logged out. Please login to continue.</div>';
            }

            this.showNotification('Logged out successfully', 'success');
        }
    }

    showLoginDialog() {
        // Redirect to login page
        window.location.href = '/auth/login';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--bg-card, #334155);
            border: 1px solid var(--border, #475569);
            border-radius: 8px;
            padding: 16px 20px;
            color: var(--text-primary, #f8fafc);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            z-index: 1000;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;

        // Add type-specific styling
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        notification.style.borderLeftColor = colors[type] || colors.info;
        notification.style.borderLeftWidth = '4px';

        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="color: ${colors[type] || colors.info};">
                    ${type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ'}
                </div>
                <div>${message}</div>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: var(--text-muted, #94a3b8); cursor: pointer; margin-left: auto;">×</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    // Quick action methods
    generateSystemReport() {
        this.executeCommand('df -h');
        setTimeout(() => this.executeCommand('free -h'), 500);
        setTimeout(() => this.executeCommand('uptime'), 1000);
        this.switchToTab('command');
        this.addChatMessage('assistant', 'System report generated! Check the Commands tab for detailed information.');
    }

    showFileManager() {
        this.executeCommand('ls -la');
        this.switchToTab('command');
        this.addChatMessage('assistant', 'File manager view loaded. Use commands like "ls -la" to explore directories.');
    }

    showProcessMonitor() {
        this.executeCommand('ps aux');
        this.switchToTab('command');
        this.addChatMessage('assistant', 'Process monitor loaded. Here are the currently running processes.');
    }

    focusOnSummarizer() {
        this.switchToTab('chat');
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.focus();
            chatInput.placeholder = 'Paste the text you want me to summarize here...';
        }
        this.addChatMessage('assistant', 'Ready to summarize! Paste your text and click the "Summarize" button.');
    }

    enableLearningMode() {
        this.switchToTab('chat');
        this.addChatMessage('assistant', `Welcome to Learning Mode! 🎓

I'm here to help you understand operating systems and command-line interfaces. Here's what we can explore:

**Basic Commands:**
• \`whoami\` - Shows your current user
• \`pwd\` - Shows current directory path
• \`ls\` - Lists files and folders
• \`date\` - Shows current date/time

**System Information:**
• \`uptime\` - How long the system has been running
• \`free -h\` - Memory usage information
• \`df -h\` - Disk space information

Try any of these commands in the Commands tab, and I'll explain what they do!`);
    }

    showTutorial() {
        this.switchToTab('chat');
        this.addChatMessage('assistant', `📖 **HeliosOS Tutorial**

**Getting Started:**
1. **Chat Tab** - Ask me questions, get help, or request summaries
2. **Commands Tab** - Run safe system commands to explore
3. **System Tab** - View real-time system statistics

**Keyboard Shortcuts:**
• Ctrl+/ - Focus on chat input
• Ctrl+\` - Focus on command input
• Ctrl+Enter - Send chat message

**Tips:**
• Use the Quick Commands dropdown for common tasks
• Press Tab in command input for auto-completion
• Use arrow keys to navigate command history

What would you like to learn more about?`);
    }

    startExploration() {
        this.switchToTab('command');
        this.addChatMessage('assistant', `🔍 **System Exploration Mode**

Let's start exploring your system! I'll run some basic commands to show you around:

1. First, let's see who you are and where you are
2. Then we'll look at what files are available
3. Finally, we'll check system status

Watch the Commands tab as I run these for you:`);

        setTimeout(() => this.executeCommand('whoami'), 1000);
        setTimeout(() => this.executeCommand('pwd'), 2000);
        setTimeout(() => this.executeCommand('ls -la'), 3000);
        setTimeout(() => this.executeCommand('uptime'), 4000);
    }

    showCommandGuide() {
        this.switchToTab('chat');
        this.addChatMessage('assistant', `📋 **Command Guide**

**File & Directory Commands:**
• \`ls\` - List files in current directory
• \`ls -la\` - List files with detailed info (including hidden files)
• \`pwd\` - Print working directory (show current path)

**System Information:**
• \`whoami\` - Show current username
• \`date\` - Show current date and time
• \`uptime\` - Show system uptime and load
• \`free -h\` - Show memory usage (human readable)
• \`df -h\` - Show disk space usage (human readable)
• \`ps aux\` - Show running processes

**Navigation Tips:**
• Use ↑/↓ arrow keys to browse command history
• Press Tab for command auto-completion
• Use the Quick Commands dropdown for easy access

**Safety Note:** Only safe, read-only commands are allowed in demo mode.

Try any command in the Commands tab!`);
    }

    focusOnChat() {
        this.switchToTab('chat');
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            chatInput.focus();
            chatInput.placeholder = 'Ask Leo anything about HeliosOS...';
        }
        this.addChatMessage('assistant', 'Hi there! I\'m ready to chat. Ask me about HeliosOS, request help with tasks, or just have a conversation!');
    }

    showQuickCommands() {
        this.switchToTab('command');
        this.addChatMessage('assistant', `⚡ **Quick Commands**

Use the dropdown menu in the Commands tab to quickly access common commands:

**Most Popular:**
• Check who you are: \`whoami\`
• See current location: \`pwd\`
• List files: \`ls\` or \`ls -la\`
• Check disk space: \`df -h\`
• Check memory: \`free -h\`
• System uptime: \`uptime\`

Just select from the dropdown and press Enter to run!`);
    }

    showCustomization() {
        this.switchToTab('chat');
        this.addChatMessage('assistant', `🎨 **Customization Options**

HeliosOS can be customized to match your preferences:

**Available Themes:**
• Dark Theme (current)
• Light Theme (coming soon)
• High Contrast (coming soon)

**User Types:**
• **Casual** - Simple, friendly interface
• **Student** - Educational focus with explanations
• **Business** - Professional tools and monitoring

**Other Settings:**
• Notification preferences
• Auto-save options
• Help mode toggle
• Language preferences

Full customization panel coming soon! For now, your experience is optimized for ${this.userType} users.`);
    }
}

// Initialize HeliosOS when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Add CSS animations if not already present
    if (!document.querySelector('#notification-animations')) {
        const style = document.createElement('style');
        style.id = 'notification-animations';
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }

            .chat-container {
                max-height: 400px;
                overflow-y: auto;
            }
        `;
        document.head.appendChild(style);
    }

    // Initialize HeliosOS
    window.heliosOS = new HeliosOS();

    // Make methods available globally for onclick handlers
    window.refreshDesktop = () => window.heliosOS.refreshDesktop();
    window.toggleFullscreen = () => window.heliosOS.toggleFullscreen();
    window.showSettings = () => window.heliosOS.showSettings();
    window.logout = () => window.heliosOS.logout();

    // Session start time tracking
    window.heliosOS.sessionStartTime = new Date();

    console.log('HeliosOS initialized successfully');
});