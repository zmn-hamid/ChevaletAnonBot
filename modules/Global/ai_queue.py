from typing import List, Union


class AIQueueManager:
    queue: List[List[int | str]] = []  # [message_id, text]

    def add_to_queue(self, message_id: str, text: str):
        self.queue.append([message_id, text])

    def get_queue(self):
        return self.queue

    def delete_item(self, index: int) -> None:
        self.queue.pop(index)


ai_queue_manager = AIQueueManager()
