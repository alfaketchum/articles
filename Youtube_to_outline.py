import subprocess
import whisper
import openai
import os
import git
import re

# === Configuration ===
GITHUB_REPO_PATH = "/path/to/your/local/repo"  # Path to your local GitHub repository
OPENAI_API_KEY = "your_openai_api_key"  # Replace with your OpenAI API key
YOUTUBE_URL = "https://www.youtube.com/watch?v=VIDEO_ID"  # Replace with the actual YouTube URL

# Function to sanitize filenames (removing special characters)
def sanitize_filename(title):
    return re.sub(r'[\/:*?"<>|]', '', title)  # Removes invalid filename characters

# === Step 1: Get YouTube Video Title ===
def get_video_title(youtube_url):
    """
    Uses yt-dlp to extract the title of the YouTube video.
    """
    result = subprocess.run(
        ["yt-dlp", "--get-title", youtube_url], capture_output=True, text=True
    )
    title = result.stdout.strip()
    return sanitize_filename(title)  # Clean title for use as a filename

# === Step 2: Download audio from YouTube with title-based filename ===
def download_audio(youtube_url):
    """
    Downloads the best audio quality of the YouTube video and saves it with its title as the filename.
    """
    video_title = get_video_title(youtube_url)
    audio_filename = f"{video_title}.mp3"  # Create filename with title
    subprocess.run([
        "yt-dlp", "-f", "bestaudio", "--extract-audio",
        "--audio-format", "mp3", "-o", audio_filename, youtube_url
    ])
    print(f"Audio downloaded successfully: {audio_filename}")
    return audio_filename  # Return the filename for further processing

# === Step 3: Transcribe the audio using Whisper ===
def transcribe_audio(audio_file):
    """
    Loads the Whisper model, transcribes the downloaded audio file, and saves
    the transcript to a text file.
    """
    model = whisper.load_model("medium")  # Load the Medium Whisper model
    result = model.transcribe(audio_file)  # Convert speech to text
    transcript_file = f"{os.path.splitext(audio_file)[0]}.txt"  # Name it after the video
    with open(transcript_file, "w") as f:
        f.write(result["text"])  # Save the transcript
    print("Transcription completed.")
    return result["text"], transcript_file  # Return transcript text & file path

# === Step 4: Generate a structured outline using ChatGPT ===
def generate_outline(transcript):
    """
    Sends the transcript to OpenAI's ChatGPT and requests a structured,
    bulleted outline of the content.
    """
    openai.api_key = OPENAI_API_KEY  # Set API key for OpenAI
    prompt = f"""
    Convert the following transcript into a structured, bulleted outline:

    {transcript}

    Format it with clear sections and sub-bullets.
    """
    
    # Call OpenAI GPT-4 to generate a structured outline
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant that structures text into organized outlines."},
            {"role": "user", "content": prompt}
        ]
    )

    outline = response["choices"][0]["message"]["content"]  # Extract GPT output
    return outline  # Return the structured outline

# === Step 5: Save the outline as an HTML file ===
def save_as_html(outline, title):
    """
    Converts the structured outline into an HTML file with basic styling.
    """
    html_filename = f"{title}.html"  # Name it after the video
    html_content = f"""
    <html>
    <head>
        <title>{title} - Outline</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            ul {{ margin-left: 20px; }}
        </style>
    </head>
    <body>
        <h1>{title} - YouTube Video Outline</h1>
        <pre>{outline}</pre>  <!-- Preformatted text to preserve structure -->
    </body>
    </html>
    """
    
    # Save the HTML file
    with open(html_filename, "w") as f:
        f.write(html_content)
    print(f"Outline saved as HTML: {html_filename}")
    return html_filename

# === Step 6: Commit and push the HTML file to GitHub ===
def push_to_github(file_path):
    """
    Uses GitPython to commit and push the generated outline file to a GitHub repository.
    """
    repo = git.Repo(GITHUB_REPO_PATH)  # Open the local Git repository
    repo.git.add(file_path)  # Stage the HTML file
    repo.index.commit(f"Added outline for {os.path.basename(file_path)}")  # Commit with a message
    origin = repo.remote(name="origin")  # Get the remote origin
    origin.push()  # Push the changes to GitHub
    print("File pushed to GitHub successfully.")

# === Main Automation Process ===
if __name__ == "__main__":
    video_title = get_video_title(YOUTUBE_URL)  # Get the clean title of the YouTube video
    audio_file = download_audio(YOUTUBE_URL)  # Step 1: Download audio with title
    transcript, transcript_file = transcribe_audio(audio_file)  # Step 2: Transcribe audio to text
    outline = generate_outline(transcript)  # Step 3: Generate structured outline
    html_file = save_as_html(outline, video_title)  # Step 4: Convert the outline to an HTML file

    # Move the file to your repo before pushing
    repo_file_path = os.path.join(GITHUB_REPO_PATH, html_file)
    os.rename(html_file, repo_file_path)

    push_to_github(repo_file_path)  # Step 5: Commit and push the file to GitHub
