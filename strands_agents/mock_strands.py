"""
Mock implementation of AWS Strands Agents framework for testing
This will be replaced with the actual framework when available
"""

class Agent:
    """Mock Strands Agent"""
    
    def __init__(self, model=None, system_prompt=None, tools=None):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
    
    def __call__(self, query):
        """Mock agent execution"""
        return f"Mock response for query: {query}"

class MockTool:
    """Mock tool implementation"""
    
    def __init__(self, name, description, function, parameters):
        self.name = name
        self.description = description
        self.function = function
        self.parameters = parameters

def create_custom_tool(name, description, function, parameters):
    """Mock tool creation"""
    return MockTool(name, description, function, parameters)

# Mock strands_agents_tools module
class MockStrandsAgentsTools:
    create_custom_tool = staticmethod(create_custom_tool)