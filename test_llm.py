import asyncio
import os
import sys

# Ensure apps/api is in python path
sys.path.insert(0, os.path.abspath('apps/api'))

from app.core.config import get_settings
from app.agents.llm import OpenAIProvider, LLMMessage, ToolCall
from app.agents.tools import create_catalog_tool_registry

async def test_llm():
    settings = get_settings()
    
    print('LLM provider:', settings.llm_provider)
    print('LLM model:', settings.llm_model)
    print('API key present:', bool(settings.llm_api_key))
    if settings.llm_api_key:
        print('API key length:', len(settings.llm_api_key))
        prefix = settings.llm_api_key[:8] if len(settings.llm_api_key) >= 8 else settings.llm_api_key
        print('API key prefix:', prefix)
        
    try:
        provider = OpenAIProvider(api_key=settings.llm_api_key, model=settings.llm_model)
        
        # Make the smallest possible OpenAI request
        messages = [LLMMessage(role='user', content='Say hello')]
        print('Testing small LLM generate_with_tools()...')
        response = await provider.generate_with_tools(messages=messages, tools=[])
        print('Response message:', response.message.content)
        
        print('Testing with tools schemas...')
        registry = create_catalog_tool_registry()
        tools = registry.get_openai_tool_schemas()
        response2 = await provider.generate_with_tools(messages=messages, tools=tools)
        print('Response message with tools:', response2.message.content)
        
    except Exception as e:
        import traceback
        print(f'Exception class: {e.__class__.__name__}')
        print(f'Exception message: {str(e)}')
        print('Traceback:')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_llm())
