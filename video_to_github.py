import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo
from github import Github

async def main():
    # جلب البيانات من البيئة (عبر الـ YML)
    api_id_env = os.environ.get('TG_API_ID')
    api_hash = os.environ.get('TG_API_HASH')
    session_string = os.environ.get('TG_SESSION')
    gh_token = os.environ.get('GH_TOKEN')
    
    # اسم مستودعك
    gh_repo = "Quranative/Quranative" 

    if not api_id_env:
        print("Error: API_ID is missing in Secrets")
        return

    api_id = int(api_id_env)
    g = Github(gh_token)
    repo = g.get_repo(gh_repo)
    
    source_channel = 'QuranGB'
    target_hashtags = ['#نبات', '#طبيعة']
    
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    
    print("Starting video transfer...")
    video_number = 1

    async for message in client.iter_messages(source_channel, reverse=True):
        has_tag = message.text and any(tag in message.text for tag in target_hashtags)
        
        if has_tag:
            is_video = False
            if message.video:
                is_video = True
            elif message.document and any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
                is_video = True
            
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
                        message=f"Upload {new_name}",
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
