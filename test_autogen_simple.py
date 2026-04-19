#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

async def test_autogen():
    try:
        print("Testing AutoGen configuration...")

        # Test imports
        from config.autogen_config import get_llm_config
        config = get_llm_config()
        print(f"Config loaded: {config is not None}")

        if config:
            print(f"Model: {config['config_list'][0]['model']}")
            print(f"API key present: {bool(config['config_list'][0]['api_key'])}")
            print(f"Base URL: {config['config_list'][0]['base_url']}")

        # Test agent creation
        from app.agents.autogen_agents import AutoGenAgentFactory
        print("Creating agents...")
        planner, executor, critic = AutoGenAgentFactory.create_agents("TEST-001")
        print("Agents created successfully")

        # Test basic team setup
        from autogen_agentchat.conditions import TextMentionTermination
        from autogen_agentchat.teams import RoundRobinGroupChat

        termination = TextMentionTermination("TERMINATE")
        team = RoundRobinGroupChat([planner, executor, critic], termination_condition=termination)
        print("Team created successfully")

        # Test simple message
        print("Testing simple message...")
        result = await team.run(task="Hello, this is a test message. Please respond with TERMINATE.")
        print(f"Response received: {len(result.messages) if hasattr(result, 'messages') else 'No messages'}")

        print("AutoGen test completed successfully!")

    except Exception as e:
        print(f"AutoGen test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_autogen())