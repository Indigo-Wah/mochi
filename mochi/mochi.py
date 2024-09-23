'''
    Mochi.py - AI chatbot built for revolt!
'''
import asyncio
import logging
import traceback
import aiohttp
import revolt
import ollama
from config_loader import load_config

config = load_config()  # Grabs config.ini


async def run_ollama_prompt(model, prompt):
    '''
        Run the spesified prompt on the specified ollama model and return the response.
    '''
    try:
        logging.info(
            "Running Ollama prompt on model %s with prompt: %s", model, prompt)
        response = await asyncio.to_thread(ollama.generate, model=model, prompt=prompt)
        if 'response' in response:
            return response['response']
        else:
            logging.error("Unexpected response from Ollama: %s", response)
            return "Error: Unexpected response from model."
    except ollama.RequestError as e:
        logging.error("Error calling Ollama API: %s", e)
        return "Error: Unable to call from the model."
    except ollama.ResponseError as e:
        logging.error("Error with response from Ollama API: %s", e)
        return "Error: Unable to get response from the model."


class Client(revolt.Client):
    '''
    Revolt Client
    '''

    async def on_message(self, message: revolt.Message):
        try:
            if config['BOT_NAME'] in message.raw_mentions:
                mode = config['CHANNELS'].get(
                    message.channel.id, config['DEFAULT_MODE'])
                logging.info(
                    "CHANNEL: %s, MODE: %s, USER: %s", message.channel.id, mode, message.author.id)

                if mode != config['DEFAULT_MODE'] and message.author.id != config['OWNER_ID']:
                    reply = "ACCESS DENIED - try in another channel :)"
                else:
                    model = config['MODELS'].get(mode)
                    history = message.state.messages
                    context = ' '.join(
                        [msg.content for msg in reversed(history)])
                    prompt = config['PROMPTS'].get(
                        mode).format(context, message.content)

                    logging.info("PROMPT: %s", prompt)

                    # Get the response from the model
                    reply = await run_ollama_prompt(model, prompt)
                    logging.info("REPLY: %s", reply)

                # Send the reply message
                await message.channel.send(reply)
        except Exception as e:
            logging.error("Error handling message: %s", e)
            traceback.print_exc()
            await message.channel.send("An error occurred while processing your request.")


async def main():
    '''
    Async Handler and Revolt Class Initialization
    '''
    try:
        async with aiohttp.ClientSession() as session:
            client = Client(session, config['BOT_TOKEN'])
            await client.start()
    except Exception as e:
        logging.error("Error in main bot function: %s", e)
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
