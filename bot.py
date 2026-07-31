import discord
from discord import app_commands
import os
import random
import re
import time
import datetime
import asyncio
import struct
import sqlite3
import json
import aiohttp

# ── Bot Setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # required for on_member_update (VIP role auto-sync) and role.members
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Guild ID for instant command sync — replace with your server ID
GUILD_ID = 1516129856944079022
SYNC_GUILD = discord.Object(id=GUILD_ID)

SUGGESTIONS_CHANNEL  = "❓｜suggestions"
SERVER_CHANGES_CH    = "🔧｜server-changes"
WIPE_ROLE           = "Admin"          # only members with this role can use /wipe
COMMANDS_CHANNEL    = "🔎｜commands"
GIVEAWAY_ROLES      = ["Admin", "Owner"]   # only these roles can start giveaways
GIVEAWAY_CHANNEL    = "🎁｜giveaways"        # giveaways always post here
VIP_GIVEAWAY_CHANNEL = "💎｜vip-giveaways"    # VIP-only giveaways always post here
POLL_ROLES          = ["Admin", "Owner"]   # only these roles can create polls
VIP_ROLE_NAME       = "VIP"                 # role granted by boosting — auto-syncs to the shop
SHOUTOUTS_CHANNEL   = "📣｜shoutouts"        # rank-up and VIP-boost shoutouts post here
POLLS_CHANNEL       = "📊｜polls"            # polls always post here
TICKET_CHANNEL      = "🎟️｜ticket-system"    # forum: new post = new ticket
PH_PROMO_CHANNEL_ID = 1528402289117626440  # channel where !ph_promo is accepted
HERMES_BOT_ID       = 1525423361600126977

# ── Hall of Fame (Deathknight Slayer) ────────────────────────────────────────
DEATHKNIGHT_SLAYER_ROLE = "Deathknight Slayer"  # exact role name — adjust if it differs in Discord
HALL_OF_FAME_CHANNEL     = "👑｜hall-of-fame"

# ── Referral bonus ───────────────────────────────────────────────────────────
REFERRAL_BONUS_COINS   = 300   # Coins credited to the inviter per new, unique referral
REFERRAL_MIN_ACCOUNT_AGE_DAYS = 3   # invited account must be at least this old — blocks disposable alt accounts
REFERRAL_LOG_CHANNEL   = "🔧｜server-changes"  # optional: quiet log of every referral (reuses existing channel)

# ── Message-based tier progression ─────────────────────────────────────────
TIER_ROLES = [
    ("Rank - Toxic",     10,    100),
    ("Rank - Alpha",     25,    200),
    ("Rank - Elemental", 60,    300),
    ("Rank - Shadow",    120,   400),
    ("Rank - Mythic",    240,   500),
    ("Rank - Legendary", 480,   600),
    ("Rank - Demonic",   900,   700),
    ("Rank - Spirit",    1400,  800),
    ("Rank - Origin",    1800,  900),
    ("Rank - Nightmare", 2500,  1000),
]

# ── ARK Server Status (RCON) ────────────────────────────────────────────────
ARK_HOST          = os.environ.get("ARK_HOST", "31.214.216.227")
ARK_RCON_PORT     = int(os.environ.get("ARK_RCON_PORT", "11690"))
ARK_RCON_PASSWORD = os.environ.get("ARK_RCON_PASSWORD", "dm7op")
ARK_MAP_NAME      = os.environ.get("ARK_MAP_NAME", "Ragnarok")
ARK_MAX_PLAYERS   = os.environ.get("ARK_MAX_PLAYERS", "20")
ARK_SERVER_NAME   = os.environ.get("ARK_SERVER_NAME", "#Primal-hell-5x-Chaos-Modded")

