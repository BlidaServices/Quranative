import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo
from github import Github

async def main():
    # قراءة البيانات من Secrets المستودع مباشرة
    api_id = int(os.environ.get('TG_API_ID'))
    api_hash = os.environ.get('TG_API_HASH')
    session_string = os.environ.get('TG_SESSION')
    gh_token = os.environ.get('GH_TOKEN')
    
    # اسم المستودع (تأكد من كتابته بشكل صحيح: username/repo)
    gh_repo = "Quranative/Quranative" 

    g = Github(gh_token)
    repo = g.get_repo(gh_repo)
    
    source_channel = 'QuranGB'
    target_hashtags = ['#نبات', '#طبيعة']
    
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    
    print("بدء استخراج الفيديوهات بالترقيم...")
    video_number = 1

    async for message in client.iter_messages(source_channel, reverse=True):
        has_tag = message.text and any(tag in message.text for tag in target_hashtags)
        
        if has_tag:
            # التحقق هل المرفق فيديو
            is_video = False
            if message.video:
                is_video = True
            elif message.document and any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
                is_video = True
            
            if is_video:
                try:
                    file_path = await message.download_media()
                    extension = os.path.splitext(file_path)[1] or ".mp4"
                    
                    # الترقيم من 1 إلى الأخير
                    new_name = f"{video_number}{extension}"
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    git_path = f"videos/{new_name}"
                    
                    repo.create_file(
                        path=git_path,
                        message=f"Upload video {new_name}",
                        content=content,
                        branch="main"
                    )
                    
                    print(f"تم رفع: {new_name}")
                    video_number += 1
                    os.remove(file_path)
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"خطأ: {e}")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
