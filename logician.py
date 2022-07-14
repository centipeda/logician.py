#!/usr/bin/env python3

"""Logician, a Discord bot."""

# imports
import asyncio
import re
import json
import os
import sys
import requests
from io import BytesIO

import interactions
from petpetgif import petpet as petpetgif
import openai

import colortable
import propaganda.convert as conversion

# load config data
if 'SECRETS_PATH' not in os.environ:
    print('Please set $SECRETS_PATH to the path to the config file.')
    sys.exit(1)

print(f'Loading configuration file at {os.environ["SECRETS_PATH"]}...')
with open(os.environ['SECRETS_PATH']) as f:
    config_data = json.loads(f.read())
    token = config_data["token"]
    mbti_guilds = config_data["mbti_guilds"]
    color_guilds = config_data["color_guilds"]
    color_position = config_data["top_color_position"]
    color_file = config_data["color_file"]
    openai_api_key = config_data["openai_api_key"]
    openai_max_tokens = config_data["openai_max_tokens"]
    openai_temp = config_data["openai_temperature"]
    openai_forbidden = [
        "remus",
        "sirius",
        "slash",
        "wolfstar",
        "remus lupin",
        "sirius black",
        "erotic fiction",
        "erotic fan fiction",
        "smut",
        "erotica"
    ]

# set up
bot = interactions.Client(token=token)
mbti_types  = ['ISTJ', 'ISTP', 'ISFJ', 'ISFP', 'INFJ', 'INFP', 'INTJ', 'INTP', 'ESTP', 
               'ESTJ', 'ESFP', 'ESFJ', 'ENFP', 'ENFJ', 'ENTP', 'ENTJ', 'none']
mbti_type_choices = [interactions.Choice(name=t, value=t) for t in mbti_types]
hexcolor_regex = re.compile("^#[a-fA-F0-9]{6}$")
colors = colortable.Colors(color_file)
openai.api_key = openai_api_key

@bot.command(
    name="type",
    description="Sets or removes your MBTI type role.",
    scope=mbti_guilds,
    options=[
        interactions.Option(
            name="mbti_type",
            description="Your MBTI type (or none)",
            type=interactions.OptionType.STRING,
            required=True,
            choices=mbti_type_choices
        )
    ]
)
async def _type(ctx: interactions.CommandContext, mbti_type: str): # set the type of the member
    guild = await ctx.get_guild()
    # remove all MBTI roles

    for role_id in ctx.author.roles:
        role = await guild.get_role(role_id)
        print(type(role))
        if role.name in mbti_types:
            await ctx.author.remove_role(role=role, guild_id=guild.id)
    # add the new MBTI role
    if mbti_type != 'none':
        for role in await guild.get_all_roles():
            if role.name == mbti_type:
                await ctx.send(f"Setting type to {mbti_type}.")
                await ctx.author.add_role(role=role, guild_id=guild.id)
                return
        await ctx.send("Sorry, we don't have that MBTI role.")
    else:
        await ctx.send("Removing MBTI type role.")


@bot.command(
    name="color",
    scope=color_guilds,
    description="Set your color role.",
    options=[
        interactions.Option(
            name="color",
            description="The name of your desired color, or a hex code starting with #",
            type=interactions.OptionType.STRING,
            required=True
        ) ]) 
async def _color(ctx: interactions.CommandContext, color: str):
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
    guild = await ctx.get_guild()
    if not ctx.author.roles:
        return
    for role_id in ctx.author.roles:
        role = await guild.get_role(role_id)
        if hexcolor_regex.match(role.name):
            await ctx.author.remove_role(role=role, guild_id=guild.id)
    # create or add new color role
    all_roles = await guild.get_all_roles()
    for role in all_roles:
        # search for existing color role
        if role.name == color:
            await ctx.author.add_role(role=role, guild_id=guild.id)
            return
    # if we haven't found it, create a new color role
    hex_color = int(color[1::], 16)
    new_color_role = await guild.create_role(name=color, color=hex_color)
    await asyncio.sleep(0.25)
    await new_color_role.modify_position(guild_id=guild.id, position=int(color_position[str(guild.id)]))
    await asyncio.sleep(0.25)
    await ctx.author.add_role(role=new_color_role, guild_id=guild.id)


@bot.command(
    name="nocolor", 
    scope=color_guilds, 
    description="Remove your color role."
)
async def _nocolor(ctx):
    # remove old color roles
    guild = await ctx.get_guild()
    for role_id in ctx.author.roles:
        role = await guild.get_role(role_id)
        if hexcolor_regex.match(role.name):
            await ctx.send("Removing color role(s).")
            await ctx.author.remove_role(role=role, guild_id=guild.id)


@bot.command(
    name="petpet", 
    scope=color_guilds, 
    description="Generate a petpet .gif from an image.",
    options=[
        interactions.Option(
            name='url',
            description='URL where the image is located.',
            type=interactions.OptionType.STRING,
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
    msg = await ctx.send(".")
    await msg.edit(content="", files=interactions.File(fp=petpet, filename="petpet.gif"))


@bot.command(
    name="propaganda", 
    scope=color_guilds, 
    description="Generate a \"you are not immune to\"  meme with the given phrase.",
    options=[
        interactions.Option(
            name='phrase',
            description='Phrase to insert into the image',
            type=interactions.OptionType.STRING,
            required=True
        )
    ])
async def _propaganda(ctx, phrase):
    if len(phrase) > 15:
        await ctx.send('Please use a phrase shorter than 15 characters.')
        return
    prop = conversion.save_meme(phrase, BytesIO())
    msg = await ctx.send(".")
    await msg.edit(content="", files=interactions.File(filename="propaganda.jpg", fp=prop))
    
@bot.command(
    name="prompt", 
    scope=color_guilds, 
    description="Generate some text to respond to the given prompt with an OpenAI language model.",
    options=[
        interactions.Option(
            name='prompt',
            description='Prompt for text generation.',
            type=interactions.OptionType.STRING,
            required=True
        )
    ])
async def _prompt(ctx, prompt):
    msg = await ctx.send("Let me think...")
    for restricted_phrase in openai_forbidden:
        if restricted_phrase in prompt.lower():
            await msg.edit(content=f"I am not legally allowed to generate a response for prompt **[{prompt}]**.")
            return
    try:
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=prompt,
            max_tokens=openai_max_tokens,
            temperature=openai_temp
        )
        print(f"{prompt}: {response}")
    except openai.OpenAIError as e:
        print(e)
        await msg.edit(content="Sorry, I couldn't create a response to \"{prompt}\".")
        return
    contents = response.choices.pop().text.strip().replace("\n\n", "\n")
    try:
        await msg.edit(content=f"**[{prompt}]** {contents}")
    except AttributeError: # if no response
        await msg.edit(content="Sorry, I couldn't create a response to \"{prompt}\".")
        

# on activation
@bot.event
async def on_ready():
    print(f'logged in as {bot.me}')

# run the bot
bot.start()

