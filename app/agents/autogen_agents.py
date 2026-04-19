from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.autogen_config import get_llm_config
from config import prompts
from app.tools.tool_registry import registry


class AutoGenAgentFactory:
    """Factory to create AutoGen 0.7+ agents with specific roles."""

    @staticmethod
    def create_agents(ticket_id: str):
        config_wrapper = get_llm_config()
        inner_config = config_wrapper["config_list"][0]

        model_client = OpenAIChatCompletionClient(
            model=inner_config["model"],
            api_key=inner_config["api_key"],
            base_url=inner_config["base_url"],
            model_info=inner_config["model_info"],
        )

        # Tools
        autogen_tools = registry.get_autogen_tools()

        # 1. Planner Agent
        planner = AssistantAgent(
            name="Planner",
            model_client=model_client,
            system_message=prompts.PLANNER_SYSTEM_PROMPT +
"\n\nYou are NOT just planning. You MUST produce FINAL RESOLUTION."
"\nReturn ONLY valid JSON in this format:"
"\n{"
"\n  \"status\": \"approved | resolved | escalated\","
"\n  \"confidence_score\": number between 0 and 1,"
"\n  \"reasoning\": \"clear explanation\","
"\n  \"final_message\": \"customer-facing response\""
"\n}"
"\nDo NOT include tool execution plans or steps."
"\nDo NOT return anything outside JSON."
"\nAfter JSON, write TERMINATE."
        )

        # 2. Executor Agent
        executor = UserProxyAgent(
            name="Executor",
            description="Executor agent that processes and executes tasks"
        )

        # 3. Critic Agent
        critic = AssistantAgent(
            name="Critic",
            model_client=model_client,
            system_message=prompts.CRITIC_SYSTEM_PROMPT +
            "\nReview the final response."
            "\nIf it is valid, repeat the FINAL JSON and then write TERMINATE."
            "\nDo not add extra conversation after TERMINATE."
        )

        return planner, executor, critic