# ── Loot Drop Data ─────────────────────────────────────────────────────────────
DROPS = {
    "white": {
        "label": "⚪ White — Starter Kit",
        "normal": (
            "• Toxic Hide Armor (5 pieces)\n"
            "• 10x Bola\n"
            "• Toxic Pick\n"
            "• Toxic Hatchet\n"
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
            "• 50–125x Polymer\n"
            "• 50–125x Cementing Paste\n"
            "• 50–125x Silica Pearls\n"
            "• 50–125x Oil"
        ),
        "double": (
            "• 75–200x Polymer\n"
            "• 75–200x Cementing Paste\n"
            "• 75–200x Silica Pearls\n"
            "• 75–200x Oil"
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
            "**Gear Pool (3–8 items, no Blueprints):**\n"
            "• Crossbow · Alpha Flak Set (5 pieces)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike · Chainsaw"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 15–35x Potent/Alpha Tranq Arrows\n"
            "• 2–5x Alpha Health Potion\n"
            "• 2–5x Medium XP Potion\n\n"
            "**Gear Pool (3–11 items, 20% Blueprint chance each):**\n"
            "• Crossbow · Alpha Flak Set (5 pieces)\n"
            "• Alpha Pick · Hatchet · Sickle · Pike · Chainsaw"
        ),
        "quality": "—",
    },
    "purple": {
        "label": "🟣 Purple — Structures",
        "normal": (
            "• 10x Metal Foundation\n"
            "• 15x Metal Wall\n"
            "• 10x Metal Ceiling\n"
            "• Dino Gateway + Gate"
        ),
        "double": (
            "• 20x Metal Foundation\n"
            "• 30x Metal Wall\n"
            "• 20x Metal Ceiling\n"
            "• Dino Gateway + Gate"
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
            "**Gear Pool (3–8 items, no Blueprints):**\n"
            "• Longneck · Volcanic Flak Set (5 pieces)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike · Chainsaw"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 15–35x Tranq Dart (random: Elemental/Alpha/Potent)\n"
            "• 8–24x Elemental ADV Sniper Bullets\n"
            "• 2–5x Large XP Potion\n"
            "• 1–5x Mythic Health Potion\n\n"
            "**Gear Pool (3–8 items, 20% Blueprint chance each):**\n"
            "• Longneck · Volcanic Flak Set (5 pieces)\n"
            "• Volcanic Pick · Hatchet · Sickle · Pike · Chainsaw\n"
            "• Fab Sniper (Mastercraft) *(Double crates only)*"
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
            "**Gear Pool (3–8 items, no Blueprints):**\n"
            "• Fab Sniper · Mythic Flak Set (5 pieces)\n"
            "• Legend Riot Set (5 pieces)\n"
            "• Mythic Pick · Hatchet · Sickle · Pike · Chainsaw"
        ),
        "double": (
            "**Guaranteed:**\n"
            "• 8–25x Mythic/Primal ADV Sniper Bullets (random)\n"
            "• 1–2x Max XP Potion\n"
            "• 1–2x Nightmare Health Potion\n"
            "• 8–25x Primal Compound Bow Arrows\n"
            "• Additional guaranteed Primal ADV Sniper Bullets\n\n"
            "**Gear Pool (3–8 items, 20% Blueprint chance each — no exception for Chainsaw/Compound Bow):**\n"
            "• Fab Sniper · Mythic Flak Set (5 pieces)\n"
            "• Legend Riot Set (5 pieces)\n"
            "• Mythic Pick · Hatchet · Sickle · Pike · Chainsaw\n"
            "• Compound Bow added to pool (20% Blueprint chance like all other items)"
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
        name="🐉 Bosses",
        value="`/boss-fight` — Boss fights modded loot",
        inline=False,
    )
    embed.add_field(
        name="📊 Server Info",
        value=(
            "`/mods` — List of all active mods with descriptions\n"
            "`/serverstatus` — Live player count & map"
        ),
        inline=False,
    )
    embed.add_field(
        name="💰 Coins",
        value=(
            "`/balance` — Check your Primal Coins balance\n"
            "`/whoami` — Get your Discord User ID (for Shop sign-up)"
        ),
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
            "**ARK Primal Chaos** — Full overhaul mod: new dino tiers, weapons, armor & bosses"
        ),
        inline=False,
    )
    embed.add_field(
        name="🦕 Dino Tools",
        value=(
            "**Awesome Spyglass** — Extended spyglass with live stat display for dinos\n"
            "**Dino Depot** — Dino & creature storage, fully crossplay-enabled (not just a cryopod clone — 200+ config options)\n"
            "**Der Dino Finder** — Adds a minimap button to locate any dino on the map"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚙️ Quality of Life",
        value=(
            "**TG Stacking Mod 1000-50** — Stack size ×1000, weight reduced by 50%\n"
            "**A Simple Performance Mod (60 FPS)** — Automatically runs performance commands on join "
            "(see below for full list)\n"
            "**Crash Protector** — Protects logged-out players from wild animals and drowning\n"
            "**Better Breeding** — Guarantees offspring inherit the best wild levels and mutations from their parents\n"
            "**Auto Engrams** — Automatically unlocks engrams as you reach the required level\n"
            "**Upgrade Station** — Upgrade items to higher quality tiers (ARK base items only)\n"
            "**Pull It!** — Pull nearby resources straight into your crafting or repair queue\n"
            "**Greenhouse Glass Fix** — Fixes greenhouse glass opacity so it actually looks like glass\n"
            "**Tribute Table** — Craft and summon all boss fights directly — no artifact or tribute farming required"
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
        title="🥚 Kibble Guide — Primal Chaos",
        description=(
            "Kibble comes in tiers — each tier is crafted from unfertilized eggs of the "
            "previous tier, so keep at least one breeding pair alive per tier as you progress.\n\u200b"
        ),
    )

    embed.add_field(
        name="📈 Progression",
        value=(
            "Alpha → Elemental → Shadow/Fairy → Mythic/Fabled/Legendary → Demonic/Angelic → **Spirit & Chaos**"
        ),
        inline=False,
    )
    embed.add_field(
        name="⚔️ Spirit & Chaos Kibble",
        value=(
            "These two top-tier kibbles aren't unlocked by eggs like the rest — you first need "
            "to **defeat the Spirit Titan and Chaos Titan** to unlock their kibble engrams."
        ),
        inline=False,
    )
    embed.add_field(
        name="💡 Tip",
        value="Don't cull your old breeders once you've moved up a tier — you'll need their eggs again for later kibble.",
        inline=False,
    )

    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed)


# ── /boss-fight ────────────────────────────────────────────────────────────────
@tree.command(name="boss-fight", description="Boss fights per map & how the loot/Element rewards work")
async def boss_fight_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    embed = discord.Embed(
        title="🐉 Boss Fights — Primal Hell",
        description=(
            "Thanks to the **Tribute Table** mod, boss fights can be crafted and summoned "
            "directly — no artifact hunting or tribute farming required. Simply craft the "
            "matching tribute item at the Tribute Table and summon the boss on the "
            "corresponding map.\n\u200b"
        ),
    )

    embed.add_field(
        name="🗺️ Ragnarok — Nunatak (Ice Wyvern)",
        value=(
            "**Element Reward per Difficulty:**\n"
            "• Gamma → **250** Element\n"
            "• Beta → **500** Element\n"
            "• Alpha → **1,000** Element"
        ),
        inline=True,
    )

    embed.add_field(
        name="📝 Note",
        value=(
            "Boss follows currently this order (250 / 500 / 1,000 Element). "
            "If boss loot gets rebalanced in a future patch, this guide will be updated."
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
            f"The first player to guess the correct number wins **{reward}**! 🎁\n\n"
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


# ── /event-custom ─────────────────────────────────────────────────────────────
EVENT_CUSTOM_ROLES = ["Admin", "Owner"]  # only these roles can post custom events


@tree.command(name="event-custom", description="[Admin only] Post a custom event announcement in #events")
@app_commands.describe(
    title="The event's title, e.g. 'Double XP Weekend'",
    info="Details about the event — rules, dates, how to join, rewards, etc.",
    how_it_works="Optional: explain how the event works / how to participate",
    hours="How many hours should the event run? e.g. 16",
    minutes="Extra minutes on top of the hours (optional), e.g. 30",
    prize="Optional: what can players win? e.g. '2,000 Primal Coins' or a Nightmare Breedpair",
    image1="Optional image to attach (e.g. a banner or screenshot)",
    image2="Optional second image",
    image3="Optional third image",
)
async def event_custom_command(
    interaction: discord.Interaction,
    title: str,
    info: str,
    hours: app_commands.Range[int, 0, 720],
    minutes: app_commands.Range[int, 0, 59] = 0,
    how_it_works: str = None,
    prize: str = None,
    image1: discord.Attachment = None,
    image2: discord.Attachment = None,
    image3: discord.Attachment = None,
):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(EVENT_CUSTOM_ROLES):
        roles_text = " / ".join(EVENT_CUSTOM_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can post custom events.", ephemeral=True)
        return

    total_seconds = hours * 3600 + minutes * 60
    if total_seconds <= 0:
        await interaction.response.send_message("❌ Duration must be more than 0 minutes (set hours and/or minutes).", ephemeral=True)
        return

    events_ch = discord.utils.get(interaction.guild.channels, name="🎉｜events")
    if events_ch is None:
        await interaction.response.send_message("❌ Could not find the **🎉｜events** channel.", ephemeral=True)
        return

    images = [img for img in (image1, image2, image3) if img is not None]
    end_time = time.time() + total_seconds
    end_ts = int(end_time)

    description = f"**{title}**\n\n{info}\n\n"
    if how_it_works:
        description += f"⚙️ **How does it work:**\n{how_it_works}\n\n"
    if prize:
        description += f"🎁 **Prize:** {prize}\n\n"
    description += f"⏰ Ends: <t:{end_ts}:R> (<t:{end_ts}:f>)"

    main_embed = discord.Embed(
        title="🎉 New Event!",
        description=description,
        color=discord.Color.gold(),
    )
    if images:
        main_embed.set_image(url=images[0].url)
    main_embed.set_footer(text=f"Hosted by {interaction.user.display_name} • Primal Hell")

    embeds = [main_embed]
    # Discord embeds only support one large image each — extra images become
    # additional embeds on the same message so they all show up together.
    for extra_img in images[1:]:
        embeds.append(discord.Embed(color=discord.Color.gold()).set_image(url=extra_img.url))

    msg = await events_ch.send(content="@everyone", embeds=embeds)
    duration_text = f"{hours}h {minutes}m" if minutes else f"{hours}h"
    await interaction.response.send_message(
        f"✅ Event posted in {events_ch.mention}. Duration: **{duration_text}** — ends <t:{end_ts}:R>.",
        ephemeral=True,
    )

    asyncio.create_task(end_custom_event_after(msg, main_embed, total_seconds))


async def end_custom_event_after(message: discord.Message, embed: discord.Embed, delay_seconds: float):
    """Marks a custom event as ended once its duration passes (best-effort —
    if the bot restarts before then, the event just won't get this final edit,
    but the countdown timestamp in the original message still displays correctly
    for everyone regardless, since Discord renders it client-side)."""
    await asyncio.sleep(delay_seconds)
    ended_embed = embed.copy()
    ended_embed.title = "🎉 Event Ended"
    ended_embed.color = discord.Color.dark_grey()
    try:
        await message.edit(embeds=[ended_embed] + message.embeds[1:])
    except discord.HTTPException:
        pass


# ── /event-100 ────────────────────────────────────────────────────────────────────
@tree.command(name="event-100", description="[Admin only] Start a 1-100 guessing giveaway with a custom prize")
@app_commands.describe(prize="What does the winner get? e.g. '500 Primal Coins' or a Nightmare Breedpair")
async def event_100_command(interaction: discord.Interaction, prize: str):
    await start_guess_event(interaction, 100, prize)


# ── /event-500 ────────────────────────────────────────────────────────────────────
@tree.command(name="event-500", description="[Admin only] Start a 1-500 guessing giveaway with a custom prize")
@app_commands.describe(prize="What does the winner get? e.g. '1,000 Primal Coins' or an Origin Token")
async def event_500_command(interaction: discord.Interaction, prize: str):
    await start_guess_event(interaction, 500, prize)


# ── /event-1000 ───────────────────────────────────────────────────────────────────
@tree.command(name="event-1000", description="[Admin only] Start a 1-1000 guessing giveaway with a custom prize")
@app_commands.describe(prize="What does the winner get? e.g. '2,000 Primal Coins' or Instant Ascension")
async def event_1000_command(interaction: discord.Interaction, prize: str):
    await start_guess_event(interaction, 1000, prize)


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
    # ── Coins system tables (shared SQLite file, separate tables) ──────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS coin_balances (
            discord_id TEXT PRIMARY KEY,
            coins INTEGER NOT NULL DEFAULT 0
        )
    """)
    # ── Message count tracking for tier progression ─────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS message_counts (
            discord_id TEXT PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0
        )
    """)
    # ── Referral rewards — invited_discord_id is PRIMARY KEY so a given
    # account can only ever trigger one payout, no matter how many times it
    # leaves and rejoins the server (leave/rejoin farming is blocked here) ──
    conn.execute("""
        CREATE TABLE IF NOT EXISTS referral_rewards (
            invited_discord_id TEXT PRIMARY KEY,
            inviter_discord_id TEXT NOT NULL,
            rewarded_at REAL NOT NULL
        )
    """)
    # ── Hall of Fame — Deathknight Slayer role, ranked by speedrun time
    # (days between joining the server and earning the role — fewer days is
    # better). discord_id is UNIQUE so re-losing/re-earning the role never
    # creates a second entry or changes someone's original record. ──────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hall_of_fame (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE NOT NULL,
            achieved_at REAL NOT NULL
        )
    """)
    # Migration: speedrun ranking needs join date + computed days-taken, and a
    # flag for backfilled entries where the achieved_at date couldn't be
    # confirmed via the audit log (so days_taken may not be fully accurate).
    hof_columns = [row[1] for row in conn.execute("PRAGMA table_info(hall_of_fame)").fetchall()]
    if "joined_at" not in hof_columns:
        conn.execute("ALTER TABLE hall_of_fame ADD COLUMN joined_at REAL")
    if "days_taken" not in hof_columns:
        conn.execute("ALTER TABLE hall_of_fame ADD COLUMN days_taken REAL")
    if "confirmed" not in hof_columns:
        conn.execute("ALTER TABLE hall_of_fame ADD COLUMN confirmed INTEGER NOT NULL DEFAULT 1")
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


# ── Coins — DB helpers ─────────────────────────────────────────────────────────
def db_add_coins(discord_id: str, amount: int) -> int:
    """Adds `amount` coins to a user's balance (creates the row if needed). Returns new balance."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO coin_balances (discord_id, coins) VALUES (?, ?) "
        "ON CONFLICT(discord_id) DO UPDATE SET coins = coins + excluded.coins",
        (discord_id, amount),
    )
    conn.commit()
    row = conn.execute("SELECT coins FROM coin_balances WHERE discord_id = ?", (discord_id,)).fetchone()
    conn.close()
    return row[0] if row else amount


def db_get_coins(discord_id: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT coins FROM coin_balances WHERE discord_id = ?", (discord_id,)).fetchone()
    conn.close()
    return row[0] if row else 0


def db_increment_message_count(discord_id: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO message_counts (discord_id, count) VALUES (?, 1) "
        "ON CONFLICT(discord_id) DO UPDATE SET count = count + 1",
        (discord_id,),
    )
    conn.commit()
    row = conn.execute("SELECT count FROM message_counts WHERE discord_id = ?", (discord_id,)).fetchone()
    conn.close()
    return row[0] if row else 1


def db_referral_already_rewarded(invited_discord_id: str) -> bool:
    """True if this Discord account has ever triggered a referral payout before
    — the check that stops leave/rejoin (or re-inviting via a different link)
    from farming multiple payouts for the same account."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT 1 FROM referral_rewards WHERE invited_discord_id = ?", (invited_discord_id,)
    ).fetchone()
    conn.close()
    return row is not None


def db_record_referral(invited_discord_id: str, inviter_discord_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO referral_rewards (invited_discord_id, inviter_discord_id, rewarded_at) "
        "VALUES (?, ?, ?)",
        (invited_discord_id, inviter_discord_id, time.time()),
    )
    conn.commit()
    conn.close()


def db_get_referral(invited_discord_id: str):
    """Returns (inviter_discord_id, rewarded_at) for a given invited account, or None."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT inviter_discord_id, rewarded_at FROM referral_rewards WHERE invited_discord_id = ?",
        (invited_discord_id,),
    ).fetchone()
    conn.close()
    return row


# ── Hall of Fame — DB helpers ──────────────────────────────────────────────────
def db_record_hall_of_fame(discord_id: str, joined_at: float, achieved_at: float, confirmed: bool = True) -> tuple[bool, int]:
    """Records (or completes) this Discord ID's Hall of Fame entry, ranked by
    speedrun time: days_taken = achieved_at (when they got the role) minus
    joined_at (when they joined the server) — fewer days is a better rank.

    Inserts a brand-new entry if this is their first time earning the role.
    If they already have an entry, this only ever fills in missing data on a
    legacy row (one recorded before this speedrun system existed) — it never
    overwrites an already-complete entry, so a later re-grant of the role can
    never change someone's original record.

    `confirmed` should be False when achieved_at was backfilled without a
    matching audit log entry (i.e. it's a "best guess", not the real date).
    Returns (is_new, rank) — rank is 1-based, fewer days_taken = better."""
    days_taken = max(0.0, (achieved_at - joined_at) / 86400)
    conn = sqlite3.connect(DB_PATH)

    cur = conn.execute(
        "INSERT OR IGNORE INTO hall_of_fame (discord_id, joined_at, achieved_at, days_taken, confirmed) "
        "VALUES (?, ?, ?, ?, ?)",
        (discord_id, joined_at, achieved_at, days_taken, 1 if confirmed else 0),
    )
    is_new = cur.rowcount > 0

    if not is_new:
        # Only patches up a legacy row that's missing this data — a complete
        # entry is never touched again.
        conn.execute(
            "UPDATE hall_of_fame SET joined_at = ?, achieved_at = ?, days_taken = ?, confirmed = ? "
            "WHERE discord_id = ? AND (joined_at IS NULL OR achieved_at IS NULL OR days_taken IS NULL)",
            (joined_at, achieved_at, days_taken, 1 if confirmed else 0, discord_id),
        )

    conn.commit()
    row = conn.execute(
        "SELECT COUNT(*) + 1 FROM hall_of_fame WHERE days_taken < "
        "(SELECT days_taken FROM hall_of_fame WHERE discord_id = ?)",
        (discord_id,),
    ).fetchone()
    conn.close()
    return is_new, (row[0] if row else 0)


def db_get_hall_of_fame() -> list[tuple[str, float, int]]:
    """Returns (discord_id, days_taken, confirmed) ordered fastest-first."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT discord_id, days_taken, confirmed FROM hall_of_fame "
        "WHERE days_taken IS NOT NULL ORDER BY days_taken ASC"
    ).fetchall()
    conn.close()
    return rows


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


async def start_giveaway(interaction: discord.Interaction, prize: str, seconds: int, winners_count: int, channel_name: str = GIVEAWAY_CHANNEL):
    channel = discord.utils.get(interaction.guild.channels, name=channel_name)
    if channel is None:
        await interaction.response.send_message(
            f"❌ Could not find the **{channel_name}** channel.", ephemeral=True
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


# ── /vip-giveaway-start ──────────────────────────────────────────────────────────
# Identical to /giveaway-start, but posts in the VIP-only giveaway channel instead.
@tree.command(name="vip-giveaway-start", description="[Admin only] Start a new giveaway in #vip-giveaways")
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
async def vip_giveaway_start_command(
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

    await start_giveaway(interaction, prize, seconds, winners, channel_name=VIP_GIVEAWAY_CHANNEL)


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


# ── ARK Server Status (RCON) ─────────────────────────────────────────────────
class SourceRcon:
    """Minimal async Source RCON client (the protocol ARK Survival Ascended uses)."""

    def __init__(self, host: str, port: int, password: str, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self._request_id = 0

    async def _send_packet(self, writer: asyncio.StreamWriter, pkt_type: int, body: str) -> int:
        self._request_id += 1
        req_id = self._request_id
        body_bytes = body.encode("utf-8") + b"\x00\x00"
        payload = struct.pack("<ii", req_id, pkt_type) + body_bytes
        packet = struct.pack("<i", len(payload)) + payload
        writer.write(packet)
        await writer.drain()
        return req_id

    async def _read_packet(self, reader: asyncio.StreamReader):
        size_bytes = await reader.readexactly(4)
        size = struct.unpack("<i", size_bytes)[0]
        payload = await reader.readexactly(size)
        req_id, pkt_type = struct.unpack("<ii", payload[:8])
        body = payload[8:-2].decode("utf-8", errors="ignore")
        return req_id, pkt_type, body

    async def command(self, cmd: str) -> str:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=self.timeout
        )
        try:
            auth_id = await self._send_packet(writer, 3, self.password)
            resp_id, _, _ = await asyncio.wait_for(self._read_packet(reader), timeout=self.timeout)
            if resp_id == -1 or resp_id != auth_id:
                raise ConnectionError("RCON Authentifizierung fehlgeschlagen (falsches Passwort?)")

            await self._send_packet(writer, 2, cmd)
            _, _, body = await asyncio.wait_for(self._read_packet(reader), timeout=self.timeout)
            return body
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


def parse_player_list(raw: str) -> list[dict]:
    """Parses the raw ListPlayers RCON response into a list of {name, steam_id}."""
    if not raw or "No Players Connected" in raw:
        return []
    players = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^\d+\.\s*(.+),\s*(\d+)$", line)
        if match:
            players.append({"name": match.group(1), "steam_id": match.group(2)})
        else:
            players.append({"name": line, "steam_id": None})
    return players


@tree.command(name="serverstatus", description="Zeigt Spieleranzahl, Map und Status des ARK Servers")
async def serverstatus_command(interaction: discord.Interaction):
    if not await check_channel(interaction):
        return

    await interaction.response.defer()

    if not ARK_HOST or not ARK_RCON_PASSWORD:
        await interaction.followup.send(
            "❌ RCON ist nicht konfiguriert (ARK_HOST / ARK_RCON_PASSWORD Umgebungsvariablen fehlen).",
            ephemeral=True,
        )
        return

    try:
        rcon = SourceRcon(ARK_HOST, ARK_RCON_PORT, ARK_RCON_PASSWORD)
        raw = await rcon.command("ListPlayers")
        players = parse_player_list(raw)

        embed = discord.Embed(
            title=f"🦖 {ARK_SERVER_NAME}",
            color=discord.Color.green(),
        )
        embed.add_field(name="Status", value="🟢 Online", inline=True)
        embed.add_field(name="Map", value=ARK_MAP_NAME, inline=True)
        embed.add_field(name="Spieler", value=f"{len(players)} / {ARK_MAX_PLAYERS}", inline=True)

        if players:
            names = "\n".join(f"• {p['name']}" for p in players)[:1000]
            embed.add_field(name="Online", value=names, inline=False)

        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
        await interaction.followup.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title="🦖 Server nicht erreichbar",
            description=f"🔴 RCON-Verbindung fehlgeschlagen: `{e}`",
            color=discord.Color.red(),
        )
        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
        await interaction.followup.send(embed=embed)


# ── /check-items & /redeem-item ────────────────────────────────────────────────
ADMIN_ITEM_ROLES = ["Admin", "Owner"]  # only these roles can view/redeem player items


def _tier_emoji(tier: str) -> str:
    return {"tier1": "🟡", "tier2": "🟣", "tier3": "🔴"}.get(tier, "📦")


@tree.command(name="check-items", description="[Admin only] View a player's won chest items")
@app_commands.describe(player="Which player's items do you want to check?")
async def check_items_command(interaction: discord.Interaction, player: discord.Member):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(ADMIN_ITEM_ROLES):
        roles_text = " / ".join(ADMIN_ITEM_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can check player items.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SHOP_API_URL}/api/admin/items/{player.id}", headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Shop returned an error (status {resp.status}).", ephemeral=True)
                    return
                items = await resp.json()
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    if not items:
        await interaction.followup.send(f"ℹ️ {player.mention} hasn't opened any chests yet.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🎒 Items — {player.display_name}",
        color=discord.Color.orange(),
    )
    lines = []
    for item in items[:25]:  # Discord embed field value limit safety
        status_icon = "✅ Redeemed" if item["status"] == "redeemed" else "🟠 Active"
        lines.append(f"`#{item['id']}` {_tier_emoji(item['tier'])} **{item['item_won']}** — {status_icon}")
    embed.description = "\n".join(lines)
    embed.set_footer(text="Use /redeem-item <ID> once you've delivered an item in-game")
    await interaction.followup.send(embed=embed, ephemeral=True)


@tree.command(name="redeem-item", description="[Admin only] Mark a player's chest item as redeemed (delivered in-game)")
@app_commands.describe(item_id="The item ID shown in /check-items (e.g. 12)")
async def redeem_item_command(interaction: discord.Interaction, item_id: int):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(ADMIN_ITEM_ROLES):
        roles_text = " / ".join(ADMIN_ITEM_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can redeem items.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    body = {"adminDiscordId": str(interaction.user.id)}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SHOP_API_URL}/api/admin/items/{item_id}/redeem", headers=headers, json=body, timeout=10
            ) as resp:
                if resp.status == 404:
                    await interaction.followup.send(f"❌ No item found with ID `#{item_id}`.", ephemeral=True)
                    return
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Shop returned an error (status {resp.status}).", ephemeral=True)
                    return
                item = await resp.json()
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    await interaction.followup.send(
        f"✅ Marked `#{item_id}` **{item['item_won']}** as redeemed for <@{item['discord_id']}>.",
        ephemeral=True,
    )


# ── /fix-discord-id ──────────────────────────────────────────────────────────────
@tree.command(name="fix-discord-id", description="[Admin only] Move a shop account from a wrong Discord ID to the correct one")
@app_commands.describe(
    old_id="The wrong Discord ID currently on the account (as shown/typed by the player)",
    new_id="The player's correct Discord ID",
)
async def fix_discord_id_command(interaction: discord.Interaction, old_id: str, new_id: str):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(ADMIN_ITEM_ROLES):
        roles_text = " / ".join(ADMIN_ITEM_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can fix account IDs.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    body = {"oldDiscordId": old_id, "newDiscordId": new_id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SHOP_API_URL}/api/admin/migrate-discord-id", headers=headers, json=body, timeout=10) as resp:
                data = await resp.json()
                if resp.status != 200:
                    await interaction.followup.send(f"❌ {data.get('error', 'Could not migrate the account.')}", ephemeral=True)
                    return
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    await interaction.followup.send(
        f"✅ Account moved from `{old_id}` to <@{new_id}>. "
        f"Balance, purchases, and item history were all preserved — new balance: **{data['newBalance']:,} Primal Coins**.",
        ephemeral=True,
    )


# ── /set-vip ──────────────────────────────────────────────────────────────────
@tree.command(name="set-vip", description="[Admin only] Give or remove VIP status on a player's shop account")
@app_commands.describe(player="The player to update", vip="Turn VIP status on or off")
@app_commands.choices(vip=[
    app_commands.Choice(name="On — grant VIP", value="on"),
    app_commands.Choice(name="Off — remove VIP", value="off"),
])
async def set_vip_command(interaction: discord.Interaction, player: discord.Member, vip: app_commands.Choice[str]):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(ADMIN_ITEM_ROLES):
        roles_text = " / ".join(ADMIN_ITEM_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can set VIP status.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    body = {"discordId": str(player.id), "isVip": vip.value == "on"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SHOP_API_URL}/api/admin/set-vip", headers=headers, json=body, timeout=10) as resp:
                data = await resp.json()
                if resp.status != 200:
                    await interaction.followup.send(f"❌ {data.get('error', 'Could not update VIP status.')}", ephemeral=True)
                    return
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    status_text = "granted ✅" if vip.value == "on" else "removed"
    await interaction.followup.send(f"💎 VIP status for {player.mention} has been **{status_text}**.", ephemeral=True)


# ── /create-promo & /list-promos ────────────────────────────────────────────────
PROMO_ADMIN_ROLES = ["Admin", "Owner"]  # only these roles can create/view promo codes


@tree.command(name="create-promo", description="[Admin only] Create a promo code — a top-up bonus % or a flat Coin reward")
@app_commands.describe(
    code="The code players will enter, e.g. BONUS20 or REWARD1000",
    type="Bonus = extra % on a Coin top-up. Reward = flat Coins, redeemable directly, no purchase needed.",
    value="Bonus: percentage (e.g. 20 = +20%). Reward: flat Coin amount (e.g. 1000).",
    expires_hours="Code expires after this many hours (omit for no expiry)",
    max_uses="Maximum number of times this code can be used in total (omit for unlimited)",
)
@app_commands.choices(type=[
    app_commands.Choice(name="Bonus — % extra on a Coin top-up", value="bonus"),
    app_commands.Choice(name="Reward — flat Coins, redeemable directly", value="reward"),
])
async def create_promo_command(
    interaction: discord.Interaction,
    code: str,
    type: app_commands.Choice[str],
    value: app_commands.Range[int, 1, 1000000],
    expires_hours: int = None,
    max_uses: int = None,
):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(PROMO_ADMIN_ROLES):
        roles_text = " / ".join(PROMO_ADMIN_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can create promo codes.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    body = {
        "code": code,
        "type": type.value,
        "bonusPercent": value if type.value == "bonus" else None,
        "rewardCoins": value if type.value == "reward" else None,
        "expiresInHours": expires_hours,
        "maxUses": max_uses,
        "createdBy": str(interaction.user.id),
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SHOP_API_URL}/api/admin/promo", headers=headers, json=body, timeout=10) as resp:
                data = await resp.json()
                if resp.status != 200:
                    await interaction.followup.send(f"❌ {data.get('error', 'Could not create code.')}", ephemeral=True)
                    return
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    if data.get("expiresAt"):
        expires_dt = datetime.datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))
        expiry_text = f"<t:{int(expires_dt.timestamp())}:R>"
    else:
        expiry_text = "Never"
    uses_text = str(data["maxUses"]) if data.get("maxUses") else "Unlimited"

    value_line = f"+{data['bonusPercent']}% Coins on top-up" if type.value == "bonus" else f"{data['rewardCoins']:,} Coins (redeemable directly, no purchase needed)"

    embed = discord.Embed(
        title="🎟️ Promo Code Created",
        description=(
            f"Code: **{data['code']}**\n"
            f"Type: **{'Bonus' if type.value == 'bonus' else 'Reward'}**\n"
            f"Value: **{value_line}**\n"
            f"Expires: {expiry_text}\n"
            f"Max uses: {uses_text}"
        ),
        color=discord.Color.gold(),
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


@tree.command(name="list-promos", description="[Admin only] List all promo codes and their usage")
async def list_promos_command(interaction: discord.Interaction):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(PROMO_ADMIN_ROLES):
        roles_text = " / ".join(PROMO_ADMIN_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can view promo codes.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SHOP_API_URL}/api/admin/promo", headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Shop returned an error (status {resp.status}).", ephemeral=True)
                    return
                promos = await resp.json()
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    if not promos:
        await interaction.followup.send("ℹ️ No promo codes exist yet.", ephemeral=True)
        return

    lines = []
    now_ms = discord.utils.utcnow().timestamp() * 1000
    for p in promos[:20]:
        expired = p["expires_at"] and datetime.datetime.fromisoformat(p["expires_at"].replace("Z", "+00:00")).timestamp() * 1000 < now_ms
        status = "🔴 Expired" if expired else "🟢 Active"
        uses = f"{p['uses_count']}/{p['max_uses']}" if p["max_uses"] else f"{p['uses_count']}/∞"
        value_text = f"+{p['bonus_percent']}%" if p.get("type") == "bonus" else f"{p['reward_coins']:,} Coins"
        lines.append(f"**{p['code']}** ({p.get('type', 'bonus')}) — {value_text} · {uses} uses · {status}")

    embed = discord.Embed(title="🎟️ Promo Codes", description="\n".join(lines), color=discord.Color.gold())
    await interaction.followup.send(embed=embed, ephemeral=True)


@tree.command(name="delete-promo", description="[Admin only] Delete a single promo code by its code")
@app_commands.describe(code="The exact promo code to delete, e.g. BONUS20")
async def delete_promo_command(interaction: discord.Interaction, code: str):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(PROMO_ADMIN_ROLES):
        roles_text = " / ".join(PROMO_ADMIN_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can delete promo codes.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{SHOP_API_URL}/api/admin/promo/{code}", headers=headers, timeout=10) as resp:
                if resp.status == 404:
                    await interaction.followup.send(f"❌ No promo code found named **{code}**.", ephemeral=True)
                    return
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Shop returned an error (status {resp.status}).", ephemeral=True)
                    return
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    await interaction.followup.send(f"🗑️ Promo code **{code}** has been deleted.", ephemeral=True)


@tree.command(name="cleanup-promos", description="[Admin only] Delete all expired or fully-used promo codes to keep the list clean")
async def cleanup_promos_command(interaction: discord.Interaction):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(PROMO_ADMIN_ROLES):
        roles_text = " / ".join(PROMO_ADMIN_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can clean up promo codes.", ephemeral=True)
        return

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        await interaction.response.send_message("❌ Shop sync is not configured (SHOP_API_URL / BOT_SYNC_SECRET missing).", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{SHOP_API_URL}/api/admin/promo/cleanup/inactive", headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    await interaction.followup.send(f"❌ Shop returned an error (status {resp.status}).", ephemeral=True)
                    return
                data = await resp.json()
    except Exception as e:
        await interaction.followup.send(f"❌ Could not reach the shop: {e}", ephemeral=True)
        return

    count = data.get("deletedCount", 0)
    if count == 0:
        await interaction.followup.send("✨ No inactive promo codes found — the list is already clean.", ephemeral=True)
    else:
        await interaction.followup.send(
            f"🧹 Cleaned up **{count}** inactive promo code{'s' if count != 1 else ''} "
            f"(expired or fully used).",
            ephemeral=True,
        )


# ── /post-shop-embed ────────────────────────────────────────────────────────────
SHOP_EMBED_ROLES = ["Admin", "Owner"]  # only these roles can post the shop announcement


class ShopLinkView(discord.ui.View):
    def __init__(self, shop_url: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="🛒 Visit the Shop", style=discord.ButtonStyle.link, url=shop_url))


@tree.command(name="post-shop-embed", description="[Admin only] Post the Primal Hell Shop announcement embed in a channel")
@app_commands.describe(channel="Which channel should the embed be posted in?")
async def post_shop_embed_command(interaction: discord.Interaction, channel: discord.TextChannel):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(SHOP_EMBED_ROLES):
        roles_text = " / ".join(SHOP_EMBED_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can post the shop embed.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔥 PRIMAL HELL SHOP",
        description=(
            "Your support fuels the growth of Primal Hell.\n\n"
            "Top up **Primal Coins** with PayPal, open **Mystery Chests**, or buy guaranteed "
            "item packs directly — no ticket, no waiting on a reply. The more you support the "
            "server, the more rewards you unlock."
        ),
        color=discord.Color.from_rgb(255, 90, 31),
    )
    embed.add_field(
        name="🔗 Shop Link",
        value=SHOP_PUBLIC_URL,
        inline=False,
    )
    embed.add_field(
        name="🛒 What you can do there",
        value=(
            "💰 Buy Primal Coins with PayPal\n"
            "📦 Open Mystery Chests for random rewards\n"
            "🛍️ Buy guaranteed packs directly — no RNG\n"
            "🎒 Track every purchase in your **My Items** tab"
        ),
        inline=False,
    )
    embed.add_field(
        name="📦 How to claim your items",
        value="After a purchase, open a ticket on Discord so a staff member can hand it to you in-game.",
        inline=False,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")

    view = ShopLinkView(SHOP_PUBLIC_URL)
    await channel.send(embed=embed, view=view)

    await interaction.response.send_message(f"✅ Shop embed posted in {channel.mention}.", ephemeral=True)


# ── /post-vip-embed ───────────────────────────────────────────────────────────
@tree.command(name="post-vip-embed", description="[Admin only] Post the VIP Status info embed in a channel")
@app_commands.describe(channel="Which channel should the embed be posted in?")
async def post_vip_embed_command(interaction: discord.Interaction, channel: discord.TextChannel):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(SHOP_EMBED_ROLES):
        roles_text = " / ".join(SHOP_EMBED_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can post the VIP embed.", ephemeral=True)
        return

    guild_icon = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None

    embed = discord.Embed(
        title="💎 VIP STATUS 💎",
        description="◈─────────────────────────────◈",
        color=discord.Color.from_rgb(88, 166, 255),
    )
    if guild_icon:
        embed.set_thumbnail(url=guild_icon)

    embed.add_field(
        name="⚙️ How Does It Work",
        value=(
            "**·** Boost the server to automatically unlock VIP status\n"
            "**·** Perks activate instantly — no ticket needed\n"
            "**·** Stays active as long as your Boost is active *(Boosts renew "
            "monthly, auto-cancel if payment stops)*"
        ),
        inline=False,
    )
    embed.add_field(name="🪙 Primal Coins", value="**1,000** monthly\nwhile boosting", inline=True)
    embed.add_field(name="👑 VIP Role", value="Exclusive\nserver role", inline=True)
    embed.add_field(name="🎉 VIP Giveaways", value="Access to\nVIP-only draws", inline=True)
    embed.add_field(
        name="🎡 VIP Lucky Wheel",
        value=(
            "VIPs get their own daily spin on a second wheel with **doubled prizes** "
            "— up to a **5,000 Coin jackpot** — on top of the regular Lucky Wheel. "
            "Find it right below the normal wheel on the Shop's Home tab."
        ),
        inline=False,
    )
    embed.add_field(
        name="📌 Things To Know",
        value=(
            "**·** VIP perks are removed automatically once your Boost expires or is cancelled\n"
            "**·** Primal Coins don't carry over — unused Coins reset each month"
        ),
        inline=False,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended", icon_url=guild_icon)

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ VIP embed posted in {channel.mention}.", ephemeral=True)


# ── /post-server-rules ────────────────────────────────────────────────────────
@tree.command(name="post-server-rules", description="[Admin only] Post the Server Rules embed in a channel")
@app_commands.describe(channel="Which channel should the embed be posted in?")
async def post_server_rules_command(interaction: discord.Interaction, channel: discord.TextChannel):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(SHOP_EMBED_ROLES):
        roles_text = " / ".join(SHOP_EMBED_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can post the server rules.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔥 Primal Hell — Server Rules",
        description=(
            "Welcome to Primal Hell! Please read and follow all rules. "
            "Breaking them may result in a warning, kick or permanent ban."
        ),
        color=discord.Color.from_rgb(255, 90, 31),
    )
    embed.add_field(
        name="🗣️ Respect",
        value="Be respectful to all players at all times. No toxicity, racism, harassment or discrimination of any kind.",
        inline=False,
    )
    embed.add_field(
        name="🌍 Language",
        value=(
            "This is a PvE community with English and German players. Please use **English** "
            "in the English chat and **German** in the German chat. Keep the correct language "
            "in the correct channel so everyone can follow along."
        ),
        inline=False,
    )
    embed.add_field(
        name="⛔ No Cheating",
        value="No cheating, exploiting, meshing or use of any unauthorized third-party tools. Violations result in a permanent ban.",
        inline=False,
    )
    embed.add_field(
        name="📢 No Spam or Advertising",
        value=(
            "No spam or excessive pinging. Advertising of other Discord servers, ARK servers or "
            f"any other content is strictly prohibited without prior approval from Staff. "
            f"Contact us via **{TICKET_CHANNEL}** to request a partnership."
        ),
        inline=False,
    )
    embed.add_field(
        name="👮 Listen to Staff",
        value=f"Follow instructions from Admins and Moderators at all times. If you disagree, open a ticket in **{TICKET_CHANNEL}**.",
        inline=False,
    )
    embed.add_field(
        name="🏗️ Base Limit",
        value=(
            "Each player/tribe is allowed a **maximum of 3 main bases**. Farm bases are excluded "
            "from this limit, but their teleporter must be set to **public** so other players can use it too."
        ),
        inline=False,
    )
    embed.add_field(
        name="🚫 Griefing & Blocking",
        value="No blocking of resources, spawns, obelisks, caves or artifact rooms. No excessive foundation spamming.",
        inline=False,
    )
    embed.add_field(
        name="🎉 Have Fun!",
        value="Help each other out and enjoy the game. We are here to have a good time together!",
        inline=False,
    )
    embed.set_footer(text="Primal Hell • Last updated July 2026")

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Server rules embed posted in {channel.mention}.", ephemeral=True)


# ── /post-hall-of-fame ─────────────────────────────────────────────────────────
HALL_OF_FAME_INTRO = (
    "Only the strongest survive Primal Hell.\n\n"
    "Every Survivor who defeats the Death Knight earns their place among legends "
    "— forever carved into this list, ranked by how fast they did it.\n\n"
    "**How to claim your spot:** Open a support ticket, show your proof of victory, "
    "and claim your exclusive role.\n\n"
    "Do you have what it takes to face the Death Knight and walk away victorious?"
)


@tree.command(name="post-hall-of-fame", description="[Admin only] Post the Deathknight Slayer Hall of Fame ranking")
async def post_hall_of_fame_command(interaction: discord.Interaction):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(SHOP_EMBED_ROLES):
        roles_text = " / ".join(SHOP_EMBED_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can post the Hall of Fame.", ephemeral=True)
        return

    channel = discord.utils.get(interaction.guild.channels, name=HALL_OF_FAME_CHANNEL)
    if channel is None:
        await interaction.response.send_message(f"❌ Could not find the **{HALL_OF_FAME_CHANNEL}** channel.", ephemeral=True)
        return

    entries = db_get_hall_of_fame()  # already ordered fastest-first

    embed = discord.Embed(
        title="👑 HALL OF FAME",
        description=HALL_OF_FAME_INTRO,
        color=discord.Color.gold(),
    )

    if not entries:
        embed.add_field(name="🏆 Rankings", value=f"No one has earned the **{DEATHKNIGHT_SLAYER_ROLE}** role yet. Will it be you?", inline=False)
    else:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, (discord_id, days_taken, confirmed) in enumerate(entries[:50], 1):  # embed length safety
            rank_icon = medals.get(i, f"**{i}.**")
            days_text = f"{days_taken:.0f} day{'s' if round(days_taken) != 1 else ''}"
            note = " *(unconfirmed)*" if not confirmed else ""
            lines.append(f"{rank_icon} <@{discord_id}> — **{days_text}** to slay the Death Knight{note}")
        embed.add_field(name="🏆 Fastest Death Knight Slayers", value="\n".join(lines), inline=False)

    embed.set_footer(text=f"Ranked by speed — days between joining Primal Hell and earning {DEATHKNIGHT_SLAYER_ROLE}")
    await channel.send(embed=embed)

    await interaction.response.send_message(f"✅ Hall of Fame posted in {channel.mention}.", ephemeral=True)


# ── /admin-commands ──────────────────────────────────────────────────────────────
ADMIN_COMMANDS_ROLES = ["Admin", "Owner"]  # only these roles can view this overview


@tree.command(name="admin-commands", description="[Admin only] Shows all available admin commands")
async def admin_commands_command(interaction: discord.Interaction):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(ADMIN_COMMANDS_ROLES):
        roles_text = " / ".join(ADMIN_COMMANDS_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can view this list.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🛠️ Admin Commands",
        description="Overview of every admin-only command on this bot.",
        color=discord.Color.dark_red(),
    )
    embed.add_field(
        name="📢 Announcements",
        value=(
            "`/wipe` — Announce a wild dino wipe in #announcements\n"
            "`/post-shop-embed` — Post the Shop announcement embed\n"
            "`/post-vip-embed` — Post the VIP Status info embed\n"
            "`/post-server-rules` — Post the Server Rules embed\n"
            "`/post-hall-of-fame` — Post the Deathknight Slayer Hall of Fame ranking"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎉 Giveaways & Events",
        value=(
            "`/giveaway-start` — Start a giveaway in #giveaways\n"
            "`/vip-giveaway-start` — Start a giveaway in #vip-giveaways\n"
            "`/event-100` / `/event-500` / `/event-1000` — Number-guess giveaways with a custom prize\n"
            "`/poll` — Create a poll in #polls"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎒 Shop Items",
        value=(
            "`/check-items <player>` — View a player's chest/shop items\n"
            "`/redeem-item <id>` — Mark an item as delivered in-game"
        ),
        inline=False,
    )
    embed.add_field(
        name="🎟️ Promo Codes",
        value=(
            "`/create-promo` — Create a Bonus (%) or Reward (flat Coins) code\n"
            "`/list-promos` — View all promo codes and their usage\n"
            "`/delete-promo <code>` — Delete one specific promo code\n"
            "`/cleanup-promos` — Delete all expired or fully-used codes at once"
        ),
        inline=False,
    )
    embed.add_field(
        name="🔥 Referrals",
        value="`/check-referral <player>` — See who invited a player and whether the bonus was paid",
        inline=False,
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /check-referral ────────────────────────────────────────────────────────────
@tree.command(name="check-referral", description="[Admin only] Check who invited a player and whether the bonus was paid")
@app_commands.describe(player="Which player do you want to check?")
async def check_referral_command(interaction: discord.Interaction, player: discord.Member):
    user_role_names = {role.name for role in interaction.user.roles}
    if not user_role_names.intersection(ADMIN_ITEM_ROLES):
        roles_text = " / ".join(ADMIN_ITEM_ROLES)
        await interaction.response.send_message(f"❌ Only **{roles_text}** can check referrals.", ephemeral=True)
        return

    row = db_get_referral(str(player.id))
    if row is None:
        await interaction.response.send_message(
            f"ℹ️ No referral bonus was ever paid out for {player.mention} "
            "(either they joined without an invite link, the inviter couldn't be determined, "
            "or their account was too new at the time).",
            ephemeral=True,
        )
        return

    inviter_id, rewarded_at = row
    embed = discord.Embed(
        title="🔥 Referral Record",
        description=(
            f"**Invited:** {player.mention}\n"
            f"**Invited by:** <@{inviter_id}>\n"
            f"**Bonus paid:** {REFERRAL_BONUS_COINS:,} Coins\n"
            f"**When:** <t:{int(rewarded_at)}:f>"
        ),
        color=discord.Color.from_rgb(255, 90, 31),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /whoami ──────────────────────────────────────────────────────────────────
@tree.command(name="whoami", description="Get your Discord User ID (needed to sign up on the Shop)")
async def whoami_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🪪 Your Discord User ID",
        description=f"`{interaction.user.id}`\n\nUse this ID when creating your account on the [Primal Hell Shop]({SHOP_PUBLIC_URL}).",
        color=discord.Color.orange(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /message-count ────────────────────────────────────────────────────────────────
@tree.command(name="message-count", description="[Admin only] Check a user's message count")
@app_commands.describe(user="User ID, mention, or username to check")
async def message_count_command(interaction: discord.Interaction, user: str):
    if not any(r.name in ("Admin", "Owner") for r in interaction.user.roles):
        await interaction.response.send_message("❌ Only **Admin** or **Owner** can use this command.", ephemeral=True)
        return
    
    # Parse user ID from mention, ID string, or username
    user_id = None
    if user.startswith("<@") and user.endswith(">"):
        user_id = user[2:-1].replace("!", "")
    elif user.isdigit():
        user_id = user
    else:
        # Try to find by username in guild
        member = discord.utils.get(interaction.guild.members, name=user) or discord.utils.get(interaction.guild.members, display_name=user)
        if member:
            user_id = str(member.id)
    
    if not user_id:
        await interaction.response.send_message("❌ Could not find user. Use ID, mention, or exact username.", ephemeral=True)
        return
    
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT count FROM message_counts WHERE discord_id = ?", (user_id,)).fetchone()
    conn.close()
    count = row[0] if row else 0
    
    # Try to get display name
    member = interaction.guild.get_member(int(user_id))
    display = member.display_name if member else f"Unknown ({user_id})"
    
    embed = discord.Embed(
        title="💬 Message Count",
        description=f"**{display}** has sent **{count:,}** messages.",
        color=discord.Color.blue(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /message-leaderboard ──────────────────────────────────────────────────────────
@tree.command(name="message-leaderboard", description="[Admin only] Show top 20 users by message count")
async def message_leaderboard_command(interaction: discord.Interaction):
    if not any(r.name in ("Admin", "Owner") for r in interaction.user.roles):
        await interaction.response.send_message("❌ Only **Admin** or **Owner** can use this command.", ephemeral=True)
        return
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT discord_id, count FROM message_counts ORDER BY count DESC LIMIT 20").fetchall()
    conn.close()

    if not rows:
        await interaction.response.send_message("No message data yet.", ephemeral=True)
        return

    lines = []
    for i, (discord_id, count) in enumerate(rows, 1):
        member = interaction.guild.get_member(int(discord_id))
        name = member.display_name if member else f"Unknown ({discord_id})"
        lines.append(f"**{i}.** {name} — **{count:,}**")

    embed = discord.Embed(
        title="📊 Message Leaderboard (Top 20)",
        description="\n".join(lines),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /balance ───────────────────────────────────────────────────────────────────
@tree.command(name="balance", description="Check your Primal Hell Coins balance")
async def balance_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    coins = None
    if SHOP_API_URL and BOT_SYNC_SECRET:
        headers = {"x-bot-secret": BOT_SYNC_SECRET}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{SHOP_API_URL}/api/admin/balance/{interaction.user.id}", headers=headers, timeout=10
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        coins = data["coins"]
        except Exception as e:
            print(f"⚠️ Could not fetch live balance for {interaction.user.id}: {e}")

    if coins is None:
        # Fallback to the bot's local (possibly outdated) copy if the shop is unreachable
        coins = db_get_coins(str(interaction.user.id))
        note = "\n\n⚠️ *Could not reach the shop — this number may be outdated.*"
    else:
        note = ""

    embed = discord.Embed(
        title="💰 Your Coin Balance",
        description=f"You currently have **{coins:,} Coins**.\n\nTop up at the [Primal Hell Shop]({SHOP_PUBLIC_URL}).{note}",
        color=discord.Color.orange(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")
    await interaction.followup.send(embed=embed, ephemeral=True)


# ── Shop Sync (PayPal Coin Shop → Bot) ────────────────────────────────────────
# Polls the shop's protected API every SHOP_SYNC_INTERVAL seconds for newly
# completed purchases, credits the coins locally, and DMs the buyer.
SHOP_API_URL       = os.environ.get("SHOP_API_URL", "").rstrip("/")   # e.g. https://primal-hell-shop.up.railway.app
if SHOP_API_URL and not SHOP_API_URL.startswith(("http://", "https://")):
    SHOP_API_URL = f"https://{SHOP_API_URL}"  # tolerate missing protocol in the env var
SHOP_PUBLIC_URL    = os.environ.get("SHOP_PUBLIC_URL", SHOP_API_URL or "https://primal-hell-shop-production.up.railway.app")
BOT_SYNC_SECRET    = os.environ.get("BOT_SYNC_SECRET", "")
SHOP_SYNC_INTERVAL = int(os.environ.get("SHOP_SYNC_INTERVAL", "30"))  # seconds


async def sync_shop_purchases():
    """Background loop: periodically pulls completed-but-unprocessed purchases
    from the shop server and credits the coins to the buyer here in the bot."""
    await client.wait_until_ready()

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        print("⚠️ SHOP_API_URL / BOT_SYNC_SECRET not set — shop coin sync is disabled.")
        return

    headers = {"x-bot-secret": BOT_SYNC_SECRET}

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                async with session.get(f"{SHOP_API_URL}/api/bot/pending-purchases", headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        print(f"⚠️ Shop sync: unexpected status {resp.status}")
                        await asyncio.sleep(SHOP_SYNC_INTERVAL)
                        continue
                    purchases = await resp.json()

                for purchase in purchases:
                    discord_id = purchase["discord_id"]
                    coins = purchase["coins"]
                    new_balance = db_add_coins(discord_id, coins)

                    # Mark as processed first (idempotency > notification delivery)
                    async with session.post(
                        f"{SHOP_API_URL}/api/bot/mark-processed/{purchase['id']}",
                        headers=headers,
                        timeout=10,
                    ):
                        pass

                    # Best-effort DM to the buyer
                    try:
                        user = await client.fetch_user(int(discord_id))
                        embed = discord.Embed(
                            title="🔥 Coins gutgeschrieben!",
                            description=(
                                f"Deine Zahlung wurde bestätigt — **{coins:,} Coins** wurden deinem Konto gutgeschrieben.\n\n"
                                f"Neues Guthaben: **{new_balance:,} Coins**"
                            ),
                            color=discord.Color.orange(),
                        )
                        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                        await user.send(embed=embed)
                    except Exception as dm_err:
                        print(f"ℹ️ Could not DM user {discord_id} about their coin top-up: {dm_err}")

                    print(f"✅ Credited {coins} coins to {discord_id} (new balance: {new_balance})")

            except Exception as e:
                print(f"⚠️ Shop sync error: {e}")

            await asyncio.sleep(SHOP_SYNC_INTERVAL)


async def sync_shop_spins():
    """Background loop: periodically pulls Lucky Wheel spins that haven't been
    DMed yet, and sends the winner a congratulations message."""
    await client.wait_until_ready()

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        print("⚠️ SHOP_API_URL / BOT_SYNC_SECRET not set — Lucky Wheel DM sync is disabled.")
        return

    headers = {"x-bot-secret": BOT_SYNC_SECRET}

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                async with session.get(f"{SHOP_API_URL}/api/bot/pending-spins", headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        print(f"⚠️ Spin sync: unexpected status {resp.status}")
                        await asyncio.sleep(SHOP_SYNC_INTERVAL)
                        continue
                    spins = await resp.json()

                for spin in spins:
                    discord_id = spin["discord_id"]
                    amount = spin["amount"]
                    is_jackpot = bool(spin["jackpot"])

                    # Mark as notified first (idempotency > notification delivery)
                    async with session.post(
                        f"{SHOP_API_URL}/api/bot/mark-spin-notified/{spin['id']}",
                        headers=headers,
                        timeout=10,
                    ):
                        pass

                    try:
                        user = await client.fetch_user(int(discord_id))
                        title = "🎉 JACKPOT!" if is_jackpot else "🎡 Lucky Wheel Win!"
                        embed = discord.Embed(
                            title=title,
                            description=(
                                f"Congratulations, you have won **{amount:,} Primal Coins** on the Lucky Wheel!\n\n"
                                "Spin again in 24 hours."
                            ),
                            color=discord.Color.gold() if is_jackpot else discord.Color.orange(),
                        )
                        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                        await user.send(embed=embed)
                    except Exception as dm_err:
                        print(f"ℹ️ Could not DM user {discord_id} about their Lucky Wheel win: {dm_err}")

                    print(f"🎡 Lucky Wheel: {discord_id} won {amount} coins (jackpot={is_jackpot})")

            except Exception as e:
                print(f"⚠️ Spin sync error: {e}")

            await asyncio.sleep(SHOP_SYNC_INTERVAL)


async def sync_shop_redemptions():
    """Background loop: periodically pulls reward-code redemptions that haven't
    been DMed yet, and sends the player a confirmation of their free Coins."""
    await client.wait_until_ready()

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        print("⚠️ SHOP_API_URL / BOT_SYNC_SECRET not set — promo redemption DM sync is disabled.")
        return

    headers = {"x-bot-secret": BOT_SYNC_SECRET}

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                async with session.get(f"{SHOP_API_URL}/api/bot/pending-redemptions", headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        print(f"⚠️ Redemption sync: unexpected status {resp.status}")
                        await asyncio.sleep(SHOP_SYNC_INTERVAL)
                        continue
                    redemptions = await resp.json()

                for redemption in redemptions:
                    discord_id = redemption["discord_id"]
                    amount = redemption["amount"]
                    code = redemption["code"]

                    # Mark as notified first (idempotency > notification delivery)
                    async with session.post(
                        f"{SHOP_API_URL}/api/bot/mark-redemption-notified/{redemption['id']}",
                        headers=headers,
                        timeout=10,
                    ):
                        pass

                    try:
                        user = await client.fetch_user(int(discord_id))
                        embed = discord.Embed(
                            title="🎟️ Promo Code Redeemed!",
                            description=(
                                f"Congratulations, code **{code}** has credited you **{amount:,} Primal Coins**!\n\n"
                                "Check your balance in the Shop or with `/balance`."
                            ),
                            color=discord.Color.green(),
                        )
                        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                        await user.send(embed=embed)
                    except Exception as dm_err:
                        print(f"ℹ️ Could not DM user {discord_id} about their promo redemption: {dm_err}")

                    print(f"🎟️ Promo redeemed: {discord_id} used {code} for {amount} coins")

            except Exception as e:
                print(f"⚠️ Redemption sync error: {e}")

            await asyncio.sleep(SHOP_SYNC_INTERVAL)


async def sync_shop_vip_spins():
    """Background loop: same as sync_shop_spins, but for the VIP Lucky Wheel."""
    await client.wait_until_ready()

    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        print("⚠️ SHOP_API_URL / BOT_SYNC_SECRET not set — VIP Lucky Wheel DM sync is disabled.")
        return

    headers = {"x-bot-secret": BOT_SYNC_SECRET}

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                async with session.get(f"{SHOP_API_URL}/api/bot/pending-vip-spins", headers=headers, timeout=10) as resp:
                    if resp.status != 200:
                        print(f"⚠️ VIP spin sync: unexpected status {resp.status}")
                        await asyncio.sleep(SHOP_SYNC_INTERVAL)
                        continue
                    spins = await resp.json()

                for spin in spins:
                    discord_id = spin["discord_id"]
                    amount = spin["amount"]
                    is_jackpot = bool(spin["jackpot"])

                    async with session.post(
                        f"{SHOP_API_URL}/api/bot/mark-vip-spin-notified/{spin['id']}",
                        headers=headers,
                        timeout=10,
                    ):
                        pass

                    try:
                        user = await client.fetch_user(int(discord_id))
                        title = "🎉 VIP JACKPOT!" if is_jackpot else "💎 VIP Lucky Wheel Win!"
                        embed = discord.Embed(
                            title=title,
                            description=(
                                f"Congratulations, you have won **{amount:,} Primal Coins** on the VIP Lucky Wheel!\n\n"
                                "Spin again in 24 hours."
                            ),
                            color=discord.Color.purple(),
                        )
                        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                        await user.send(embed=embed)
                    except Exception as dm_err:
                        print(f"ℹ️ Could not DM user {discord_id} about their VIP Lucky Wheel win: {dm_err}")

                    print(f"💎 VIP Lucky Wheel: {discord_id} won {amount} coins (jackpot={is_jackpot})")

            except Exception as e:
                print(f"⚠️ VIP spin sync error: {e}")

            await asyncio.sleep(SHOP_SYNC_INTERVAL)


async def push_vip_status_to_shop(discord_id: str, is_vip: bool):
    """Tells the shop to set/unset a player's VIP flag. Silently ignores players
    who don't have a shop account yet (they'll get VIP once they sign up and an
    admin re-syncs, or next time their role changes)."""
    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        return
    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SHOP_API_URL}/api/admin/set-vip",
                headers=headers,
                json={"discordId": discord_id, "isVip": is_vip},
                timeout=10,
            ) as resp:
                if resp.status == 200:
                    print(f"💎 Synced VIP={is_vip} for {discord_id} (role change)")
                elif resp.status != 404:  # 404 = no shop account yet, not an error
                    print(f"⚠️ Could not sync VIP status for {discord_id}: status {resp.status}")
    except Exception as e:
        print(f"⚠️ Could not sync VIP status for {discord_id}: {e}")


@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """Automatically grants/removes shop VIP status the moment someone's VIP
    role changes (typically from boosting/un-boosting the server). Also
    tracks the Deathknight Slayer Hall of Fame the moment that role is added."""
    had_role = any(r.name == VIP_ROLE_NAME for r in before.roles)
    has_role = any(r.name == VIP_ROLE_NAME for r in after.roles)
    if had_role != has_role:
        await push_vip_status_to_shop(str(after.id), has_role)

        # Public shoutout when someone newly boosts (not when VIP is removed)
        if has_role:
            shoutout_ch = discord.utils.get(after.guild.channels, name=SHOUTOUTS_CHANNEL)
            if shoutout_ch:
                await shoutout_ch.send(
                    f"💎 VIP Shoutout — **{after.display_name}** just boosted the server and unlocked VIP status! 🚀"
                )

    # Deathknight Slayer Hall of Fame tracking — only fires the moment the
    # role is newly added, and only ever counts someone's FIRST time earning it.
    # Ranked by speedrun time: days between joining the server and earning
    # the role, fewer days = better rank.
    had_slayer = any(r.name == DEATHKNIGHT_SLAYER_ROLE for r in before.roles)
    has_slayer = any(r.name == DEATHKNIGHT_SLAYER_ROLE for r in after.roles)
    if has_slayer and not had_slayer:
        joined_at = after.joined_at.timestamp() if after.joined_at else time.time()
        achieved_at = time.time()
        is_new, rank = db_record_hall_of_fame(str(after.id), joined_at, achieved_at, confirmed=True)
        if is_new:
            hof_channel = discord.utils.get(after.guild.channels, name=HALL_OF_FAME_CHANNEL)
            if hof_channel:
                days_taken = max(0.0, (achieved_at - joined_at) / 86400)
                medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                rank_text = medals.get(rank, f"#{rank}")
                await hof_channel.send(
                    f"👑 **{after.display_name}** has slain the Deathknight — **{days_taken:.0f} days** "
                    f"after joining Primal Hell — and earned the **{DEATHKNIGHT_SLAYER_ROLE}** role! "
                    f"They now hold Hall of Fame spot **{rank_text}**! 🏆"
                )


async def sync_vip_roles_on_startup():
    """One-time catch-up on bot startup: makes sure everyone currently holding
    the VIP role is flagged as VIP in the shop, in case a boost happened while
    the bot was offline. Does not remove VIP from anyone (that's handled live
    by on_member_update going forward)."""
    await client.wait_until_ready()
    for guild in client.guilds:
        role = discord.utils.get(guild.roles, name=VIP_ROLE_NAME)
        if not role:
            continue
        for member in role.members:
            await push_vip_status_to_shop(str(member.id), True)


async def sync_hall_of_fame_on_startup():
    """One-time catch-up on bot startup: makes sure everyone currently holding
    the Deathknight Slayer role has a complete Hall of Fame entry — both brand
    new members never recorded before, and legacy entries recorded before the
    speedrun ranking system existed (missing join/achieved dates). Never
    touches an already-complete entry; on_member_update handles everything
    live and accurately from here on.

    Ranked by days_taken = role-grant date minus server-join date. The grant
    date is recovered best-effort from the audit log (Discord retains ~45
    days of entries and requires "View Audit Log" permission) — if it can't
    be found, "now" is used as a placeholder and the entry is marked
    unconfirmed, since days_taken won't be accurate for it."""
    await client.wait_until_ready()
    for guild in client.guilds:
        role = discord.utils.get(guild.roles, name=DEATHKNIGHT_SLAYER_ROLE)
        if not role or not role.members:
            continue

        earned_at = {}
        try:
            async for entry in guild.audit_logs(limit=500, action=discord.AuditLogAction.member_role_update):
                after_roles = getattr(entry.after, "roles", None) or []
                if entry.target and any(r.id == role.id for r in after_roles):
                    if entry.target.id not in earned_at:
                        earned_at[entry.target.id] = entry.created_at.timestamp()
        except discord.Forbidden:
            print("⚠️ Missing 'View Audit Log' permission — backfilled days-taken may not be fully accurate.")
        except discord.HTTPException as e:
            print(f"⚠️ Could not read audit log for Hall of Fame backfill: {e}")

        for member in role.members:
            joined_at = member.joined_at.timestamp() if member.joined_at else time.time()
            confirmed = member.id in earned_at
            achieved_at = earned_at.get(member.id, time.time())

            is_new, rank = db_record_hall_of_fame(str(member.id), joined_at, achieved_at, confirmed=confirmed)
            if is_new:
                tag = "confirmed via audit log" if confirmed else "NOT confirmed — days-taken may be wrong"
                days_taken = max(0.0, (achieved_at - joined_at) / 86400)
                print(f"👑 Hall of Fame backfill: {member.display_name} — {days_taken:.0f} days, rank #{rank} ({tag})")


