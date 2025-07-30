import asyncio 
from mcp import ClientSession, StdioServerParameters
import requests 

from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command='python3',
        args=['server.py']
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            while True:
                 should_continue = await chat_with_tools(session)
                 if not should_continue:
                      break
                 print('Pass')



async def chat_with_tools(session : ClientSession):
            user_question = input('You: ')

            if user_question.lower()=='exit':
                return False


            tools = [{
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "adds two float numbers together",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"}
                        },
                        "required": ["a", "b"]
                    }
                }
            }]

            response = requests.post('http://localhost:11434/api/chat', json={
                'model':'qwen3:1.7b',
                "messages": [{"role": "user", "content": user_question}],
                'tools': tools,
                'think':True,
                "stream": False
            })

            result = response.json()
            message = result['message']

            if 'tool_calls' in message:
                tool_call = message['tool_calls'][0]
                name = tool_call["function"]['name']
                args = tool_call["function"]['arguments']
                print(f'Ollama wants to call tool {name} with args {args}')

                
                result_mcp = await session.call_tool(name,args)
                tool_output =  result_mcp.content[0].text
                print(f'Mcp response is {tool_output}')

                final_response = requests.post('http://localhost:11434/api/chat', json={
                'model':'qwen3:1.7b',
                "messages": [{"role": "user", "content": user_question},message,{'role':'tool' , "content":tool_output}],
                'tools': tools,
                "stream": False,
                'think':False
            })
                final_answer = final_response.json()["message"]["content"]
                print(f"Final answer: {final_answer}")
            else:
                print(f"Ollama answered directly: {message['content']}")
            return True




if __name__ == '__main__':
    asyncio.run(main())