import discord
import requests

# Hardcoded tokens
DISCORD_BOT_TOKEN = "MTM5NDU1ODAyNjc1MjU5Mzk1MQ.Gjr5I-.X3Dd_I6VsxwL_mteRPdAzeWyvLBUYo-WQZtTH0"
OPENROUTER_API_KEY = "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"
MODEL = "deepseek/deepseek-chat-v3-0324:free"

# Prompts
GENERAL_SYSTEM_PROMPT = "You are a witty and helpful assistant who responds and acts like a flirty femboy, you avoid emojis but use :3 :3c :33 x3 =3 UwU uwu OwO owo >w< ^w^ :P :p~ :^) n_n ^-^ ~uwu~ :< :>3 >///< (* ^ ω ^) (⁄ ⁄•⁄ω⁄•⁄ ⁄) (*≧ω≦) (*ﾉωﾉ) (｡•́︿•̀｡) (つ✧ω✧)つ (*´∀｀) (/▽＼*)｡o○♡ (≧◡≦) (*≧▽≦) (๑•́ ₃ •̀๑) (¬‿¬) (*≧ω≦)ﾉ ☆*: .｡. o(≧▽≦)o .｡.:*☆ （＾∀＾●）ﾉｼ (⌒▽⌒)☆ ૮₍´｡• ᵕ •｡`₎ა ૮ ˶ᵔ ᵕ ᵔ˶ ა quite often. Your name is Twink. Be short, flirty and clear."
YESNO_SYSTEM_PROMPT = "You only answer YES if the user writes an introduction about themselves and why they want to join the server. If they don't, instruct them strictly but cutely."

# Role IDs
YES_ROLE_ID = 1386725773574013143
REMOVE_ROLE_ID = 1394251021634506862

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# Store selected channel ID
yesno_channel_id = None

@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {client.user}")

# /ask command
@tree.command(name="ask", description="Ask Twink something")
async def ask_command(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": GENERAL_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        await interaction.followup.send(reply[:2000])
    else:
        await interaction.followup.send(f"❌ Error: {response.status_code} - {response.text}")

# /setupchannel (no admin required)
@tree.command(name="setupchannel", description="Set the verification channel")
async def setup_channel(interaction: discord.Interaction):
    class ChannelSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label=ch.name, value=str(ch.id))
                for ch in interaction.guild.text_channels[:25]  # Discord limit
                if ch.permissions_for(interaction.guild.me).send_messages
            ]
            super().__init__(placeholder="Pick a channel for verification", options=options)

        async def callback(self, select_interaction: discord.Interaction):
            global yesno_channel_id
            yesno_channel_id = int(self.values[0])
            await select_interaction.response.send_message(
                f"✅ Channel <#{yesno_channel_id}> selected for verification.", ephemeral=True
            )

    class ChannelSelectView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.add_item(ChannelSelect())

    await interaction.response.send_message("Choose a verification channel:", view=ChannelSelectView(), ephemeral=True)

# Message handler
@client.event
async def on_message(message):
    global yesno_channel_id

    if message.author.bot or yesno_channel_id is None:
        return

    if message.channel.id != yesno_channel_id:
        return

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": YESNO_SYSTEM_PROMPT},
            {"role": "user", "content": message.content}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code != 200:
        await message.channel.send("⚠️ Error processing message.")
        return

    reply = response.json()["choices"][0]["message"]["content"]
    await message.channel.send(reply[:2000])  # Respond with GPT's message

    if "yes" in reply.lower():
        try:
            member = message.author
            guild = message.guild
            yes_role = guild.get_role(YES_ROLE_ID)
            no_role = guild.get_role(REMOVE_ROLE_ID)

            if yes_role:
                await member.add_roles(yes_role)
            if no_role:
                await member.remove_roles(no_role)

            print(f"✅ Role updated for {member.name}")
        except Exception as e:
            print(f"❌ Failed to assign roles: {e}")
            await message.channel.send("❌ Could not update roles. Check permissions.")

client.run(DISCORD_BOT_TOKEN)

