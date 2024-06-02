from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def menu(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="add_operation", description="Добавление операций"),
        BotCommand(command="operations", description="Просмотр операций"),
        BotCommand(command="reg", description="Регистрация")
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
