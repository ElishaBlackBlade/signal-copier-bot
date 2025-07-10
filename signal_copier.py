# signal_copier.py (for Replit)
# This bot logs in as a real Telegram user to read messages from a source channel,
# parses them for trade signals, and forwards them to your destination channel.
# This version is designed to read credentials from Replit's "Secrets" manager.

import os
import re
import asyncio
from telethon import TelegramClient, events

# --- Signal Parsing Function ---
def parse_trade_signal(message_text):
    """
    Uses regular expressions to find trade details in a message.
    This function needs to be customized based on the format of the source channel.
    """
    # Define patterns for different signal formats
    patterns = {
        'action': r'(BUY|SELL)\s*([A-Z]{3,6}\/[A-Z]{3,6}|XAUUSD|XAU\/USD|GBPUSD|EURUSD)',
        'entry': r'(Entry|Enter|En)\s*[:\s]*([\d.]+)',
        'tp': r'(TP|Take\s*Profit)\s*[:\s]*([\d.]+)',
        'sl': r'(SL|Stop\s*Loss)\s*[:\s]*([\d.]+)'
    }

    trade = {}

    # Find action and symbol
    action_match = re.search(patterns['action'], message_text, re.IGNORECASE)
    if action_match:
        trade['action'] = action_match.group(1).upper()
        # Standardize symbol format
        trade['symbol'] = action_match.group(2).upper().replace('/', '')
    else:
        return None # If no action/symbol found, it's not a trade signal

    # Find entry, TP, and SL
    entry_match = re.search(patterns['entry'], message_text, re.IGNORECASE)
    if entry_match: trade['entry'] = entry_match.group(2)

    tp_match = re.search(patterns['tp'], message_text, re.IGNORECASE)
    if tp_match: trade['tp'] = tp_match.group(2)

    sl_match = re.search(patterns['sl'], message_text, re.IGNORECASE)
    if sl_match: trade['sl'] = sl_match.group(2)

    # Only return a valid trade if it has at least an action and a symbol
    if 'action' in trade and 'symbol' in trade:
        return trade

    return None

# --- Main Application ---
async def main():
    print("--- Starting Telegram Signal Copier ---")

    # Load credentials from Replit Secrets
    try:
        api_id = int(os.environ['API_ID'])
        api_hash = os.environ['API_HASH']
        source_channel_ids = [int(x.strip()) for x in os.environ['SOURCE_CHANNEL_IDS'].split(',')]
        destination_channel_id = int(os.environ['DESTINATION_CHANNEL_ID'])
    except (KeyError, ValueError) as e:
        print(f"Error reading secrets. Please check all secrets are set correctly. Missing key: {e}")
        return

    # Create the client and connect
    # The 'signal_copier.session' file will be created to remember your login.
    client = TelegramClient('signal_copier.session', api_id, api_hash)

    @client.on(events.NewMessage(chats=source_channel_ids))
    async def handler(event):
        print(f"New message received from source channel {event.chat_id}...")
        message_text = event.message.message

        if not message_text:
            print("Message has no text. Skipping.")
            return

        # Try to parse a trade signal from the message
        trade_signal = parse_trade_signal(message_text)

        if trade_signal:
            print(f"✅ Trade Signal Detected: {trade_signal}")

            # Format the message for your channel
            formatted_message = (
                f"🔥 **Forwarded Signal: {trade_signal.get('symbol')}** 🔥\n\n"
                f"```\n"
                f"Action:      {trade_signal.get('action')}\n"
                f"Entry:       {trade_signal.get('entry', 'Not Specified')}\n"
                f"Stop Loss:   {trade_signal.get('sl', 'Not Specified')}\n"
                f"Take Profit: {trade_signal.get('tp', 'Not Specified')}\n"
                f"```"
            )

            # Send the formatted message to your destination channel
            try:
                await client.send_message(destination_channel_id, formatted_message, parse_mode='Markdown')
                print("Successfully forwarded signal to destination channel.")
            except Exception as e:
                print(f"Error sending message to destination channel: {e}")
        else:
            print("No valid trade signal found in the message.")

    # Start the client
    await client.start()
    print(f"Client started. Listening for new messages in channels: {source_channel_ids}...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
