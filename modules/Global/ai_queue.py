from typing import List

from telegram import Message


class AIQueueManager:
    queue: List[Message] = []

    def add_to_queue(self, message: Message):
        self.queue.append(message)

    def get_queue(self):
        return self.queue

    def delete_item(self, index: int) -> None:
        self.queue.pop(index)


ai_queue_manager = AIQueueManager()
