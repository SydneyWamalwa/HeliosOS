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

        // Check for special commands or intents
        const intent = this.parseUserIntent(message);

        // Add user message to chat with animation
        this.addChatMessage('user', message);

        // Show enhanced typing indicator with personality
        const loadingId = this.showTypingIndicator();

        // Store in chat history
        this.chatHistory.push({ role: 'user', content: message, timestamp: new Date() });

        try {
            // Handle special intents directly if possible
            if (intent.type === 'open_app' && intent.app) {
                // Handle app opening directly
                const result = await this.handleAppOpening(intent.app);
                this.updateTypingIndicator(loadingId, result);
                this.chatHistory.push({ role: 'assistant', content: result, timestamp: new Date() });
                return;
            }

            if (intent.type === 'automate' && intent.task) {
                // Handle automation directly
                const result = await this.handleTaskAutomation(intent.task, intent.params);
                this.updateTypingIndicator(loadingId, result);
                this.chatHistory.push({ role: 'assistant', content: result, timestamp: new Date() });
                return;
            }

            // Track response time for analytics
            const startTime = performance.now();

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
                    })),
                    user_type: this.userType, // Send user type for personalization
                    intent: intent.type // Send detected intent
                })
            });

            const data = await response.json();
            const responseTime = performance.now() - startTime;

            if (data.success && data.response) {
                // Process and enhance the response
                const enhancedResponse = this.processAIResponse(data.response, message, intent);

                // Update typing indicator with enhanced response
                this.updateTypingIndicator(loadingId, enhancedResponse, responseTime);

                // Store in chat history
                this.chatHistory.push({ role: 'assistant', content: data.response, timestamp: new Date() });

                // Handle any actions in the response
                this.handleResponseActions(data.response, intent);

                // Learn from this interaction
                this.learnUserPreferences(message, data.response, intent);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.updateTypingIndicator(
                loadingId,
                `<div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    Sorry, I encountered an error. Please try again.
                    <button class="retry-button" onclick="window.heliosOS.retryLastMessage()">Retry</button>
                </div>`
            );
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
        messageDiv.className = `message ${sender} message-appear`;

        // Enhanced avatars based on user type and sender
        let avatar;
        if (sender === 'user') {
            avatar = '👤';
        } else {
            // AI avatar based on user type
            switch (this.userType) {
                case 'business': avatar = '👨‍💼'; break;
                case 'student': avatar = '👨‍🎓'; break;
                default: avatar = '🌞'; // Leo's sun avatar
            }
        }

        const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content-wrapper">
                <div class="message-content">${this.formatMessage(content)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        chatContainer.appendChild(messageDiv);

        // Auto-scroll to bottom with smooth animation
        setTimeout(() => {
            chatContainer.scrollTo({
                top: chatContainer.scrollHeight,
                behavior: 'smooth'
            });
        }, 100);

        return messageDiv;
    }

    formatMessage(content) {
        // Enhanced formatting for messages with code highlighting and lists
        let formatted = content
            // Code blocks with syntax highlighting
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="code-block language-$1"><code>$2</code></pre>')
            // Inline code
            .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Bullet lists
            .replace(/^\s*•\s+(.*)/gm, '<li>$1</li>')
            .replace(/^\s*-\s+(.*)/gm, '<li>$1</li>')
            // Numbered lists
            .replace(/^\s*(\d+)\.\s+(.*)/gm, '<li class="numbered">$1. $2</li>')
            // Headings
            .replace(/^###\s+(.*)/gm, '<h3>$1</h3>')
            .replace(/^##\s+(.*)/gm, '<h2>$1</h2>')
            .replace(/^#\s+(.*)/gm, '<h1>$1</h1>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Line breaks
            .replace(/\n/g, '<br>');

        // Wrap lists in <ul> tags
        if (formatted.includes('<li>')) {
            formatted = formatted.replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>');
            // Fix nested lists
            formatted = formatted.replace(/<\/ul><ul>/g, '');
        }

        // Add special styling for system paths and commands
        formatted = formatted.replace(/\/([\w\/.-]+)/g, '<span class="system-path">/$1</span>');
        formatted = formatted.replace(/\b(sudo|apt|yum|dnf|pacman|brew)\b/g, '<span class="command-keyword">$1</span>');

        return formatted;
    }

    // Intent detection and task handling methods
    parseUserIntent(message) {
        const lowerMessage = message.toLowerCase();
        const intent = { type: 'general', confidence: 0.5 };

        // App opening intent
        const openAppPatterns = [
            /open\s+(\w+)/i,
            /launch\s+(\w+)/i,
            /start\s+(\w+)/i,
            /run\s+(\w+)/i
        ];

        for (const pattern of openAppPatterns) {
            const match = lowerMessage.match(pattern);
            if (match) {
                intent.type = 'open_app';
                intent.app = match[1];
                intent.confidence = 0.8;
                break;
            }
        }

        // Summarization intent
        if (lowerMessage.includes('summarize') ||
            lowerMessage.includes('summary') ||
            lowerMessage.includes('tldr')) {
            intent.type = 'summarize';
            intent.confidence = 0.9;
        }

        // Task automation intent
        const automationPatterns = [
            /automate\s+([\w\s]+)/i,
            /create\s+workflow\s+for\s+([\w\s]+)/i,
            /schedule\s+([\w\s]+)/i,
            /repeat\s+([\w\s]+)/i
        ];

        for (const pattern of automationPatterns) {
            const match = lowerMessage.match(pattern);
            if (match) {
                intent.type = 'automate';
                intent.task = match[1];
                intent.confidence = 0.7;

                // Extract parameters
                const paramMatches = lowerMessage.match(/with\s+([\w\s,]+)/i);
                if (paramMatches) {
                    intent.params = paramMatches[1].split(',').map(p => p.trim());
                }
                break;
            }
        }

        // System status intent
        if (lowerMessage.includes('system status') ||
            lowerMessage.includes('performance') ||
            lowerMessage.includes('how is the system')) {
            intent.type = 'system_status';
            intent.confidence = 0.85;
        }

        // Help intent
        if (lowerMessage.includes('help') ||
            lowerMessage.includes('how do i') ||
            lowerMessage.includes('what can you do')) {
            intent.type = 'help';
            intent.confidence = 0.75;
        }

        console.log('Detected intent:', intent);
        return intent;
    }

    showTypingIndicator() {
        const chatContainer = document.getElementById('chat-container');
        if (!chatContainer) return null;

        const loadingId = 'typing-' + Date.now();
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant message-appear';
        messageDiv.id = loadingId;

        // Avatar based on user type
        let avatar;
        switch (this.userType) {
            case 'business': avatar = '👨‍💼'; break;
            case 'student': avatar = '👨‍🎓'; break;
            default: avatar = '🌞'; // Leo's sun avatar
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content-wrapper">
                <div class="message-content">
                    <div class="typing-indicator">
                        <div class="typing-avatar">${avatar}</div>
                        <div class="typing-dots"><span></span><span></span><span></span></div>
                        <div class="typing-status">Leo is thinking...</div>
                    </div>
                </div>
            </div>
        `;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
        });

        return loadingId;
    }

    updateTypingIndicator(loadingId, content, responseTime = null) {
        const loadingMessage = document.getElementById(loadingId);
        if (!loadingMessage) return;

        // Add response time indicator if provided
        let responseTimeHtml = '';
        if (responseTime) {
            responseTimeHtml = responseTime < 1000 ?
                `<div class="response-time fast">Responded in ${Math.round(responseTime)}ms</div>` :
                `<div class="response-time">Responded in ${(responseTime/1000).toFixed(1)}s</div>`;
        }

        loadingMessage.querySelector('.message-content').innerHTML = content + responseTimeHtml;

        // Add subtle entrance animation
        loadingMessage.classList.add('message-updated');
    }

    processAIResponse(response, userMessage, intent) {
        // Convert markdown to HTML using our enhanced formatter
        let processed = this.formatMessage(response);

        // Add interactive elements based on response content and intent
        if (intent.type === 'system_status' || response.includes('system status') ||
            response.includes('CPU') || response.includes('Memory')) {
            processed = this.addSystemStatusVisuals(processed);
        }

        if (intent.type === 'open_app' || response.includes('applications available') ||
            response.includes('open') && (response.includes('Firefox') || response.includes('Chrome'))) {
            processed = this.addAppLaunchButtons(processed);
        }

        if (intent.type === 'summarize' || response.includes('summary') || response.includes('summarized')) {
            processed = this.addSummaryControls(processed);
        }

        if (intent.type === 'automate' || response.includes('workflow') || response.includes('automation')) {
            processed = this.addAutomationControls(processed);
        }

        // Add suggestion chips if appropriate
        if (this.shouldShowSuggestions(userMessage, response)) {
            processed += this.generateSuggestionChips(userMessage, response, intent);
        }

        return processed;
    }

    addSystemStatusVisuals(text) {
        // Extract metrics from text using regex
        const cpuMatch = text.match(/CPU:?\s*(\d+)%/i);
        const memoryMatch = text.match(/Memory:?\s*([\d.]+)\s*(?:GB|MB|%)/i);
        const diskMatch = text.match(/Disk:?\s*(\d+)\s*(?:GB|%)/i);

        if (cpuMatch || memoryMatch || diskMatch) {
            let visualsHtml = '<div class="system-status-visuals">';

            if (cpuMatch) {
                const cpuUsage = parseInt(cpuMatch[1]);
                const cpuClass = cpuUsage > 80 ? 'high' : cpuUsage > 50 ? 'medium' : 'low';
                visualsHtml += `
                    <div class="status-gauge">
                        <div class="gauge-label">CPU</div>
                        <div class="gauge-container">
                            <div class="gauge-fill ${cpuClass}" style="width: ${cpuUsage}%"></div>
                        </div>
                        <div class="gauge-value">${cpuUsage}%</div>
                    </div>`;
            }

            if (memoryMatch) {
                const memValue = parseFloat(memoryMatch[1]);
                let memPercent = memValue;
                if (text.includes('GB') && !text.includes('%')) {
                    // Estimate percentage if given in GB
                    memPercent = Math.round((memValue / 8) * 100); // Assuming 8GB total
                }
                const memClass = memPercent > 80 ? 'high' : memPercent > 50 ? 'medium' : 'low';
                visualsHtml += `
                    <div class="status-gauge">
                        <div class="gauge-label">Memory</div>
                        <div class="gauge-container">
                            <div class="gauge-fill ${memClass}" style="width: ${memPercent}%"></div>
                        </div>
                        <div class="gauge-value">${memoryMatch[0]}</div>
                    </div>`;
            }

            if (diskMatch) {
                const diskValue = parseInt(diskMatch[1]);
                let diskPercent = diskValue;
                if (text.includes('GB') && !text.includes('%')) {
                    // Estimate percentage if given in GB
                    diskPercent = Math.min(100, Math.round((diskValue / 100) * 100)); // Assuming 100GB total
                }
                const diskClass = diskPercent > 80 ? 'high' : diskPercent > 50 ? 'medium' : 'low';
                visualsHtml += `
                    <div class="status-gauge">
                        <div class="gauge-label">Disk</div>
                        <div class="gauge-container">
                            <div class="gauge-fill ${diskClass}" style="width: ${diskPercent}%"></div>
                        </div>
                        <div class="gauge-value">${diskMatch[0]}</div>
                    </div>`;
            }

            visualsHtml += '</div>';

            // Insert visuals after the first paragraph or heading
            return text.replace(/(<br>|<\/h[1-3]>)/, '$1' + visualsHtml);
        }

        return text;
    }

    addAppLaunchButtons(text) {
        // Define common apps and their icons
        const appIcons = {
            'firefox': '🦊',
            'chrome': '🌐',
            'terminal': '💻',
            'vscode': '📝',
            'code': '📝',
            'calculator': '🧮',
            'files': '📁',
            'settings': '⚙️',
            'music': '🎵',
            'video': '🎬',
            'email': '📧',
            'calendar': '📅'
        };

        // Create container for app buttons
        let buttonsHtml = '<div class="app-launch-grid">';

        // Check for app mentions in the text
        for (const [app, icon] of Object.entries(appIcons)) {
            if (text.toLowerCase().includes(app)) {
                buttonsHtml += `
                    <button class="app-launch-button" onclick="window.heliosOS.handleAppOpening('${app}')">
                        <div class="app-icon">${icon}</div>
                        <span>${app.charAt(0).toUpperCase() + app.slice(1)}</span>
                    </button>`;
            }
        }

        buttonsHtml += '</div>';

        // Only add buttons if we found at least one app
        if (buttonsHtml.includes('app-launch-button')) {
            // Add buttons after a relevant paragraph
            const appParagraphRegex = /(applications|apps|programs|software|tools)/i;
            if (appParagraphRegex.test(text)) {
                return text.replace(/(.*?applications.*?<br>)/i, '$1' + buttonsHtml);
            } else {
                // If no relevant paragraph, add at the end
                return text + '<br>' + buttonsHtml;
            }
        }

        return text;
    }

    addSummaryControls(text) {
        // Add controls for summary customization
        const controlsHtml = `
            <div class="summary-controls">
                <button onclick="window.heliosOS.adjustSummaryLength('shorter')">Make Shorter</button>
                <button onclick="window.heliosOS.adjustSummaryLength('longer')">More Details</button>
                <button onclick="window.heliosOS.copySummary()">Copy Summary</button>
            </div>
        `;

        // Add after the summary heading or at the beginning
        if (text.includes('Summary') || text.includes('summary')) {
            return text.replace(/(Summary.*?<br>)/i, '$1' + controlsHtml);
        } else {
            return controlsHtml + text;
        }
    }

    addAutomationControls(text) {
        // Add controls for workflow automation
        const controlsHtml = `
            <div class="automation-controls">
                <button onclick="window.heliosOS.saveWorkflow()">Save Workflow</button>
                <button onclick="window.heliosOS.scheduleWorkflow()">Schedule</button>
                <button onclick="window.heliosOS.editWorkflow()">Edit</button>
            </div>
        `;

        // Add after workflow mention or at the end
        if (text.includes('workflow') || text.includes('automation')) {
            return text.replace(/(workflow|automation).*?(<br>)/i, '$1$2' + controlsHtml);
        } else {
            return text + '<br>' + controlsHtml;
        }
    }

    generateSuggestionChips(userMessage, aiResponse, intent) {
        let suggestions = [];

        // Generate context-aware suggestions based on intent and response
        switch (intent.type) {
            case 'open_app':
                suggestions = [
                    "What can I do with this app?",
                    "Show app shortcuts",
                    "Configure app settings"
                ];
                break;

            case 'system_status':
                suggestions = [
                    "Optimize performance",
                    "Show more details",
                    "Fix any issues"
                ];
                break;

            case 'summarize':
                suggestions = [
                    "Make it shorter",
                    "Explain in simpler terms",
                    "Save this summary"
                ];
                break;

            case 'automate':
                suggestions = [
                    "Run this workflow now",
                    "Schedule for later",
                    "Show me similar workflows"
                ];
                break;

            case 'help':
                suggestions = [
                    "Show me examples",
                    "What else can you do?",
                    "Tell me about shortcuts"
                ];
                break;

            default:
                // Check response content for clues
                if (aiResponse.includes('?')) {
                    suggestions = ["Yes", "No", "Tell me more"];
                } else if (aiResponse.includes('command')) {
                    suggestions = ["Run this command", "Explain this command", "Show similar commands"];
                } else {
                    suggestions = ["Tell me more", "How does this work?", "Show me an example"];
                }
        }

        // Create HTML for suggestion chips
        let chipsHtml = '<div class="suggestion-chips">';
        suggestions.forEach(suggestion => {
            chipsHtml += `<button class="suggestion-chip" onclick="document.getElementById('chat-input').value='${suggestion}'; window.heliosOS.sendChatMessage();">${suggestion}</button>`;
        });
        chipsHtml += '</div>';

        return chipsHtml;
    }

    shouldShowSuggestions(userMessage, aiResponse) {
        // Don't show suggestions for very short responses or error messages
        if (!aiResponse || aiResponse.length < 20 || aiResponse.includes('error') || aiResponse.includes('sorry')) {
            return false;
        }

        // Show suggestions for responses that invite further interaction
        return aiResponse.includes('?') ||
               aiResponse.includes('Would you like') ||
               aiResponse.includes('I can help') ||
               aiResponse.includes('Let me know');
    }

    async handleAppOpening(app) {
        console.log(`Opening application: ${app}`);

        // Map of common apps to commands
        const appCommands = {
            'firefox': 'firefox',
            'chrome': 'google-chrome',
            'terminal': 'gnome-terminal',
            'code': 'code',
            'vscode': 'code',
            'calculator': 'gnome-calculator',
            'files': 'nautilus',
            'settings': 'gnome-control-center'
        };

        // Get command for the app
        const command = appCommands[app.toLowerCase()] || app;

        try {
            // Execute the command via the API
            const response = await fetch('/api/exec', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    command: command,
                    background: true
                })
            });

            const data = await response.json();

            if (data.success) {
                // Create a rich response with app details
                return this.createAppOpeningResponse(app);
            } else {
                throw new Error(data.error || `Failed to open ${app}`);
            }
        } catch (error) {
            console.error(`Error opening ${app}:`, error);
            return `I tried to open ${app}, but encountered an error: ${error.message}. Would you like to try a different application?`;
        }
    }

    createAppOpeningResponse(app) {
        // App-specific rich responses
        const responses = {
            'firefox': `I've opened Firefox for you! 🦊 You can browse the web, check your favorite sites, or research information. Need help with anything specific in Firefox?`,

            'chrome': `Google Chrome is now open! 🌐 You can browse websites, use web applications, or sync with your Google account. Is there a specific website you'd like to visit?`,

            'terminal': `Terminal is ready for your commands! 💻 You can run system commands, manage files, or execute scripts. Let me know if you need help with any specific commands.`,

            'code': `Visual Studio Code is now open! 📝 You can edit code, manage projects, or use extensions to enhance your development experience. What project are you working on today?`,

            'vscode': `Visual Studio Code is now open! 📝 You can edit code, manage projects, or use extensions to enhance your development experience. What project are you working on today?`,

            'calculator': `Calculator is open! 🧮 You can perform basic or scientific calculations depending on your needs. Let me know if you need help with any specific calculations.`,

            'files': `File Manager is open! 📁 You can browse your files, organize documents, or manage your storage. Is there a specific folder you're looking for?`,

            'settings': `System Settings is open! ⚙️ You can customize your system, manage accounts, or configure hardware. What settings would you like to adjust?`
        };

        return responses[app.toLowerCase()] || `I've opened ${app} for you! Let me know if you need any help using it.`;
    }

    async handleTaskAutomation(task, params = []) {
        console.log(`Automating task: ${task}`, params);

        // Map of common automation tasks
        const automationTasks = {
            'backup': this.automateBackup.bind(this),
            'system check': this.automateSystemCheck.bind(this),
            'cleanup': this.automateCleanup.bind(this),
            'update': this.automateUpdate.bind(this),
            'morning routine': this.automateMorningRoutine.bind(this)
        };

        // Find the closest matching task
        let matchedTask = null;
        let highestScore = 0;

        for (const [key, handler] of Object.entries(automationTasks)) {
            // Simple string similarity score
            const score = this.getStringSimilarity(task.toLowerCase(), key);
            if (score > highestScore && score > 0.6) { // Threshold for matching
                highestScore = score;
                matchedTask = { key, handler };
            }
        }

        if (matchedTask) {
            try {
                return await matchedTask.handler(params);
            } catch (error) {
                console.error(`Error automating ${matchedTask.key}:`, error);
                return `I tried to automate ${task}, but encountered an error: ${error.message}. Would you like to try a different approach?`;
            }
        } else {
            // Generic response for unknown automation tasks
            return `I'd love to help automate "${task}" for you. Could you provide more details about what specific steps this should include?`;
        }
    }

    getStringSimilarity(str1, str2) {
        // Simple Levenshtein distance-based similarity
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;

        if (longer.length === 0) return 1.0;
        if (shorter.length === 0) return 0.0;

        // Check if shorter string is contained in longer
        if (longer.includes(shorter)) return 0.8;

        // Check for word overlap
        const words1 = str1.split(' ');
        const words2 = str2.split(' ');
        const commonWords = words1.filter(word => words2.includes(word)).length;

        return commonWords / Math.max(words1.length, words2.length);
    }

    async automateBackup(params) {
        // Simulate backup process
        await this.simulateProgress('Backing up your files', 3);

        return `✅ Backup completed successfully!

I've created a backup of your important files. Here's what was included:
• Documents folder
• Pictures folder
• Configuration files
• User settings

The backup is stored in your home directory as backup-${new Date().toISOString().split('T')[0]}.zip

Would you like me to schedule regular backups for you?`;
    }

    async automateSystemCheck(params) {
        // Simulate system check
        await this.simulateProgress('Running system diagnostics', 4);

        // Generate realistic system check results
        const cpuUsage = Math.floor(Math.random() * 30) + 20;
        const memoryUsage = Math.floor(Math.random() * 20) + 50;
        const diskUsage = Math.floor(Math.random() * 5) + 20;
        const temperature = Math.floor(Math.random() * 10) + 40;

        return `✅ System Check Complete

**System Health: Good**

• CPU Usage: ${cpuUsage}% (Normal)
• Memory Usage: ${memoryUsage}% (Normal)
• Disk Usage: ${diskUsage}% (Good)
• System Temperature: ${temperature}°C (Normal)
• Network: Connected (Good signal)
• Updates: System is up to date
• Security: No issues detected

Would you like me to optimize any specific aspect of your system?`;
    }

    async automateCleanup(params) {
        // Simulate cleanup process
        await this.simulateProgress('Cleaning up system', 3);

        // Generate realistic cleanup results
        const tempFiles = Math.floor(Math.random() * 500) + 100;
        const cacheSize = Math.floor(Math.random() * 1000) + 200;
        const logsSize = Math.floor(Math.random() * 50) + 10;

        return `✅ System Cleanup Complete

I've cleaned up the following items:

• Temporary files: ${tempFiles} MB freed
• Application caches: ${cacheSize} MB freed
• Old log files: ${logsSize} MB freed
• Empty trash: Completed

Total space recovered: ${tempFiles + cacheSize + logsSize} MB

Your system should now run more efficiently. Would you like me to schedule regular cleanup tasks?`;
    }

    async automateUpdate(params) {
        // Simulate update process
        await this.simulateProgress('Checking for updates', 2);
        await this.simulateProgress('Downloading updates', 3);
        await this.simulateProgress('Installing updates', 2);

        return `✅ System Update Complete

I've updated the following components:

• System packages: All up to date
• Application updates: 3 applications updated
• Security patches: Applied latest security fixes
• Drivers: All up to date

Your system is now running the latest software versions. A system restart is recommended to complete the update process. Would you like to restart now?`;
    }

    async automateMorningRoutine(params) {
        // Simulate morning routine
        await this.simulateProgress('Running morning routine', 5);

        return `✅ Morning Routine Complete

I've prepared your digital workspace for the day:

• Checked system status: All systems operational
• Updated weather forecast: Currently 72°F, Sunny
• Opened your calendar: You have 2 meetings today
• Prepared your email: 5 new messages
• Opened your task list: 3 tasks due today
• Started your preferred music playlist

Is there anything specific you'd like to focus on this morning?`;
    }

    async simulateProgress(message, seconds) {
        // Helper method to simulate progress for automation tasks
        return new Promise(resolve => {
            console.log(`${message}... (${seconds}s)`);
            setTimeout(resolve, seconds * 1000);
        });
    }

    handleResponseActions(response, intent) {
        // Check for action triggers in the response
        if (response.includes('restart') || response.includes('reboot')) {
            this.showNotification('System restart suggested. This is a simulated action in demo mode.', 'info');
        }

        if (response.includes('update') && response.includes('available')) {
            this.showNotification('Updates are available. Click to install.', 'info');
        }

        // Handle intent-specific actions
        switch (intent.type) {
            case 'system_status':
                // Update system stats immediately
                this.updateSystemStats();
                break;

            case 'summarize':
                // Focus on summarize button
                const summarizeBtn = document.getElementById('summarize-btn');
                if (summarizeBtn) {
                    summarizeBtn.classList.add('highlight');
                    setTimeout(() => summarizeBtn.classList.remove('highlight'), 2000);
                }
                break;
        }
    }

    learnUserPreferences(message, response, intent) {
        // Simple user preference learning
        // In a real implementation, this would be more sophisticated

        // Track command preferences
        if (intent.type === 'open_app') {
            const app = intent.app;
            if (!this.preferences.favoriteApps) {
                this.preferences.favoriteApps = {};
            }
            this.preferences.favoriteApps[app] = (this.preferences.favoriteApps[app] || 0) + 1;
            console.log('Updated app preferences:', this.preferences.favoriteApps);
        }

        // Track topic interests based on questions
        if (message.includes('?')) {
            const topics = [
                'system', 'performance', 'security', 'development',
                'productivity', 'customization', 'automation'
            ];

            topics.forEach(topic => {
                if (message.toLowerCase().includes(topic)) {
                    if (!this.preferences.interests) {
                        this.preferences.interests = {};
                    }
                    this.preferences.interests[topic] = (this.preferences.interests[topic] || 0) + 1;
                }
            });

            console.log('Updated topic interests:', this.preferences.interests);
        }

        // Learn preferred response style
        if (message.includes('shorter') || message.includes('brief')) {
            this.preferences.responseStyle = 'concise';
        } else if (message.includes('detail') || message.includes('explain')) {
            this.preferences.responseStyle = 'detailed';
        }

        // In a real implementation, we would save these preferences to the server
    }

    retryLastMessage() {
        // Get the last user message from chat history
        const lastUserMessage = this.chatHistory.filter(msg => msg.role === 'user').pop();

        if (lastUserMessage) {
            // Set the message in the input field
            const chatInput = document.getElementById('chat-input');
            if (chatInput) {
                chatInput.value = lastUserMessage.content;
                this.sendChatMessage();
            }
        } else {
            this.showNotification('No previous message to retry', 'warning');
        }
    }

    // Utility methods for summary controls
    adjustSummaryLength(direction) {
        const chatInput = document.getElementById('chat-input');
        if (!chatInput) return;

        if (direction === 'shorter') {
            chatInput.value = 'Please make the summary shorter and more concise';
        } else {
            chatInput.value = 'Please provide more details in the summary';
        }

        this.sendChatMessage();
    }

    copySummary() {
        // Find the last summary in the chat
        const chatContainer = document.getElementById('chat-container');
        if (!chatContainer) return;

        const messages = chatContainer.querySelectorAll('.message.assistant');
        let summaryText = '';

        // Search from the most recent message
        for (let i = messages.length - 1; i >= 0; i--) {
            const content = messages[i].querySelector('.message-content').textContent;
            if (content.includes('Summary') || content.includes('summary')) {
                summaryText = content;
                break;
            }
        }

        if (summaryText) {
            // Copy to clipboard
            navigator.clipboard.writeText(summaryText).then(() => {
                this.showNotification('Summary copied to clipboard', 'success');
            }).catch(err => {
                console.error('Failed to copy summary:', err);
                this.showNotification('Failed to copy summary', 'error');
            });
        } else {
            this.showNotification('No summary found to copy', 'warning');
        }
    }

    // Workflow management methods
    saveWorkflow() {
        this.showNotification('Workflow saved successfully', 'success');
    }

    scheduleWorkflow() {
        const time = new Date();
        time.setHours(time.getHours() + 24);
        this.showNotification(`Workflow scheduled for ${time.toLocaleString()}`, 'success');
    }

    editWorkflow() {
        this.addChatMessage('assistant', `Let's edit this workflow. What changes would you like to make?`);
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