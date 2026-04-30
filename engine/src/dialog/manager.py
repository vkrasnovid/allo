"""Dialog manager — orchestrates conversation flow."""

import json
import logging
from typing import AsyncGenerator, Optional

from src.state.redis_manager import DialogStateManager
from src.prompts.builder import build_system_prompt, build_tool_definitions, PromptBlock, ClientContext
from src.tools.executor import ToolExecutor
from src.dialog.guard import validate_llm_response_text, hallucination_log

logger = logging.getLogger(__name__)


class DialogManager:
    """
    Orchestrates the conversation: manages state, calls LLM, executes tools.
    """

    def __init__(
        self,
        state_manager: DialogStateManager,
        tool_executor: ToolExecutor,
        llm_client=None,  # OpenClaw or direct LLM client
    ):
        self.state = state_manager
        self.tools = tool_executor
        self.llm = llm_client

    async def process_user_message(
        self,
        tenant_id: str,
        call_id: str,
        text: str,
        client_phone: Optional[str] = None,
    ) -> dict:
        """
        Process a single user message through the dialog.
        Returns the AI response and any tool calls made.
        """

        # Add user message to history
        await self.state.add_message(tenant_id, call_id, "user", text)

        # Get dialog history
        messages = await self.state.get_llm_messages(tenant_id, call_id)

        # Build context
        context = await self.state.get_all_context(tenant_id, call_id)
        business_name = context.get("business_name", "Салон красоты")

        # Build client context
        client_ctx = None
        if client_phone:
            booking_info = await self.state.get_history_for_client(tenant_id, client_phone)
            client_data = await self.tools.booking_client.get_or_create_client(tenant_id, client_phone)
            if client_data and "client" in client_data:
                c = client_data["client"]
                client_ctx = ClientContext(
                    name=c.get("name"),
                    total_visits=c.get("total_visits", 0),
                    last_visit_at=c.get("last_visit_at"),
                )

        # Build system prompt
        prompt_blocks_raw = context.get("prompt_blocks", [])
        prompt_blocks = [
            PromptBlock(key=b.get("block_key", ""), content=b.get("content", ""), position=b.get("position", 0))
            for b in prompt_blocks_raw
        ]

        system_prompt = build_system_prompt(
            business_name=business_name,
            blocks=prompt_blocks,
            client_context=client_ctx,
        )

        # Prepare messages for LLM
        llm_messages = [{"role": "system", "content": system_prompt}]
        llm_messages.extend(messages)

        tool_defs = build_tool_definitions()

        result = {
            "reply": None,
            "tool_calls": [],
            "state": await self.state.get_state(tenant_id, call_id),
            "finished": False,
        }

        if self.llm:
            # Use LLM
            llm_result = await self.llm.chat_complete(
                messages=llm_messages,
                tools=tool_defs,
            )

            response_text = llm_result.get("content", "")
            tool_calls = llm_result.get("tool_calls", [])

            # Validate response
            response_text = validate_llm_response_text(response_text)

            result["reply"] = response_text

            # Execute tool calls
            for tc in tool_calls:
                tool_name = tc.get("function", {}).get("name", "")
                tool_args_raw = tc.get("function", {}).get("arguments", "{}")
                try:
                    tool_args = json.loads(tool_args_raw) if isinstance(tool_args_raw, str) else tool_args_raw
                except json.JSONDecodeError:
                    tool_args = {}

                tool_result = await self.tools.execute_tool(
                    tool_name=tool_name,
                    args=tool_args,
                    tenant_id=tenant_id,
                    call_id=call_id,
                )

                result["tool_calls"].append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": tool_result,
                })

                # Store tool result in dialog history
                await self.state.add_message(
                    tenant_id, call_id,
                    "system",
                    json.dumps({"tool_call": tool_name, "result": tool_result}, ensure_ascii=False),
                )
        else:
            # No LLM — return raw context (for testing)
            result["reply"] = "[NO LLM] Dialog manager running without LLM client"
            result["context"] = {
                "system_prompt_len": len(system_prompt),
                "message_count": len(messages),
                "state": result["state"],
            }

        # Add AI response to history
        if result["reply"]:
            await self.state.add_message(tenant_id, call_id, "assistant", result["reply"])

        return result

    async def handle_interrupt(self, tenant_id: str, call_id: str, interrupted_text: str):
        """Handle client interrupting AI speech."""
        await self.state.add_message(tenant_id, call_id, "system", f"[INTERRUPT] Клиент прервал: {interrupted_text}")
        logger.info(f"Dialog interrupted: call={call_id}, text='{interrupted_text}'")
