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
        "label": "⚪ White — Starter Kit",
        "normal": (
            "• Hide Toxic Rüstung (5 Teile)\n"
            "• 10x Bola\n"
            "• Metal Pick\n"
            "• Metal Hatchet\n"
            "• 10x Med Brew"
        ),
        "double": (
            "• Alles aus Normal\n"
            "• Crossbow\n"
            "• 25x Tranq Arrows\n"
            "• 1–3x Small XP Potion"
        ),
        "quality": "Primitiv",
    },
    "green": {
        "label": "🟢 Green — Resources",
        "normal": (
            "• 75–175x Polymer\n"
            "• 75–175x Cementing Paste\n"
            "• 75–175x Silica Pearls\n"
            "• 75–175x Öl"
        ),
        "double": (
            "• 125–250x Polymer\n"
            "• 125–250x Cementing Paste\n"
            "• 125–250x Silica Pearls\n"
            "• 125–250x Öl"
        ),
        "quality": "—",
    },
    "blue": {
        "label": "🔵 Blue — Alpha Tier",
        "normal": (
            "**Garantiert:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Pool (3–8 Items, 85% Item / 15% BP):**\n"
            "• Crossbow · Alpha Flak Set (5 Teile)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike"
        ),
        "double": (
            "**Garantiert:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Pool (5–10 Items, 85% Item / 15% BP):**\n"
            "• Crossbow · Alpha Flak Set (5 Teile)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike"
        ),
        "quality": "—",
    },
    "purple": {
        "label": "🟣 Purple — Structures",
        "normal": (
            "• 10x Metal Foundation\n"
            "• 15x Metal Wall\n"
            "• 10x Metal Ceiling\n"
            "• Dino Gateway + Gate\n"
            "• 3x Dedicated Storage"
        ),
        "double": (
            "• 20x Metal Foundation\n"
            "• 30x Metal Wall\n"
            "• 20x Metal Ceiling\n"
            "• Dino Gateway + Gate\n"
            "• 5x Dedicated Storage"
        ),
        "quality": "—",
    },
    "yellow": {
        "label": "🟡 Yellow — Volcanic Tier",
        "normal": (
            "**Garantiert:**\n"
            "• 15–35x Tranq Dart (zufällig: Elemental/Alpha/Potent)\n"
            "• 8–25x Elemental ADV Sniper Bullets\n"
            "• 2–5x Large XP Potion\n"
            "• 1–5x Mythic Health Potion\n\n"
            "**Pool (3–8 Items, 85% Item / 15% BP):**\n"
            "• Longneck · Volcanic Flak Set (5 Teile)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike"
        ),
        "double": (
            "**Garantiert:**\n"
            "• 15–35x Tranq Dart (zufällig: Elemental/Alpha/Potent)\n"
            "• 8–25x Elemental ADV Sniper Bullets\n"
            "• 2–5x Large XP Potion\n"
            "• 1–5x Mythic Health Potion\n"
            "• Elemental Compound Bow Arrows\n"
            "• Fab Sniper Mastercraft\n\n"
            "**Pool (5–10 Items, 85% Item / 15% BP):**\n"
            "• Longneck · Volcanic Flak Set (5 Teile)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike"
        ),
        "quality": "—",
    },
    "red": {
        "label": "🔴 Red — Endgame Exclusives",
        "normal": (
            "**Garantiert:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n\n"
            "**Pool (3–8 Items, 85% Item / 15% BP):**\n"
            "• Fab Sniper · Mythic Flak Set (5 Teile)\n"
            "• Legend Riot Set (5 Teile)"
        ),
        "double": (
            "**Garantiert:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n"
            "• Primal ADV Sniper Bullets\n\n"
            "**Pool (5–10 Items, 85% Item / 15% BP):**\n"
            "• Fab Sniper · Mythic Flak Set (5 Teile)\n"
            "• Legend Riot Set (5 Teile)"
        ),
        "quality": "—",
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
    app_commands.Choice(name="⚪ White — Starter Kit",       value="white"),
    app_commands.Choice(name="🟢 Green — Resources",         value="green"),
    app_commands.Choice(name="🔵 Blue — Alpha Tier",         value="blue"),
    app_commands.Choice(name="🟣 Purple — Structures",       value="purple"),
    app_commands.Choice(name="🟡 Yellow — Volcanic Tier",    value="yellow"),
    app_commands.Choice(name="🔴 Red — Endgame Exclusives",  value="red"),
])
async def drop_command(interaction: discord.Interaction, color: str):
    if not await check_channel(interaction):
        return

    data = DROPS[color]
    q = f"\n**Quality:** {data['quality']}" if data["quality"] != "—" else ""

    embed = discord.Embed(title=f"Drop — {data['label']}")
    embed.add_field(name="Normal", value=data["normal"] + q, inline=False)
    embed.add_field(name="\u200b", value="\u200b", inline=False)  # spacer
    embed.add_field(name="Double (mit Ring)", value=data["double"] + q, inline=False)
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /drops Command ─────────────────────────────────────────────────────────────
@tree.command(name="drops", description="Shows all loot drops at a glance")
async def drops_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="Drop — Overview",
        description=(
            "⚪ White → Starter Kit\n"
            "🟢 Green → Resources\n"
            "🔵 Blue → Alpha Tier\n"
            "🟣 Purple → Structures\n"
            "🟡 Yellow → Volcanic Tier\n"
            "🔴 Red → Endgame Exclusives\n\n"
            "Use `/drop <color>` for full details.\n"
            "**Double** = Crate mit Ring — immer besser!"
        )
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── Start ──────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online as {client.user}")

client.run(os.environ["DISCORD_TOKEN"])
