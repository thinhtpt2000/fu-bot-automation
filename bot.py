# bot.py
import os
from asyncio import TimeoutError
from sqlite3 import IntegrityError

import discord
from discord.ext import commands
from dotenv import load_dotenv

import automation
from enum_bot import BotStatus
import db_utils as db
import bot_utils as utils
import timeit

bot = commands.Bot(command_prefix='!!')


def run():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.command(help='Check schedule with saved FAP account')
async def schedule(ctx):
    mention = ctx.author.mention
    start = timeit.default_timer()
    try:
        user = db.read(str(ctx.author))
        if user is None or len(user) < 2:
            raise ValueError(BotStatus.USER_NOT_FOUND)
        email, hash_pwd = user
        if email is None or hash_pwd is None:
            raise ValueError(BotStatus.USER_NOT_FOUND)
        pwd = utils.decode(hash_pwd)
        await ctx.channel.send(f'Finding weekly schedule with email: {email}')
        result, name = await automation.get_schedule(ctx.author, email, pwd)
        stop = timeit.default_timer()
        if result == BotStatus.END_SUCCESS:
            await ctx.channel.send(f'Done in {round(stop - start, 2)}s, {mention}!', file=discord.File(name))
        else:
            await ctx.channel.send(f'Not found data {mention}!')
    except RuntimeError as err:
        await ctx.channel.send('Error with code: ' + str(err) + ' ' + mention,
                               file=discord.File(f'{ctx.author}.png'))
    except ValueError as err:
        await ctx.channel.send('Error with code: ' + str(err) + ' ' + mention)


@bot.command(help='Check schedule with Google access token')
async def schedule_with_token(ctx, access_token=None):
    await ctx.channel.send('Finding weekly schedule with given token')
    mention = ctx.author.mention
    try:
        result, name = await automation.get_schedule_by_token(ctx.author, access_token)
        if result == BotStatus.END_SUCCESS:
            await ctx.channel.send(f'Done {mention}!', file=discord.File(name))
        else:
            await ctx.channel.send(f'Not found data {mention}!')
    except RuntimeError as err:
        print(err)
        await ctx.channel.send('Error with code: ' + str(err) + ' ' + mention)


@bot.command(help='Create new FAP account')
async def register(ctx):
    def check_direct_msg(msg: discord.Message):
        return isinstance(msg.channel, discord.DMChannel) and msg.author == ctx.author
    mention = ctx.author.mention
    user = db.read(str(ctx.author))
    if user is not None and len(user) >= 2:
        await ctx.channel.send('Sorry, you have been set FAP account before. Please choose !update instead.')
        return
    await ctx.channel.send(f'Check your direct message please {mention}')
    await ctx.author.send(f'Hi {mention}, please send your FAP account as example: bot@fpt.edu.vn 123456')
    try:
        message = await bot.wait_for("message", check=check_direct_msg, timeout=120)
        reply = message.content
        x = reply.split()
        if len(x) < 2:
            await ctx.author.send('Your request is cancelled due to wrong input format.')
            return
        await ctx.author.send(f"Your info have seen set.")
        db.create(str(ctx.author), x[0], x[1])
    except TimeoutError:
        await ctx.author.send('Sorry, timeout!')
    except IntegrityError:
        await ctx.author.send('Sorry, you have been set FAP account before. Please choose !update instead.')


@bot.command(help='Update FAP account (email, password)')
async def update(ctx):
    def check_direct_msg(msg: discord.Message):
        return isinstance(msg.channel, discord.DMChannel) and msg.author == ctx.author
    mention = ctx.author.mention
    await ctx.channel.send(f'Check your direct message please {mention}')
    await ctx.author.send(f'Hi {mention}, '
                          'update one value means password will be updated only. '
                          'Send email and password if you want to update all.')
    try:
        message = await bot.wait_for("message", check=check_direct_msg, timeout=120)
        reply = message.content
        x = reply.split()
        if len(x) == 1:
            db.update_pwd(str(ctx.author), x[0])
        elif len(x) > 1:
            db.update(str(ctx.author), x[0], x[1])
        else:
            await ctx.author.send('Your request is cancelled due to wrong input format.')
            return
        await ctx.author.send(f"Your info have seen update.")
    except TimeoutError:
        await ctx.author.send('Sorry, timeout!')
    except IntegrityError:
        await ctx.author.send('Sorry, you have been set FAP account. Please choose update instead.')


@bot.command(help='Delete saved FAP account')
async def delete(ctx):
    mention = ctx.author.mention
    try:
        db.delete(str(ctx.author))
        await ctx.channel.send(f'Deleted {mention}!')
    except RuntimeError as err:
        print(err)
        await ctx.channel.send('Error with code: ' + str(err) + ' ' + mention)


@bot.command(help='Check ping pong latency')
async def ping(ctx):
    mention = ctx.author.mention
    b_latency = round(bot.latency * 1000)
    await ctx.channel.send(f'Latency: {b_latency}ms {mention}')


@bot.command(name='cmas', pass_context=True)
async def cal_mas(ctx, *, query):
    mention = ctx.author.mention
    try:
        await ctx.channel.send(f'Processing for question: {query}')
        isFound = False
        async for name in automation.request_wolfram_alpha(ctx.author, query):
            isFound = True
            await ctx.channel.send(file=discord.File(name))
        if isFound:
            await ctx.channel.send(f'Done {mention}!')
        else:
            await ctx.channel.send(f'Sorry, no answer, {mention}!')
    except RuntimeError as err:
        await ctx.channel.send('Error with code: ' + str(err) + ' ' + mention,
                               file=discord.File(f'{ctx.author}.png'))
    except ValueError as err:
        await ctx.channel.send('Error with code: ' + str(err) + ' ' + mention)
