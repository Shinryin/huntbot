#!/usr/bin/env python3

from __future__ import print_function

import asyncio

import os
import datetime
import discord
import logging

from tabulate import tabulate

from pprint import pprint

from dotenv import load_dotenv

from discord.ext import commands
from discord.ext import tasks

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from apiclient import discovery

from discord_webhook import DiscordWebhook

import httplib2

def parse_world(world):
    worlds = {
            "L": "Lich",
            "O": "Odin",
            "P": "Phoenix",
            "S": "Shiva",
            "T": "Twintania",
            "Z": "Zodiark"
            }

    initial=world[0].capitalize()
    return worlds[initial]

def worldTimeLoc(world,leg=None):
    locs = {
            "Lich": "C3",
            "Odin": "C4",
            "Phoenix": "C5",
            "Shiva": "C6",
            "Twintania": "C7",
            "Zodiark": "C8"
            }
    if leg==1:
        locs = {
                "Lich": "C18",
                "Odin": "C19",
                "Phoenix": "C20",
                "Shiva": "C21",
                "Twintania": "C22",
                "Zodiark": "C23"
                }
    return locs[world]

def worldStatusLoc(world,leg=None):
    locs = {
            "Lich": "E3",
            "Odin": "E4",
            "Phoenix": "E5",
            "Shiva": "E6",
            "Twintania": "E7",
            "Zodiark": "E8"
            }
    if leg==1:
        locs = {
                "Lich": "E18",
                "Odin": "E19",
                "Phoenix": "E20",
                "Shiva": "E21",
                "Twintania": "E22",
                "Zodiark": "E23"
                }
    return locs[world]

async def bot_log(msg):
    await bot.get_channel(LOG_CHANNEL).send(msg)

async def update_channel(server, status, started, legacy=None):

    ids = {
            "Lich": 888868356659228682,
            "Odin": 888868371423191051,
            "Phoenix": 888868382877831188,
            "Shiva": 888868394772860988,
            "Twintania": 888868418361630811,
            "Zodiark": 888868429950484491
            }

    ids_l = {
            "Lich": 895686404531707964,
            "Odin": 895686423351533609,
            "Phoenix": 895686443064766545,
            "Shiva": 895686465483309116,
            "Twintania": 895686484659679343,
            "Zodiark": 895686518335737936
            }
    
    servers = {
            "Lich": "lich",
            "Odin": "odin",
            "Phoenix": "phoe",
            "Shiva": "shiva",
            "Twintania": "twin",
            "Zodiark": "zodi"
            }

    statuses = {
            "Up": "up",
            "Scouting": "scouting",
            "Scouted": "scouted",
            "Running": "run",
            "Dead": "dead",
            "Sniped": "sniped"
            }

    statusicons = {
            "Up": "✅",
            "Scouting": "📡",
            "Scouted": "🌐",
            "Running": "🚋",
            "Dead": "🔒",
            "Sniped": "🏹"
            }
    if legacy != 1:
        chan=bot.get_channel(ids[server])
    else:
        chan=bot.get_channel(ids_l[server])
    newname=f"{statusicons[status]}{servers[server]}-{statuses[status]}"
    if chan.name != newname:
        print("need to update name")
        await chan.edit(name=newname)
    else:
        print("no need to update name")


async def update_sheet(world, status, time, legacy=None):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    creds = None

    secret=os.path.join(os.getcwd(),'nuny.json')
    creds = service_account.Credentials.from_service_account_file(secret,scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)

    sheet=service.spreadsheets()
    timecell="Up Times!"+worldTimeLoc(world,legacy)
    statuscell="Up Times!"+worldStatusLoc(world,legacy)
    if time != 0:
        temp=datetime.datetime(1899,12,30)
        delta=time-temp
        time=float(delta.days)+(float(delta.seconds)/86440)
        body={
                "valueInputOption": "RAW",
                "data": [
                    {
                        'range': timecell,
                        'values': [[time]]
                    },
                    {
                        'range': statuscell,
                        'values': [[status]]
                    }
                ]
            }

    else:
        body={
                "valueInputOption": "RAW",
                "data": [
                    {
                        'range': statuscell,
                        'values': [[status]]
                    }
                ]
            }

    response=sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

