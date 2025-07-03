"""
Test agent using Google Gemini Flash LLM with ACP-SDK integration.

This agent demonstrates basic LLM integration and can be used for testing
the agent communication protocol and LLM responses.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from acp_sdk import server

from .base import BaseAgent, AgentCapability, Message, TaskResult, MessageType
from ..core.config import get_settings
from ..core.logging import get_logger


class TestAgent(BaseAgent):
    """Test agent using Google Gemini Flash for simple LLM interactions."""
    
    def __init__(self, agent_id: str = "test_agent"):
        super().__init__(agent_id, "Test Agent")
        self.settings = get_settings()
        self.llm: Optional[ChatGoogleGenerativeAI] = None
        
    async def initialize(self) -> bool:
        """Initialize the test agent with Gemini Flash LLM."""
        try:
            llm_config = self.settings.get_llm_config()
            
            if llm_config["provider"] != "google":
                self.logger.error("Test agent requires Google Gemini API key")
                return False
            
            self.llm = ChatGoogleGenerativeAI(
                model=llm_config["model"],
                google_api_key=llm_config["api_key"],
                temperature=0.7,
                max_tokens=1000,
            )
            
            self.logger.info(f"Initialized with model: {llm_config['model']}")
            
            # Add capabilities
            self.add_capability(AgentCapability(
                name="chat",
                description="Chat with Gemini Flash LLM",
                input_schema={"message": "string"},
                output_schema={"response": "string", "confidence": "float"}
            ))
            
            self.add_capability(AgentCapability(
                name="analyze_text",
                description="Analyze text for insights",
                input_schema={"text": "string", "analysis_type": "string"},
                output_schema={"analysis": "string", "insights": "array"}
            ))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize: {str(e)}")
            return False
    
    async def process_message(self, message: Message) -> Optional[Message]:
        """Process incoming messages."""
        try:
            content = message.content
            action = content.get("action")
            
            if action == "chat":
                response = await self._handle_chat(content.get("message", ""))
                return Message(
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={
                        "action": "chat_response",
                        "response": response["response"],
                        "confidence": response["confidence"],
                        "timestamp": datetime.now().isoformat()
                    },
                    correlation_id=message.id
                )
            
            elif action == "analyze_text":
                analysis = await self._handle_text_analysis(
                    content.get("text", ""),
                    content.get("analysis_type", "general")
                )
                return Message(
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type=MessageType.RESPONSE,
                    content={
                        "action": "analysis_response",
                        "analysis": analysis["analysis"],
                        "insights": analysis["insights"],
                        "timestamp": datetime.now().isoformat()
                    },
                    correlation_id=message.id
                )
            
            else:
                return Message(
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type=MessageType.ERROR,
                    content={
                        "error": f"Unknown action: {action}",
                        "supported_actions": ["chat", "analyze_text"]
                    },
                    correlation_id=message.id
                )
                
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return Message(
                sender=self.agent_id,
                receiver=message.sender,
                message_type=MessageType.ERROR,
                content={"error": str(e)},
                correlation_id=message.id
            )
    
    async def execute_task(self, task: Dict[str, Any]) -> TaskResult:
        """Execute a specific task."""
        task_id = task.get("id", "unknown")
        start_time = datetime.now()
        
        try:
            task_type = task.get("type")
            
            if task_type == "chat":
                result = await self._handle_chat(task.get("message", ""))
            elif task_type == "analyze_text":
                result = await self._handle_text_analysis(
                    task.get("text", ""),
                    task.get("analysis_type", "general")
                )
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                task_id=task_id,
                agent_id=self.agent_id,
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"model": self.settings.google_model}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                task_id=task_id,
                agent_id=self.agent_id,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _handle_chat(self, message: str) -> Dict[str, Any]:
        """Handle chat interaction with Gemini Flash."""
        if not self.llm:
            raise RuntimeError("LLM not initialized")
        
        try:
            # Add context about the agent's purpose
            system_prompt = (
                "You are a helpful AI assistant for the Mairie Radar system, "
                "which analyzes French municipal budget data for anomalies. "
                "You can help users understand budget information, explain "
                "financial terms, and provide insights about municipal spending."
            )
            
            full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
            
            response = await self.llm.ainvoke(full_prompt)
            
            # Simple confidence estimation based on response length and content
            confidence = min(0.9, len(response.content) / 200.0 + 0.3)
            
            return {
                "response": response.content,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"Chat error: {str(e)}")
            return {
                "response": f"I'm sorry, I encountered an error: {str(e)}",
                "confidence": 0.0
            }
    
    async def _handle_text_analysis(self, text: str, analysis_type: str) -> Dict[str, Any]:
        """Handle text analysis requests."""
        if not self.llm:
            raise RuntimeError("LLM not initialized")
        
        try:
            if analysis_type == "budget":
                prompt = (
                    f"Analyze this budget-related text for key insights, "
                    f"anomalies, or important financial information:\n\n{text}\n\n"
                    f"Provide a structured analysis with specific insights."
                )
            elif analysis_type == "anomaly":
                prompt = (
                    f"Look for potential anomalies or irregularities in this text:\n\n{text}\n\n"
                    f"Identify any unusual patterns, discrepancies, or concerning elements."
                )
            else:
                prompt = f"Analyze this text and provide insights:\n\n{text}"
            
            response = await self.llm.ainvoke(prompt)
            
            # Extract insights (simple heuristic)
            insights = []
            for line in response.content.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or 
                           'insight' in line.lower() or 'important' in line.lower()):
                    insights.append(line.lstrip('-•').strip())
            
            return {
                "analysis": response.content,
                "insights": insights[:5]  # Limit to top 5 insights
            }
            
        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}")
            return {
                "analysis": f"Analysis failed: {str(e)}",
                "insights": []
            }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get list of agent capabilities."""
        return self.capabilities


