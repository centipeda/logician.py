import discord
from discord.ext import commands
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
import re
import json

# import data
with open("client_secrets") as f:
    config_data = json.loads(f.read())
    token = config_data["token"]
    mbti_guilds = config_data["mbti_guilds"]
    color_guilds = config_data["color_guilds"]
    color_position = config_data["top_color_position"]

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

hexcolor_regex = re.compile("^#[a-fA-F0-9]{6}")
@slash.slash(name="color", guild_ids=color_guilds,
            description="Set your color role.",
            options=[
                create_option(
                    name="color",
                    description="Your desired color, as a hex code starting with #",
                    option_type=3, # string
                    required=True
                )
            ])
async def _color(ctx, color: str):
    # validate color code
    if hexcolor_regex.match(color):
        await ctx.send(f"Setting color to {color}.")
    else:
        await ctx.send(f"Sorry, {color} is not a valid hex color.")
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


# @bot.command(name='test')
# async def _test(ctx):
#     for role in ctx.author.roles:
#         if hexcolor_regex.match(role.name):
#             await ctx.send(f"readjusting {role.name} to {color_position[str(ctx.guild.id)]}")
#             await role.edit(position=color_position[str(ctx.guild.id)])

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