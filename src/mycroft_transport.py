import uuid
from typing import List, Optional

from steamship import Block, Steamship
from steamship.agents.mixins.transports.transport import Transport
from steamship.agents.schema import Metadata, AgentContext, Agent, LLMAgent
from steamship.agents.service.agent_service import AgentService
from steamship.agents.utils import with_llm
from steamship.invocable import post


class MycroftTransport(Transport):
	
	client: Steamship
	agent_service: AgentService
	agent: LLMAgent
	message_output: List[Block]

	def __init__(self, client: Steamship, agent_service: AgentService, agent: LLMAgent):
		super(MycroftTransport, self).__init__(client=client)
		self.client = client
		self.agent_service = agent_service
		self.agent = agent
		self.message_output = []
		self.voice_generator = client.use_plugin("elevenlabs")

	def _parse_inbound(self, payload: dict, context: Optional[dict] = None) -> Optional[Block]:
		mycroft_user_id = payload.get("user_id")
		message_text = payload.get("message")
		message_id = str(uuid.uuid4())
		result = Block(text=message_text)
		result.set_chat_id(str(mycroft_user_id))
		result.set_message_id(str(message_id))
		return result

	def _send(self, blocks: List[Block], metadata: Metadata):
		# This transport isn't a PUSH
		pass


	@post("mycroft_respond")
	def mycroft_respond(self, **payload) -> str:
		incoming_message = self.parse_inbound(payload)
		context = AgentContext.get_or_create(
			self.client, context_keys={"chat_id": incoming_message.chat_id}
		)
		context.chat_history.append_user_message(
			text=incoming_message.text, tags=incoming_message.tags
		)
		context.emit_funcs = [self.save_for_emit]

		context = with_llm(context=context, llm=self.agent.llm)
		try:
			self.agent_service.run_agent(self.agent, context)
		except Exception as e:
			self.message_output = [self.response_for_exception(e, chat_id=incoming_message.chat_id)]

		# We don't call self.steamship_widget_transport.send because the result is the return value
		text_response = "\n".join([block.text for block in self.message_output])
		voice_response = self.voice_generator.generate(text=text_response, append_output_to_file=True).wait()
		return voice_response.blocks[0].raw_data_url

	def save_for_emit(self, blocks: List[Block], metadata: Metadata):
		self.message_output = blocks