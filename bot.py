import discord
from discord import app_commands
import os

# ── Bot Setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SUGGESTIONS_CHANNEL = "❓｜suggestions"
COMMANDS_CHANNEL    = "🔎｜commands"

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
            "• 20x Potent Tranq Arrows\n"
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
            "**Pool (1–5 Items, 85% Item / 15% BP):**\n"
            "• Crossbow · Alpha Flak Set (5 Teile)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike"
        ),
        "double": (
            "**Garantiert:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Pool (1–5 Items, 85% Item / 15% BP):**\n"
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
            "**Pool (1–5 Items, 85% Item / 15% BP):**\n"
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
            "**Pool (1–5 Items, 85% Item / 15% BP):**\n"
            "• Longneck · Volcanic Flak Set (5 Teile)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike"
        ),
        "quality": "—",
    },
    "red": {
        "label": "🔴 Red — Primal/Mythic Tier",
        "normal": (
            "**Garantiert:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n\n"
            "**Pool (1–5 Items, 85% Item / 15% BP):**\n"
            "• Fab Sniper · Mythic Flak Set (5 Teile)\n"
            "• Legend Riot Set (5 Teile)"
        ),
        "double": (
            "**Garantiert:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n"
            "• Primal ADV Sniper Bullets\n\n"
            "**Pool (1–5 Items, 85% Item / 15% BP):**\n"
            "• Fab Sniper · Mythic Flak Set (5 Teile)\n"
            "• Legend Riot Set (5 Teile)"
        ),
        "quality": "—",
    },
}

# ── Channel Lock ───────────────────────────────────────────────────────────────
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

# ── /commands ──────────────────────────────────────────────────────────────────
@tree.command(name="commands", description="Shows all available bot commands")
async def commands_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Available Commands",
        description="Here's everything the bot can do:",
    )
    embed.add_field(
        name="🎁 Drops",
        value=(
            "`/drop <color>` — Full contents of a specific supply crate\n"
            "`/drops` — Quick overview of all drop colors"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎯 Taming",
        value="`/taming-guide` — gives you knowledge of everything you need to know on how to tame in ARK Primal Chaos!",
        inline=False,
    )
    embed.add_field(
        name="💡 Suggestions",
        value="`/suggestion <text>` — Submit a suggestion to the admins",
        inline=False,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /drop Command ──────────────────────────────────────────────────────────────
@tree.command(name="drop", description="Shows the contents of a loot drop")
@app_commands.describe(color="Which drop color?")
@app_commands.choices(color=[
    app_commands.Choice(name="⚪ White — Starter Kit",      value="white"),
    app_commands.Choice(name="🟢 Green — Resources",        value="green"),
    app_commands.Choice(name="🔵 Blue — Alpha Tier",        value="blue"),
    app_commands.Choice(name="🟣 Purple — Structures",      value="purple"),
    app_commands.Choice(name="🟡 Yellow — Volcanic Tier",   value="yellow"),
    app_commands.Choice(name="🔴 Red — Primal/Mythic Tier", value="red"),
])
async def drop_command(interaction: discord.Interaction, color: str):
    if not await check_channel(interaction):
        return

    data = DROPS[color]
    q = f"\n**Quality:** {data['quality']}" if data["quality"] != "—" else ""

    embed = discord.Embed(title=f"Drop — {data['label']}")
    embed.add_field(name="Normal", value=data["normal"] + q, inline=False)
    embed.add_field(name="\u200b", value="\u200b", inline=False)
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
            "🔴 Red → Primal/Mythic Tier\n\n"
            "Use `/drop <color>` for full details.\n"
            "**Double** = Crate mit Ring — immer besser!"
        )
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /taming-guide ──────────────────────────────────────────────────────────────
@tree.command(name="taming-guide", description="Tranq ammo tiers & Fab Sniper multiplier explained")
async def taming_guide_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="🎯 Taming Guide — Primal Chaos",
        description=(
            "Primal Chaos adds tiered tranq ammo — the higher the tier, the more torpor per hit. "
            "Combined with a higher % Fab Sniper blueprint, the effect multiplies significantly.\n\u200b"
        ),
    )

    embed.add_field(
        name="🔫 Fab Sniper — ADV Sniper Bullets @ 100% weapon",
        value=(
            "• Potent → **2.1k** torpor\n"
            "• Alpha → **4.6k** torpor\n"
            "• Elemental → **8.6k** torpor\n"
            "• Mythic → **13k** torpor\n"
            "• Primal → **20.8k** torpor"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎯 Longneck — Tranq Darts @ 100% weapon",
        value=(
            "• Potent → **1.9k** torpor\n"
            "• Alpha → **3.8k** torpor\n"
            "• Elemental → **7.4k** torpor\n"
            "• Mythic → **11.3k** torpor"
        ),
        inline=True,
    )

    embed.add_field(
        name="🪃 Crossbow — Tranq Arrows @ 100% weapon",
        value=(
            "• Potent → **640** torpor\n"
            "• Alpha → **1.2k** torpor"
        ),
        inline=True,
    )

    embed.add_field(
        name="📈 Weapon % Multiplier (Fab Sniper Example)",
        value=(
            "The weapon % on a blueprint scales torpor directly.\n\n"
            "**Formula:** `Base Torpor × (Weapon % ÷ 100)`\n\n"
            "Example with **Mythic ADV Bullet (13k base)**:\n"
            "• 100% → **13k** torpor\n"
            "• 200% → **26k** torpor\n"
            "• 300% → **39k** torpor\n\n"
            "⚠️ *Values tested on a Bronto. Torpor per hit varies by dino.*"
        ),
        inline=False,
    )

    embed.add_field(
        name="💡 Taming Tips",
        value=(
            "• Use the **Awesome Spyglass** to monitor torpor & max torpor in real time\n"
            "• Higher tier ammo isn't always needed — Potent/Alpha works fine on weaker dinos\n"
            "• Mythic/Primal Bullets recommended for high-level Chaos dinos or boss tames\n"
            "• **Boss dinos** must be brought below 20% HP before they take any torpor"
        ),
        inline=False,
    )

    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /suggestion ────────────────────────────────────────────────────────────────
@tree.command(name="suggestion", description="Submit a suggestion to the admins")
@app_commands.describe(text="Your suggestion")
async def suggestion_command(interaction: discord.Interaction, text: str):
    suggestions_ch = discord.utils.get(interaction.guild.channels, name=SUGGESTIONS_CHANNEL)

    if suggestions_ch is None:
        await interaction.response.send_message(
            f"❌ Could not find the **{SUGGESTIONS_CHANNEL}** channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="💡 New Suggestion",
        description=text,
        color=discord.Color.gold(),
    )
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    embed.set_footer(text=f"User ID: {interaction.user.id} | Primal Hell • ARK Survival Ascended")

    msg = await suggestions_ch.send(embed=embed)

    # Add voting reactions
    await msg.add_reaction("✅")
    await msg.add_reaction("➖")
    await msg.add_reaction("❌")

    await interaction.response.send_message(
        f"✅ Your suggestion has been submitted to {suggestions_ch.mention}!",
        ephemeral=True,
    )


# ── Start ──────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online as {client.user}")

client.run(os.environ["DISCORD_TOKEN"])
