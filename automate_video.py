import asyncio
import configparser
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo
from github import Github

async def main():
    config = configparser.ConfigParser()
    config.read('/storage/emulated/0/Telegram/config.ini')
    
    api_id = int(config.get('Telegram', 'api_id'))
    api_hash = config.get('Telegram', 'api_hash')
    session_string = config.get('Telegram', 'session_string')
    
    gh_token = "YOUR_GITHUB_TOKEN"
    gh_repo = "username/repository"
    
    g = Github(gh_token)
    repo = g.get_repo(gh_repo)
    
    source_channel = 'QuranGB'
    target_hashtags = ['#نبات', '#طبيعة']
    
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    
    print("بدء الرفع بالترقيم التسلسلي (1، 2، 3...)")

    # عداد الفيديوهات
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
                    # تحميل الملف مؤقتاً
                    file_path = await message.download_media()
                    
                    # استخراج الامتداد (مثل .mp4)
                    extension = os.path.splitext(file_path)[1]
                    if not extension:
                        extension = ".mp4"
                    
                    # الاسم الجديد (الترقيم)
                    new_name = f"{video_number}{extension}"
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    git_path = f"videos/{new_name}"
                    
                    # الرفع إلى GitHub
                    repo.create_file(
                        path=git_path,
                        message=f"Upload video {new_name}",
                        content=content,
                        branch="main"
                    )
                    
                    print(f"تم رفع: {new_name}")
                    
                    # زيادة الرقم للفيديو القادم
                    video_number += 1
                    
                    # تنظيف الملفات المحلية
                    os.remove(file_path)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"خطأ في الرسالة {message.id}: {e}")

    await client.disconnect()
    print("تم الانتهاء من رفع جميع الفيديوهات بالترتيب.")

if __name__ == '__main__':
    asyncio.run(main())