# ── Discord-activity tier reward: direct Coin credit (no promo code needed) ────
async def grant_tier_reward(discord_id: str, amount: int, tier_name: str):
    """Directly credits Coins to the player's shop balance for reaching a new
    Discord-activity tier, then DMs them — same pattern as the Lucky Wheel,
    no promo code / manual redemption required."""
    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        return
    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SHOP_API_URL}/api/admin/grant-coins",
                headers=headers,
                json={"discordId": discord_id, "amount": amount},
                timeout=10,
            ) as resp:
                if resp.status != 200:
                    print(f"⚠️ Could not grant tier reward for {discord_id}: status {resp.status}")
                    return
                data = await resp.json()
    except Exception as e:
        print(f"⚠️ Could not grant tier reward for {discord_id}: {e}")
        return

    try:
        user = await client.fetch_user(int(discord_id))
        embed = discord.Embed(
            title="🎉 Tier Unlocked!",
            description=(
                f"You reached **{tier_name}**!\n\n"
                f"**{amount:,} Primal Coins** have been credited to your account automatically.\n"
                f"New balance: **{data['newBalance']:,} Coins**"
            ),
            color=discord.Color.gold(),
        )
        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
        await user.send(embed=embed)
    except Exception as dm_err:
        print(f"ℹ️ Could not DM user {discord_id} about their tier reward: {dm_err}")


