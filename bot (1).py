import discord
from discord import app_commands
import os

# ── Bot Setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ── Loot Drop Data ─────────────────────────────────────────────────────────────
DROPS = {
    "white": {
        "label": "White Supply Crate",
        "normal": "• Flak Set\n• 10x Bola\n• Metal Pick\n• Metal Hatchet\n• 10x Med Brew",
        "double": "• Flak Set\n• 10x Bola\n• Metal Pick\n• Metal Hatchet\n• 10x Med Brew\n• Crossbow\n• 25x Tranq Arrows",
        "quality": "Primitive → Purple",
    },
    "green": {
        "label": "Green Supply Crate",
        "normal": "• 100–200x Polymer\n• 100–250x Cementing Paste\n• 100–175x Silica Pearls",
        "double": "• Everything 2–3x",
        "quality": "—",
    },
    "blue": {
        "label": "Blue Supply Crate",
        "normal": "• Fabricated Sniper\n• 50x ADV Sniper Bullets",
        "double": "• Fabricated Sniper\n• 50x ADV Sniper Bullets\n• 50% Chance: Fab Sniper BP / Crossbow BP / Shotgun BP / Compound Bow BP",
        "quality": "Purple → Mastercraft",
    },
    "purple": {
        "label": "Purple Supply Crate",
        "normal": "• Pike\n• Sickle\n• Flak Set\n• 50% Chance: BP (Sniper / Pike / Sickle)\n• 50% Chance: Crossbow BP",
        "double": "• Pike\n• Sickle\n• Flak Set\n• 50% Chance: Fab Sniper BP\n• 50% Chance: Crossbow BP",
        "quality": "Mastercraft → Ascendant",
    },
    "yellow": {
        "label": "Yellow Supply Crate",
        "normal": "• 10x Metal Foundation\n• 15x Metal Wall\n• 10x Metal Ceiling\n• Dino Gate + Door\n• 5x Tek Dedicated Storage",
        "double": "• 20x Metal Foundation\n• 30x Metal Wall\n• 20x Metal Ceiling\n• Dino Gate + Door\n• Industrial Forge or Grinder\n• 10x Tek Dedicated Storage",
        "quality": "—",
    },
    "red": {
        "label": "Red Supply Crate",
        "normal": "• Fabricated Sniper or Crossbow\n• 25x ADV Sniper Bullets\n• 25x Tranq Arrows\n• 25x Flame Arrows\n• 25x Med Brew",
        "double": "• Everything 2–3x",
        "quality": "Mastercraft → Ascendant",
    },
}

# ── Channel Lock ───────────────────────────────────────────────────────────────
COMMANDS_CHANNEL = "🔎｜commands"

async def check_channel(interaction: discord.Interaction) -> bool:
    if interaction.channel.name != COMMANDS_CHANNEL:
        correct = discord.utils.get(interaction.guild.channels, name=COMMANDS_CHANNEL)
        hinweis = f"<#{correct.id}>" if correct else f"**{COMMANDS_CHANNEL}**"
        await interaction.response.send_message(
            f"This command only works in {hinweis}.",
            ephemeral=True,
        )
        return False
    return True

# ── /drop Command ──────────────────────────────────────────────────────────────
@tree.command(name="drop", description="Shows the contents of a loot drop")
@app_commands.describe(color="Which drop color?")
@app_commands.choices(color=[
    app_commands.Choice(name="White",  value="white"),
    app_commands.Choice(name="Green",  value="green"),
    app_commands.Choice(name="Blue",   value="blue"),
    app_commands.Choice(name="Purple", value="purple"),
    app_commands.Choice(name="Yellow", value="yellow"),
    app_commands.Choice(name="Red",    value="red"),
])
async def drop_command(interaction: discord.Interaction, color: str):
    if not await check_channel(interaction):
        return

    data = DROPS[color]
    q = f"\nQuality: {data['quality']}" if data["quality"] != "—" else ""

    embed = discord.Embed(title=f"Drop — {data['label']}")
    embed.add_field(name="Normal", value=data["normal"] + q, inline=True)
    embed.add_field(name="Double", value=data["double"] + q, inline=True)
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /drops Command ─────────────────────────────────────────────────────────────
@tree.command(name="drops", description="Shows all loot drops at a glance")
async def drops_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(title="Drop — Overview")

    for data in DROPS.values():
        q = f"\nQuality: {data['quality']}" if data["quality"] != "—" else ""
        embed.add_field(
            name=data["label"],
            value=f"**Normal**\n{data['normal']}{q}\n\n**Double**\n{data['double']}{q}",
            inline=False,
        )

    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── Start ──────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online as {client.user}")

client.run(os.environ["DISCORD_TOKEN"])
