import os
import re

def refactor():
    files = [
        "d:/Projects/Afford Medicals/RA2311003020537/vehicle_maintence_scheduler/scheduler.py",
        "d:/Projects/Afford Medicals/RA2311003020537/vehicle_maintence_scheduler/main.py",
        "d:/Projects/Afford Medicals/RA2311003020537/vehicle_maintence_scheduler/api_client.py",
        "d:/Projects/Afford Medicals/RA2311003020537/notification_app_be/priority_inbox.py",
        "d:/Projects/Afford Medicals/RA2311003020537/notification_app_be/main.py",
        "d:/Projects/Afford Medicals/RA2311003020537/notification_app_be/api_client.py",
        "d:/Projects/Afford Medicals/RA2311003020537/logging_middleware/middleware.py",
        "d:/Projects/Afford Medicals/RA2311003020537/auth/token_manager.py",
    ]

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace imports:
        # from logging_middleware.logger import logger
        # from logging_middleware import logger
        content = re.sub(r'from logging_middleware\.logger import logger', 'from logging_middleware.logger import Log', content)
        content = re.sub(r'from logging_middleware import logger', 'from logging_middleware.logger import Log', content)
        
        # Replace logger.set_token(token)
        content = re.sub(r'logger\.set_token\((.*?)\)', r'set_token(\1)', content)
        # Import set_token where token_manager uses it
        if "token_manager.py" in filepath:
            content = content.replace("from logging_middleware.logger import Log", "from logging_middleware.logger import Log, set_token")

        # Replace logger.<level>(message, package="...")
        # Handle single and multiline string/kwargs
        # Simplistic regex to match logger.info("...", package="...")
        
        def replace_log(match):
            level = match.group(1)
            args = match.group(2)
            
            # Find the message (first argument, can be f-string or string, and could span lines)
            # Find the package
            package_match = re.search(r'package\s*=\s*(["\']\w+["\'])', args)
            package = package_match.group(1) if package_match else '"utils"'
            
            # Message is everything before `, package=`
            message_part = re.sub(r',\s*package\s*=\s*["\']\w+["\'].*', '', args, flags=re.DOTALL).strip()
            
            return f'Log("backend", "{level}", {package}, {message_part})'

        content = re.sub(r'logger\.(debug|info|warn|error|fatal)\((.*?)\)', replace_log, content, flags=re.DOTALL)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

refactor()
