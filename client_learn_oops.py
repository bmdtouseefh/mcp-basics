import asyncio 
from mcp import ClientSession, StdioServerParameters
import ollama
from ollama import Message, AsyncClient
import requests 
from typing import Optional
from contextlib import AsyncExitStack

from mcp.client.stdio import stdio_client

class SimpleMCPClient():
     
    def __init__(self, model):
          self.session: Optional[ClientSession] = None
          self.exit_stack = AsyncExitStack()
          self.model = model
          self.tools = []
          self.chat_history = []

    async def chat_with_tools(session : ClientSession):
            user_question = input('You: ')

            if user_question.lower()=='exit':
                return False

    
    def add_to_history(self, role, content, tool_calls=None):
        """Add message to chat history"""
        message = {"role": role, "content": content}
        
        if tool_calls:
            message["tool_calls"] = tool_calls
            
        self.chat_history.append(message)
        
        # if len(self.chat_history) > 20:
        #     self.chat_history = self.chat_history[-20:]
    
    

    async def process_query(self, query: str) -> str:
         """Process a query using Qwen 3 and available tools"""

         self.add_to_history('user',query)

         response = await AsyncClient().chat(self.model,self.chat_history,tools=self.tools, stream=False)

         message: Message = response['message']

         print(message)

         if message.get('tool_calls'):
            return await self.handle_tool_calls_with_history(message)
         else:
            self.add_to_history("assistant", message['content'])
            return message['content']
         
    async def handle_tool_calls_with_history(self, assistant_message: Message):
        """Process tool calls and maintain history"""

        self.add_to_history("assistant", assistant_message.get("content", ""), 
                           assistant_message.get("tool_calls"))
        
        # Process each tool call
        for tool_call in assistant_message["tool_calls"]:
            tool_name = tool_call["function"]["name"]
            args = tool_call["function"]["arguments"]
            
            print(f"🔧 Using {tool_name} with {args}...")
            
            try:
                # Call MCP tool
                mcp_result = await self.session.call_tool(tool_name, args)
                tool_output = mcp_result.content[0].text
                
                # Add tool result to history
                self.add_to_history("tool", tool_output)
                
            except Exception as e:
                error_output = f"Error calling {tool_name}: {e}"
                self.add_to_history("tool", error_output)

        try:
            print(f'History after tool pass:{self.chat_history}')
            final_response = await AsyncClient().chat(
                model=self.model,
                messages=self.chat_history
            )
            
            final_content = final_response['message']['content']
            self.add_to_history("assistant", final_content)
            print(f'History at last pass:{self.chat_history}')
            return final_content
            
        except Exception as e:
            return f"❌ Error getting final response: {e}"
    
         

    async def connect(self, server_script: str):
        server_params = StdioServerParameters(
        command='python3',
        args=[server_script],
        env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.read, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.read, self.write))
        await self.session.initialize()

        response = await self.session.list_tools()
        self.tools = [
             {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            } for tool in response.tools]
        print('\n Connected to MCP server with tools: ', [tool['function']['name'] for tool in self.tools])


async def main():
    client = SimpleMCPClient('llama3.2:3b')

    try:
        print("🔌 Connecting to MCP server...")
        await client.connect('server.py')
        
        print("\n🤖 Chat with Ollama + MCP Tools")
        print("Type 'quit' to exit\n")

        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("Assistant: ", end="", flush=True)
            response = await client.process_query(user_input)
            print('from loop',response)
            print()






    except KeyboardInterrupt:
         print('Bye')
    except Exception as e:
         print('Error:',e)









if __name__ == '__main__':
    asyncio.run(main())