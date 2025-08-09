class HeliosOS {
    constructor() {
        this.apiBase = '/api';
        this.token = localStorage.getItem('helios_token');
        this.user = null;
        this.chatHistory = [];
        this.commandHistory = [];
        this.currentHistoryIndex = -1;
        this.maxHistorySize = 50;

        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.checkAuth();
        this.loadUserPreferences();
        this.updateStatus();

        // Auto-refresh status every 30 seconds
        setInterval(() => this.updateStatus(), 30000);

        // Auto-save preferences every minute
        setInterval(() => this.saveUserPreferences(), 60000);
    }

    setupEventListeners() {
        // Chat functionality
        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');
        const summarizeBtn = document.getElementById('summarize-btn');

        // Command execution
        const runBtn = document.getElementById('run-btn');
        const cmdInput = document.getElementById('cmd-input');
        const quickSelect = document.getElementById('quick-select');

        // Auth
        const loginBtn = document.getElementById('login-btn');
        const registerBtn = document.getElementById('register-btn');
        const logoutBtn = document.getElementById('logout-btn');

        // Use the elements that exist in the current template
        // For chat functionality
        if (!sendBtn && document.getElementById('send')) {
            document.getElementById('send').addEventListener('click', () => this.sendChatMessage());
        } else if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendChatMessage());
        }

        if (!chatInput && document.getElementById('input')) {
            const input = document.getElementById('input');
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        } else if (chatInput) {
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendChatMessage();
                }
            });
        }

        if (summarizeBtn) {
            summarizeBtn.addEventListener('click', () => this.summarizeText());
        }

        if (runBtn && cmdInput) {
            runBtn.addEventListener('click', () => this.executeCommand());
            cmdInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.executeCommand();
                }
                if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    this.navigateCommandHistory(-1);
                }
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.navigateCommandHistory(1);
                }
            });
        }

        if (quickSelect) {
            quickSelect.addEventListener('change', (e) => {
                if (e.target.value && cmdInput) {
                    cmdInput.value = e.target.value;
                    e.target.value = '';
                }
            });
        }

        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.showLoginDialog());
        }

        if (registerBtn) {
            registerBtn.addEventListener('click', () => this.showRegisterDialog());
        }

        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    async checkAuth() {
        if (!this.token) {
            this.showAuthRequired();
            return false;
        }

        try {
            const response = await this.apiCall('/auth/me', 'GET');
            if (response.success) {
                this.user = response.user;
                this.showMainInterface();
                return true;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
        }

        this.showAuthRequired();
        return false;
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        const url = `${this.apiBase}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}`);
            }

            return result;

        } catch (error) {
            console.error(`API call failed: ${method} ${endpoint}`, error);
            throw error;
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('chat-input') || document.getElementById('input');
        if (!input) return;

        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addChatMessage('user', message);
        this.chatHistory.push({role: 'user', content: message});

        // Clear input
        input.value = '';

        // Show typing indicator
        const typingId = this.addChatMessage('assistant', 'Leo is thinking...', true);

        try {
            const response = await this.apiCall('/ai/chat', 'POST', {
                messages: this.chatHistory.slice(-10) // Last 10 messages
            });

            // Remove typing indicator
            this.removeChatMessage(typingId);

            // Add Leo's response
            this.addChatMessage('assistant', response.response);
            this.chatHistory.push({role: 'assistant', content: response.response});

            // Trim history if too long
            if (this.chatHistory.length > this.maxHistorySize) {
                this.chatHistory = this.chatHistory.slice(-this.maxHistorySize);
            }

        } catch (error) {
            this.removeChatMessage(typingId);
            this.addChatMessage('assistant', `Sorry, I encountered an error: ${error.message}`, false, 'error');
        }
    }

    async summarizeText() {
        const input = document.getElementById('chat-input') || document.getElementById('input');
        if (!input) return;

        const text = input.value.trim();

        if (!text) {
            this.showNotification('Please enter text to summarize', 'warning');
            return;
        }

        // Show loading state
        const summarizeBtn = document.getElementById('summarize-btn') || document.getElementById('summarize');
        if (!summarizeBtn) return;

        const originalText = summarizeBtn.textContent;
        summarizeBtn.textContent = 'Summarizing...';
        summarizeBtn.disabled = true;

        try {
            const response = await this.apiCall('/ai/summarize', 'POST', {text});

            // Add summary to chat
            this.addChatMessage('assistant', `📝 **Summary:** ${response.summary}`);
            this.addChatMessage('assistant', `📊 Compression: ${response.compression_ratio}x (${response.original_length} → ${response.summary_length} chars)`);

            // Clear input
            input.value = '';

        } catch (error) {
            this.addChatMessage('assistant', `Failed to summarize: ${error.message}`, false, 'error');
        } finally {
            summarizeBtn.textContent = originalText;
            summarizeBtn.disabled = false;
        }
    }

    async executeCommand() {
        const input = document.getElementById('cmd-input') || document.getElementById('command');
        if (!input) return;

        const command = input.value.trim();

        if (!command) {
            this.showNotification('Please enter a command', 'warning');
            return;
        }

        // Show loading state
        const runBtn = document.getElementById('run-btn') || document.getElementById('run');
        if (!runBtn) return;

        const originalText = runBtn.textContent;
        runBtn.textContent = 'Running...';
        runBtn.disabled = true;

        try {
            const response = await this.apiCall('/exec', 'POST', {command});

            // Add command and output to display
            this.addCommandToOutput(command, response.output, response.exit_code);

            // Clear input
            input.value = '';

            // Add to command history
            this.commandHistory.push(command);
            if (this.commandHistory.length > this.maxHistorySize) {
                this.commandHistory = this.commandHistory.slice(-this.maxHistorySize);
            }

            // Reset history index
            this.currentHistoryIndex = -1;

        } catch (error) {
            this.addCommandToOutput(command, `Error: ${error.message}`, 1);
        } finally {
            runBtn.textContent = originalText;
            runBtn.disabled = false;
        }
    }

    navigateCommandHistory(direction) {
        if (this.commandHistory.length === 0) return;

        const input = document.getElementById('cmd-input');
        if (!input) return;

        if (direction === -1) { // Up arrow
            this.currentHistoryIndex = Math.min(
                this.currentHistoryIndex + 1,
                this.commandHistory.length - 1
            );
        } else { // Down arrow
            this.currentHistoryIndex = Math.max(this.currentHistoryIndex - 1, -1);
        }

        if (this.currentHistoryIndex >= 0) {
            const historyIndex = this.commandHistory.length - 1 - this.currentHistoryIndex;
            input.value = this.commandHistory[historyIndex];
        } else {
            input.value = '';
        }
    }

    addChatMessage(role, content, isTemporary = false, type = 'normal') {
        const chat = document.getElementById('chat-container');
        if (!chat) return null;

        const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `chat-message ${role} ${type}`;

        const avatar = role === 'user' ? '👤' : '🤖';
        const timestamp = new Date().toLocaleTimeString();

        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="avatar">${avatar}</span>
                <span class="role">${role === 'user' ? 'You' : 'Leo'}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;

        chat.appendChild(messageDiv);
        chat.scrollTop = chat.scrollHeight;

        return isTemporary ? messageId : null;
    }

    removeChatMessage(messageId) {
        if (!messageId) return;
        const element = document.getElementById(messageId);
        if (element) {
            element.remove();
        }
    }

    addCommandToOutput(command, output, exitCode) {
        const container = document.getElementById('cmd-output');
        if (!container) {
            // If no dedicated output container, add to chat
            this.addChatMessage('assistant', `Command: \`${command}\`\n\nOutput:\n\`\`\`\n${output}\n\`\`\`\n\nExit code: ${exitCode}`, false, exitCode === 0 ? 'normal' : 'error');
            return;
        }

        const outputDiv = document.createElement('div');
        outputDiv.className = `command-output ${exitCode === 0 ? 'success' : 'error'}`;

        const timestamp = new Date().toLocaleTimeString();

        outputDiv.innerHTML = `
            <div class="command-header">
                <span class="command-text">$ ${command}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <pre class="command-result">${this.escapeHtml(output)}</pre>
            <div class="command-footer">
                <span class="exit-code">Exit code: ${exitCode}</span>
            </div>
        `;

        container.appendChild(outputDiv);
        container.scrollTop = container.scrollHeight;

        // Limit output history
        while (container.children.length > 100) {
            container.removeChild(container.firstChild);
        }
    }

    formatMessage(content) {
        // Simple markdown-like formatting with HTML escaping
        return this.escapeHtml(content)
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async updateStatus() {
        try {
            const response = await fetch('/health');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const status = await response.json();

            const statusElement = document.getElementById('system-status');
            if (statusElement) {
                statusElement.textContent = status.status;
                statusElement.className = `status ${status.status}`;
            }

            // Update component statuses with null checks
            if (status.components) {
                if (status.components.database) {
                    this.updateComponentStatus('db-status', status.components.database);
                }

                if (status.components.ai_service && status.components.ai_service.status) {
                    this.updateComponentStatus('ai-status', status.components.ai_service.status);
                }
            }

        } catch (error) {
            console.error('Status update failed:', error);
            const statusElement = document.getElementById('system-status');
            if (statusElement) {
                statusElement.textContent = 'error';
                statusElement.className = 'status error';
            }

            // Set component statuses to error
            this.updateComponentStatus('db-status', 'error');
            this.updateComponentStatus('ai-status', 'error');
        }
    }

    updateComponentStatus(elementId, status) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = status;
            element.className = `component-status ${status}`;
        }
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span>${this.escapeHtml(message)}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;

        // Find or create notifications container
        let container = document.getElementById('notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 300px;
            `;
            document.body.appendChild(container);
        }

        container.appendChild(notification);

        // Auto-remove notification
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }

    async login(username, password) {
        try {
            const response = await this.apiCall('/auth/login', 'POST', {
                username,
                password
            });

            if (response.success) {
                this.token = response.token;
                this.user = response.user;
                localStorage.setItem('helios_token', this.token);

                this.showMainInterface();
                this.showNotification('Login successful!', 'success');

                return true;
            }
        } catch (error) {
            this.showNotification(`Login failed: ${error.message}`, 'error');
            return false;
        }
    }

    async register(username, password, email = '') {
        try {
            const response = await this.apiCall('/auth/register', 'POST', {
                username,
                password,
                email
            });

            if (response.success) {
                this.token = response.token;
                this.user = response.user;
                localStorage.setItem('helios_token', this.token);

                this.showMainInterface();
                this.showNotification('Registration successful!', 'success');

                return true;
            }
        } catch (error) {
            this.showNotification(`Registration failed: ${error.message}`, 'error');
            return false;
        }
    }

    logout() {
        localStorage.removeItem('helios_token');
        this.token = null;
        this.user = null;
        this.chatHistory = [];
        this.commandHistory = [];

        this.showAuthRequired();
        this.showNotification('Logged out successfully', 'info');
    }

    showAuthRequired() {
        const authContainer = document.getElementById('auth-container');
        const mainContainer = document.getElementById('main-container');

        if (authContainer) {
            authContainer.style.display = 'flex';
        }

        if (mainContainer) {
            mainContainer.style.display = 'none';
        }
    }

    showMainInterface() {
        const authContainer = document.getElementById('auth-container');
        const mainContainer = document.getElementById('main-container');

        if (authContainer) {
            authContainer.style.display = 'none';
        }

        if (mainContainer) {
            mainContainer.style.display = 'grid';
        }

        // Update user info
        const userInfo = document.getElementById('user-info');
        if (userInfo && this.user) {
            userInfo.textContent = `Welcome, ${this.user.username}`;
        }
    }

    loadUserPreferences() {
        const prefs = localStorage.getItem('helios_preferences');
        if (prefs) {
            try {
                const preferences = JSON.parse(prefs);
                this.applyPreferences(preferences);
            } catch (error) {
                console.error('Failed to load preferences:', error);
            }
        }
    }

    saveUserPreferences() {
        if (!this.user) return;

        const preferences = {
            theme: document.body.className,
            chatHistory: this.chatHistory.slice(-20), // Save last 20 messages
            timestamp: Date.now()
        };

        try {
            localStorage.setItem('helios_preferences', JSON.stringify(preferences));
        } catch (error) {
            console.error('Failed to save preferences:', error);
        }
    }

    applyPreferences(preferences) {
        if (preferences.theme) {
            document.body.className = preferences.theme;
        }

        if (preferences.chatHistory && Array.isArray(preferences.chatHistory)) {
            this.chatHistory = preferences.chatHistory;
            this.renderChatHistory();
        }
    }

    renderChatHistory() {
        const chat = document.getElementById('chat-container');
        if (!chat) return;

        chat.innerHTML = '';

        for (const message of this.chatHistory) {
            this.addChatMessage(message.role, message.content);
        }
    }

    async loadAuditData() {
        try {
            const [commandAudit, aiAudit] = await Promise.all([
                this.apiCall('/audit/commands?per_page=20'),
                this.apiCall('/audit/ai?per_page=20')
            ]);

            this.renderCommandAudit(commandAudit.audits || []);
            this.renderAIAudit(aiAudit.interactions || []);

        } catch (error) {
            console.error('Failed to load audit data:', error);
        }
    }

    renderCommandAudit(audits) {
        const container = document.getElementById('command-audit');
        if (!container) return;

        container.innerHTML = audits.map(audit => `
            <div class="audit-item ${audit.return_code === 0 ? 'success' : 'error'}">
                <div class="audit-header">
                    <code>${this.escapeHtml(audit.command)}</code>
                    <span class="timestamp">${new Date(audit.created_at).toLocaleString()}</span>
                </div>
                <div class="audit-details">
                    <span>Exit: ${audit.return_code}</span>
                    <span>Time: ${audit.execution_time}s</span>
                </div>
            </div>
        `).join('');
    }

    renderAIAudit(interactions) {
        const container = document.getElementById('ai-audit');
        if (!container) return;

        container.innerHTML = interactions.map(interaction => `
            <div class="audit-item ${interaction.success ? 'success' : 'error'}">
                <div class="audit-header">
                    <span>${this.escapeHtml(interaction.type)}</span>
                    <span class="model">${this.escapeHtml(interaction.model)}</span>
                    <span class="timestamp">${new Date(interaction.created_at).toLocaleString()}</span>
                </div>
                <div class="audit-details">
                    <span>Time: ${interaction.response_time?.toFixed(2) || 'N/A'}s</span>
                </div>
            </div>
        `).join('');
    }

    showLoginDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'modal-overlay';
        dialog.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        dialog.innerHTML = `
            <div class="modal" style="
                background: white;
                padding: 20px;
                border-radius: 8px;
                min-width: 300px;
                max-width: 400px;
            ">
                <div class="modal-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                ">
                    <h3>Login to HeliosOS</h3>
                    <button onclick="this.closest('.modal-overlay').remove()" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                    ">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="login-form">
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px;">Username</label>
                            <input type="text" id="login-username" required style="
                                width: 100%;
                                padding: 8px;
                                border: 1px solid #ccc;
                                border-radius: 4px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div class="form-group" style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 5px;">Password</label>
                            <input type="password" id="login-password" required style="
                                width: 100%;
                                padding: 8px;
                                border: 1px solid #ccc;
                                border-radius: 4px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div class="form-actions" style="
                            display: flex;
                            gap: 10px;
                            justify-content: flex-end;
                        ">
                            <button type="button" onclick="this.closest('.modal-overlay').remove()" style="
                                padding: 8px 16px;
                                border: 1px solid #ccc;
                                background: white;
                                border-radius: 4px;
                                cursor: pointer;
                            ">Cancel</button>
                            <button type="submit" class="btn primary" style="
                                padding: 8px 16px;
                                background: #007bff;
                                color: white;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                            ">Login</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        dialog.querySelector('#login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;

            if (await this.login(username, password)) {
                dialog.remove();
            }
        });

        document.body.appendChild(dialog);
        document.getElementById('login-username').focus();
    }

    showRegisterDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'modal-overlay';
        dialog.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        dialog.innerHTML = `
            <div class="modal" style="
                background: white;
                padding: 20px;
                border-radius: 8px;
                min-width: 300px;
                max-width: 400px;
            ">
                <div class="modal-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                ">
                    <h3>Register for HeliosOS</h3>
                    <button onclick="this.closest('.modal-overlay').remove()" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                    ">&times;</button>
                </div>
                <div class="modal-body">
                    <form id="register-form">
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px;">Username</label>
                            <input type="text" id="register-username" required minlength="3" style="
                                width: 100%;
                                padding: 8px;
                                border: 1px solid #ccc;
                                border-radius: 4px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px;">Email (optional)</label>
                            <input type="email" id="register-email" style="
                                width: 100%;
                                padding: 8px;
                                border: 1px solid #ccc;
                                border-radius: 4px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div class="form-group" style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px;">Password</label>
                            <input type="password" id="register-password" required minlength="8" style="
                                width: 100%;
                                padding: 8px;
                                border: 1px solid #ccc;
                                border-radius: 4px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div class="form-group" style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 5px;">Confirm Password</label>
                            <input type="password" id="register-confirm" required minlength="8" style="
                                width: 100%;
                                padding: 8px;
                                border: 1px solid #ccc;
                                border-radius: 4px;
                                box-sizing: border-box;
                            ">
                        </div>
                        <div class="form-actions" style="
                            display: flex;
                            gap: 10px;
                            justify-content: flex-end;
                        ">
                            <button type="button" onclick="this.closest('.modal-overlay').remove()" style="
                                padding: 8px 16px;
                                border: 1px solid #ccc;
                                background: white;
                                border-radius: 4px;
                                cursor: pointer;
                            ">Cancel</button>
                            <button type="submit" class="btn primary" style="
                                padding: 8px 16px;
                                background: #007bff;
                                color: white;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                            ">Register</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        dialog.querySelector('#register-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('register-username').value;
            const email = document.getElementById('register-email').value;
            const password = document.getElementById('register-password').value;
            const confirm = document.getElementById('register-confirm').value;

            if (password !== confirm) {
                this.showNotification('Passwords do not match', 'error');
                return;
            }

            if (await this.register(username, password, email)) {
                dialog.remove();
            }
        });

        document.body.appendChild(dialog);
        document.getElementById('register-username').focus();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.heliosOS = new HeliosOS();
});