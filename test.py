import disnake
from disnake.ext import commands

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Отправляем chat_id в ответ на любое сообщение
    await message.channel.send(f'Ваш chat_id: {message.author.id}')

bot.run('YOUR_TELEGRAM_BOT_TOKEN')  # Замените на ваш токен бота