import discord
import requests
import asyncio
import os
from keep_alive import keep_alive

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CMC_API_KEY = os.getenv("CMC_API_KEY")
TEXT_CHANNEL_ID = int(os.getenv("TEXT_CHANNEL_ID", "1388588609723961445"))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", "1388795944325353595"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': CMC_API_KEY
}

def get_omd_data():
    """Fetch OMD cryptocurrency data from CoinMarketCap API"""
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        parameters = {'symbol': 'OMD', 'convert': 'USD'}
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        data = response.json()
        
        if 'data' not in data or 'OMD' not in data['data']:
            raise ValueError("Invalid API response structure")
            
        omd_data = data["data"]["OMD"]["quote"]["USD"]
        price = round(omd_data["price"], 8)
        change = round(omd_data["percent_change_24h"], 2)
        volume = omd_data["volume_24h"]
        return price, change, volume
    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Error: {e}")
        raise
    except (KeyError, ValueError) as e:
        print(f"❌ Data Processing Error: {e}")
        raise

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    
    # Set bot presence - online status with custom activity
    activity = discord.Game(name="Monitoring OMD prices")
    await client.change_presence(status=discord.Status.online, activity=activity)
    print(f"🟢 Bot status set to online with activity: {activity.name}")
    
    # Main monitoring loop
    while not client.is_closed():
        try:
            price, change, volume = get_omd_data()
            print(f"📊 Fetched OMD data - Price: ${price}, Change: {change}%, Volume: ${volume:,.2f}")

            # Text Channel Embed Update
            text_channel = client.get_channel(TEXT_CHANNEL_ID)
            if text_channel:
                # Determine embed color based on price change
                embed_color = 0x00ff00 if change >= 0 else 0xff0000
                
                embed = discord.Embed(
                    title="📊 $OMD Price Update",
                    description="Latest update from CoinMarketCap",
                    color=embed_color,
                    timestamp=discord.utils.utcnow()
                )
                
                # Format change with appropriate emoji
                change_emoji = "📈" if change >= 0 else "📉"
                change_sign = "+" if change >= 0 else ""
                
                embed.add_field(name="💲 Price", value=f"${price}", inline=True)
                embed.add_field(name=f"{change_emoji} 24h Change", value=f"{change_sign}{change}%", inline=True)
                embed.add_field(name="💰 Volume (24h)", value=f"${volume:,.2f}", inline=True)
                
                embed.add_field(
                    name="📊 Chart",
                    value="[View on CoinMarketCap](https://coinmarketcap.com/currencies/onemilliondollars/)",
                    inline=False
                )
                
                embed.set_footer(text="OMD Price Bot", icon_url=client.user.avatar.url if client.user.avatar else None)
                
                await text_channel.send(embed=embed)
                print(f"✅ Updated text channel with price: ${price}")
            else:
                print(f"❌ Text channel {TEXT_CHANNEL_ID} not found")

            # Voice Channel Update
            voice_channel = client.get_channel(VOICE_CHANNEL_ID)
            if voice_channel:
                current_name = voice_channel.name
                
                # Remove old price in brackets if it exists, keep custom text
                if "($" in current_name:
                    base_name = current_name.split(" ($")[0]
                else:
                    base_name = current_name
                
                # Add new price in brackets
                new_name = f"{base_name} (${price})"
                
                # Only update if the name actually changed
                if current_name != new_name:
                    await voice_channel.edit(name=new_name)
                    print(f"✅ Updated voice channel name to: {new_name}")
                else:
                    print(f"ℹ️ Voice channel name unchanged: {new_name}")
            else:
                print(f"❌ Voice channel {VOICE_CHANNEL_ID} not found")

        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}")
            # Continue running even if there's an error
            
        # Wait 15 minutes before next update
        print(f"⏰ Waiting 15 minutes for next update...")
        await asyncio.sleep(900)

@client.event
async def on_disconnect():
    print("⚠️ Bot disconnected from Discord")

@client.event
async def on_resumed():
    print("🔄 Bot connection resumed")
    # Reset presence after reconnection
    activity = discord.Game(name="Monitoring OMD prices")
    await client.change_presence(status=discord.Status.online, activity=activity)

@client.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Discord event error in {event}: {args}")

# Start the keep-alive server for 24/7 operation
keep_alive()

# Start the Discord bot
try:
    client.run(TOKEN)
except Exception as e:
    print(f"❌ Failed to start bot: {e}")
