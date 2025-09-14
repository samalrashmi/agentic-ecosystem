# Agentic Ecosystem

A comprehensive agentic AI platform that orchestrates Business Analyst, Architecture, Developer, and Tester agents to create enterprise-grade applications automatically.

## Overview

The Agentic Ecosystem is a revolutionary platform that transforms user specifications into fully-functional, tested applications through intelligent agent collaboration. The system follows industry best practices and implements a complete software development lifecycle using AI agents.

## Architecture

The system consists of five main agents:

1. **Orchestrator Agent** - Coordinates all agents and manages the overall workflow
2. **Business Analyst (BA) Agent** - Analyzes requirements and creates user stories
3. **Architecture Agent** - Designs system architecture and technology stack
4. **Developer Agent** - Implements the application code and tests
5. **Tester Agent** - Performs comprehensive QA testing and validation

## Key Features

- **End-to-End Automation**: From specification to deployable application
- **Multi-Agent Collaboration**: Specialized agents working together seamlessly
- **Industry Best Practices**: Follows software engineering standards
- **Domain Expertise**: Specialized knowledge for different industries
- **Real-time Monitoring**: Track progress through WebSocket connections
- **Comprehensive Testing**: Functional, security, performance, and usability testing
- **Open Source Stack**: Uses only free, open-source technologies
- **MCP Protocol**: Built on Model Context Protocol for agent communication
- **RESTful APIs**: Complete API for integration with external systems

## Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenAI API key (for LLM functionality)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd agentic-ecosystem
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Start the server:**
   ```bash
   python main.py server
   ```

6. **In another terminal, create your first project:**
   ```bash
   python main.py cli create
   ```

## Usage

### Starting the Server

```bash
python main.py server
```

The server will start on `http://localhost:8000` by default.

### Using the CLI

#### Create a New Project
```bash
python main.py cli create
```

You'll be prompted to enter your project specification. Be as detailed as possible:

```
Enter your project specification:
I want to build an e-commerce platform for selling handmade crafts. 
The platform should allow artisans to create profiles, list products with images and descriptions, 
manage inventory, and process orders. Customers should be able to browse products, add to cart, 
and make secure payments. Include features for reviews, ratings, and order tracking.
```

#### Monitor Project Progress
```bash
python main.py cli monitor <project-id>
```

#### Check Project Status
```bash
python main.py cli status <project-id>
```

#### List All Projects
```bash
python main.py cli list
```

#### View Workflow History
```bash
python main.py cli workflow <project-id>
```

#### Send Clarifications
```bash
python main.py cli clarify <project-id>
```

### Using the REST API

#### Create Project
```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "specification": "Build a task management application with user authentication, project creation, task assignment, and progress tracking."
  }'
```

#### Get Project Status
```bash
curl http://localhost:8000/projects/{project-id}
```

#### WebSocket for Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client123');
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe_project',
    project_id: 'your-project-id'
  }));
};
```

## Agent Workflow

The system follows this workflow:

1. **User Input** → Orchestrator receives project specification
2. **Requirements Analysis** → BA Agent analyzes and clarifies requirements
3. **Architecture Design** → Architecture Agent creates technical design
4. **User Stories** → BA Agent creates detailed user stories with acceptance criteria
5. **Development** → Developer Agent implements the application
6. **Testing** → Tester Agent performs comprehensive QA testing
7. **Delivery** → Complete application ready for deployment

## Domain Expertise

The system has specialized knowledge for various domains:

- **Financial Services**: Banking, payments, trading platforms
- **Manufacturing**: Supply chain, production management, IoT integration
- **Healthcare**: Patient management, HIPAA compliance, medical workflows
- **E-commerce**: Product catalogs, shopping carts, payment processing
- **Education**: Learning management, student portals, course delivery
- **Logistics**: Shipping, tracking, route optimization

## Technology Stacks

The Architecture Agent recommends appropriate technology stacks based on project requirements:

### Web Applications
- **Frontend**: React, Vue.js, Angular
- **Backend**: Python (Django/FastAPI), Node.js, Java Spring Boot
- **Database**: PostgreSQL, MongoDB, Redis
- **Deployment**: Docker, Kubernetes

### Mobile Applications
- **Cross-platform**: React Native, Flutter
- **Native**: Swift (iOS), Kotlin (Android)

### Data & Analytics
- **Processing**: Apache Spark, Pandas
- **Visualization**: D3.js, Chart.js
- **Storage**: InfluxDB, TimescaleDB

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000

# Agent Configuration
BA_AGENT_MODEL=gpt-4
ARCHITECT_AGENT_MODEL=gpt-4
DEVELOPER_AGENT_MODEL=gpt-4
TESTER_AGENT_MODEL=gpt-4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Database (for persistence)
DATABASE_URL=sqlite:///./agentic_ecosystem.db
```

## API Reference

### Endpoints

- `GET /` - Server information
- `GET /health` - Health check with agent statuses
- `POST /projects` - Create new project
- `GET /projects` - List all projects
- `GET /projects/{id}` - Get project status
- `GET /projects/{id}/workflow` - Get workflow history
- `POST /projects/{id}/clarifications` - Send clarification
- `WS /ws/{client_id}` - WebSocket for real-time updates

### Project Phases

Projects progress through these phases:

1. `requirements_analysis` - BA Agent analyzing requirements
2. `awaiting_clarification` - Waiting for user input
3. `architecture_design` - Architecture Agent designing system
4. `user_story_creation` - BA Agent creating user stories
5. `development` - Developer Agent implementing features
6. `qa_testing` - Tester Agent performing QA
7. `completed` - Project finished and ready for deployment
8. `failed` - Project encountered unrecoverable errors

## Examples

### Example Project Specifications

#### E-commerce Platform
```
Build an e-commerce platform for selling electronics. Features needed:
- Product catalog with categories and search
- User registration and authentication
- Shopping cart and checkout
- Payment integration (Stripe)
- Order management and tracking
- Admin panel for inventory management
- Product reviews and ratings
- Email notifications
- Mobile responsive design
```

#### Task Management System
```
Create a team task management application similar to Trello:
- User authentication and team management
- Project boards with customizable columns
- Drag-and-drop task cards
- Task assignments and due dates
- Comments and file attachments
- Real-time collaboration
- Email notifications
- Reporting and analytics dashboard
```

#### Healthcare Portal
```
Develop a patient portal for a medical practice:
- Patient registration and profile management
- Appointment scheduling system
- Medical records access
- Prescription management
- Doctor-patient messaging
- Insurance information management
- HIPAA compliance
- Integration with existing EMR systems
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Type Checking
```bash
mypy src/
```

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check if port 8000 is available
   - Verify all dependencies are installed
   - Check the logs for specific error messages

2. **Agents not responding**
   - Verify OpenAI API key is set correctly
   - Check internet connectivity
   - Review agent logs for errors

3. **Project stuck in one phase**
   - Use the CLI to send clarifications if needed
   - Check the workflow history for issues
   - Monitor real-time updates

### Getting Help

- Check the logs in the terminal where you started the server
- Use `python main.py cli status <project-id>` to see current status
- Review the workflow history: `python main.py cli workflow <project-id>`
- Monitor real-time updates: `python main.py cli monitor <project-id>`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
1. Check the troubleshooting section
2. Review existing issues on GitHub
3. Create a new issue with detailed description
4. Include logs and error messages

---

Built with ❤️ using Python, FastAPI, LangChain, and the power of AI agents.
