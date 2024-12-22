import os
import disnake
from disnake.ext import commands
from disnake import TextInputStyle
import sqlite3
from telegram import Bot
import vk_api
from datetime import datetime
import pytz
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
VK_TOKEN = os.getenv('VK_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
VK_GROUP_ID = int(os.getenv('VK_GROUP_ID'))


# Определяем модальное меню для опроса
class MyModal(disnake.ui.Modal):
    def __init__(self, channel_id):
        self.channel_id = channel_id
        components = [
            disnake.ui.TextInput(
                label="Название",
                placeholder="Введите название embed",
                custom_id="name",
                style=TextInputStyle.short,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Описание для переноса используйте /",
                placeholder="Введите сообщение",
                custom_id="message",
                style=TextInputStyle.paragraph,
            ),
            disnake.ui.TextInput(
                label="HEX цвет",
                placeholder="Введите HEX код цвета (например, #FF5733)",
                custom_id="color",
                style=TextInputStyle.short,
                max_length=7,
            ),
            disnake.ui.TextInput(
                label="Thumbnail URL",
                placeholder="Введите URL для thumbnail",
                custom_id="thumbnail",
                style=TextInputStyle.short,
                max_length=200,
            )
        ]
        super().__init__(title="Ваш опрос", components=components)

    async def callback(self, inter: disnake.ModalInteraction):
        name = inter.text_values["name"]
        message = inter.text_values["message"].replace('/', '\n')  # Заменяем '/' на перенос строки
        color_value = inter.text_values["color"]
        
        # Проверяем, что color_value является корректным HEX-кодом
        if len(color_value) == 7 and color_value.startswith('#') and all(c in '0123456789abcdefABCDEF' for c in color_value[1:]):
            thumbnail_url = inter.text_values["thumbnail"]  # Получаем URL для thumbnail
            channel = inter.guild.get_channel(int(self.channel_id))

            default_footer = "NEW LEGACY © 2024 Все права защищены"  # Вернули значение
            footer_icon_url = "https://cdn.discordapp.com/attachments/1320038948080320624/1320097297291284551/LogoServer2.png?"  # Вернули значение


            embed = disnake.Embed(title="Подтверждение публикации", color=int(color_value.lstrip('#'), 16))
            embed.set_footer(text=default_footer, icon_url=footer_icon_url)
            embed.add_field(name="Название", value=name, inline=False)
            embed.add_field(name="Описание", value=message, inline=False)
            embed.add_field(name="Цвет", value=color_value, inline=False)
            embed.add_field(name="Thumbnail", value=thumbnail_url, inline=False)
            embed.set_thumbnail(url=thumbnail_url)

            await inter.response.send_message(
                f"Вы уверены, что хотите опубликовать это сообщение в канале {channel.mention}?",
                embed=embed,
                components=[
                    disnake.ui.Button(label="Да", style=disnake.ButtonStyle.success, custom_id="confirm"),
                    disnake.ui.Button(label="Нет", style=disnake.ButtonStyle.danger, custom_id="cancel")
                ], ephemeral=True
            )
        else:
            await inter.response.send_message("Ошибка: некорректный HEX-код цвета.", ephemeral=True)

class ChannelDropdown(disnake.ui.StringSelect):
    def __init__(self, channels):
        options = [disnake.SelectOption(label=channel.name, value=str(channel.id)) for channel in channels if isinstance(channel, disnake.TextChannel)]
        super().__init__(
            placeholder="Выберите канал",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.send_modal(modal=MyModal(channel_id=self.values[0]))

class DropDownView(disnake.ui.View):
    def __init__(self, channels):
        super().__init__()
        self.add_item(ChannelDropdown(channels))

bot = commands.InteractionBot()

@bot.slash_command(name="panel")
@commands.has_permissions(administrator=True)
async def panel(inter: disnake.ApplicationCommandInteraction):
    embed = disnake.Embed(title="Панель управления", description="Выберите действие:", color=0x808080)
    default_footer = "NEW LEGACY © 2024 Все права защищены"
    footer_icon_url = "https://cdn.discordapp.com/attachments/1320038948080320624/1320097297291284551/LogoServer2.png?"
    embed.set_footer(text=default_footer, icon_url=footer_icon_url)
    await inter.response.send_message(embed=embed, components=[
        disnake.ui.Button(label="EmbedMenu", style=disnake.ButtonStyle.grey, custom_id="embed_menu"),
        disnake.ui.Button(label="WipeMenu", style=disnake.ButtonStyle.grey, custom_id="wipe_menu")
    ], ephemeral=True)

@bot.listen("on_button_click")
async def button_listener(inter: disnake.MessageInteraction):
    default_footer = "NEW LEGACY © 2024 Все права защищены"
    footer_icon_url = "https://cdn.discordapp.com/attachments/1320038948080320624/1320097297291284551/LogoServer2.png?"
    
    if inter.component.custom_id == "confirm":
        await inter.response.defer()
        if inter.message.embeds:
            embed = inter.message.embeds[0]
            name = embed.fields[0].value if len(embed.fields) > 0 else "Нет названия"
            message = embed.fields[1].value if len(embed.fields) > 1 else "Нет сообщения"
            thumbnail_url = embed.fields[3].value if len(embed.fields) > 3 else None
            color = embed.color
        else:
            await inter.followup.send("Ошибка: сообщение не содержит embed.", ephemeral=True)
            return

        channel_id = inter.message.content.split(" ")[-1].strip('<>#')
        channel_id = channel_id.split('>')[0]
        try:
            channel = inter.guild.get_channel(int(channel_id))
        except ValueError:
            await inter.followup.send("Ошибка: некорректный ID канала.", ephemeral=True)
            return

        if channel:
            embed = disnake.Embed(title=name, description=message, color=color)
            if thumbnail_url:
                embed.set_thumbnail(url=thumbnail_url)
            embed.set_footer(text=default_footer, icon_url=footer_icon_url)
            await channel.send(embed=embed)
            await inter.followup.send("Сообщение успешно опубликовано!", ephemeral=True)
        else:
            await inter.followup.send("Ошибка: Канал не найден.", ephemeral=True)
    elif inter.component.custom_id == "cancel":
        await inter.response.send_message("Публикация отменена.", ephemeral=True)
    elif inter.component.custom_id == "embed_menu":
        channels = inter.guild.channels
        view = DropDownView(channels)
        await inter.response.send_message("Пожалуйста, выберите канал:", view=view, ephemeral=True)
    elif inter.component.custom_id == "wipe_menu":
        embed = disnake.Embed(title="Информация об оповещении", color=0x808080)
        embed.add_field(name="Дата Оповещение", value="22.12.2024-19.56 ПО МСК", inline=False)
        embed.add_field(name="Текст Оповещение", value="Ваш текст сообщения", inline=False)

        await inter.response.send_message(embed=embed, components=[
            disnake.ui.Button(label="Редактировать", style=disnake.ButtonStyle.grey, custom_id="edit_notification"),
            disnake.ui.Button(label="Отправить сейчас", style=disnake.ButtonStyle.success, custom_id="send_now")
        ], ephemeral=True)
    elif inter.component.custom_id == "edit_notification":
        db = sqlite3.connect('notifications.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM notifications WHERE id=1")
        row = cursor.fetchone()
        db.close()

        if row and len(row) >= 3:
            date_notification = row[1]
            message_notification = row[2]
            thumbnail_url = row[3] if len(row) > 3 else None
        else:
            await inter.followup.send("Ошибка: уведомление не найдено.", ephemeral=True)
            return

        await inter.response.send_modal(modal=EditNotificationModal(date_notification, message_notification, thumbnail_url))
    elif inter.component.custom_id == "send_now":
        await send_notification()
        await inter.response.send_message("Уведомление отправлено!", ephemeral=True)

async def send_notification():
    db = sqlite3.connect('notifications.db')
    cursor = db.cursor()
    cursor.execute("SELECT * FROM notifications WHERE id=1")
    row = cursor.fetchone()
    db.close()

    if row:
        date_notification, message_notification = row[1], row[2]
        msk_tz = pytz.timezone('Europe/Moscow')
        notification_date = datetime.strptime(date_notification, "%d.%m.%Y-%H:%M")
        notification_date = msk_tz.localize(notification_date)

        current_time = datetime.now(msk_tz)

        if notification_date >= current_time:
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            if channel:
                await channel.send(message_notification)

            telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
            await telegram_bot.send_message(chat_id='-1002471147671', text=message_notification)

            vk_session = vk_api.VkApi(token=VK_TOKEN)
            vk = vk_session.get_api()

            try:
                vk.wall.post(owner_id=VK_GROUP_ID, message=message_notification)
            except vk_api.exceptions.ApiError:
                pass

        db = sqlite3.connect('notifications.db')
        cursor = db.cursor()
        cursor.execute("UPDATE notifications SET date=NULL, message=NULL WHERE id=1")
        db.commit()
        db.close()

class EditNotificationModal(disnake.ui.Modal):
    def __init__(self, date_notification, message_notification, thumbnail_url):
        super().__init__(title="Редактировать Оповещение", components=[
            disnake.ui.TextInput(label="Дата Оповещение (формат: 22.12.2024-19:26)", placeholder="Введите дату", custom_id="date_input", value=date_notification),
            disnake.ui.TextInput(label="Текст Оповещение", placeholder="Введите текст сообщения", custom_id="message_input", value=message_notification)
        ])
        self.thumbnail_url = thumbnail_url

    async def callback(self, inter: disnake.ModalInteraction):
        date_notification = inter.text_values["date_input"]
        message_notification = inter.text_values["message_input"]

        db = sqlite3.connect('notifications.db')
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY,
            date TEXT,
            message TEXT
        )""")
        
        cursor.execute("SELECT * FROM notifications WHERE id=1")
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE notifications SET date=?, message=? WHERE id=1", (date_notification, message_notification))
        else:
            cursor.execute("INSERT INTO notifications (id, date, message) VALUES (1, ?, ?)", (date_notification, message_notification))
        db.commit()
        db.close()

        try:
            msk_tz = pytz.timezone('Europe/Moscow')
            notification_date = msk_tz.localize(datetime.strptime(date_notification, "%d.%m.%Y-%H:%M"))
            if notification_date < datetime.now(msk_tz):
                await inter.response.send_message("Ошибка: эта дата уже прошла.", ephemeral=True)
                return
        except ValueError:
            await inter.response.send_message("Ошибка: неверный формат даты.", ephemeral=True)
            return

        embed = disnake.Embed(title="Информация об оповещении", color=0x808080)
        embed.add_field(name="Дата Оповещение", value=f"<t:{int(notification_date.timestamp())}:f>", inline=False)
        embed.add_field(name="Текст Оповещение", value=message_notification, inline=False)
        if self.thumbnail_url:
            embed.set_thumbnail(url=self.thumbnail_url)

        message_to_update = await inter.channel.fetch_message(inter.message.id)
        await message_to_update.edit(embed=embed)

        await inter.response.send_message("Оповещение успешно обновлено!", ephemeral=True)

async def notification_checker():
    while True:
        db = sqlite3.connect('notifications.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM notifications WHERE id=1")
        row = cursor.fetchone()
        db.close()

        if row:
            date_notification, message_notification = row[1], row[2]
            if date_notification:  # Проверяем, что date_notification не None
                msk_tz = pytz.timezone('Europe/Moscow')
                notification_date = datetime.strptime(date_notification, "%d.%m.%Y-%H:%M")
                notification_date = msk_tz.localize(notification_date)

                current_time = datetime.now(msk_tz)

                if notification_date <= current_time:
                    channel = bot.get_channel(DISCORD_CHANNEL_ID)
                    if channel:
                        await channel.send(message_notification)

                    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
                    await telegram_bot.send_message(chat_id='-1002471147671', text=message_notification)

                    vk_session = vk_api.VkApi(token=VK_TOKEN)
                    vk = vk_session.get_api()

                    try:
                        vk.wall.post(owner_id=VK_GROUP_ID, message=message_notification)
                    except vk_api.exceptions.ApiError:
                        pass

                    db = sqlite3.connect('notifications.db')
                    cursor = db.cursor()
                    cursor.execute("UPDATE notifications SET date=NULL, message=NULL WHERE id=1")
                    db.commit()
                    db.close()
            else:
                # Обработка случая, когда date_notification равно None
                await asyncio.sleep(60)
                continue
        await asyncio.sleep(60)

bot.loop.create_task(notification_checker())

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
