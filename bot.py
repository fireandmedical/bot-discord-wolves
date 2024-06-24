import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True  # Aktifkan intent members
intents.message_content = True  # Aktifkan intent message content

# Inisialisasi bot dengan prefix dan intents, nonaktifkan perintah help bawaan
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Dictionary untuk menyimpan link dan judulnya
links = {}

# Event ketika bot siap digunakan
@bot.event
async def on_ready():
    print(f'Bot siap digunakan. Masuk sebagai {bot.user.name}')

# Event ketika anggota baru bergabung
@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name='welcome')
    if welcome_channel:
        embed = discord.Embed(title="Selamat Datang!", description=f'Selamat datang di WOLVES COMMUNITY, {member.mention}!', color=0x00ff00)
        embed.set_thumbnail(url=str(member.avatar.url))
        await welcome_channel.send(embed=embed)
    # Berikan peran default kepada anggota baru
    default_role = discord.utils.get(member.guild.roles, name='Guest')
    if default_role:
        await member.add_roles(default_role)

# Event ketika anggota keluar
@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name='welcome')
    if channel:
        embed = discord.Embed(title="Sampai Jumpa!", description=f'{member.name} telah meninggalkan server.', color=0xff0000)
        embed.set_thumbnail(url=str(member.avatar.url))
        await channel.send(embed=embed)

    # Simpan peran yang dimiliki anggota saat mereka keluar
    with open('left_members.txt', 'a') as f:
        roles = [role.name for role in member.roles if role != member.guild.default_role]
        f.write(f'{member.id}:{",".join(roles)}\n')

# Event ketika anggota kembali ke server
@bot.event
async def on_member_update(before, after):
    if before.pending and not after.pending:  # Jika anggota baru menyelesaikan verifikasi
        # Kembalikan peran yang sebelumnya dimiliki
        with open('left_members.txt', 'r') as f:
            lines = f.readlines()
        with open('left_members.txt', 'w') as f:
            for line in lines:
                member_id, roles = line.strip().split(':')
                if int(member_id) == after.id:
                    roles_to_add = [discord.utils.get(after.guild.roles, name=role) for role in roles.split(',')]
                    for role in roles_to_add:
                        if role:
                            await after.add_roles(role)
                else:
                    f.write(line)

# Kelas untuk menangani interaksi tombol dan modal
class UsernameModal(discord.ui.Modal, title='Isi Username Anda'):
    username = discord.ui.TextInput(label='Username', placeholder='Masukkan username Anda di sini')

    def __init__(self, interaction, role):
        super().__init__()
        self.interaction = interaction
        self.role = role

    async def on_submit(self, interaction: discord.Interaction):
        # Tambahkan peran setelah pengguna mengisi username
        await interaction.user.edit(nick=self.username.value)
        await interaction.user.add_roles(self.role)
        await interaction.response.send_message(f'Terima kasih {self.username.value}, Anda telah diberikan peran {self.role.name}.', ephemeral=True)

class RoleButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝Register Role", style=discord.ButtonStyle.green)
    async def register_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name='Member')
        if role:
            modal = UsernameModal(interaction, role)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message('Peran tidak ditemukan.', ephemeral=True)

    @discord.ui.button(label="🔄Refund Role", style=discord.ButtonStyle.red)
    async def refund_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name='Member')
        if role and role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f'Peran {role.name} telah dihapus dari Anda.', ephemeral=True)
        else:
            await interaction.response.send_message('Anda tidak memiliki peran tersebut atau peran tidak ditemukan.', ephemeral=True)

# Perintah untuk menampilkan tombol register dan refund role
@bot.command()
async def role_buttons(ctx):
    view = RoleButtonView()

    # Embed untuk menampilkan pesan
    embed = discord.Embed(
        title="Selamat Datang di Wolves Community",
        description="Klik tombol di bawah untuk register atau refund peran:",
        color=0x7289DA  # Pilih warna sesuai tema server Anda
    )

    # Tambahkan logo server jika tersedia
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)

    await ctx.send(embed=embed, view=view)

