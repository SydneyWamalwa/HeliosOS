# HeliosOS - AI-Powered Operating System

HeliosOS is an advanced AI-powered operating system that provides intelligent application management and natural language interaction through Leo, an enhanced AI assistant.

## Features

### Enhanced AI Agent
- **Natural Language Processing**: Advanced command understanding and intent recognition
- **Dynamic Application Discovery**: Automatically discovers and manages all installed applications
- **Context Awareness**: Learns from user patterns and provides personalized suggestions
- **Plugin System**: Extensible architecture for adding new capabilities
- **Real-time Monitoring**: Continuous system and application monitoring

### Leo AI Assistant
- **Voice and Text Commands**: Natural language interaction for all system operations
- **Application Manipulation**: Launch, control, and manage any application
- **Workflow Automation**: Execute complex multi-step processes
- **Smart Suggestions**: Context-aware recommendations based on usage patterns
- **Learning Capabilities**: Adapts to user preferences and behavior

### Application Management
- **Universal Compatibility**: Works with all installed applications, including future ones
- **Intelligent Categorization**: Automatically organizes applications by type and usage
- **Performance Monitoring**: Tracks resource usage and system health
- **Security Integration**: Built-in security validation and audit logging

## Quick Start

### Prerequisites
- Python 3.11+
- Linux-based system (Ubuntu recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/SydneyWamalwa/HeliosOS.git
cd HeliosOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python run.py init-db
```

4. Start HeliosOS:
```bash
python run.py
```

5. Access the system:
   - Web Interface: http://localhost:5003
   - API Endpoints: http://localhost:5003/api/v3/

## API Endpoints

### Leo AI Assistant
- `POST /api/v3/leo/command` - Process natural language commands
- `GET /api/v3/leo/capabilities` - Get Leo's capabilities
- `GET /api/v3/leo/suggestions` - Get personalized suggestions

### Application Management
- `POST /api/v3/applications/discover` - Discover installed applications
- `POST /api/v3/applications/{app_name}/manipulate` - Control applications
- `POST /api/v3/applications/bulk-action` - Perform bulk operations

### System Monitoring
- `GET /api/v3/system/comprehensive-status` - Get detailed system status
- `GET /api/v3/health/detailed` - Health check for all components

## Usage Examples

### Natural Language Commands
```bash
# Application management
"open firefox"
"close all browsers"
"list running applications"

# System operations
"show system status"
"what should i do next"
"run morning workflow"

# File operations
"create document report.txt"
"open file presentation.pptx"
```

### API Usage
```python
import requests

# Process a command through Leo
response = requests.post('http://localhost:5003/api/v3/leo/command', 
                        json={'command': 'open firefox'})
result = response.json()

# Get system status
status = requests.get('http://localhost:5003/api/v3/system/comprehensive-status')
system_info = status.json()
```

## Architecture

### Core Components
- **Enhanced AI Agent**: Advanced NLP and application management
- **Leo Interface**: Natural language processing and user interaction
- **Plugin System**: Extensible architecture for new capabilities
- **Application Manager**: Dynamic discovery and control of applications
- **Security Layer**: Command validation and audit logging

### Plugin Development
Create custom plugins by extending the base plugin classes:

```python
from app.plugin_system import ApplicationHandlerPlugin

class MyAppPlugin(ApplicationHandlerPlugin):
    def get_metadata(self):
        return PluginMetadata(
            name="MyApp",
            version="1.0.0",
            description="Custom application handler",
            plugin_type=PluginType.APPLICATION_HANDLER
        )
    
    async def can_handle_application(self, app_name):
        return "myapp" in app_name.lower()
    
    async def launch_application(self, app_name, parameters):
        # Custom launch logic
        pass
```

## Default Credentials
- Admin: `admin` / `admin123`
- Demo: `demo` / `demo123`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team.

---

**HeliosOS** - Intelligent computing for the modern world.

