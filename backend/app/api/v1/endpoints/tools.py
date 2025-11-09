from fastapi import APIRouter
from app.tools.factory import ToolFactory
from app.utils.logger import logger

router = APIRouter()


@router.get("/tools/status")
async def get_tools_status():
    """
    Get installation status of all pentesting tools
    """
    tools = ['nmap', 'nuclei', 'whatweb', 'sslscan']
    status = {}

    for tool_name in tools:
        try:
            tool = ToolFactory._tools[tool_name]()
            is_installed = tool.is_installed()
            status[tool_name] = {
                'installed': is_installed,
                'status': 'ready' if is_installed else 'mock mode'
            }
        except Exception as e:
            logger.error(f"Error checking {tool_name}: {str(e)}")
            status[tool_name] = {
                'installed': False,
                'status': 'error',
                'error': str(e)
            }

    all_installed = all(tool['installed'] for tool in status.values())

    return {
        'tools': status,
        'all_installed': all_installed,
        'message': 'All tools installed' if all_installed else 'Some tools missing - using mock mode'
    }