def fetch_sheet(range):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = None
    secret=os.path.join(os.getcwd(),'nuny.json')
    creds = service_account.Credentials.from_service_account_file(secret,scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet=service.spreadsheets()
    result=sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range, valueRenderOption="UNFORMATTED_VALUE").execute()
    return result.get('values', [])


async def update_from_sheets():
    EW_RANGE = 'Up Times!B3:E8'
    LEGACY_RANGE = 'Up Times!B18:E23'

    values=fetch_sheet(EW_RANGE)

    if not values:
        print('No data found.')
    else:
        for row in values:
            if ready == 1:
                await update_channel(row[0],row[3],datetime.datetime(1899,12,30)+datetime.timedelta(days=row[1]),0)

    values=fetch_sheet(LEGACY_RANGE)

    if not values:
        print('No data found.')
    else:
        for row in values:
            if ready == 1:
                await update_channel(row[0],row[3],datetime.datetime(1899,12,30)+datetime.timedelta(days=row[1]),1)



async def update_from_sheets_to_chat(legacy=None):
    range = 'Up Times!B3:E8'
    if legacy==1:
        range = 'Up Times!B18:E23'
    
    values=fetch_sheet(range)

    if not values:
        print('No data found.')
    else:
        taulu=[]
        taulu.append(["Server","Started","+6h","Status"])
        for row in values:
            if ready == 1:
                t1=datetime.datetime.strftime(datetime.datetime(1899,12,30)+datetime.timedelta(days=row[1]),"%H:%M")
                t2=datetime.datetime.strftime(datetime.datetime(1899,12,30)+datetime.timedelta(days=row[2]),"%H:%M")
                taulu.append([row[0],t1,t2,row[3]])
    message="```"
    message+=tabulate(taulu,headers="firstrow",tablefmt="fancy_grid")+"```"
    return message

def parse_parameters(time,leg):
    try:
        if time==None:
            time=datetime.datetime.utcnow()
        else:
            if time[0].capitalize()=="L":
                leg="L"
                time=datetime.datetime.utcnow()
            else:
                if time[0]=="+":
                    time=datetime.timedelta(minutes=int(time[1:]))+datetime.datetime.utcnow()
                else:
                    t=time.split(":")
                    h=int(t[0])
                    m=int(t[1])
                    time=datetime.datetime.utcnow().replace(hour=h,minute=m,second=45)
    except ValueError:
        time=datetime.datetime.utcnow()
    l=0
    if leg[0].capitalize()=="L":
        l=1
    return [time,l]


########################

logging.basicConfig(level=logging.INFO)

load_dotenv()
TOKEN=os.getenv('DISCORD_TOKEN')
SPREADSHEET_ID=os.getenv('SPREADSHEET_ID')
LOG_CHANNEL=int(os.getenv('LOG_CHANNEL'))
BOT_CHANNEL=int(os.getenv('BOT_CHANNEL'))
WEBHOOK_TEST=os.getenv('WEBHOOK_TEST')
WEBHOOK_ESC=os.getenv('WEBHOOK_ESC_FC')
WEBHOOK_CC=os.getenv('WEBHOOK_CC')
WEBHOOK_CH=os.getenv('WEBHOOK_CH')
WEBHOOK_ANGEL=os.getenv('WEBHOOK_ANGEL')
WEBHOOK_FALOOP=os.getenv('WEBHOOK_FALOOP')
WEBHOOK_WRKJN=os.getenv('WEBHOOK_WRKJN')
ROLE_EW_TEST=int(os.getenv('ROLE_TEST_EW'))
ROLE_SHB_TEST=int(os.getenv('ROLE_TEST_SHB'))
ROLE_EW_ESC=int(os.getenv('ROLE_ESC_FC'))
ROLE_SHB_ESC=int(os.getenv('ROLE_ESC_FC'))
ROLE_EW_CC=int(os.getenv('ROLE_CC_EW'))
ROLE_SHB_CC=int(os.getenv('ROLE_CC_SHB'))
ROLE_EW_CH=int(os.getenv('ROLE_CH_EW'))
ROLE_SHB_CH=int(os.getenv('ROLE_CH_SHB'))
ROLE_EW_FALOOP=int(os.getenv('ROLE_FALOOP_EW'))
ROLE_SHB_FALOOP=int(os.getenv('ROLE_FALOOP_SHB'))