# ACP-SDK Server Decorator Integration
@server.agent(
    name="test_agent",
    description="Test agent using Google Gemini Flash for LLM interactions",
    version="0.1.0"
)
class ACPTestAgent:
    """ACP-SDK wrapped version of the test agent."""
    
    def __init__(self):
        self.agent = TestAgent()
        self.logger = get_logger("acp.test_agent")
    
    @server.capability(
        name="chat",
        description="Chat with Gemini Flash LLM",
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "User message"}
            },
            "required": ["message"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "response": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            }
        }
    )
    async def chat(self, message: str) -> Dict[str, Any]:
        """Chat capability exposed via ACP."""
        self.logger.info(f"Chat request: {message[:50]}...")
        
        if not self.agent.llm:
            await self.agent.initialize()
        
        result = await self.agent._handle_chat(message)
        
        self.logger.info(f"Chat response generated with confidence: {result['confidence']}")
        return result
    
    @server.capability(
        name="analyze_text",
        description="Analyze text for insights and anomalies",
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
                "analysis_type": {
                    "type": "string", 
                    "enum": ["general", "budget", "anomaly"],
                    "description": "Type of analysis to perform"
                }
            },
            "required": ["text"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "analysis": {"type": "string"},
                "insights": {"type": "array", "items": {"type": "string"}}
            }
        }
    )
    async def analyze_text(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Text analysis capability exposed via ACP."""
        self.logger.info(f"Analysis request: {analysis_type} for {len(text)} characters")
        
        if not self.agent.llm:
            await self.agent.initialize()
        
        result = await self.agent._handle_text_analysis(text, analysis_type)
        
        self.logger.info(f"Analysis completed with {len(result['insights'])} insights")
        return result


# Factory function for creating the agent
def create_test_agent() -> TestAgent:
    """Create and return a test agent instance."""
    return TestAgent()


# Factory function for ACP-wrapped agent
def create_acp_test_agent() -> ACPTestAgent:
    """Create and return an ACP-wrapped test agent instance."""
    return ACPTestAgent()


# CLI entry point for running the agent standalone
async def main():
    """Run the test agent in standalone mode."""
    logger = get_logger("test_agent.main")
    
    try:
        agent = create_test_agent()
        
        if not await agent.initialize():
            logger.error("Failed to initialize agent")
            return
        
        logger.info("Test agent initialized successfully")
        logger.info("Starting agent loop...")
        
        # Run the agent
        await agent.run()
        
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 