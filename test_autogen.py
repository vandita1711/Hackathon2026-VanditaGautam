#!/usr/bin/env python3

try:
    from config.autogen_config import get_llm_config
    config = get_llm_config()
    print('AutoGen config:', config is not None)
    if config:
        print('Model:', config['config_list'][0]['model'])
        print('API key present:', bool(config['config_list'][0]['api_key']))
        print('Base URL:', config['config_list'][0]['base_url'])
        print('Model info:', config['config_list'][0]['model_info'])
    else:
        print('No config returned - likely no API key')
except Exception as e:
    print('Error getting config:', e)
    import traceback
    traceback.print_exc()

# Test AutoGen import
try:
    import autogen
    print('AutoGen version:', autogen.__version__)
except Exception as e:
    print('AutoGen import error:', e)

# Test basic AutoGen functionality
try:
    from autogen import AssistantAgent
    print('AssistantAgent import successful')
except Exception as e:
    print('AssistantAgent import error:', e)