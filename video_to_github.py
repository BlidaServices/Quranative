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
    
    # بيانات GitHub - يفضل وضعها في config.ini أو كمتغيرات بيئة
    gh_token = "YOUR_GITHUB_TOKEN"
    gh_repo = "username/repository"
    
    g = Github(gh_token)
    repo = g.get_repo(gh_repo)
    
    source_channel = 'QuranGB'
    target_hashtags = ['#نبات', '#طبيعة']
    
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    await client.start()
    
    print("بدء استخراج الفيديوهات والرفع إلى GitHub...")

    async for message in client.iter_messages(source_channel, reverse=True):
        # التحقق من الوسم
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
                    print(f"جاري معالجة الفيديو: {message.id}")
                    # تحميل الملف محلياً
                    file_path = await message.download_media()
                    file_name = os.path.basename(file_path)
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # الرفع للمجلد المحدد
                    git_path = f"videos/{file_name}"
                    
                    repo.create_file(
                        path=git_path,
                        message=f"Auto-upload video {file_name}",
                        content=content,
                        branch="main"
                    )
                    
                    print(f"تم الرفع بنجاح: {git_path}")
                    os.remove(file_path)
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"حدث خطأ مع الرسالة {message.id}: {e}")

    await client.disconnect()
    print("اكتملت المهمة.")

if __name__ == '__main__':
    asyncio.run(main())
