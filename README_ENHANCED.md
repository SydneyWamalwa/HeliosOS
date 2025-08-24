# HeliosOS 2.0 - AI-Powered Cloud Operating System

![HeliosOS Logo](https://img.shields.io/badge/HeliosOS-2.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11-green?style=for-the-badge)
![React](https://img.shields.io/badge/React-18.2-blue?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=for-the-badge)
![AI Powered](https://img.shields.io/badge/AI-Powered-purple?style=for-the-badge)

## 🌟 Overview

HeliosOS 2.0 is a revolutionary AI-powered cloud operating system designed for modern professionals, students, and developers. It combines the power of artificial intelligence with a comprehensive suite of open-source applications, all accessible through a beautiful web interface.

### ✨ Key Features

- 🤖 **AI-Powered Command Processing** - Natural language interaction with your OS
- 📱 **Modern Web Interface** - Responsive, mobile-friendly design
- 🔄 **Workflow Automation** - Create and execute custom automation sequences
- 📦 **Integrated Applications** - 11+ pre-configured open-source applications
- 🎯 **User-Centric Design** - Tailored for Business, Students, and Programmers
- 🔒 **Enterprise Security** - Robust authentication and authorization
- 🐳 **Container-Based** - Easy deployment and scaling with Docker

## 🎯 Target Audiences

### 👔 Business Professionals
- **LibreOffice Suite** - Complete office productivity
- **Odoo ERP** - Enterprise resource planning
- **Rocket.Chat** - Team communication
- **AI Assistant** - Intelligent task automation

### 🎓 Students
- **Joplin Notes** - Advanced note-taking
- **Zotero** - Research management
- **Firefox** - Web browsing and research
- **Study Workflows** - Automated study session setup

### 👨‍💻 Programmers
- **VS Code Server** - Full IDE in the browser
- **Gitea** - Git repository management
- **Portainer** - Container orchestration
- **Development Workflows** - Automated environment setup

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 4GB+ RAM
- Modern web browser

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/SydneyWamalwa/HeliosOS.git
cd HeliosOS
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Deploy with Docker Compose**
```bash
docker-compose -f docker-compose-enhanced.yml up -d
```

4. **Access HeliosOS**
- Open your browser to `http://localhost`
- Create your account and start exploring!

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                     │
├─────────────────────────────────────────────────────────────┤
│  React Frontend  │  Flask Backend  │  AI Command Processor │
├─────────────────────────────────────────────────────────────┤
│     Application Manager     │     Workflow Engine          │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis Cache  │  Docker Container Runtime   │
└─────────────────────────────────────────────────────────────┘
```

### Core Services

- **Frontend**: React 18 with modern UI components
- **Backend**: Flask with async support
- **Database**: PostgreSQL with JSON support
- **Cache**: Redis for session and data caching
- **Proxy**: Nginx for load balancing and SSL
- **AI**: OpenAI integration for natural language processing

## 🤖 AI Features

### Natural Language Commands
```
"Open LibreOffice and create a new document"
"Start my morning work routine"
"Show me system status"
"Create a new project in VS Code"
```

### Intelligent Workflows
- **Morning Routine**: Automatically opens email, calendar, and productivity tools
- **Development Setup**: Launches IDE, Git client, and container management
- **Study Session**: Prepares note-taking and research tools

### Context-Aware Suggestions
- Application recommendations based on usage patterns
- Workflow suggestions based on time of day
- Personalized productivity tips

## 📦 Integrated Applications

### Business Suite
| Application | Purpose | Port | Status |
|-------------|---------|------|--------|
| LibreOffice | Office Suite | 9980 | ✅ Ready |
| Odoo ERP | Business Management | 8069 | ✅ Ready |
| Rocket.Chat | Team Communication | 3002 | ✅ Ready |

### Development Tools
| Application | Purpose | Port | Status |
|-------------|---------|------|--------|
| VS Code Server | Code Editor | 8080 | ✅ Ready |
| Gitea | Git Service | 3000 | ✅ Ready |
| Portainer | Container Management | 9000 | ✅ Ready |

### Student Tools
| Application | Purpose | Port | Status |
|-------------|---------|------|--------|
| Joplin | Note Taking | 22300 | ✅ Ready |
| Zotero | Reference Manager | 3003 | ✅ Ready |

### General Applications
| Application | Purpose | Port | Status |
|-------------|---------|------|--------|
| Firefox | Web Browser | 3001 | ✅ Ready |

## 🔧 Configuration

### Environment Variables

```bash
# Core Configuration
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/helios
OPENAI_API_KEY=your-openai-key

# Application Settings
FLASK_ENV=production
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-jwt-secret
BCRYPT_LOG_ROUNDS=13
```

### Custom Workflows

Create custom workflows using the web interface or API:

```json
{
  "name": "custom_workflow",
  "display_name": "My Custom Workflow",
  "steps": [
    {
      "type": "application",
      "name": "Launch Firefox",
      "parameters": {"action": "start", "application": "firefox"}
    },
    {
      "type": "delay",
      "name": "Wait",
      "parameters": {"duration": 3}
    },
    {
      "type": "command",
      "name": "Show Status",
      "parameters": {"command": "show system status"}
    }
  ]
}
```

## 🔌 API Reference

### Authentication
```bash
POST /auth/login
POST /auth/register
POST /auth/logout
```

### AI Commands
```bash
POST /api/v3/ai/enhanced-command
GET /api/v3/ai/suggestions
```

### Application Management
```bash
GET /api/v2/applications
POST /api/v2/applications/{app_name}/start
POST /api/v2/applications/{app_name}/stop
```

### Workflow Management
```bash
GET /api/v3/workflows
POST /api/v3/workflows
POST /api/v3/workflows/{id}/execute
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
python3 test_enhanced_system.py
```

Test coverage includes:
- ✅ Core Components
- ✅ AI Command Processor
- ✅ Application Manager
- ✅ Workflow Engine
- ✅ Enhanced AI Client
- ✅ Database Models
- ✅ API Routes
- ✅ Configuration

## 🚀 Deployment

### Production Deployment

1. **Prepare Environment**
```bash
export OPENAI_API_KEY=your-production-key
export SECRET_KEY=your-production-secret
```

2. **Deploy with SSL**
```bash
docker-compose -f docker-compose-enhanced.yml up -d
```

3. **Configure Domain**
Update nginx.conf with your domain and SSL certificates.

### Scaling

Scale individual services:
```bash
docker-compose scale helios-app=3
docker-compose scale postgres=1
```

## 🔒 Security

### Authentication
- JWT-based stateless authentication
- Bcrypt password hashing
- Session management with Redis

### API Security
- Rate limiting on all endpoints
- CORS configuration
- Input validation and sanitization

### Container Security
- Non-root user execution
- Resource limits
- Network isolation

## 📊 Monitoring

### Health Checks
- Application health endpoints
- Database connection monitoring
- Container resource usage

### Logging
- Structured logging with timestamps
- Error tracking and alerting
- Performance metrics

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. **Clone and Setup**
```bash
git clone https://github.com/SydneyWamalwa/HeliosOS.git
cd HeliosOS
pip install -r requirements_enhanced.txt
```

2. **Run Tests**
```bash
python3 test_enhanced_system.py
```

3. **Start Development Server**
```bash
flask run --debug
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 **Email**: support@helios-os.com
- 💬 **Discord**: [Join our community](https://discord.gg/helios-os)
- 🐛 **Issues**: [GitHub Issues](https://github.com/SydneyWamalwa/HeliosOS/issues)
- 📖 **Documentation**: [Full Documentation](https://docs.helios-os.com)

## 🗺️ Roadmap

### Version 2.1 (Q4 2025)
- [ ] Voice command integration
- [ ] Mobile application
- [ ] Advanced AI features
- [ ] Plugin system

### Version 2.2 (Q1 2026)
- [ ] Multi-tenant support
- [ ] Advanced analytics
- [ ] Custom application integration
- [ ] Enterprise features

## 🙏 Acknowledgments

- OpenAI for AI capabilities
- The open-source community for amazing applications
- Docker for containerization technology
- React team for the frontend framework

---

**Made with ❤️ by the HeliosOS Team**

*Transform your digital workspace with AI-powered automation*

