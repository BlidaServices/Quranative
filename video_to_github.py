import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo
from github import Github, Auth

async def main():
    api_id_env = os.environ.get('TG_API_ID')
    api_hash = os.environ.get('TG_API_HASH')
    session_string = os.environ.get('TG_SESSION')
    gh_token = os.environ.get('GH_TOKEN')
    
    gh_repo_name = "Quranative/Quranative" 

    if not api_id_env or not gh_token:
        print("Error: Missing environment variables.")
        return

    auth = Auth.Token(gh_token)
    g = Github(auth=auth)
    
    try:
        repo = g.get_repo(gh_repo_name)
    except Exception as e:
        print(f"Error: Could not find repository. Details: {e}")
        return
    
    source_channel = 'QuranGB'
    target_hashtags = ['#نبات', '#طبيعة']
    
    client = TelegramClient(StringSession(session_string), int(api_id_env), api_hash)
    await client.start()
    
    print("Starting video transfer to 'videos' folder...")
    video_number = 1

    async for message in client.iter_messages(source_channel, reverse=True):
        has_tag = message.text and any(tag in message.text for tag in target_hashtags)
        
        if has_tag:
            is_video = message.video or (message.document and any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes))
            
            if is_video:
                try:
                    file_path = await message.download_media()
                    extension = os.path.splitext(file_path)[1] or ".mp4"
                    new_name = f"{video_number}{extension}"
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # الرفع لمجلد videos
                    repo.create_file(
                        path=f"videos/{new_name}",
                        message=f"Upload video {new_name}",
                        content=content,
                        branch="main"
                    )
                    
                    print(f"Uploaded: {new_name}")
                    video_number += 1
                    os.remove(file_path)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Failed to upload {message.id}: {e}")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
