import discord
from discord import app_commands
import os
import random
import re
import time
import asyncio
import sqlite3
import json

# ── Bot Setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SUGGESTIONS_CHANNEL  = "❓｜suggestions"
SERVER_CHANGES_CH    = "🔧｜server-changes"
WIPE_ROLE           = "Admin"          # only members with this role can use /wipe
COMMANDS_CHANNEL    = "🔎｜commands"
MYSTERYBOX_ROLES    = ["Admin", "Owner"]   # only these roles can open mystery boxes
GIVEAWAY_ROLES      = ["Admin", "Owner"]   # only these roles can start giveaways
GIVEAWAY_CHANNEL    = "🎁｜giveaways"        # giveaways always post here
POLL_ROLES          = ["Admin", "Owner"]   # only these roles can create polls
POLLS_CHANNEL       = "📊｜polls"            # polls always post here

# ── Mystery Box Config ─────────────────────────────────────────────────────────
# Adjust these two to match how your Ticket Tool actually names channels/categories.
TICKET_CHANNEL_PREFIX     = "ticket-"          # e.g. channel name starts with "ticket-"
TICKET_CATEGORY_KEYWORDS  = ["ticket", "dono"] # fallback: category name contains one of these

# (item name, weight in %) — must sum to 100
MYSTERYBOX_ITEMS = [
    ("7 Dedi Boxes of choice — 19€",                       2.00),
    ("500 Kibble Set — 16€",                                2.00),
    ("Instant Ascension → Level 180 — 15€",                 2.00),
    ("15 BPs of choice — 13€",                               2.00),
    ("4 Dedi Boxes of choice — 13€",                        7.67),
    ("8 Breedpairs — 12€",                                  7.67),
    ("3x Origin Set (33 Tokens + 33 Blood) — 10€",          7.67),
    ("250 Kibble Set — 11€",                                7.67),
    ("10 BPs of choice — 9€",                                7.67),
    ("4 Breedpairs — 9€",                                    7.67),
    ("2x Origin Set (22 Tokens + 22 Blood) — 7€",           7.67),
    ("2 Dedi Boxes of choice — 7€",                          7.67),
    ("100 Kibble Set — 6€",                                  7.67),
    ("2 Breedpairs — 5€",                                    7.67),
    ("5 BPs of choice — 5€",                                 7.67),
    ("1x Origin Set (11 Tokens + 11 Blood) — 4€",           7.67),
]
_MYSTERYBOX_NAMES   = [item[0] for item in MYSTERYBOX_ITEMS]
_MYSTERYBOX_WEIGHTS = [item[1] for item in MYSTERYBOX_ITEMS]

# ── Loot Drop Data ─────────────────────────────────────────────────────────────
DROPS = {
    "white": {
        "label": "⚪ White — Starter Kit",
        "normal": (
            "• Toxic Hide Armor (5 pieces)\n"
            "• 10x Bola\n"
            "• Metal Pick\n"
            "• Metal Hatchet\n"
            "• 10x Med Brew"
        ),
        "double": (
            "• Everything from Normal\n"
            "• Crossbow\n"
            "• 20x Potent Tranq Arrows\n"
            "• 1–3x Small XP Potion"
        ),
        "quality": "Primitive",
    },
    "green": {
        "label": "🟢 Green — Resources",
        "normal": (
            "• 75–175x Polymer\n"
            "• 75–175x Cementing Paste\n"
            "• 75–175x Silica Pearls\n"
            "• 75–175x Oil"
        ),
        "double": (
            "• 125–250x Polymer\n"
            "• 125–250x Cementing Paste\n"
            "• 125–250x Silica Pearls\n"
            "• 125–250x Oil"
        ),
        "quality": "—",
    },
    "blue": {
        "label": "🔵 Blue — Alpha Tier",
        "normal": (
            "**Guaranteed:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Gear Pool (1–5 items, no Blueprints):**\n"
            "• Crossbow · Alpha Flak Set (5 pieces)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Gear Pool (3–7 items, 20% Blueprint chance each):**\n"
            "• Crossbow · Alpha Flak Set (5 pieces)\n"
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
            "**Guaranteed:**\n"
            "• 10–20x Tranq Dart (random: Elemental/Alpha/Potent)\n"
            "• 8–16x Elemental ADV Sniper Bullets\n"
            "• 2–5x Large XP Potion\n"
            "• 1–5x Mythic Health Potion\n\n"
            "**Gear Pool (1–5 items, no Blueprints):**\n"
            "• Longneck · Volcanic Flak Set (5 pieces)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike · Fab Sniper (Mastercraft)"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 10–20x Tranq Dart (random: Elemental/Alpha/Potent)\n"
            "• 8–24x Elemental ADV Sniper Bullets\n"
            "• 2–5x Large XP Potion\n"
            "• 1–5x Mythic Health Potion\n\n"
            "**Gear Pool (1–5 items, 20% Blueprint chance each):**\n"
            "• Longneck · Volcanic Flak Set (5 pieces)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike · Fab Sniper (Mastercraft)"
        ),
        "quality": "—",
    },
    "red": {
        "label": "🔴 Red — Endgame Exclusives",
        "normal": (
            "**Guaranteed:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets (random)\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n"
            "• 8–25x Primal Compound Bow Arrows\n\n"
            "**Gear Pool (1–5 items, no Blueprints):**\n"
            "• Fab Sniper · Mythic Flak Set (5 pieces)\n"
            "• Legend Riot Set (5 pieces)"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets (random)\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n"
            "• 8–25x Primal Compound Bow Arrows\n"
            "• Additional guaranteed Primal ADV Sniper Bullets\n\n"
            "**Gear Pool (1–5 items, 20% Blueprint chance each):**\n"
            "• Fab Sniper · Mythic Flak Set (5 pieces)\n"
            "• Legend Riot Set (5 pieces)\n"
            "• Compound Bow Blueprint (always Blueprint)"
        ),
        "quality": "—",
    },
}

