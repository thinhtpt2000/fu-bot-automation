# bot.py
import asyncio
import os
from asyncio import TimeoutError
from sqlite3 import IntegrityError
import akinator
from akinator.async_aki import Akinator

import discord
from discord.ext import commands
from discord.ext.commands import BucketType
from dotenv import load_dotenv
from selenium.common.exceptions import WebDriverException

import automation
from enum_bot import BotStatus
import db_utils as db
import bot_utils as utils
import timeit

bot = commands.Bot(command_prefix='!!')

emojis_c = ['✅', '❌', '🤷', '👍', '👎', '⏮', '🛑']
emojis_w = ['✅', '❌']

load_dotenv()
channel_id = int(os.getenv('GUESS_GAME_CHANNEL'))

aki = Akinator()


def run():
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)


def w(name, desc, picture):
    embed_win = discord.Embed(title=f"It's {name} ({desc})! Was I correct?",
                              colour=0x00FF00)
    embed_win.set_image(url=picture)
    return embed_win


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
    except WebDriverException:
        await ctx.channel.send('Error with code: ' + str(BotStatus.START_FAILED) + ' ' + mention)


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
    except WebDriverException:
        await ctx.channel.send('Error with code: ' + str(BotStatus.START_FAILED) + ' ' + mention)


@bot.command(name='ftime', help='Check schedule with cookie')
async def schedule_with_cookie(ctx, app_id):
    start = timeit.default_timer()
    await ctx.channel.send('Finding weekly schedule with given id')
    mention = ctx.author.mention
    try:
        result, name = await automation.get_schedule_by_cookie(ctx.author, app_id)
        stop = timeit.default_timer()
        if result == BotStatus.END_SUCCESS:
            await ctx.channel.send(f'Done in {round(stop - start, 2)}s, {mention}!', file=discord.File(name))
        else:
            await ctx.channel.send(f'Not found data {mention}!')
    except RuntimeError as err:
        print(err)
        await ctx.channel.send('Error with code: ' + str(err) + ' ' + mention)
    except WebDriverException:
        await ctx.channel.send('Error with code: ' + str(BotStatus.START_FAILED) + ' ' + mention)


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


@bot.command(name='qa', pass_context=True)
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
    except WebDriverException:
        await ctx.channel.send('Error with code: ' + str(BotStatus.START_FAILED) + ' ' + mention)


