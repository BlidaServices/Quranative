import os
import asyncio
import configparser
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo

# الإعدادات من البيئة (عبر GitHub Actions)
API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')

async def main():
    source_channel = 'QuranGB'
    target_hashtags = ['#نبات', '#طبيعة']
    save_path = 'pictures'
    
    # إنشاء المجلد إذا لم يكن موجوداً
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    
    print("بدء فحص تلجرام وتحميل الصور...")
    
    counter = 1
    # reverse=True للبدء من الأقدم للأحدث
    async for message in client.iter_messages(source_channel, reverse=True):
        has_tag = message.text and any(tag in message.text for tag in target_hashtags)
        
        if has_tag:
            # التحقق من أن المرفق صورة أو ملف صورة وليس فيديو
            is_video = False
            if message.video:
                is_video = True
            elif message.document and any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
                is_video = True
            
            if (message.photo or message.document) and not is_video:
                # تحديد الامتداد (افتراضياً jpg للصور)
                ext = '.jpg'
                if message.document and message.document.mime_type == 'image/png':
                    ext = '.png'
                
                filename = f"{counter}{ext}"
                full_path = os.path.join(save_path, filename)
                
                # تحميل الصورة
                await client.download_media(message, file=full_path)
                print(f"تم تحميل: {filename}")
                counter += 1
                
                # تأخير بسيط لتفادي الضغط
                await asyncio.sleep(0.5)

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
