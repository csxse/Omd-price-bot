import discord
import requests
import asyncio
import os
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CMC_API_KEY = os.getenv("CMC_API_KEY")
TEXT_CHANNEL_ID = 1388588609723961445
VOICE_CHANNEL_ID = 1388795944325353595

intents = discord.Intents.default()
client = discord.Client(intents=intents)

headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': CMC_API_KEY
}

def get_omd_data():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {'symbol': 'OMD', 'convert': 'USD'}
    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()
    price = round(data["data"]["OMD"]["quote"]["USD"]["price"], 8)
    change = round(data["data"]["OMD"]["quote"]["USD"]["percent_change_24h"], 2)
    volume = data["data"]["OMD"]["quote"]["USD"]["volume_24h"]
    return price, change, volume

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    while not client.is_closed():
        try:
            price, change, volume = get_omd_data()

            # Text Channel Embed
            text_channel = client.get_channel(TEXT_CHANNEL_ID)
            embed = discord.Embed(
                title="📊 $OMD Price Update",
                description="Latest update from CoinMarketCap",
                color=0x00ff00
            )
            embed.add_field(name="💲 Price", value=f"${price}", inline=True)
            embed.add_field(name="📈 24h Change", value=f"{change}%", inline=True)
            embed.add_field(name="💰 Volume (24h)", value=f"${volume:,.2f}", inline=True)

            embed.add_field(
                name="📊 Chart",
                value="[View on CoinMarketCap](https://coinmarketcap.com/currencies/onemilliondollars/)",
                inline=False
            )
            await text_channel.send(embed=embed)

            # Voice Channel Update (preserves your custom text)
            voice_channel = client.get_channel(VOICE_CHANNEL_ID)
            if voice_channel:
                current_name = voice_channel.name
                # Remove old price in brackets if it exists, keep your custom text
                if "($" in current_name:
                    base_name = current_name.split(" ($")[0]
                else:
                    base_name = current_name

                # Add new price in brackets
                new_name = f"{base_name} (${price})"
                await voice_channel.edit(name=new_name)

        except Exception as e:
            print(f"❌ Error: {e}")

        await asyncio.sleep(900)  # Update every 15 minutes

keep_alive()
client.run(TOKEN)