async def push_tier_progress_to_shop(discord_id: str, message_count: int):
    """Keeps the shop's Profile tab progress bar in sync with the bot's live
    message count. Best-effort — failures are silently ignored so a shop
    hiccup never disrupts normal chatting."""
    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        return
    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SHOP_API_URL}/api/admin/update-tier-progress",
                headers=headers,
                json={"discordId": discord_id, "messageCount": message_count},
                timeout=10,
            ):
                pass
    except Exception:
        pass


# ── Referral Bonus (invite tracking → direct Coin credit) ─────────────────────
# guild_id → {invite_code: (uses, inviter_id, max_uses)} — a snapshot of every
# invite's use-count, refreshed on startup / invite create / member join, so we
# can diff "before vs after" and figure out which invite was used to join.
invite_cache: dict[int, dict[str, tuple[int, int | None, int | None]]] = {}


async def cache_guild_invites(guild: discord.Guild):
    try:
        invites = await guild.invites()
    except discord.Forbidden:
        print(f"⚠️ Missing 'Manage Server' permission — cannot track invites in {guild.name}. "
              f"Referral bonus won't work until the bot role has this permission.")
        return
    except discord.HTTPException as e:
        print(f"⚠️ Could not fetch invites for {guild.name}: {e}")
        return

    invite_cache[guild.id] = {
        inv.code: (inv.uses or 0, inv.inviter.id if inv.inviter else None, inv.max_uses)
        for inv in invites
    }