@bot.command(name='guess')
@commands.max_concurrency(1, per=BucketType.default, wait=False)
async def guess(ctx, *, extra):
    if ctx.channel.id == channel_id:
        desc_loss = ''
        d_loss = ''

        def check_c(reaction, user):
            return user == ctx.author and str(
                reaction.emoji) in emojis_c and reaction.message.content == q

        def check_w(reaction, user):
            return user == ctx.author and str(reaction.emoji) in emojis_w

        async with ctx.typing():
            if extra == 'people':
                q = await aki.start_game(child_mode=True)
            elif extra == 'objects' or extra == 'animals':
                q = await aki.start_game(language=f'en_{extra}',
                                         child_mode=True)
            elif extra == 'help':
                desc_helpme = '__**HOW TO PLAY**__\n\nUse the `!!guess` command followed by the game mode you want to play. Here is ' \
                              'a list of currently available game modes : **people, animals, objects**.\nFor example : `!!guess people`\n\n__**GAME MODES**__\n\n' \
                              '**People** : This is the game mode for guessing people (fictional or real)\n**Animals** : ' \
                              'This is the game mode for guessing animals\n**Objects** : This is the game mode for guessing objects' \
                              '\n\n__**MISCELLANEOUS**__\n\n**1.**Wait until all emojis are displayed before adding your reaction, or' \
                              ' else it will not register it and you will have to react again once it is done displaying' \
                              '\n**2.**The game ends in 45 seconds if you do not answer the question by reacting with the right' \
                              ' emoji\n**3.** The bot might sometimes be slow, please be patient and wait for it to ask you the questions. If it is stuck, do not worry the game will automatically end in 30 seconds and you can start playing again\n**4.** Only one person can play at a time\n\n' \
                              '__**EMOJI MEANINGS**__\n\n✅ = This emoji means "yes"\n❌ = This emoji means "no"\n🤷 = This emoji means' \
                              '"I do not know"\n👍 = This emoji means "probably"\n👎 = This emoji means "probably not"\n⏮ = This ' \
                              'emoji repeats the question before\n🛑 = This emoji ends the game being played'
                embed_var_helpme = discord.Embed(description=desc_helpme, color=0x00FF00)
                await ctx.send(embed=embed_var_helpme)
                return
            else:
                title_error_three = 'This game mode does not exist'
                desc_error_three = 'Use **.help** to see a list of all the game modes available'
                embed_var_three = discord.Embed(title=title_error_three,
                                                description=desc_error_three,
                                                color=0xFF0000)
                await ctx.reply(embed=embed_var_three)
                return

            embed_question = discord.Embed(
                title=
                'Tip : Wait until all emojis finish being added before reacting'
                ' or you will have to unreact and react again',
                color=0x00FF00)
            await ctx.reply(embed=embed_question)

        while aki.progression <= 85:
            message = await ctx.reply(q)

            for m in emojis_c:
                await message.add_reaction(m)

            try:
                symbol, username = await bot.wait_for('reaction_add',
                                                      timeout=45.0,
                                                      check=check_c)
            except asyncio.TimeoutError:
                embed_game_ended = discord.Embed(
                    title='You took too long,the game has ended',
                    color=0xFF0000)
                await ctx.reply(embed=embed_game_ended)
                return

            if str(symbol) == emojis_c[0]:
                a = 'y'
            elif str(symbol) == emojis_c[1]:
                a = 'n'
            elif str(symbol) == emojis_c[2]:
                a = 'idk'
            elif str(symbol) == emojis_c[3]:
                a = 'p'
            elif str(symbol) == emojis_c[4]:
                a = 'pn'
            elif str(symbol) == emojis_c[5]:
                a = 'b'
            elif str(symbol) == emojis_c[6]:
                embed_game_end = discord.Embed(
                    title='I ended the game because you asked me to do it',
                    color=0x00FF00)
                await ctx.reply(embed=embed_game_end)
                return

            if a == "b":
                try:
                    q = await aki.back()
                except akinator.CantGoBackAnyFurther:
                    pass
            else:
                q = await aki.answer(a)

        await aki.win()

        wm = await ctx.reply(
            embed=w(aki.first_guess['name'], aki.first_guess['description'],
                    aki.first_guess['absolute_picture_path']))

        for e in emojis_w:
            await wm.add_reaction(e)

        try:
            s, u = await bot.wait_for('reaction_add',
                                      timeout=30.0,
                                      check=check_w)
        except asyncio.TimeoutError:
            for times in aki.guesses:
                d_loss = d_loss + times['name'] + '\n'
            t_loss = 'Here is a list of all the people I had in mind :'
            embed_loss = discord.Embed(title=t_loss,
                                       description=d_loss,
                                       color=0xFF0000)
            await ctx.reply(embed=embed_loss)
            return

        if str(s) == emojis_w[0]:
            embed_win = discord.Embed(
                title='Great, guessed right one more time!', color=0x00FF00)
            await ctx.reply(embed=embed_win)
        elif str(s) == emojis_w[1]:
            for times in aki.guesses:
                desc_loss = desc_loss + times['name'] + '\n'
            title_loss = 'No problem, I will win next time! But here is a list of all the people I had in mind :'
            embed_loss = discord.Embed(title=title_loss,
                                       description=desc_loss,
                                       color=0xFF0000)
            await ctx.reply(embed=embed_loss)
    else:
        right_channel = bot.get_channel(channel_id)
        channel_mention = right_channel.mention
        wrong_channel = discord.Embed(
            title='You can only play in the following channel ' +
                  channel_mention,
            color=0xFF0000)
        await ctx.reply(embed=wrong_channel)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        title_error_one = 'You have not entered anything after the command'
        desc_error_one = 'Use **!!help** to see a list of all the game modes available'
        embed_var_one = discord.Embed(title=title_error_one,
                                      description=desc_error_one,
                                      color=0xFF0000)
        await ctx.reply(embed=embed_var_one)
    if isinstance(error, commands.CommandNotFound):
        title_error_two = 'The command you have entered does not exist'
        desc_error_two = 'Use **!!help** to see a list of all the commands available'
        embed_var_two = discord.Embed(title=title_error_two,
                                      description=desc_error_two,
                                      color=0xFF0000)
        await ctx.reply(embed=embed_var_two)
    if isinstance(error, commands.MaxConcurrencyReached):
        title_error_four = 'Someone is already playing'
        desc_error_four = 'Please wait until the person currently playing is done with their turn'
        embed_var_four = discord.Embed(title=title_error_four,
                                       description=desc_error_four,
                                       color=0xFF0000)
        await ctx.reply(embed=embed_var_four)
