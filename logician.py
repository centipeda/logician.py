#!/usr/bin/env python3

"""Logician, a Discord bot."""

import re
import json
import os
import sys
from io import BytesIO

import discord
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
from petpetgif import petpet as petpetgif
import requests

import colortable
import propaganda.convert as conversion

if 'SECRETS_PATH' not in os.environ:
    print('Please set $SECRETS_PATH to the path to the config file.')
    sys.exit(1)
    
# import data
print(f'Loading configuration file at {os.environ["SECRETS_PATH"]}...')
with open(os.environ['SECRETS_PATH']) as f:
    config_data = json.loads(f.read())
    token = config_data["token"]
    mbti_guilds = config_data["mbti_guilds"]
    color_guilds = config_data["color_guilds"]
    color_position = config_data["top_color_position"]
    color_file = config_data["color_file"]

intents = discord.Intents.default()
bot = commands.Bot(intents=intents, command_prefix="$")
slash = SlashCommand(bot, sync_commands=True)

mbti_types  = ['ISTJ', 'ISTP', 'ISFJ', 'ISFP', 'INFJ', 'INFP', 'INTJ', 'INTP', 'ESTP', 
               'ESTJ', 'ESFP', 'ESFJ', 'ENFP', 'ENFJ', 'ENTP', 'ENTJ', 'none']
mbti_type_choices = [create_choice(name=t, value=t) for t in mbti_types]

@slash.slash(name="type", guild_ids=mbti_guilds,
            description="Sets or removes your MBTI type role.",
            options=[
                create_option(
                    name="mbti_type",
                    description="Your MBTI type",
                    option_type=3, # string
                    required=True,
                    choices=mbti_type_choices
                )
            ])
async def _type(ctx, mbti_type: str): # set the type of the member
    # remove all MBTI roles
    # print(ctx.author.roles)
    for role in ctx.author.roles:
        if role.name in mbti_types:
            await ctx.author.remove_roles(role)
    # add the new MBTI role
    if mbti_type != 'none':
        for role in ctx.guild.roles:
            if role.name == mbti_type:
                await ctx.send(f"Setting type to {mbti_type}.")
                await ctx.author.add_roles(role)
                return
        await ctx.send("Sorry, we don't have that MBTI role.")
    else:
        await ctx.send("Removing MBTI type role.")

hexcolor_regex = re.compile("^#[a-fA-F0-9]{6}$")
colors = colortable.Colors(color_file)
@slash.slash(name="color", guild_ids=color_guilds,
            description="Set your color role.",
            options=[
                create_option(
                    name="color",
                    description="The name of your desired color, or a hex code starting with #",
                    option_type=3, # string
                    required=True
                )
            ])
async def _color(ctx, color: str):
    # validate color name or code
    if colors.lookup(color):
        colorname = color[::]
        color = colors.lookup(color)
        await ctx.send(f"Setting color to {colorname} ({color}).")
    elif hexcolor_regex.match(color):
        await ctx.send(f"Setting color to {color}.")
    else:
        await ctx.send(f"Sorry, I don't know what color {color} is.")
        return
    # remove old color roles
    for role in ctx.author.roles:
        if hexcolor_regex.match(role.name):
            await ctx.author.remove_roles(role)
    # create or add new color role
    for role in ctx.guild.roles:
        # search for existing color role
        if role.name == color:
            await ctx.author.add_roles(role)
            return
    # if we haven't found it, create a new color role
    hexColor = int(color[1::], 16)
    newColorRole = await ctx.guild.create_role(name=color, color=hexColor)
    await newColorRole.edit(position=color_position[str(ctx.guild.id)])
    await ctx.author.add_roles(newColorRole)

@slash.slash(name="nocolor", guild_ids=color_guilds, description="Remove your color role.")
async def _nocolor(ctx):
    # remove old color roles
    for role in ctx.author.roles:
        if hexcolor_regex.match(role.name):
            await ctx.send("Removing color role(s).")
            await ctx.author.remove_roles(role)

@slash.slash(name="petpet", guild_ids=color_guilds, 
        description="Generate a petpet .gif from an image.",
        options=[
            create_option(
                name='url',
                description='URL where the image is located.',
                option_type=3, # string
                required=True
            )
        ])
async def _petpetgif(ctx, url):
    try:
        resp = requests.get(url, stream=True)
    except Exception as e:
        print(e)
        await ctx.send('Failed to retrieve image from link.')
        return
    if not resp.headers['Content-Type'].startswith('image'):
        await ctx.send('Please provide a link to an image.')
        return
    
    imagedata = resp.raw
    petpet = BytesIO()
    try:
        petpetgif.make(imagedata, petpet)
        petpet.seek(0)
    except Exception as e:
        print(e)
        await ctx.send('Failed to create petpet.')
        return
    await ctx.send(file=discord.File(petpet, filename="petpet.gif"))

@slash.slash(name="propaganda", guild_ids=color_guilds, 
        description="Generate a \"you are not immune to\"  meme with the given phrase.",
        options=[
            create_option(
                name='phrase',
                description='Phrase to insert into the image',
                option_type=3, # string
                required=True
            )
        ])
async def _propaganda(ctx, phrase):
    if len(phrase) > 15:
        await ctx.send('Please use a phrase shorter than 15 characters.')
        return
    prop = conversion.save_meme(phrase, BytesIO())
    await ctx.send(file=discord.File(prop, filename="propaganda.jpg"))
    
@bot.command(name='reboot')
async def _reboot(ctx):
    if ctx.author.top_role.permissions.administrator:
        await ctx.send("Goodbye... for now.")
        await ctx.bot.logout()
    else:
        await ctx.send("I'm afraid I can't do that.")

# on activation
@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')

# run the bot
bot.run(token)
