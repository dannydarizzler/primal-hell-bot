import discord
from discord import app_commands
import os

# ── Bot Setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ── Loot Drop Daten (aus README) ───────────────────────────────────────────────
DROPS = {
    "weiß": {
        "emoji": "⚪",
        "label": "Weiß — Starter Kit",
        "color": discord.Color.from_str("#FFFFFF"),
        "normal": {
            "items": "Flak-Set, 10x Bolas, Metallpickel, Metallaxt, 10x Med Brews",
            "qualität": "Primitiv → Lila",
        },
        "double": {
            "items": "Alles aus Normal + Crossbow + 25x Tranq Arrows",
            "qualität": "Primitiv → Lila",
        },
    },
    "grün": {
        "emoji": "🟢",
        "label": "Grün — Ressourcen",
        "color": discord.Color.green(),
        "normal": {
            "items": "100–200x Polymer, 100–250x Zement, 100–175x Siliziumperlen",
            "qualität": "—",
        },
        "double": {
            "items": "Alles doppelt bis dreifach",
            "qualität": "—",
        },
    },
    "blau": {
        "emoji": "🔵",
        "label": "Blau — Waffen",
        "color": discord.Color.blue(),
        "normal": {
            "items": "Fabrizierter Sniper + 50x ADV Sniper Bullets",
            "qualität": "Lila → Meisterwerk",
        },
        "double": {
            "items": "Alles aus Normal + 50% Chance: Fab Sniper BP / Crossbow BP / Shotgun BP / Compound Bow BP",
            "qualität": "Lila → Meisterwerk",
        },
    },
    "lila": {
        "emoji": "🟣",
        "label": "Lila — Bessere Rüstung",
        "color": discord.Color.purple(),
        "normal": {
            "items": "Pike, Sichel, Flak-Set\n50% Chance: BP (Sniper / Pike / Sichel)\n50% Chance: Crossbow BP",
            "qualität": "Meisterwerk → Aufgestiegen",
        },
        "double": {
            "items": "Alles aus Normal\n50% Chance: Fab Sniper BP (unabhängig)\n50% Chance: Crossbow BP (unabhängig)",
            "qualität": "Meisterwerk → Aufgestiegen",
        },
    },
    "gelb": {
        "emoji": "🟡",
        "label": "Gelb — Strukturen",
        "color": discord.Color.yellow(),
        "normal": {
            "items": "10x Metal Foundations, 15x Metal Walls, 10x Metal Ceilings, Dino Gate, Dino Door, 5x Tek Dedicated Storage",
            "qualität": "—",
        },
        "double": {
            "items": "20x Metal Foundations, 30x Metal Walls, 20x Metal Ceilings, Dino Gate, Dino Door, zufällig: Industrial Forge oder Industrial Grinder, 10x Tek Dedicated Storage",
            "qualität": "—",
        },
    },
    "rot": {
        "emoji": "🔴",
        "label": "Rot — OP Waffen",
        "color": discord.Color.red(),
        "normal": {
            "items": "Fabricated Sniper oder Crossbow\n25x ADV Sniper Bullets, 25x Tranq Arrows, 25x Flame Arrows, 25x Med Brews",
            "qualität": "Meisterwerk → Aufgestiegen",
        },
        "double": {
            "items": "Alles doppelt bis dreifach",
            "qualität": "Meisterwerk → Aufgestiegen",
        },
    },
}

# ── Channel Lock ───────────────────────────────────────────────────────────────
COMMANDS_CHANNEL = "🔎｜commands"

async def check_channel(interaction: discord.Interaction) -> bool:
    if interaction.channel.name != COMMANDS_CHANNEL:
        # Richtigen Kanal suchen und verlinken
        correct = discord.utils.get(interaction.guild.channels, name=COMMANDS_CHANNEL)
        hinweis = f"<#{correct.id}>" if correct else f"**{COMMANDS_CHANNEL}**"
        await interaction.response.send_message(
            f"❌ Dieser Command funktioniert nur im {hinweis} Kanal.",
            ephemeral=True,  # Nur der User sieht diese Meldung
        )
        return False
    return True

# ── /drop Command ──────────────────────────────────────────────────────────────
@tree.command(name="drop", description="Zeigt den Inhalt eines Loot Drops")
@app_commands.describe(farbe="Welche Drop-Farbe?")
@app_commands.choices(farbe=[
    app_commands.Choice(name="⚪ Weiß — Starter Kit",    value="weiß"),
    app_commands.Choice(name="🟢 Grün — Ressourcen",     value="grün"),
    app_commands.Choice(name="🔵 Blau — Waffen",         value="blau"),
    app_commands.Choice(name="🟣 Lila — Rüstung",        value="lila"),
    app_commands.Choice(name="🟡 Gelb — Strukturen",     value="gelb"),
    app_commands.Choice(name="🔴 Rot — OP Waffen",       value="rot"),
])
async def drop_command(interaction: discord.Interaction, farbe: str):
    if not await check_channel(interaction):
        return

    data = DROPS[farbe]
    embed = discord.Embed(
        title=f"{data['emoji']} {data['label']}",
        color=data["color"],
    )
    embed.add_field(
        name="🔹 Normal Drop",
        value=f"**Items:** {data['normal']['items']}\n**Qualität:** {data['normal']['qualität']}",
        inline=False,
    )
    embed.add_field(
        name="🔸 Double Drop (mit Ring)",
        value=f"**Items:** {data['double']['items']}\n**Qualität:** {data['double']['qualität']}",
        inline=False,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /drops Command (alle auf einmal) ──────────────────────────────────────────
@tree.command(name="drops", description="Zeigt alle Loot Drops auf einen Blick")
async def drops_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="🎁 Alle Loot Drops — Übersicht",
        description="Jede Farbe hat eine **Normal** und eine **Double** Variante (mit Ring).\nDouble enthält immer mehr oder besseres.",
        color=discord.Color.from_str("#FF4500"),
    )
    for data in DROPS.values():
        embed.add_field(
            name=f"{data['emoji']} {data['label']}",
            value=(
                f"🔹 **Normal:** {data['normal']['items']}\n"
                f"🔸 **Double:** {data['double']['items']}"
            ),
            inline=False,
        )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended • /drop <farbe> für Details")
    await interaction.response.send_message(embed=embed)


# ── Start ──────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot ist online als {client.user}")

client.run(os.environ["DISCORD_TOKEN"])
