import uuid
from typing import List, Optional

from steamship import Block, Task
from steamship.agents.llms.openai import OpenAI
from steamship.agents.react import ReACTAgent
from steamship.agents.schema import AgentContext, Action, FinishAction
from steamship.agents.schema.context import Metadata
from steamship.agents.service.agent_service import AgentService
from steamship.agents.tools.search import SearchTool
from steamship.agents.utils import with_llm
from steamship.invocable import post
from steamship.invocable.mixins.indexer_pipeline_mixin import IndexerPipelineMixin
from steamship.utils.repl import AgentREPL

from example_tools.vector_search_qa_tool import VectorSearchQATool
from mycroft_transport import MycroftTransport


class MycroftAgentService(AgentService):


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._agent = ReACTAgent(
            tools=[
                SearchTool(),
            ],
            llm=OpenAI(self.client, temperature=0),
        )
        self.add_mixin(
            MycroftTransport(
                client=self.client, agent_service=self, agent=self._agent
            )
        )