async def grant_referral_reward(inviter_discord_id: str, invited_display_name: str):
    """Directly credits the inviter's shop balance with the referral bonus,
    then DMs them a referral bonus message — same pattern as the tier/wheel
    rewards, no promo code or manual redemption needed."""
    if not SHOP_API_URL or not BOT_SYNC_SECRET:
        return
    headers = {"x-bot-secret": BOT_SYNC_SECRET}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SHOP_API_URL}/api/admin/grant-coins",
                headers=headers,
                json={"discordId": inviter_discord_id, "amount": REFERRAL_BONUS_COINS},
                timeout=10,
            ) as resp:
                if resp.status != 200:
                    print(f"⚠️ Could not grant referral reward for {inviter_discord_id}: status {resp.status}")
                    return
                data = await resp.json()
    except Exception as e:
        print(f"⚠️ Could not grant referral reward for {inviter_discord_id}: {e}")
        return

    try:
        user = await client.fetch_user(int(inviter_discord_id))
        embed = discord.Embed(
            title="🔥 Referral Bonus!",
            description=(
                f"**{invited_display_name}** joined Primal Hell using your invite!\n\n"
                f"You've been credited **{REFERRAL_BONUS_COINS:,} Primal Coins** as a thank you "
                f"for growing the community.\n"
                f"New balance: **{data['newBalance']:,} Coins**\n\n"
                "Keep sharing your invite link — every new survivor earns you more Coins!\n\n"
                "See you in the fire."
            ),
            color=discord.Color.from_rgb(255, 90, 31),
        )
        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
        await user.send(embed=embed)
    except Exception as dm_err:
        print(f"ℹ️ Could not DM user {inviter_discord_id} about their referral reward: {dm_err}")