ready = 0

bot = commands.Bot(command_prefix=".")

@bot.command(name='scout', aliases=['sc','scouting'],help='Begin scouting.\nTime parameter is optional and can be in form "+15" (minutes) or "15:24" (server time)')
async def scouting(ctx, world, time=None, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return

    world=parse_world(world)
    parm=parse_parameters(time,legacy)
    time=parm[0]
    l=parm[1]
    await update_sheet(world,"Scouting",time,l)
    await update_channel(world,"Scouting",time,l)
    await ctx.message.add_reaction("✅")


@bot.command(name='scouted', aliases=['scdone','scend'],help='End scouting.\n Time parameter is optional, defaults to current time and can be manually set in form "+15" (minutes) or "15:24" (server time)')
async def scoutend(ctx, world, time=None, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return

    world=parse_world(world)
    parm=parse_parameters(time,legacy)
    time=parm[0]
    l=parm[1]

    await update_sheet(world,"Scouted",time,l)
    await ctx.message.add_reaction("✅")


@bot.command(name='start', aliases=['begin','run','go'],help='Start train.\n Time parameter is optional, defaults to current time and can be manually set in form "+15" (minutes) or "15:24" (server time)')
async def begintrain(ctx, world, time=None, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return

    world=parse_world(world)
    parm=parse_parameters(time,legacy)
    time=parm[0]
    l=parm[1]

    await update_sheet(world,"Running",time,l)
    await ctx.message.add_reaction("✅")


@bot.command(name='end', aliases=['done','dead','finish'],help='Finish train.\n Time parameter is optional, defaults to current time and can be manually set in form "+15" (minutes) or "15:24" (server time)')
async def endtrain(ctx, world, time=None, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return

    world=parse_world(world)
    parm=parse_parameters(time,legacy)
    time=parm[0]
    l=parm[1]

    await update_sheet(world,"Dead",time,l)
    await ctx.message.add_reaction("✅")


@bot.command(name='up', aliases=['reset'],help='Reset train')
async def resettrain(ctx, world, time=None,legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return

    world=parse_world(world)
    parm=parse_parameters(time,legacy)
    time=parm[0]
    l=parm[1]

    await update_sheet(world,"Up",time,l)
    await ctx.message.add_reaction("✅")


@bot.command(name="status", aliases=['getstatus','stat'],help='Get train status')
async def getstatus(ctx, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return
    leg=0
    if legacy[0].capitalize() == "L":
        leg=1
    msg=await update_from_sheets_to_chat(leg)
    await ctx.send(msg)
    await ctx.message.add_reaction("✅")

@bot.command(name="testadvertise", aliases=['testshout','testsh'],help='Advertise your train. Put multi-part parameters in quotes (eg. .shout twin "Fort Jobb")')
async def advertise(ctx, world, start, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return

    username=ctx.message.author.display_name

    world=parse_world(world)
    parm=parse_parameters(None,legacy)
    l=parm[1]
    if l==0:
        msg=f"About to send this notification to test server: ```@Endwalker_role [{world}] Hunt train starting in 10 minutes at {start} ({username}).```React with ✅ to send or wait 15 seconds to cancel."
    if l==1:
        msg=f"About to send this notification to test server: ```@Legacy_role [{world}] Hunt train starting in 10 minutes at {start} ({username}).```React with ✅ to send or wait 15 seconds to cancel."

    msg1=await ctx.send(msg)
    await msg1.add_reaction("✅")

    def check(reaction, user):
        return reaction.message.id==msg1.id and str(reaction.emoji)=='✅' and user.id == ctx.author.id

    try:
        res=await bot.wait_for("reaction_add", check=check,timeout=15)
    except asyncio.TimeoutError:
        print ("Timed out")
        await msg1.delete()
        await ctx.message.add_reaction('❌')
        pass
    else:
        if res:
            reaction, user=res
            print (reaction.emoji)

# test server
            print ("test")
            mentions={
                "roles": [ROLE_EW_TEST, ROLE_SHB_TEST]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_TEST}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_TEST}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_TEST,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

            await msg1.delete()
            await ctx.message.add_reaction('✅')

@bot.command(name="advertise", aliases=['ad','shout','sh'],help='Advertise your train. Put multi-part parameters in quotes (eg. .shout twin "Fort Jobb")')
async def advertise(ctx, world, start, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return

    username=ctx.message.author.display_name

    world=parse_world(world)
    parm=parse_parameters(None,legacy)
    l=parm[1]
    if l==0:
        msg=f"About to send this notification to Faloop, CH and CC servers: ```@Endwalker_role [{world}] Hunt train starting in 10 minutes at {start} ({username}).```React with ✅ to send or wait 15 seconds to cancel."
    if l==1:
        msg=f"About to send this notification to Faloop, CH and CC servers: ```@Legacy_role [{world}] Hunt train starting in 10 minutes at {start} ({username}).```React with ✅ to send or wait 15 seconds to cancel."

    msg1=await ctx.send(msg)
    await msg1.add_reaction("✅")

    def check(reaction, user):
        return reaction.message.id==msg1.id and str(reaction.emoji)=='✅' and user.id == ctx.author.id

    try:
        res=await bot.wait_for("reaction_add", check=check,timeout=15)
    except asyncio.TimeoutError:
        print ("Timed out")
        await msg1.delete()
        await ctx.message.add_reaction('❌')
        pass
    else:
        if res:
            reaction, user=res
            print (reaction.emoji)

# test server 
            print ("test")
            mentions={
                "roles": [ROLE_EW_TEST, ROLE_SHB_TEST]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_TEST}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_TEST}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_TEST,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

# ch server
            print ("ch")
            mentions={
                "roles": [ROLE_EW_CH, ROLE_SHB_CH]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_CH}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_CH}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_CH,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

# cc server
            print ("cc")
            mentions={
                "roles": [ROLE_EW_CC, ROLE_SHB_CC]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_CC}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_CC}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_CC,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

# esc server
            print ("esc")
            mentions={
                "roles": [ROLE_EW_ESC]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_ESC}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_ESC}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_ESC,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

# angel server
            print ("angel")
            if l==0:
                msg=f"[{world}] Hunt train starting in 10 minutes at {start} ({username})."
                webhook = DiscordWebhook(url=WEBHOOK_ANGEL,rate_limit_retry=True,content=msg,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
                resp=webhook.execute()

# wrkjn server
            print ("wrkjn")
            if l==0:
                msg=f"[{world}] Hunt train starting in 10 minutes at {start} ({username})."
                webhook = DiscordWebhook(url=WEBHOOK_WRKJN,rate_limit_retry=True,content=msg,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
                resp=webhook.execute()

# faloop server
            print ("faloop")
            mentions={
                "roles": [ROLE_EW_FALOOP, ROLE_SHB_FALOOP]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_FALOOP}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_FALOOP}> [{world}] Hunt train starting in 10 minutes at {start} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_FALOOP,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()


            await msg1.delete()
            await ctx.message.add_reaction('✅')

@bot.command(name="advmanual", aliases=['adm','mshout','msh'],help='Advertise your train. Put multi-part parameters in quotes (eg. .mshout "[Twintania] Hunt train starting in 10 minutes at Fort Jobb")')
async def madvertise(ctx, message, legacy="0"):
    if ctx.channel.id != BOT_CHANNEL:
        print (f"{BOT_CHANNEL} != {ctx.channel.id}")
        return
    username=ctx.message.author.display_name

    print (message)

    parm=parse_parameters(None,legacy)
    l=parm[1]
    if l==0:
        msg=f"About to send this notification to Faloop, CH and CC servers: ```@Endwalker_role {message} ({username}).```React with ✅ to send or wait 15 seconds to cancel."
    if l==1:
        msg=f"About to send this notification to Faloop, CH and CC servers: ```@Legacy_role {message} ({username}).```React with ✅ to send or wait 15 seconds to cancel."

    msg1=await ctx.send(msg)
    await msg1.add_reaction("✅")

    def check(reaction, user):
        return reaction.message.id==msg1.id and str(reaction.emoji)=='✅' and user.id == ctx.author.id

    try:
        res=await bot.wait_for("reaction_add", check=check,timeout=15)
    except asyncio.TimeoutError:
        print ("Timed out")
        await msg1.delete()
        await ctx.message.add_reaction('❌')
        pass
    else:
        if res:
            reaction, user=res
            print (reaction.emoji)

            
# test discord
            print ("test")
            mentions={
                "roles": [ROLE_EW_TEST, ROLE_SHB_TEST]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_TEST}> {message} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_TEST}> {message} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_TEST,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

# ch discord
            print ("ch")
            mentions={
                "roles": [ROLE_EW_CH, ROLE_SHB_CH]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_CH}> {message} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_CH}> {message} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_CH,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

# cc discord
            print ("cc")
            mentions={
                "roles": [ROLE_EW_CC, ROLE_SHB_CC]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_CC}> {message} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_CC}> {message} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_CC,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()
	

# esc discord
            print ("esc")
            mentions={
                "roles": [ROLE_EW_ESC]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_ESC}> {message} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_ESC}> {message} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_ESC,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()

