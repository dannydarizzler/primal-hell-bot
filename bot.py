import discord
from discord import app_commands
import os

# ── Bot Setup ──────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

SUGGESTIONS_CHANNEL  = "❓｜suggestions"
SERVER_CHANGES_CH    = "🔧｜server-changes"
WIPE_ROLE           = "Admin"          # only members with this role can use /wipe
COMMANDS_CHANNEL    = "🔎｜commands"

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

# ── Channel Lock ───────────────────────────────────────────────────────────────
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
        value="`/taming-guide` — Tranq ammo tiers & Fab Sniper damage multiplier explained",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Armor",
        value="`/armor-guide` — All armor tiers from Hide Toxic to Legend Riot, including perks",
        inline=False,
    )
    embed.add_field(
        name="📊 Server Info",
        value="`/mods` — List of all active mods with descriptions",
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
            "**Upgrade Station** — Upgrade any item to higher quality tiers"
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
            "Armor progresses through 5 tiers. Higher tiers offer better protection "
            "and unique passive perks on certain pieces. All Primal Chaos flak armors "
            "drop exclusively as Blueprints.\n\u200b"
        ),
    )
    embed.add_field(
        name="1️⃣ Hide Toxic — Starter",
        value=(
            "Basic protection for early game survival.\n"
            "Available from the ⚪ **White drop**."
        ),
        inline=False,
    )
    embed.add_field(
        name="2️⃣ Alpha Flak — Alpha Tier",
        value=(
            "Solid mid-game armor, upgrade from Toxic Hide.\n"
            "Available from the 🔵 **Blue drop** (Blueprint, Double only)."
        ),
        inline=False,
    )
    embed.add_field(
        name="3️⃣ Volcanic Flak — Volcanic Tier",
        value=(
            "Strong late-game armor with improved stats.\n"
            "Available from the 🟡 **Yellow drop** (Blueprint, Double only)."
        ),
        inline=False,
    )
    embed.add_field(
        name="4️⃣ Mythic Flak — Mythic Tier ⭐ (2500 armor)",
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
        name="5️⃣ Legend Riot — Legend Tier ⭐⭐ (3000 armor)",
        value=(
            "Top-tier armor with the strongest passive perks.\n"
            "Available from the 🔴 **Red drop** (Blueprint, Double only).\n\n"
            "🪖 Helmet → **×4 Health**\n"
            "👕 Chestpiece → **×4 Torpor Resistance**\n"
            "🧤 Gauntlets → **×4 Melee Damage**\n"
            "👖 Leggings → **×4 Stamina**\n"
            "👢 Boots → **+25% Movement Speed**"
        ),
        inline=False,
    )
    embed.add_field(name="​", value="​", inline=False)
    embed.add_field(
        name="📊 Base Stats — Armor Values (per piece)",
        value=(
            "• Alpha Flak → **500** armor\n"
            "• Volcanic Flak → **1000** armor\n"
            "• Mythic Flak → **2500** armor\n"
            "• Legend Riot → **3000** armor"
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
active_giveaway = {}   # guild_id → {"number": int, "channel_id": int}

# ── /event-100 ────────────────────────────────────────────────────────────────
@tree.command(name="event-100", description="[Admin only] Start a 1-100 guessing giveaway in #events")
async def event_100_command(interaction: discord.Interaction):
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

    import random
    number = random.randint(1, 100)
    global_ch = discord.utils.get(interaction.guild.channels, name="🌍｜chat")
    if global_ch is None:
        await interaction.response.send_message(
            "❌ Could not find the **🌍｜chat** channel.", ephemeral=True
        )
        return

    active_giveaway[interaction.guild.id] = {
        "number": number,
        "guess_channel_id": global_ch.id,
        "announce_channel_id": events_ch.id,
    }

    embed = discord.Embed(
        title="🎉 Global Chat Giveaway!",
        description=(
            "A giveaway is now live in the **Global Chat**!\n\n"
            "Guess a number between **1 and 100**.\n"
            "The first player to guess the correct number wins a surprise! 🎁\n\n"
            "Type your guess directly in this channel. Good luck! 🍀"
        ),
        color=discord.Color.gold(),
    )
    embed.set_footer(text="Primal Hell • ARK Survival Ascended")

    msg = await events_ch.send(content="@everyone", embed=embed)

    await interaction.response.send_message(
        f"✅ Giveaway started in {events_ch.mention}. Secret number: **{number}**",
        ephemeral=True,
    )

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
                embed = discord.Embed(
                    title="🎉 We have a winner!",
                    description=(
                        f"Congratulations {message.author.mention}! 🏆\n\n"
                        f"The correct number was **{guess}**!\n"
                        "Please open a ticket in **#ticket-system** to claim your surprise! 🎁"
                    ),
                    color=discord.Color.green(),
                )
                embed.set_footer(text="Primal Hell • ARK Survival Ascended")
                if announce_ch:
                    await announce_ch.send(content="@everyone", embed=embed)

# ── Start ──────────────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online as {client.user}")

client.run(os.environ["DISCORD_TOKEN"])
