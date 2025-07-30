from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    'calculator',
    host='0.0.0.0',
    port=8050
)

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together"""
    return a+b

@mcp.tool()
def call(name: str)->str:
    """Greets user by name"""
    return f"Hello {name}"

if __name__ == '__main__':
    transport = 'stdio'
    if transport == 'stdio':
        print('server')
        mcp.run(transport='stdio')
    elif transport == 'sse':
        print('remote')
        mcp.run(transport='sse')