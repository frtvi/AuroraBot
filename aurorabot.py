import os
import re
import sqlite3
import datetime as dt
import random
from zoneinfo import ZoneInfo

import discord # type: ignore
from discord import app_commands # type: ignore
from discord.ext import tasks # type: ignore

# =====================
# Configurações
# =====================
TOKEN = "Seu token aqui"   # <-- SUBSTITUA PELO SEU TOKEN
TIMEZONE = "America/Sao_Paulo"     # instale 'tzdata' no Windows para funcionar
DAILY_HOUR = 9                     # hora local para checar aniversariantes (no fuso acima)

# Banco salvo ao lado do script
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "birthdays.db")
DATE_REGEX = re.compile(r"^(\d{2})/(\d{2})$")  # dd/mm
DEFAULT_CHANNEL_ID = ID-DO-CANAL-AQUI  # defina um canal padrão (ou use /setchannel)

print("Banco de dados em:", os.path.abspath(DB_PATH))

# =====================
# Banco de dados
# =====================
class BirthdayDB:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        with self._conn() as con:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS birthdays (
                    guild_id INTEGER NOT NULL,
                    user_id  INTEGER NOT NULL,
                    month    INTEGER NOT NULL,
                    day      INTEGER NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    guild_id   INTEGER PRIMARY KEY,
                    channel_id INTEGER
                )
                """
            )
            con.commit()

    # birthdays
    def set_birthday(self, guild_id: int, user_id: int, month: int, day: int):
        with self._conn() as con:
            con.execute(
                """
                INSERT INTO birthdays (guild_id, user_id, month, day)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET month=excluded.month, day=excluded.day
                """,
                (guild_id, user_id, month, day),
            )
            con.commit()

    def birthdays_on(self, guild_id: int, month: int, day: int):
        with self._conn() as con:
            cur = con.execute(
                "SELECT user_id FROM birthdays WHERE guild_id=? AND month=? AND day=?",
                (guild_id, month, day),
            )
            return [r[0] for r in cur.fetchall()]

    def all_birthdays(self, guild_id: int):
        with self._conn() as con:
            cur = con.execute(
                "SELECT user_id, day, month FROM birthdays WHERE guild_id=? ORDER BY month, day",
                (guild_id,),
            )
            return cur.fetchall()

    # settings
    def set_channel(self, guild_id: int, channel_id: int):
        with self._conn() as con:
            con.execute(
                """
                INSERT INTO settings (guild_id, channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET channel_id=excluded.channel_id
                """,
                (guild_id, channel_id),
            )
            con.commit()

    def get_channel(self, guild_id: int):
        with self._conn() as con:
            cur = con.execute("SELECT channel_id FROM settings WHERE guild_id=?", (guild_id,))
            row = cur.fetchone()
            return int(row[0]) if row and row[0] else None


db = BirthdayDB(DB_PATH)

# =====================
# Comandos
# =====================
def get_tz():
    try:
        return ZoneInfo(TIMEZONE)
    except Exception:
        print(f"[AVISO] Banco de timezones não encontrado para '{TIMEZONE}'. Usando UTC. "
              f"Instale 'tzdata' (pip install tzdata) para corrigir.")
        return dt.timezone.utc

def parse_ddmm(text: str):
    m = DATE_REGEX.match(text.strip())
    if not m:
        return None
    day = int(m.group(1))
    month = int(m.group(2))
    try:
        # valida com ano bissexto arbitrário para permitir 29/02
        dt.date(2024, month, day)
    except ValueError:
        return None
    return day, month

# =====================
# Bot Aurora
# =====================
intents = discord.Intents.default()
intents.guilds = True
# Evita exigir privileged intent; usaremos menções por ID e fetch_user para DM
intents.members = False

class BirthdayBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tz = get_tz()

    async def setup_hook(self):
        # sincroniza globalmente (fallback) e inicia task diária
        try:
            await self.tree.sync()
            print("[SYNC] Comandos globais sincronizados.")
        except Exception as e:
            print(f"[SYNC][ERRO] Falha ao sincronizar globalmente: {e}")
        self.daily_birthday_check.start()

    async def on_guild_join(self, guild: discord.Guild):
        try:
            await self.tree.sync(guild=guild)
            print(f"[SYNC] Comandos sincronizados para guild {guild.id}")
        except Exception as e:
            print(f"[SYNC][ERRO] Falha ao sincronizar em {guild.id}: {e}")

    async def on_ready(self):
        print(f"{self.user} está online!")
        await self.change_presence(activity=discord.Game(name="Aurora, a bruxa entre mundos ✨"))
        # garante sync por guild e manda apresentação
        for guild in self.guilds:
            try:
                await self.tree.sync(guild=guild)
                print(f"[SYNC] Comandos sincronizados para guild {guild.id}")
            except Exception as e:
                print(f"[SYNC][ERRO] Falha ao sincronizar em {guild.id}: {e}")

            channel_id = db.get_channel(guild.id) or DEFAULT_CHANNEL_ID
            if channel_id:
                try:
                    channel = guild.get_channel(channel_id) or await self.fetch_channel(channel_id)
                    await channel.send(
                        "🌌 **Aurora desperta...**\n"
                        "Entre os ventos gelados de Freljord e o murmúrio dos espíritos, eu observo.\n"
                        "Celebrarei cada alma que nasce sob a luz das auroras. ❄️"
                    )
                except Exception as e:
                    print(f"Erro ao enviar mensagem inicial em {guild.id}: {e}")

    @tasks.loop(time=dt.time(hour=DAILY_HOUR, minute=0, tzinfo=get_tz()))
    async def daily_birthday_check(self):
        now = dt.datetime.now(self.tz)
        month, day = now.month, now.day
        for guild in self.guilds:
            channel_id = db.get_channel(guild.id) or DEFAULT_CHANNEL_ID
            user_ids = db.birthdays_on(guild.id, month, day)
            if not user_ids:
                continue

            # Mensagens baseadas exclusivamente na lore fornecida (canal)
            channel_messages = [
                "❄️ Hoje os ventos de Freljord sussurram o nome de {users}. "
                "Testemunhando o desespero, seguimos celebrando a coragem de existir. — *Aurora, a bruxa entre mundos*",
                "🌌 Sob a luz que atravessa os reinos, {users} é lembrado. "
                "Que cada passo recupere o que foi perdido, como o amigo selvagem que busca sua identidade. — *Aurora, a bruxa entre mundos*",
                "💫 Entre mortais e espíritos, {users} encontra um novo ciclo. "
                "Que a pesquisa pela própria alma te leve além do véu. — *Aurora, a bruxa entre mundos*",
                "🕯️ Nos cantos inóspitos de Freljord, até o frio celebra {users}. "
                "Que a esperança aqueça aquilo que o destino tentou congelar. — *Aurora, a bruxa entre mundos*",
                "🌬️ Hoje, {users} é chamado entre mundos. "
                "Que a jornada para resgatar quem você é brilhe como a aurora. — *Aurora, a bruxa entre mundos*",
            ]

            # Mensagens baseadas na lore (DM)
            dm_messages = [
                "❄️ **Desde que nascemos, buscamos quem somos.** Hoje celebro você. "
                "Que a passagem entre mundos te traga paz e reencontro. — *Aurora, a bruxa entre mundos*",
                "🌌 **A luz atravessa o véu** para tocar sua história. "
                "Que a coragem te acompanhe ao resgatar o que foi perdido. — *Aurora, a bruxa entre mundos*",
                "💫 **Os espíritos escutam seu nome.** "
                "Que sua pesquisa interior encontre respostas no silêncio de Freljord. — *Aurora, a bruxa entre mundos*",
                "🕯️ **Mesmo no gelo, há calor.** "
                "Que seu aniversário aqueça memórias e ilumine sua identidade. — *Aurora, a bruxa entre mundos*",
                "🌬️ **Entre os reinos, eu caminho ao seu lado.** "
                "Que este novo ciclo seja uma trilha de descobertas. — *Aurora, a bruxa entre mundos*",
            ]

            # Envia no canal (se configurado)
            if channel_id:
                try:
                    channel = guild.get_channel(channel_id) or await self.fetch_channel(channel_id)
                    mentions = [f"<@{uid}>" for uid in user_ids]  # sem privileged intents
                    if mentions:
                        msg = random.choice(channel_messages).format(users=", ".join(mentions))
                        await channel.send(msg)
                except Exception as e:
                    print(f"Erro ao enviar mensagem no guild {guild.id}: {e}")

            # Envia DM para cada aniversariante
            for uid in user_ids:
                try:
                    user = await self.fetch_user(uid)  # não requer privileged intents
                    if user:
                        dm_text = random.choice(dm_messages)
                        await user.send(dm_text)
                except Exception as e:
                    print(f"Erro ao enviar DM para {uid}: {e}")

bot = BirthdayBot()

# =====================
# Comandos
# =====================
@bot.tree.command(name="sync", description="(Admin) Sincroniza os comandos da Aurora neste servidor")
@app_commands.checks.has_permissions(administrator=True)
async def sync(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        synced = await bot.tree.sync(guild=interaction.guild)
        await interaction.followup.send(
            f"✅ Sincronizado! {len(synced)} comandos registrados neste servidor.",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(f"❌ Falha ao sincronizar: {e}", ephemeral=True)

@bot.tree.command(name="help", description="Mostra os comandos disponíveis da Aurora")
async def help_cmd(interaction: discord.Interaction):
    help_text = (
        "✨ **Comandos da Aurora** ✨\n"
        "/cadastrar [dd/mm] → Cadastra sua data de aniversário.\n"
        "/editar [dd/mm] → Edita sua data de aniversário.\n"
        "/aniversarios → Lista todos os aniversários do servidor.\n"
        "/setchannel [#canal] → Define o canal de avisos (admin).\n"
        "/sobre → Conheça minha história.\n"
        "/sync → Sincroniza os comandos (admin).\n\n"
        "❄️ *Sou Aurora, a bruxa entre mundos. Onde houver um coração a ser celebrado, lá estarei.* ❄️"
    )
    await interaction.response.send_message(help_text, ephemeral=True)

@bot.tree.command(name="sobre", description="A lore da Aurora")
async def sobre(interaction: discord.Interaction):
    lore = (
        "Desde que nasceu, Aurora vive com uma habilidade inigualável de viajar entre os reinos dos mortais e dos espíritos.\n"
        "Determinada a aprender mais sobre os habitantes do reino espiritual, ela deixou seu lar para trás com o objetivo de conduzir mais pesquisas "
        "e acabou encontrando um semideus corrompido, perdido e deformado.\n\n"
        "Testemunhando tamanho desespero, Aurora decidiu encontrar uma maneira de ajudar seu amigo selvagem a resgatar sua identidade perdida, "
        "uma jornada que a levaria até os cantos mais inóspitos de Freljord."
    )
    await interaction.response.send_message(lore, ephemeral=True)

@bot.tree.command(name="cadastrar", description="Cadastrar sua data de aniversário (dd/mm)")
@app_commands.describe(data="Data no formato dd/mm, ex: 07/09")
async def cadastrar(interaction: discord.Interaction, data: str):
    if not interaction.guild:
        return await interaction.response.send_message("Use este comando dentro de um servidor.", ephemeral=True)
    parsed = parse_ddmm(data)
    if not parsed:
        return await interaction.response.send_message("Formato inválido. Use **dd/mm**.", ephemeral=True)
    day, month = parsed
    db.set_birthday(interaction.guild.id, interaction.user.id, month, day)
    await interaction.response.send_message(
        f"✅ Data cadastrada: **{day:02d}/{month:02d}**! ❄️", ephemeral=True
    )

@bot.tree.command(name="editar", description="Editar sua data de aniversário (dd/mm)")
@app_commands.describe(data="Nova data no formato dd/mm, ex: 31/01")
async def editar(interaction: discord.Interaction, data: str):
    if not interaction.guild:
        return await interaction.response.send_message("Use este comando dentro de um servidor.", ephemeral=True)
    parsed = parse_ddmm(data)
    if not parsed:
        return await interaction.response.send_message("Formato inválido. Use **dd/mm**.", ephemeral=True)
    day, month = parsed
    db.set_birthday(interaction.guild.id, interaction.user.id, month, day)
    await interaction.response.send_message(
        f"✏️ Data atualizada para **{day:02d}/{month:02d}**! 🌌", ephemeral=True
    )

@bot.tree.command(name="setchannel", description="(Admin) Define o canal para mensagens de aniversário")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(canal="Selecione o canal de texto onde a Aurora vai celebrar")
async def setchannel(interaction: discord.Interaction, canal: discord.TextChannel):
    if not interaction.guild:
        return await interaction.response.send_message("Use este comando dentro de um servidor.", ephemeral=True)
    db.set_channel(interaction.guild.id, canal.id)
    await interaction.response.send_message(f"✅ Canal definido para {canal.mention}", ephemeral=True)

@bot.tree.command(name="aniversarios", description="Mostra todos os aniversários cadastrados no servidor")
async def aniversarios(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("Use este comando dentro de um servidor.", ephemeral=True)

    rows = db.all_birthdays(interaction.guild.id)
    if not rows:
        await interaction.response.send_message(
            "🌬️ Nenhum viajante entre mundos cadastrou seu aniversário ainda. ❄️",
            ephemeral=True,
        )
        return

    linhas = []
    for user_id, day, month in rows:
        # tenta obter nome do usuário; se não der, menciona por ID
        nome = f"<@{user_id}>"
        try:
            user = await bot.fetch_user(user_id)
            if user:
                nome = user.display_name
        except Exception:
            pass
        linhas.append(f"✨ {nome} — {day:02d}/{month:02d}")

    texto = "\n".join(linhas)
    embed = discord.Embed(
        title="🎂 Aniversários sob a luz da Aurora 🌌",
        description=texto,
        color=discord.Color.teal(),
    )
    embed.set_footer(text="Aurora, a bruxa entre mundos ❄️")

    await interaction.response.send_message(embed=embed, ephemeral=False)

# =====================
# Execução
# =====================
if __name__ == "__main__":
    if not TOKEN or TOKEN == "COLOQUE_SEU_TOKEN_AQUI":
        print("[ERRO] Insira o token do bot na variável TOKEN.")
    else:
        bot.run(TOKEN)
