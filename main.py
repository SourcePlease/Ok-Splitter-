import requests
import random
import string
from telegram import ChatAction, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler


# Telegram bot token
TOKEN = "<5559484124:AAG_VXdPqdVbjE2v4KTVxRNEKtb8-zxIxb8>"

# Helper function to generate a random string
def generate_random_string(length):
    letters = string.ascii_lowercase + string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(length))


# Handler function for the /start command
def start_handler(update, context):
    update.message.reply_text("Welcome to the URL Uploader Bot! Send me a URL and I will upload the file to Telegram.")


# Helper function to split a file into chunks
def split_file(file_path, chunk_size):
    with open(file_path, 'rb') as f:
        chunk = f.read(chunk_size)
        while chunk:
            yield chunk
            chunk = f.read(chunk_size)


# Handler function to process URL messages
def url_handler(update, context):
    url = update.message.text

    try:
        # Send 'typing' action to show the bot is working
        context.bot.sendChatAction(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

        # Download the file from the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Generate a random string as file name
        file_name = generate_random_string(10)

        # Save the downloaded content to a file
        file_path = f"{file_name}.{response.headers['Content-Type'].split('/')[-1]}"
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Check the file size and perform splitting if necessary
        file_size = os.path.getsize(file_path)
        if file_size > 2 * 1024 * 1024 * 1024:  # 2GB
            chunk_size = 200 * 1024 * 1024  # 200MB
            i = 1
            for chunk in split_file(file_path, chunk_size):
                chunk_file_path = f"{file_name}_part{i}.part"
                with open(chunk_file_path, 'wb') as f:
                    f.write(chunk)
                context.bot.send_document(chat_id=update.effective_chat.id, document=open(chunk_file_path, 'rb'))

                i += 1
                os.remove(chunk_file_path)
        else:
            # Send the file to Telegram
            context.bot.send_document(chat_id=update.effective_chat.id, document=open(file_path, 'rb'))

        # Remove the temporary file
        os.remove(file_path)

        # Generate a random thumbnail from the downloaded file
        thumbnail_file = f"{file_name}.png"
        os.system(f"ffmpeg -hide_banner -loglevel panic -i {file_path} -vf 'select=gt(scene\,0.5)' -frames:v 1 {thumbnail_file}")

        # Send the thumbnail as a photo
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(thumbnail_file, 'rb'))

        # Remove the temporary thumbnail file
        os.remove(thumbnail_file)

    except Exception as e:
        print(e)
        update.message.reply_text("Sorry, an error occurred. Please try again later.")


# Create the Telegram bot and set the handlers
def main():
    updater = Updater(token=TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start_handler))
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), url_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