@client.event
async def on_invite_create(invite: discord.Invite):
    await cache_guild_invites(invite.guild)


@client.event
async def on_invite_delete(invite: discord.Invite):
    cache = invite_cache.get(invite.guild.id)
    if cache is not None:
        cache.pop(invite.code, None)


@client.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    before = invite_cache.get(guild.id, {})

    try:
        after_invites = await guild.invites()
    except discord.Forbidden:
        return  # bot lacks Manage Server — can't determine the inviter
    except discord.HTTPException:
        return

    after = {
        inv.code: (inv.uses or 0, inv.inviter.id if inv.inviter else None, inv.max_uses)
        for inv in after_invites
    }

    inviter_id = None

    # Case 1: an invite still exists and its use-count went up
    for code, (uses, inv_id, max_uses) in after.items():
        prev = before.get(code)
        if prev is not None and uses > prev[0]:
            inviter_id = inv_id
            break

    # Case 2: an invite hit max_uses on this exact join and got auto-deleted,
    # so it's in "before" but missing from "after"
    if inviter_id is None:
        for code, (uses, inv_id, max_uses) in before.items():
            if code not in after and max_uses and uses + 1 >= max_uses:
                inviter_id = inv_id
                break

    invite_cache[guild.id] = after

    if inviter_id is None or inviter_id == member.id:
        return  # couldn't determine inviter, or someone "invited themselves" (e.g. vanity URL)

    # Anti-farm: block brand-new Discord accounts (common alt-account abuse pattern)
    account_age_days = (discord.utils.utcnow() - member.created_at).days
    if account_age_days < REFERRAL_MIN_ACCOUNT_AGE_DAYS:
        print(f"ℹ️ Referral skipped: {member.id} account too new ({account_age_days}d) — possible alt account.")
        return

    # Anti-farm: this exact Discord account has already triggered a referral
    # payout before (regardless of who invited it this time) — leaving and
    # rejoining, even via a different invite, can never pay out twice.
    if db_referral_already_rewarded(str(member.id)):
        return

    db_record_referral(str(member.id), str(inviter_id))
    asyncio.create_task(grant_referral_reward(str(inviter_id), member.display_name))

    log_ch = discord.utils.get(guild.channels, name=REFERRAL_LOG_CHANNEL)
    if log_ch:
        try:
            await log_ch.send(
                f"🔥 Referral: <@{inviter_id}> invited **{member.display_name}** "
                f"(`{member.id}`) — {REFERRAL_BONUS_COINS} Coins credited."
            )
        except discord.HTTPException:
            pass


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

    # ── PH_PROMO code generation (Hermes bot only) ──
    if (message.author.id == HERMES_BOT_ID
            and message.channel.id == PH_PROMO_CHANNEL_ID):
        m = re.match(r'^!ph_promo (\w+) (\d+) (\d{17,19})$', message.content)
        if m:
            tier = m.group(1)
            amount = int(m.group(2))
            discord_id = m.group(3)
            chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            code = f"PH-{tier.upper()}-{''.join(random.choices(chars, k=6))}"
            if SHOP_API_URL and BOT_SYNC_SECRET:
                headers = {"x-bot-secret": BOT_SYNC_SECRET}
                body = {"code": code, "type": "reward", "rewardCoins": amount, "maxUses": 1, "createdBy": str(message.author.id)}
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(f"{SHOP_API_URL}/api/admin/promo", headers=headers, json=body, timeout=10) as resp:
                            if resp.status != 200:
                                return
                except Exception:
                    return
            await message.channel.send(f"PH_PROMO_OK|tier={tier}|amount={amount}|code={code}|discord={discord_id}")
            try:
                user = await client.fetch_user(int(discord_id))
                tier_label = tier.capitalize()
                dm_embed = discord.Embed(
                    title=f"🎉 Tier Unlocked!",
                    description=(
                        f"You reached the **{tier_label}** tier!\n\n"
                        f"Your Primal Coin code ({amount} coins): `{code}`\n\n"
                        f"👉 **Redeem the code under \"Buy Coins\" in the** [Primal Hell Shop]({SHOP_PUBLIC_URL})"
                    ),
                    color=discord.Color.gold(),
                )
                dm_embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                await user.send(embed=dm_embed)
            except Exception:
                pass

    # ── Tier progression (message count → role + direct Coin credit) ──
    if not message.author.bot and message.guild:
        try:
            uid = str(message.author.id)
            new_count = db_increment_message_count(uid)
            asyncio.create_task(push_tier_progress_to_shop(uid, new_count))

            for tier_name, threshold, coins in TIER_ROLES:
                if new_count == threshold:
                    role = discord.utils.get(message.guild.roles, name=tier_name)
                    if role and role not in message.author.roles:
                        # Remove lower tier roles
                        lower_tiers = [r for r in message.author.roles if any(r.name == t[0] for t in TIER_ROLES)]
                        for r in lower_tiers:
                            try:
                                await message.author.remove_roles(r)
                            except Exception:
                                pass
                        # Add new tier role
                        try:
                            await message.author.add_roles(role)
                        except Exception:
                            pass

                    # Directly credit Coins and DM — no promo code needed
                    asyncio.create_task(grant_tier_reward(uid, coins, tier_name))

                    # Public shoutout so everyone sees the promotion
                    shoutout_ch = discord.utils.get(message.guild.channels, name=SHOUTOUTS_CHANNEL)
                    if shoutout_ch:
                        asyncio.create_task(shoutout_ch.send(
                            f"📣 Shoutout to Survivor **{message.author.display_name}** — just reached **{tier_name}**! 🎉"
                        ))
        except Exception:
            pass

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
                        f"You won **{reward}**! 🎁\n"
                        "Please open a ticket in **#ticket-system** to claim your reward!"
                    ),
                    color=discord.Color.green(),
                )
                embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                if announce_ch:
                    await announce_ch.send(content="@everyone", embed=embed)


