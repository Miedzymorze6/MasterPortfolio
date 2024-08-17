import os
import requests
from PIL import Image
from io import BytesIO
import yt_dlp as ytdlp
from pydub import AudioSegment
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
import telebot
import eyed3
from eyed3.id3.frames import ImageFrame

# Replace with your own Telegram bot token
API_TOKEN = 'MY_TOKEN_IS_HIDDEN' #sample bot needed
bot = telebot.TeleBot(API_TOKEN)

# Set ffmpeg path
AudioSegment.converter = "C:\\Users\\User\\PycharmProjects\\pythonProject5\\Telegram\\ffmpeg.exe"  #change path as convenient


def get_youtube_video_id(url):
    """Extract video ID from the YouTube URL."""
    if 'v=' in url:
        return url.split('v=')[1].split('&')[0]
    return None


def get_youtube_video_title(url):
    """Get the title of the YouTube video."""
    try:
        with ytdlp.YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            return info_dict.get('title', 'Unknown Title')
    except Exception as e:
        print(f"Error getting video title: {e}")
        return 'Unknown Title'


def calculate_average_color(image):
    """Calculate the average color of an image."""
    pixels = list(image.getdata())
    avg_color = tuple(sum(col) // len(pixels) for col in zip(*pixels))
    return avg_color


def download_and_center_thumbnail(video_url, output_file, size=(1000, 1000)):
    """Download the YouTube video thumbnail, center it, and fill the background with the average color."""
    video_id = get_youtube_video_id(video_url)
    if not video_id:
        print("Invalid YouTube URL.")
        return False

    # Construct the thumbnail URL
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"          

    # Download the thumbnail
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        # Open image
        image = Image.open(BytesIO(response.content))

        # Ensure image is in RGB mode
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Calculate the average color of the original image
        avg_color = calculate_average_color(image)

        # Create a new image with the desired size and background color as average color
        new_image = Image.new("RGB", size, avg_color)

        # Calculate the position to paste the original image onto the center of the new image
        paste_x = (size[0] - image.width) // 2
        paste_y = (size[1] - image.height) // 2

        # Paste the original image onto the new image
        new_image.paste(image, (paste_x, paste_y))

        # Save as JPEG
        new_image.save(output_file, 'JPEG')
        print(f"Thumbnail saved to {output_file}")
        return True
    else:
        print("Failed to retrieve the thumbnail. Check the video URL and try again.")
        return False


def download_audio(video_url: str, bitrate: str, title: str) -> str:
    """Download audio from YouTube and save it as MP3."""
    try:
        # Clean the title to use it as a filename
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
        mp3_filename = f"{safe_title}.mp3"

        # Download video using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{safe_title}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': bitrate,
            }],
            'ffmpeg_location': 'C:\\Users\\User\\PycharmProjects\\pythonProject5\\Telegram\\ffmpeg.exe',      #change path as convenient
        }
        with ytdlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Return the MP3 file path
        return mp3_filename
    except Exception as e:
        print(f"Error: {e}")
        return None


def add_cover_to_mp3(mp3_file, cover_image, title):
    """Add or update album cover and title in the MP3 file."""
    try:
        # Using eyed3 to add title and cover image
        audio = eyed3.load(mp3_file)

        # Initialize the tag if it doesn't exist
        if audio.tag is None:
            audio.initTag()

        # Set the metadata
        audio.tag.title = title

        # Add an image (cover art) to the tag
        with open(cover_image, 'rb') as img_file:
            audio.tag.images.set(3, img_file.read(), 'image/jpeg')

        # Save the changes
        audio.tag.save(version=eyed3.id3.ID3_V2_4)
        print(f"Album cover and title added to {mp3_file}")
    except Exception as e:
        print(f"Error adding cover or title: {e}")


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Send me a YouTube link to convert to audio.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    video_url = message.text
    markup = telebot.types.InlineKeyboardMarkup()

    # Use shorter callback data
    bitrates = ["128", "160", "192", "256", "320"]
    for bitrate in bitrates:
        # Create a short, encoded string for the callback data
        callback_data = f"{bitrate}"
        markup.add(telebot.types.InlineKeyboardButton(f"{bitrate} kbps", callback_data=callback_data))

    bot.reply_to(message, 'Select bitrate for the audio:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    bitrate = call.data
    video_url = call.message.reply_to_message.text  # Assuming the video URL was in the original message

    bot.answer_callback_query(call.id)
    bot.edit_message_text(text=f"Downloading and converting video to {bitrate} kbps audio...",
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id)

    title = get_youtube_video_title(video_url)
    audio_file = download_audio(video_url, bitrate, title)
    if audio_file:
        thumbnail_file = "thumbnail_centered_avg_color.jpg"
        if download_and_center_thumbnail(video_url, thumbnail_file):
            add_cover_to_mp3(audio_file, thumbnail_file, title)

            with open(audio_file, 'rb') as f:
                bot.send_audio(call.message.chat.id, f, title=title, caption=f"Converted to {bitrate} kbps")

            with open(thumbnail_file, 'rb') as f:
                bot.send_photo(call.message.chat.id, f, caption="Cover Photo")

            # Clean up
            os.remove(audio_file)
            os.remove(thumbnail_file)
        else:
            bot.send_message(call.message.chat.id, "Failed to process the thumbnail.")
    else:
        bot.send_message(call.message.chat.id, "Failed to convert video to audio.")


if __name__ == '__main__':
    bot.polling()