# ── Channel Lock (commands channel) ────────────────────────────────────────────
async def check_channel(interaction: discord.Interaction) -> bool:
    if interaction.channel.name != COMMANDS_CHANNEL:
        correct = discord.utils.get(interaction.guild.channels, name=COMMANDS_CHANNEL)
        channel_mention = f"<#{correct.id}>" if correct else f"**{COMMANDS_CHANNEL}**"
        await interaction.response.send_message(
            f"This command only works in {channel_mention}.",
            ephemeral=True,
        )
        return False
    return True


# ── Channel Lock (ticket channels, for Mystery Box) ────────────────────────────
def is_ticket_channel(channel: discord.abc.GuildChannel) -> bool:
    name = channel.name.lower()
    if name.startswith(TICKET_CHANNEL_PREFIX):
        return True
    category = getattr(channel, "category", None)
    if category and any(kw in category.name.lower() for kw in TICKET_CATEGORY_KEYWORDS):
        return True
    return False


async def check_ticket_channel(interaction: discord.Interaction) -> bool:
    if not is_ticket_channel(interaction.channel):
        await interaction.response.send_message(
            "❌ This command only works inside a **Dono-request** ticket. "
            "Open a ticket first to use Mystery Boxes.",
            ephemeral=True,
        )
        return False

    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(MYSTERYBOX_ROLES):
        roles_text = " / ".join(MYSTERYBOX_ROLES)
        await interaction.response.send_message(
            f"❌ Only **{roles_text}** can open Mystery Boxes.",
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
        value="`/taming-guide` — Ammo tiers & damage multiplier explained",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Armor",
        value="`/armor-guide` — All armor tiers and perks explained",
        inline=False,
    )
    embed.add_field(
        name="🥚 Kibble",
        value="`/kibble-guide` — Which unfertilized eggs unlock which kibble tier",
        inline=False,
    )
    embed.add_field(
        name="📊 Server Info",
        value="`/mods` — List of all active mods with descriptions",
        inline=False,
    )
    embed.add_field(
        name="💡 Suggestions",
        value="`/suggestion <text>` — Submit a suggestion",
        inline=False,
    )

    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


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
    embed.add_field(name="Double (with Ring)", value=data["double"] + q, inline=False)
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
            "**Double** = Crate with ring — always better!"
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
            "Combined with a higher % Fab Sniper blueprint, the effect multiplies significantly.\n"
            "⚠️ *Reference values below are approximate (measured on Level 150, unboosted creatures) "
            "and can vary depending on the target dino and server stat multipliers.*\n\u200b"
        ),
    )

    embed.add_field(
        name="🔫 Fab Sniper — ADV Sniper Bullets @ 100% weapon",
        value=(
            "• Potent → **2k** torpor\n"
            "• Alpha → **4.5k** torpor\n"
            "• Elemental → **8.5k** torpor\n"
            "• Mythic → **13k** torpor\n"
            "• Primal → **20k** torpor *(boss drop only)*"
        ),
        inline=True,
    )

    embed.add_field(
        name="🎯 Longneck — Tranq Darts @ 100% weapon",
        value=(
            "• Potent → **0.9–1.9k** torpor\n"
            "• Alpha → **1.7–3.8k** torpor\n"
            "• Elemental → **2.6–6.4k** torpor\n"
            "• Mythic → **5.5–9.2k** torpor"
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
        name="🏹 Compound Bow — Compound Tranq Arrows @ 100% weapon",
        value=(
            "• Primal → **30k** torpor *(boss drop only)*\n\n"
            "*Only the Primal tier still exists in-game — Potent/Alpha/Elemental/Mythic "
            "Compound Tranq Arrows have been removed from the mod.*"
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
            "• **Boss dinos** must be brought below 20% HP before they take any torpor\n"
            "• The **Compound Bow** hits noticeably harder per torpor tier than the Crossbow — worth upgrading to once available"
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


# ── /mods ──────────────────────────────────────────────────────────────────────
@tree.command(name="mods", description="Shows all active mods on the server")
async def mods_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔧 Active Mods — Primal Hell",
        description="These mods are currently running on the server:",
    )
    embed.add_field(
        name="⚔️ Gameplay Overhaul",
        value=(
            "**ARK Primal Chaos** — Full overhaul mod: new dino tiers, weapons, armor & bosses\n"
            
        ),
        inline=False,
    )
    embed.add_field(
        name="🦕 Dino Tools",
        value=(
            "**Awesome Spyglass** — Extended spyglass with live stat display for dinos\n"
            "**Dino Depot** — Dino management & storage\n"
            "**Der Dino Finder** — Locate any dino on the map"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚙️ Quality of Life",
        value=(
            "**TG Stacking Mod 1000-50** — Stack size ×1000, weight reduced by 50%\n"
            "**A Simple Performance Mod (60 FPS)** — Automatically runs performance commands on join "
            "(see below for full list)\n"
            "**Crash Protector** — Protects your character from wild dinos and drowning when you crash\n"
            "**Better Breeding** — Garanties always the better stats while breeding\n"
            "**Tribute Table** — Craft and summon all boss fights directly — no artifact or tribute farming required"
        ),
        inline=False,
    )
    embed.add_field(
        name="⛏️ Tool Harvesting Multipliers (Primal Chaos)",
        value=(
            "The in-game item descriptions for these tools are inaccurate — actual multipliers:\n"
            "• Toxic Tools → **×1.5** harvesting\n"
            "• Alpha Tools → **×2** harvesting\n"
            "• Elemental Tools (Volcanic) → **×2.5** harvesting\n"
            "• Mythic Tools → **×3** harvesting\n"
            "*(Applies to Pick, Hatchet, Sickle, and Pike of each tier.)*"
        ),
        inline=False,
    )
    embed.add_field(
        name="🖥️ Performance Mod — Applied Commands (PC)",
        value=(
            "`r.VolumetricCloud 0` — Disables clouds\n"
            "`r.Nanite.MaxPixelsPerEdge 4` — Reduces triangle count\n"
            "`foliage.MaxTrianglesToRender 500000` — Limits foliage rendering"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎮 Performance Mod — Additional Commands (Console only)",
        value=(
            "`sg.GlobalIlluminationQuality 2` · `sg.ResolutionQuality 80`\n"
            "`sg.AntiAliasingQuality 1` · `sg.ShadowQuality 2` · `sg.ShadingQuality 1`\n"
            "`sg.PostProcessQuality 1` · `sg.FoliageQuality 1` · `sg.EffectsQuality 1`\n"
            "`sg.ReflectionQuality 1` · `sg.TextureQuality 2` · `r.Vsync 1`\n"
            "`r.ScreenPercentage 50` · `r.DynamicRes.MinScreenPercentage 50`\n"
            "`r.Lumen.ScreenProbeGather.RadianceCache.ProbeResolution 16`"
        ),
        inline=False,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /armor-guide ───────────────────────────────────────────────────────────────
@tree.command(name="armor-guide", description="Armor tier overview with perks")
async def armor_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="🛡️ Primal Chaos Armor Guide",
        description=(
            "Armor progresses through 7 tiers. Higher tiers offer better protection "
            "and unique passive perks on certain pieces. All Primal Chaos flak armors "
            "drop exclusively as Blueprints.\n"
            "*(Armor values below are per full 5-piece set — divide by 5 for the value of a single piece.)*\n\u200b"
        ),
    )
    embed.add_field(
        name="1️⃣ Hide Toxic — Starter (Lvl 3, 400 armor/set)",
        value=(
            "Basic protection for early game survival.\n"
            "Available from the ⚪ **White drop**."
        ),
        inline=False,
    )
    embed.add_field(
        name="2️⃣ Alpha Chitin — Early Alpha (Lvl 37, 1250 armor/set)",
        value=(
            "Bridges the gap between Toxic Hide and Alpha Flak.\n"
            "*Not currently obtainable from any Primal Hell drop — will be added once confirmed available.*"
        ),
        inline=False,
    )
    embed.add_field(
        name="3️⃣ Alpha Flak — Alpha Tier (Lvl 56, 2500 armor/set)",
        value=(
            "Solid mid-game armor, upgrade from Toxic Hide.\n"
            "Available from the 🔵 **Blue drop** (Blueprint, Double only)."
        ),
        inline=False,
    )
    embed.add_field(
        name="4️⃣ Volcanic Flak — Volcanic Tier (Lvl 56, 5000 armor/set)",
        value=(
            "Strong late-game armor with improved stats.\n"
            "Available from the 🟡 **Yellow drop** (Blueprint, Double only)."
        ),
        inline=False,
    )
    embed.add_field(
        name="5️⃣ Mythic Flak — Mythic Tier ⭐ (Lvl 56, 12500 armor/set)",
        value=(
            "High-end armor with piece-specific passive perks.\n"
            "Available from the 🔴 **Red drop** (Blueprint, Double only).\n\n"
            "🪖 Helmet → **×4 Food & Water**\n"
            "👕 Chestpiece → **×4 Weight**\n"
            "🧤 Gauntlets → **×4 Crafting Speed**\n"
            "👖 Leggings → **×4 Stamina**\n"
            "👢 Boots → **×4 Fall Damage Reduction**"
        ),
        inline=False,
    )
    embed.add_field(
        name="6️⃣ Legend Riot — Legend Tier ⭐⭐ (Lvl 98, 15000 armor/set)",
        value=(
            "Top-tier craftable armor with the strongest passive perks.\n"
            "Available from the 🔴 **Red drop** (Blueprint, Double only).\n\n"
            "🪖 Helmet → **×4 Health**\n"
            "👕 Chestpiece → **×4 Torpor Resistance**\n"
            "🧤 Gauntlets → **×4 Melee Damage**\n"
            "👖 Leggings → **×4 Stamina**\n"
            "👢 Boots → **+25% Movement Speed & Reduced Fall Damage**"
        ),
        inline=False,
    )
    embed.add_field(
        name="7️⃣ DeathKnight — Endgame Boss Armor ⭐⭐⭐ (20000 armor/set)",
        value=(
            "The strongest armor in Primal Chaos — unbreakable, with the same perk spread "
            "as Legend Riot but at a higher tier.\n"
            "Drops exclusively from defeating the **Deathknight** boss (not obtainable from supply drops).\n\n"
            "🪖 Helmet → **Torpor Resistance**\n"
            "👕 Chestpiece → **Damage Increase**\n"
            "🧤 Gauntlets → **Health / Recovery**\n"
            "👖 Leggings → **Stamina**\n"
            "👢 Boots → **Reduced Fall Damage & Increased Movement Speed**"
        ),
        inline=False,
    )
    embed.add_field(name="​", value="​", inline=False)
    embed.add_field(
        name="📊 Base Stats — Armor Values (per full set / per piece)",
        value=(
            "• Toxic Hide → 400 *(80/piece)*\n"
            "• Alpha Chitin → 1250 *(250/piece)*\n"
            "• Alpha Flak → 2500 *(500/piece)*\n"
            "• Volcanic Flak → 5000 *(1000/piece)*\n"
            "• Mythic Flak → 12500 *(2500/piece)*\n"
            "• Legend Riot → 15000 *(3000/piece)*\n"
            "• DeathKnight → 20000 *(4000/piece)*"
        ),
        inline=True,
    )
    embed.add_field(
        name="📝 Notes",
        value=(
            "• Flak Blueprints can be found in supply drops\n"
            "• The **Upgrade Station** can upgrade finished armor pieces to higher quality\n"
            "• ⚠️ The Upgrade Station works on **ARK base items only** — "
            "Primal Chaos items with no base ARK equivalent (e.g. Reaper saddle) cannot be upgraded"
        ),
        inline=True,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /kibble-guide ──────────────────────────────────────────────────────────────
@tree.command(name="kibble-guide", description="Kibble progression tree — which egg unlocks which kibble")
async def kibble_guide_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="🥚 Kibble Progression Guide — Primal Chaos",
        description=(
            "Each kibble tier is crafted from **unfertilized eggs** of the previous tier "
            "(combined with standard resources) in the **Primal Cauldron**. "
            "Use the tier below to know which eggs to stockpile next.\n\u200b"
        ),
    )

    embed.add_field(
        name="1️⃣ Alpha Kibble",
        value=(
            "**Needs:** Unfertilized **Toxic** Eggs\n"
            "**Unlocks taming:** Alpha-tier creatures"
        ),
        inline=False,
    )
    embed.add_field(
        name="2️⃣ Elemental Kibble",
        value=(
            "**Needs:** Unfertilized **Alpha** Eggs\n"
            "**Unlocks taming:** Hydro · Volcanic · Electric creatures"
        ),
        inline=False,
    )
    embed.add_field(
        name="3️⃣ Shadow & Fairy Kibble",
        value=(
            "**Needs:** **Elemental Fruits** (grown from Elemental Seeds, dropped by the "
            "Hydro/Volcanic/Electric bosses)\n"
            "**Unlocks taming:** Shadow · Fairy creatures"
        ),
        inline=False,
    )
    embed.add_field(
        name="4️⃣ Mythic, Fabled & Legendary Kibble",
        value=(
            "**Needs:** Unfertilized **Shadow / Fairy** Eggs\n"
            "**Unlocks taming:** Mythic (gatherers) · Fabled (haulers) · Legendary (combat)"
        ),
        inline=False,
    )
    embed.add_field(
        name="5️⃣ Demonic & Angelic Kibble",
        value=(
            "**Needs:** Unfertilized **Mythic / Fabled / Legendary** Eggs *(pattern-based, "
            "not officially confirmed — verify in-game before relying on it)*\n"
            "**Unlocks taming:** Demonic · Angelic creatures"
        ),
        inline=False,
    )
    embed.add_field(
        name="6️⃣ Spirit & Chaos Kibble",
        value=(
            "**Needs:** Defeat the **Spirit Titan** and **Chaos Titan** bosses "
            "(summoned at the Primal Smithy) — this unlocks the kibble engram itself, "
            "not just an egg tier\n"
            "**Unlocks taming:** Spirit · Chaos creatures — these kibbles are also required "
            "as a crafting ingredient for Origin → Nightmare Evolution"
        ),
        inline=False,
    )
    embed.add_field(name="​", value="​", inline=False)
    embed.add_field(
        name="🐣 Essential: Keep a Breeding Pair of Every Tier",
        value=(
            "To reach the endgame in this mod, it's essential to keep at least **one breeding "
            "pair alive from every single tier** — from Toxic all the way up to Legendary/Fabled/Mythic. "
            "You'll constantly need unfertilized eggs from earlier tiers to craft the next kibble tier, "
            "so don't cull or release your old breeders once you've moved on — you'll need their eggs again."
        ),
        inline=False,
    )
    embed.add_field(
        name="📚 Which Dinos Lay Eggs?",
        value=(
            "Check the **#primal-chaos-creature-list-by-tier** channel — it lists every creature "
            "by tier and marks which ones are egg-layers, so you know exactly what to breed for "
            "each kibble stage."
        ),
        inline=False,
    )
    embed.add_field(
        name="🥚 Getting Unfertilized Eggs Efficiently",
        value=(
            "• Set `layegginterval` to **0.3** in Game.ini for steady egg production\n"
            "• Keep at least 1 male + multiple females of the tier, **mate-boosted**\n"
            "• **Disable mating** — this makes dinos lay unfertilized eggs instead\n"
            "• Tame an **Oviraptor** for an extra egg-laying speed boost"
        ),
        inline=False,
    )
    embed.add_field(
        name="📝 Note",
        value=(
            "Steps 1–4 and 6 are directly confirmed by the community progression guide. "
            "Step 5 (Demonic & Angelic) follows the same egg-based pattern as earlier tiers "
            "but hasn't been explicitly verified — if you test this in-game, let an admin know "
            "so this guide can be updated."
        ),
        inline=False,
    )

    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /wipe ──────────────────────────────────────────────────────────────────────
@tree.command(name="wipe", description="[Admin only] Announce an upcoming wild dino wipe in #announcements")
async def wipe_command(interaction: discord.Interaction):
    role = discord.utils.get(interaction.guild.roles, name=WIPE_ROLE)
    if role not in interaction.user.roles:
        await interaction.response.send_message(
            f"❌ You need the **{WIPE_ROLE}** role to use this command.",
            ephemeral=True,
        )
        return

    announcements_ch = discord.utils.get(interaction.guild.channels, name="📣｜announcements")
    if announcements_ch is None:
        await interaction.response.send_message(
            "❌ Could not find the **📣｜announcements** channel.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="⚠️ Wild Dino Wipe — 15 Minute Warning",
        description=(
            "**A wild dino wipe will take place in 15 minutes.**\n\n"
            "All wild dinosaurs on the map will be removed and will begin respawning shortly after. "
            "This is a routine reset to restore creature spawns that are no longer appearing in the world.\n\n"
            "Please make sure your tames are secured before the wipe takes place.\n"
            "There may be a brief lag spike when the wipe is executed — this is normal."
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(text=f"Announced by {interaction.user.display_name} • Primal Hell")

    await announcements_ch.send(content="@everyone", embed=embed)

    await interaction.response.send_message(
        f"✅ Wipe warning posted in {announcements_ch.mention}.",
        ephemeral=True,
    )


# ── Active Giveaway State ─────────────────────────────────────────────────────
active_giveaway = {}   # guild_id → {"number", "guess_channel_id", "announce_channel_id", "range_max", "reward"}

# ── Event Configs — add new tiers here if needed ───────────────────────────────
EVENT_CONFIGS = {
    "100":  {"range_max": 100,  "reward": "5€"},
    "500":  {"range_max": 500,  "reward": "10€"},
    "1000": {"range_max": 1000, "reward": "20€"},
}


# ── Generic Event Starter (shared logic for all guessing giveaways) ───────────
async def start_guess_event(interaction: discord.Interaction, range_max: int, reward: str):
    role = discord.utils.get(interaction.guild.roles, name=WIPE_ROLE)
    if role not in interaction.user.roles:
        await interaction.response.send_message(
            f"❌ You need the **{WIPE_ROLE}** role to use this command.",
            ephemeral=True,
        )
        return

    if not await check_channel(interaction):
        return

    events_ch = discord.utils.get(interaction.guild.channels, name="🎉｜events")
    if events_ch is None:
        await interaction.response.send_message(
            "❌ Could not find the **🎉｜events** channel.", ephemeral=True
        )
        return

    global_ch = discord.utils.get(interaction.guild.channels, name="🌍｜chat")
    if global_ch is None:
        await interaction.response.send_message(
            "❌ Could not find the **🌍｜chat** channel.", ephemeral=True
        )
        return

    number = random.randint(1, range_max)

    active_giveaway[interaction.guild.id] = {
        "number": number,
        "guess_channel_id": global_ch.id,
        "announce_channel_id": events_ch.id,
        "range_max": range_max,
        "reward": reward,
    }

    embed = discord.Embed(
        title="🎉 Global Chat Giveaway!",
        description=(
            "A giveaway is now live in the **Global Chat**!\n\n"
            f"Guess a number between **1 and {range_max}**.\n"
            f"The first player to guess the correct number wins **{reward} Shop Credit**! 🎁\n\n"
            "Type your guess directly in this channel. Good luck! 🍀"
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")

    await events_ch.send(content="@everyone", embed=embed)

    await interaction.response.send_message(
        f"✅ Giveaway started in {events_ch.mention}. Range: 1–{range_max} | "
        f"Reward: {reward} | Secret number: **{number}**",
        ephemeral=True,
    )


# ── /event-100-5 ────────────────────────────────────────────────────────────────
@tree.command(name="event-100-5", description="[Admin only] Start a 1-100 guessing giveaway — 5€ Shop Credit reward")
async def event_100_5_command(interaction: discord.Interaction):
    cfg = EVENT_CONFIGS["100"]
    await start_guess_event(interaction, cfg["range_max"], cfg["reward"])


# ── /event-500-10 ───────────────────────────────────────────────────────────────
@tree.command(name="event-500-10", description="[Admin only] Start a 1-500 guessing giveaway — 10€ Shop Credit reward")
async def event_500_10_command(interaction: discord.Interaction):
    cfg = EVENT_CONFIGS["500"]
    await start_guess_event(interaction, cfg["range_max"], cfg["reward"])


# ── /event-1000-20 ──────────────────────────────────────────────────────────────
@tree.command(name="event-1000-20", description="[Admin only] Start a 1-1000 guessing giveaway — 20€ Shop Credit reward")
async def event_1000_20_command(interaction: discord.Interaction):
    cfg = EVENT_CONFIGS["1000"]
    await start_guess_event(interaction, cfg["range_max"], cfg["reward"])


# ── Giveaway System ─────────────────────────────────────────────────────────────
active_giveaways = {}  # message_id → {prize, host_id, winners_count, entries, end_time, channel_id}

# ── SQLite persistence (mount a Railway Volume at DB_PATH's directory) ─────────
DB_PATH = os.environ.get("DB_PATH", "/data/giveaways.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS giveaways (
            message_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            prize TEXT NOT NULL,
            host_id INTEGER NOT NULL,
            winners_count INTEGER NOT NULL,
            entries TEXT NOT NULL,
            end_time REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def db_save_giveaway(message_id: int, giveaway: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO giveaways "
        "(message_id, channel_id, prize, host_id, winners_count, entries, end_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            message_id,
            giveaway["channel_id"],
            giveaway["prize"],
            giveaway["host_id"],
            giveaway["winners_count"],
            json.dumps(list(giveaway["entries"])),
            giveaway["end_time"],
        ),
    )
    conn.commit()
    conn.close()


def db_update_entries(message_id: int, entries: set):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE giveaways SET entries = ? WHERE message_id = ?",
        (json.dumps(list(entries)), message_id),
    )
    conn.commit()
    conn.close()


def db_delete_giveaway(message_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM giveaways WHERE message_id = ?", (message_id,))
    conn.commit()
    conn.close()


def db_load_all_giveaways() -> dict:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT message_id, channel_id, prize, host_id, winners_count, entries, end_time FROM giveaways"
    ).fetchall()
    conn.close()

    loaded = {}
    for message_id, channel_id, prize, host_id, winners_count, entries_json, end_time in rows:
        loaded[message_id] = {
            "prize": prize,
            "host_id": host_id,
            "winners_count": winners_count,
            "entries": set(json.loads(entries_json)),
            "end_time": end_time,
            "channel_id": channel_id,
        }
    return loaded


init_db()

_DURATION_PATTERN = re.compile(r'(\d+)\s*(d|h|m|s)', re.IGNORECASE)


def parse_duration(duration_str: str) -> int | None:
    """Parses strings like '1d2h30m' or '2h' into total seconds. Returns None if invalid."""
    matches = _DURATION_PATTERN.findall(duration_str.replace(" ", ""))
    if not matches:
        return None
    unit_seconds = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = sum(int(value) * unit_seconds[unit.lower()] for value, unit in matches)
    return total if total > 0 else None


def format_duration(seconds: int) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "< 1m"


def build_giveaway_embed(giveaway: dict, ended: bool = False) -> discord.Embed:
    end_ts = int(giveaway["end_time"])
    title = f"🎉 {giveaway['prize']}" + (" — ENDED" if ended else "")
    embed = discord.Embed(
        title=title,
        description=(
            f"Ends: <t:{end_ts}:R> (<t:{end_ts}:f>)\n"
            f"Hosted by: <@{giveaway['host_id']}>\n"
            f"Entries: **{len(giveaway['entries'])}**\n"
            f"Winners: **{giveaway['winners_count']}**"
        ),
        color=discord.Color.dark_grey() if ended else discord.Color.blurple(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    return embed


class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.blurple, custom_id="giveaway_join")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        message_id = interaction.message.id
        giveaway = active_giveaways.get(message_id)
        if giveaway is None:
            await interaction.response.send_message(
                "❌ This giveaway has already ended (or the bot restarted and lost track of it — "
                "sorry about that, ask an admin to start a new one).",
                ephemeral=True,
            )
            return

        if interaction.user.id in giveaway["entries"]:
            await interaction.response.send_message("✅ You're already entered in this giveaway!", ephemeral=True)
            return

        giveaway["entries"].add(interaction.user.id)
        db_update_entries(message_id, giveaway["entries"])
        await interaction.response.send_message("🎉 You've entered the giveaway! Good luck!", ephemeral=True)

        embed = build_giveaway_embed(giveaway)
        try:
            await interaction.message.edit(embed=embed)
        except discord.HTTPException:
            pass


async def start_giveaway(interaction: discord.Interaction, prize: str, seconds: int, winners_count: int):
    channel = discord.utils.get(interaction.guild.channels, name=GIVEAWAY_CHANNEL)
    if channel is None:
        await interaction.response.send_message(
            f"❌ Could not find the **{GIVEAWAY_CHANNEL}** channel.", ephemeral=True
        )
        return

    end_time = time.time() + seconds

    giveaway = {
        "prize": prize,
        "host_id": interaction.user.id,
        "winners_count": winners_count,
        "entries": set(),
        "end_time": end_time,
        "channel_id": channel.id,
    }

    embed = build_giveaway_embed(giveaway)
    view = GiveawayView()
    msg = await channel.send(embed=embed, view=view)
    active_giveaways[msg.id] = giveaway
    db_save_giveaway(msg.id, giveaway)

    await interaction.response.send_message(
        f"✅ Giveaway started in {channel.mention}! Ends in {format_duration(seconds)}.",
        ephemeral=True,
    )

    asyncio.create_task(end_giveaway_after(msg.id, seconds))


async def end_giveaway_after(message_id: int, delay: float):
    await asyncio.sleep(delay)
    await finish_giveaway(message_id)


async def finish_giveaway(message_id: int):
    giveaway = active_giveaways.pop(message_id, None)
    if giveaway is None:
        return  # already ended or bot restarted in the meantime
    db_delete_giveaway(message_id)

    channel = client.get_channel(giveaway["channel_id"])
    if channel is None:
        return

    try:
        msg = await channel.fetch_message(message_id)
        await msg.edit(embed=build_giveaway_embed(giveaway, ended=True), view=None)
    except discord.HTTPException:
        pass

    entries = list(giveaway["entries"])
    if not entries:
        await channel.send(f"😔 No one entered the **{giveaway['prize']}** giveaway — no winner could be drawn.")
        return

    winners_count = min(giveaway["winners_count"], len(entries))
    winners = random.sample(entries, winners_count)
    winner_mentions = ", ".join(f"<@{uid}>" for uid in winners)

    result_embed = discord.Embed(
        title="🎉 Giveaway Ended!",
        description=(
            f"**Prize:** {giveaway['prize']}\n"
            f"**Winner{'s' if winners_count > 1 else ''}:** {winner_mentions}\n\n"
            "Please open a ticket in **#ticket-system** to claim your prize!"
        ),
        color=discord.Color.green(),
    )
    result_embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await channel.send(content=winner_mentions, embed=result_embed)


# ── /giveaway-start ─────────────────────────────────────────────────────────────
# Duration is a fixed dropdown (24h / 48h / 72h / Custom). If "Custom" is picked,
# the custom_duration field is required (e.g. "5d", "6h30m", "90m").
@tree.command(name="giveaway-start", description="[Admin only] Start a new giveaway in #giveaways")
@app_commands.describe(
    prize="What are you giving away?",
    duration="How long should the giveaway run?",
    winners="How many winners?",
    custom_duration="Only used when Duration = Custom (e.g. 5d, 6h30m, 90m)",
)
@app_commands.choices(duration=[
    app_commands.Choice(name="24 Hours", value="24h"),
    app_commands.Choice(name="48 Hours", value="48h"),
    app_commands.Choice(name="72 Hours", value="72h"),
    app_commands.Choice(name="Custom",   value="custom"),
])
async def giveaway_start_command(
    interaction: discord.Interaction,
    prize: str,
    duration: app_commands.Choice[str],
    winners: int,
    custom_duration: str = None,
):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(GIVEAWAY_ROLES):
        roles_text = " / ".join(GIVEAWAY_ROLES)
        await interaction.response.send_message(
            f"❌ Only **{roles_text}** can start giveaways.", ephemeral=True
        )
        return

    if winners < 1:
        await interaction.response.send_message(
            "❌ Winners must be a positive whole number.", ephemeral=True
        )
        return

    if duration.value == "custom":
        if not custom_duration:
            await interaction.response.send_message(
                "❌ You selected **Custom** — please also fill in `custom_duration` "
                "(e.g. `5d`, `6h30m`, `90m`).",
                ephemeral=True,
            )
            return
        seconds = parse_duration(custom_duration)
        if seconds is None:
            await interaction.response.send_message(
                "❌ Invalid custom duration format. Use combinations like `1d`, `2h30m`, `45m`.",
                ephemeral=True,
            )
            return
    else:
        seconds = parse_duration(duration.value)

    await start_giveaway(interaction, prize, seconds, winners)


# ── Poll System ─────────────────────────────────────────────────────────────────
POLL_NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


# ── /poll ────────────────────────────────────────────────────────────────────────
@tree.command(name="poll", description="[Admin only] Create a poll in #polls")
@app_commands.describe(
    question="The poll question",
    options="Answer options separated by | (e.g. Ragnarok|Valguero|The Island)",
    info="Optional note shown below the question (e.g. '2 Maps can win this poll')",
)
async def poll_command(interaction: discord.Interaction, question: str, options: str, info: str = None):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(POLL_ROLES):
        roles_text = " / ".join(POLL_ROLES)
        await interaction.response.send_message(
            f"❌ Only **{roles_text}** can create polls.", ephemeral=True
        )
        return

    option_list = [opt.strip() for opt in options.split("|") if opt.strip()]

    if len(option_list) < 2:
        await interaction.response.send_message(
            "❌ Please provide at least 2 options, separated by `|` "
            "(e.g. `Ragnarok|Valguero|The Island`).",
            ephemeral=True,
        )
        return

    if len(option_list) > len(POLL_NUMBER_EMOJIS):
        await interaction.response.send_message(
            f"❌ Too many options — max **{len(POLL_NUMBER_EMOJIS)}** allowed.",
            ephemeral=True,
        )
        return

    polls_ch = discord.utils.get(interaction.guild.channels, name=POLLS_CHANNEL)
    if polls_ch is None:
        await interaction.response.send_message(
            f"❌ Could not find the **{POLLS_CHANNEL}** channel.", ephemeral=True
        )
        return

    options_text = "\n\n".join(
        f"{POLL_NUMBER_EMOJIS[i]}  {opt}" for i, opt in enumerate(option_list)
    )
    description = f"{options_text}\n\n📌 {info}" if info else options_text

    embed = discord.Embed(
        title=f"📊 {question}",
        description=description,
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Poll by {interaction.user.display_name} • Primal Hell")

    msg = await polls_ch.send(embed=embed)
    for i in range(len(option_list)):
        await msg.add_reaction(POLL_NUMBER_EMOJIS[i])

    await interaction.response.send_message(
        f"✅ Poll posted in {polls_ch.mention}!", ephemeral=True
    )


# ── Mystery Box Logic ──────────────────────────────────────────────────────────
def draw_mysterybox(amount: int) -> list[str]:
    """Draws `amount` DISTINCT items (no duplicates) based on weights.
    Each pick is weighted, but the picked item is removed from the pool
    before the next pick, so mysterybox2/3 always yield different items."""
    amount = min(amount, len(_MYSTERYBOX_NAMES))
    remaining_names = list(_MYSTERYBOX_NAMES)
    remaining_weights = list(_MYSTERYBOX_WEIGHTS)

    results = []
    for _ in range(amount):
        picked = random.choices(remaining_names, weights=remaining_weights, k=1)[0]
        idx = remaining_names.index(picked)
        results.append(picked)
        del remaining_names[idx]
        del remaining_weights[idx]

    return results


async def send_mysterybox_result(interaction: discord.Interaction, amount: int):
    if not await check_ticket_channel(interaction):
        return

    results = draw_mysterybox(amount)

    embed = discord.Embed(
        title=f"📦 Mystery Box{'es' if amount > 1 else ''} Opened!",
        description="\n".join(f"🎁 **{item}**" for item in results),
        color=discord.Color.orange(),
    )
    embed.set_footer(text="Primal Hell • A staff member will fulfill this shortly")

    await interaction.response.send_message(embed=embed)


# ── /mysterybox1, /mysterybox2, /mysterybox3 ──────────────────────────────────
@tree.command(name="mysterybox1", description="Open 1 Mystery Box (Dono-request tickets only)")
async def mysterybox1_command(interaction: discord.Interaction):
    await send_mysterybox_result(interaction, 1)


@tree.command(name="mysterybox2", description="Open 2 Mystery Boxes (Dono-request tickets only)")
async def mysterybox2_command(interaction: discord.Interaction):
    await send_mysterybox_result(interaction, 2)


@tree.command(name="mysterybox3", description="Open 3 Mystery Boxes (Dono-request tickets only)")
async def mysterybox3_command(interaction: discord.Interaction):
    await send_mysterybox_result(interaction, 3)


# ── GitHub Webhook → @everyone ping ───────────────────────────────────────────
@client.event
async def on_message(message: discord.Message):
    # Ignore own messages to prevent infinite loop
    if message.author == client.user:
        return
    # Only react to the GitHub webhook bot in the server-changes channel
    # GitHub webhook → @everyone
    if (message.author.bot
            and message.author != client.user
            and message.channel.name == SERVER_CHANGES_CH):
        await message.channel.send("@everyone")

    # Giveaway guess detection
    if not message.author.bot and message.guild:
        giveaway = active_giveaway.get(message.guild.id)
        if giveaway and message.channel.id == giveaway["guess_channel_id"]:
            try:
                guess = int(message.content.strip())
            except ValueError:
                return
            if guess == giveaway["number"]:
                del active_giveaway[message.guild.id]
                announce_ch = message.guild.get_channel(giveaway["announce_channel_id"])
                reward = giveaway["reward"]
                embed = discord.Embed(
                    title="🎉 We have a winner!",
                    description=(
                        f"Congratulations {message.author.mention}! 🏆\n\n"
                        f"The correct number was **{guess}**!\n"
                        f"You won **{reward} Shop Credit**! 🎁\n"
                        "Please open a ticket in **#ticket-system** to claim your reward!"
                    ),
                    color=discord.Color.green(),
                )
                embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                if announce_ch:
                    await announce_ch.send(content="@everyone", embed=embed)


# ── Deleting a giveaway message cancels it ─────────────────────────────────────
@client.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    giveaway = active_giveaways.pop(payload.message_id, None)
    if giveaway is None:
        return  # not a tracked giveaway message

    db_delete_giveaway(payload.message_id)

    channel = client.get_channel(payload.channel_id)
    if channel:
        await channel.send(
            f"🚫 The **{giveaway['prize']}** giveaway was cancelled (message deleted). "
            "No winners were drawn."
        )


# ── Start ──────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    client.add_view(GiveawayView())
    await tree.sync()

    # Reload giveaways that survived a restart and reschedule their timers
    loaded = db_load_all_giveaways()
    active_giveaways.update(loaded)
    now = time.time()
    for message_id, giveaway in loaded.items():
        remaining = giveaway["end_time"] - now
        if remaining <= 0:
            asyncio.create_task(finish_giveaway(message_id))
        else:
            asyncio.create_task(end_giveaway_after(message_id, remaining))

    print(f"✅ Bot online as {client.user} — {len(loaded)} giveaway(s) restored from DB")

client.run(os.environ["DISCORD_TOKEN"])