# ── Ticket auto-response ─────────────────────────────────────────────────────────
@client.event
async def on_thread_create(thread: discord.Thread):
    if thread.parent and thread.parent.name == TICKET_CHANNEL:
        embed = discord.Embed(
            title="🎟️ Thank you for opening a ticket!",
            description=(
                "A staff member will be with you shortly.\n\n"
                "Please describe your request in detail so we can help you as quickly as possible."
            ),
            color=discord.Color.green(),
        )
        embed.set_footer(text="Primal Hell • ARK Survival Ascended")
        await thread.send(embed=embed)


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
    if SYNC_GUILD:
        # Every @tree.command() above registers globally by default. Guild-scoped
        # sync only pushes commands that exist in the tree's *guild* scope — so
        # without this copy step, tree.sync(guild=...) always pushes an empty
        # list and silently wipes/no-ops the guild's command set. This is what
        # was happening: 0 commands registered every single startup.
        tree.copy_global_to(guild=SYNC_GUILD)
        synced = await tree.sync(guild=SYNC_GUILD)
        print(f"✅ Commands synced to guild {GUILD_ID} — {len(synced)} command(s) registered:")
        print(", ".join(sorted(c.name for c in synced)))

        # One-time cleanup: an old global sync from before guild-only syncing
        # was introduced left every command *also* registered globally, which
        # made Discord show each command twice (once global, once guild-scoped).
        # This wipes the stale global registration. Global changes can take up
        # to ~1 hour to fully disappear from Discord's client cache even after
        # this runs, so don't worry if duplicates linger briefly right after deploy.
        tree.clear_commands(guild=None)
        cleared = await tree.sync()
        print(f"🧹 Cleared stale global commands ({len(cleared)} remain globally — should be 0).")
    else:
        synced = await tree.sync()
        print(f"✅ Commands synced globally (may take up to 1 hour to appear) — {len(synced)} command(s) registered:")
        print(", ".join(sorted(c.name for c in synced)))

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

    # Start the shop → bot coin sync loop (only once, even across reconnects)
    if not getattr(client, "_shop_sync_started", False):
        client._shop_sync_started = True
        asyncio.create_task(sync_shop_purchases())
        asyncio.create_task(sync_shop_spins())
        asyncio.create_task(sync_shop_redemptions())
        asyncio.create_task(sync_shop_vip_spins())
        asyncio.create_task(sync_vip_roles_on_startup())
        asyncio.create_task(sync_hall_of_fame_on_startup())

    # Snapshot every guild's current invites so the referral system has a
    # baseline to diff against on the next member join
    for guild in client.guilds:
        await cache_guild_invites(guild)

    print(f"✅ Bot online as {client.user} — {len(loaded)} giveaway(s) restored from DB")

client.run(os.environ["DISCORD_TOKEN"])