# Perintah untuk membuat saluran teks baru
@bot.command()
@commands.has_permissions(manage_channels=True)
async def create_text_channel(ctx, channel_name):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        await guild.create_text_channel(channel_name)
        embed = discord.Embed(title="Saluran Teks Dibuat", description=f'Saluran teks "{channel_name}" telah dibuat.', color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Kesalahan", description=f'Saluran teks "{channel_name}" sudah ada.', color=0xff0000)
        await ctx.send(embed=embed)

# Perintah untuk membuat saluran suara baru
@bot.command()
@commands.has_permissions(manage_channels=True)
async def create_voice_channel(ctx, channel_name):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        await guild.create_voice_channel(channel_name)
        embed = discord.Embed(title="Saluran Suara Dibuat", description=f'Saluran suara "{channel_name}" telah dibuat.', color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Kesalahan", description=f'Saluran suara "{channel_name}" sudah ada.', color=0xff0000)
        await ctx.send(embed=embed)

# Perintah untuk memberikan peran kepada anggota
@bot.command()
@commands.has_permissions(manage_roles=True)
async def assign_role(ctx, member: discord.Member, role: discord.Role):
    if role in member.roles:
        embed = discord.Embed(title="Kesalahan", description=f'{member.mention} sudah memiliki peran {role.name}.', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await member.add_roles(role)
        embed = discord.Embed(title="Peran Diberikan", description=f'Peran {role.name} telah diberikan kepada {member.mention}.', color=0x00ff00)
        await ctx.send(embed=embed)

# Perintah untuk menghapus peran dari anggota
@bot.command()
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, role: discord.Role):
    if role not in member.roles:
        embed = discord.Embed(title="Kesalahan", description=f'{member.mention} tidak memiliki peran {role.name}.', color=0xff0000)
        await ctx.send(embed=embed)
    else:
        await member.remove_roles(role)
        embed = discord.Embed(title="Peran Dihapus", description=f'Peran {role.name} telah dihapus dari {member.mention}.', color=0x00ff00)
        await ctx.send(embed=embed)

# Perintah untuk menampilkan semua peran anggota
@bot.command()
async def list_roles(ctx, member: discord.Member):
    roles = [role.name for role in member.roles if role != ctx.guild.default_role]
    if roles:
        embed = discord.Embed(title="Peran Anggota", description=f'{member.mention} memiliki peran berikut: {", ".join(roles)}', color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Peran Anggota", description=f'{member.mention} tidak memiliki peran.', color=0xff0000)
        await ctx.send(embed=embed)

# Perintah untuk menyimpan link dengan judul dalam kategori
@bot.command()
async def link(ctx, category: str, title: str, url: str):
    # Simpan link dalam kategori yang sesuai
    if category not in links:
        links[category] = {}
    links[category][title] = url
    embed = discord.Embed(title="Link Disimpan", description=f'Link dengan judul "{title}" dalam kategori "{category}" telah disimpan.', color=0x00ff00)
    await ctx.send(embed=embed)

# Perintah untuk menampilkan semua link yang disimpan
@bot.command()
async def infolink(ctx):
    if not links:
        embed = discord.Embed(title="Info Link", description="Belum ada link yang disimpan.", color=0xff0000)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Info Link", description="Berikut adalah daftar link yang tersimpan berdasarkan kategorinya:", color=0x00ff00)
        for category, links_data in links.items():
            # Tampilkan kategori hanya sekali jika sama dengan kategori sebelumnya
            first_title = True
            for title, url in links_data.items():
                if first_title:
                    embed.add_field(name=f"**{category}**", value=f"[{title}]({url})", inline=False)
                    first_title = False
                else:
                    embed.add_field(name='\u200b', value=f"[{title}]({url})", inline=False)
        
        await ctx.send(embed=embed)

# Perintah bantuan khusus
@bot.command(name='help', aliases=['h', 'bantuan'])
async def custom_help(ctx):
    embed = discord.Embed(title="Bantuan - Perintah", description="Daftar perintah yang tersedia:", color=0x00ff00)
    
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_footer(text=f"Diminta oleh {ctx.author}", icon_url=ctx.author.avatar.url)
    
    commands_info = {
        "create_text_channel <nama_saluran>": "Membuat saluran teks baru.",
        "create_voice_channel <nama_saluran>": "Membuat saluran suara baru.",
        "assign_role <anggota> <peran>": "Memberikan peran kepada anggota.",
        "remove_role <anggota> <peran>": "Menghapus peran dari anggota.",
        "list_roles <anggota>": "Menampilkan semua peran anggota.",
        "role_buttons": "Menampilkan tombol register dan refund peran.",
        "link <kategori> <judul> <url>": "Menyimpan link dengan judul dan kategori.",
        "infolink": "Menampilkan daftar link yang disimpan.",
        "help": "Menampilkan semua informasi perintah dan fungsinya.",
    }
    
    for cmd, desc in commands_info.items():
        embed.add_field(name=f"!{cmd}", value=desc, inline=False)
    
    await ctx.send(embed=embed)

# Jalankan bot
bot.run('MTI1NDY5NTIwMzkzMjA4MjE5OA.Gcp6D3.FCuSd_rMmHFTkNM6A9DoeikIUT7HPnt3Yd5hf8')
