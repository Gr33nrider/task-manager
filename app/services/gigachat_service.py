import json
import logging
from typing import List, Dict, Any, Optional
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class GigaChatService:
    """Сервис для работы с GigaChat API"""
    
    def __init__(self):
        self.client = GigaChat(
            credentials=settings.gigachat_credentials,
            scope=settings.gigachat_scope,
            model=settings.gigachat_model,
            verify_ssl_certs=False,
            timeout=60.0,
        )
    
    async def decompose_task(
        self, 
        title: str, 
        description: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Разбивает задачу на подзадачи с оценкой времени
        """
        prompt = self._build_decomposition_prompt(title, description)
        
        try:
            response = await self._async_chat(prompt)
            subtasks = self._parse_subtasks_response(response)
            return subtasks
        except Exception as e:
            logger.error(f"GigaChat decomposition failed: {e}")
            return [{
                "title": f"Разобрать задачу: {title}",
                "estimated_hours": 1.0
            }]
    
    async def estimate_task_time(self, title: str, description: Optional[str] = None) -> float:
        """Оценивает время выполнения задачи в часах"""
        prompt = self._build_estimation_prompt(title, description)
        
        try:
            response = await self._async_chat(prompt)
            hours = self._parse_estimation_response(response)
            return hours
        except Exception as e:
            logger.error(f"GigaChat estimation failed: {e}")
            return 4.0
    
    def _build_decomposition_prompt(self, title: str, description: Optional[str]) -> str:
        """Создаёт промпт для декомпозиции задачи"""
        task_text = f"Название задачи: {title}\n"
        if description:
            task_text += f"Описание: {description}\n"
        
        return f"""
Ты — Agile-коуч и эксперт по декомпозиции задач в IT-разработке.

{task_text}

Разбей эту задачу на 3-7 конкретных подзадач. Для каждой подзадачи:
1. Дай чёткое название
2. Оцени время выполнения в часах (от 0.5 до 8 часов)

Верни ответ ТОЛЬКО в формате JSON массива:
[
    {{"title": "Название подзадачи 1", "estimated_hours": 2.5}},
    {{"title": "Название подзадачи 2", "estimated_hours": 1.0}}
]

Никаких пояснений, только JSON!
"""
    
    def _build_estimation_prompt(self, title: str, description: Optional[str]) -> str:
        """Создаёт промпт для оценки времени"""
        task_text = f"Название задачи: {title}\n"
        if description:
            task_text += f"Описание: {description}\n"
        
        return f"""
Ты — эксперт по оценке задач в IT-разработке.

{task_text}

Оцени общее время выполнения этой задачи в часах. Учти:
- Время на анализ и планирование
- Время на разработку
- Время на тестирование
- Время на документацию

Верни ответ ТОЛЬКО в формате JSON:
{{"estimated_hours": 4.5}}

Никаких пояснений, только JSON!
"""
    
    async def _async_chat(self, prompt: str) -> str:
        """
        Асинхронный вызов GigaChat.
        GigaChat SDK пока не имеет встроенной асинхронности,
        поэтому используем run_in_executor для неблокирующего вызова.
        """
        def sync_chat():
            messages = [
                Messages(role=MessagesRole.SYSTEM, content="Ты — полезный AI-ассистент."),
                Messages(role=MessagesRole.USER, content=prompt)
            ]
            chat = Chat(messages=messages, temperature=settings.gigachat_temperature)
            response = self.client.chat(chat)
            return response.choices[0].message.content
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sync_chat)
        return result
    
    def _parse_subtasks_response(self, response: str) -> List[Dict[str, Any]]:
        """Парсит ответ GigaChat в список подзадач"""
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                subtasks = json.loads(json_str)
                
                if isinstance(subtasks, list):
                    validated = []
                    for item in subtasks:
                        if isinstance(item, dict) and "title" in item:
                            validated.append({
                                "title": item["title"],
                                "estimated_hours": float(item.get("estimated_hours", 1.0))
                            })
                    return validated
            
            raise ValueError("Invalid JSON format")
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse GigaChat response: {response[:200]}")
            return [{
                "title": response[:200] if response else "Разобрать задачу",
                "estimated_hours": 2.0
            }]
    
    def _parse_estimation_response(self, response: str) -> float:
        """Парсит ответ GigaChat в число часов"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                return float(data.get("estimated_hours", 4.0))
            
            raise ValueError("Invalid JSON format")
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse estimation response: {response[:200]}")
            return 4.0


gigachat_service = GigaChatService()