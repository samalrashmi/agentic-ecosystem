# Test Suite Documentation

## Overview

This test suite validates the inter-agent communication system for the agentic ecosystem. It focuses on testing message flows, broker functionality, and communication patterns between agents using mock requests and responses.

## Test Files

### 1. `test_message_broker.py`
Tests the core MessageBroker functionality:
- **Connection/Disconnection**: Tests broker connection lifecycle
- **Subscription Management**: Tests topic subscription and unsubscription
- **Message Publishing**: Tests message publishing to subscribed/unsubscribed topics
- **Multiple Subscribers**: Tests multiple subscribers to the same topic
- **Message Ordering**: Tests that messages are processed in correct order
- **Error Handling**: Tests graceful handling of subscriber exceptions
- **Integration Tests**: Tests realistic orchestrator→BA→architect workflows

**Key Features Tested:**
- Message delivery to subscribers
- Graceful handling of missing subscribers
- Concurrent message processing
- Broker lifecycle management

### 2. `test_message_flow.py`
Tests complete agent communication workflows:
- **Full Pipeline Simulation**: Tests complete Orchestrator→BA→Architect→Developer→Tester→Orchestrator workflow
- **Specific Agent Flows**: Tests BA→Architect specification flow with realistic data
- **Error Handling**: Tests system resilience when handlers fail
- **Message Validation**: Tests message structure and enum values
- **Integration Scenarios**: Tests multiple subscribers and message ordering

**Key Features Tested:**
- End-to-end workflow simulation
- Message metadata preservation across agents
- Project ID consistency throughout workflow
- Realistic message content and structure

### 3. `conftest.py`
Provides shared test fixtures and utilities:
- **Mock Message Broker**: Provides mocked MessageBroker for testing
- **Sample Data**: Creates sample project specifications and messages
- **Test Helpers**: Helper functions for creating test messages with various parameters

## Test Coverage

### ✅ What's Covered
- **Message Broker Core Functionality**: Publish, subscribe, unsubscribe, connection management
- **Agent Communication Patterns**: Orchestrator→BA→Architect→Developer→Tester workflows
- **Message Structure Validation**: All message fields, enums, and metadata
- **Error Handling**: Graceful degradation when handlers fail
- **Concurrency**: Multiple subscribers and concurrent message processing
- **Integration Flows**: Realistic multi-agent workflows with proper data flow

### 🚫 What's Not Covered (Intentionally)
- **Actual Agent Implementation**: Tests use mocked agents to avoid OpenAI API dependencies
- **Real LLM Integration**: Tests focus on message flow rather than AI processing
- **Database Operations**: Tests use in-memory data structures
- **Performance Testing**: Focused on functional correctness

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test files
pytest tests/test_message_broker.py -v
pytest tests/test_message_flow.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Test Strategy

### 1. **Mock-First Approach**
- Uses mocked MessageBroker and agent handlers
- Avoids external dependencies (OpenAI API keys)
- Focuses on communication patterns rather than implementation details

### 2. **Workflow Simulation**
- Tests realistic agent communication patterns
- Validates message content and metadata flow
- Ensures project consistency across agent handoffs

### 3. **Error Resilience**
- Tests system behavior when individual agents fail
- Validates graceful degradation and error propagation
- Ensures broker stability under error conditions

## Example Test Scenarios

### Full Workflow Test
```python
# Simulates: Orchestrator → BA → Architect → Developer → Tester → Orchestrator
initial_message = Message(
    from_agent=AgentType.ORCHESTRATOR,
    to_agent=AgentType.BA,
    message_type=MessageType.SPECIFICATION,
    content="Please analyze this e-commerce project",
    project_id="ecommerce_001"
)
```

### BA to Architect Flow
```python
# Tests specific BA analysis to Architect design handoff
ba_message = Message(
    from_agent=AgentType.BA,
    to_agent=AgentType.ARCHITECT,
    content="Analysis complete with requirements and constraints",
    metadata={"analysis_data": {...}}
)
```

## Benefits of This Test Suite

1. **Fast Execution**: No external API calls or real agent initialization
2. **Reliable**: Deterministic outcomes without network dependencies  
3. **Comprehensive**: Covers all critical communication paths
4. **Maintainable**: Clear separation of concerns and good documentation
5. **Debuggable**: Easy to understand message flows and identify issues

## Future Enhancements

- Add performance benchmarks for message throughput
- Add integration tests with real agents (when API keys available)
- Add message persistence and recovery testing
- Add load testing for high-volume scenarios
