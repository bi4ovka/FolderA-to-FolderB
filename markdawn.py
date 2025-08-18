import re
from typing import List, Tuple
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

TOKEN = "8116261824:AAGQo1eyDljZPnQjq9Fsep0-hA9qQrzGRkY"

current_mode = "md"

def escape_markdown(text: str, mode: str = "md") -> str:
    """Экранирует специальные символы Markdown"""
    if mode == "md":
        escape_chars = r'_*`['
    else:  # md2
        escape_chars = r'_*[]()~`>#+-=|{}.!'
    
    pattern = '([' + re.escape(escape_chars) + '])'
    return re.sub(pattern, r'\\\1', text)

def split_text_with_code_blocks(text: str, max_length: int = 4096) -> List[Tuple[str, str]]:
    """
    Разбивает текст на части, сохраняя код-блоки
    Возвращает список кортежей (тип, текст)
    """
    text = text.strip()
    if not text:
        return []

    # Регулярка для поиска код-блоков
    code_block_pattern = re.compile(r'```[^\n]*\n[\s\S]*?\n```|```.*?```|`[^`]*`', re.MULTILINE)

    segments = []
    last_idx = 0
    for m in code_block_pattern.finditer(text):
        start, end = m.span()
        if start > last_idx:
            segments.append(("text", text[last_idx:start]))
        segments.append(("code", m.group()))
        last_idx = end
    if last_idx < len(text):
        segments.append(("text", text[last_idx:]))

    result = []
    current_chunk = ""
    current_type = "text"

    def flush_chunk():
        nonlocal current_chunk
        if current_chunk:
            result.append((current_type, current_chunk.strip()))
            current_chunk = ""

    for kind, content in segments:
        if kind == "code":
            flush_chunk()
            # Код-блоки отправляем как есть
            result.append(("code", content))
            current_type = "text"
            continue
        
        # Обычный текст разбиваем по словам
        words = content.split()
        for word in words:
            if len(current_chunk) + len(word) + 1 > max_length:
                flush_chunk()
            current_chunk += (" " if current_chunk else "") + word
    
    flush_chunk()
    return result

async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Я бот-тестировщик. Кидай текст, я нарежу. Можно переключать режим /mode md или /mode md2"
    )

async def mode_handler(message: types.Message):
    global current_mode
    args = message.text.strip().split()
    if len(args) == 1:
        await message.answer(f"Текущий режим: {current_mode}")
        return

    mode = args[1].lower()
    if mode in ["md", "md2"]:
        current_mode = mode
        await message.answer(f"Режим обновлён: {current_mode}")
    else:
        await message.answer("Неизвестный режим. Доступно: md, md2")

async def text_handler(message: types.Message):
    global current_mode
    if not message.text:
        return

    parts = split_text_with_code_blocks(message.text)
    parse_mode = "MarkdownV2" if current_mode == "md2" else "Markdown"

    for kind, text in parts:
        try:
            if kind == "code":
                # Код-блоки отправляем без изменений
                await message.answer(text, parse_mode=None)
            else:
                # Экранируем текст в соответствии с режимом
                escaped_text = escape_markdown(text, current_mode)
                # Разбиваем слишком длинные сообщения
                while len(escaped_text) > 4096:
                    part = escaped_text[:4096]
                    escaped_text = escaped_text[4096:]
                    await message.answer(part, parse_mode=parse_mode)
                if escaped_text:
                    await message.answer(escaped_text, parse_mode=parse_mode)
        except Exception as e:
            # Если возникла ошибка, отправляем как обычный текст
            await message.answer(f"Ошибка обработки. Отправляю как обычный текст:\n\n{text}")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.message.register(start_handler, Command("start"))
    dp.message.register(mode_handler, Command("mode"))
    dp.message.register(text_handler)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())