# angel server
            print ("angel")
            if l==0:
                msg=f"{message} ({username})."
                webhook = DiscordWebhook(url=WEBHOOK_ANGEL,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
                resp=webhook.execute()

# wrkjn server
            print ("wrkjn")
            if l==0:
                msg=f"{message} ({username})."
                webhook = DiscordWebhook(url=WEBHOOK_WRKJN,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
                resp=webhook.execute()


# cc discord
            print ("faloop")
            mentions={
                "roles": [ROLE_EW_FALOOP, ROLE_SHB_FALOOP]
            }
            if l==0:
                msg=f"<@&{ROLE_EW_FALOOP}> {message} ({username})."
            if l==1:
                msg=f"<@&{ROLE_SHB_FALOOP}> {message} ({username})."
            webhook = DiscordWebhook(url=WEBHOOK_FALOOP,rate_limit_retry=True,content=msg,allowed_mentions=mentions,username="Nunyunuwi",avatar_url="https://jvaarani.kapsi.fi/nuny.png")
            resp=webhook.execute()



            await msg1.delete()
            await ctx.message.add_reaction('✅')



@bot.event
async def on_ready():
    global ready
    print(f'{bot.user} has connected to Discord!')
    ready=1

@tasks.loop(seconds = 60)
async def STLoop():
    now=datetime.datetime.strftime(datetime.datetime.utcnow(),"%H:%M")
    if ready == 1:
        await bot.change_presence(activity=discord.Game(f"Server time: {now}"))

@tasks.loop(seconds = 300)
async def SheetLoop():
    await update_from_sheets()

SheetLoop.start()
STLoop.start()

bot.run(TOKEN)
