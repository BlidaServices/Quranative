import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo

# جلب البيانات من متغيرات البيئة التي يمررها ملف الـ YML
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')

async def main():
    if not SESSION_STRING:
        print("خطأ: SESSION_STRING غير موجود!")
        return

    source_channel = 'QuranGB'
    save_path = 'videos'
    id_file = 'last_video_id.txt'
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    existing_files = [f for f in os.listdir(save_path) if f.split('.')[0].isdigit()]
    counter = max([int(f.split('.')[0]) for f in existing_files]) + 1 if existing_files else 1

    last_processed_id = 0
    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                last_processed_id = int(content)

    client = TelegramClient(StringSession(SESSION_STRING.strip()), int(API_ID), API_HASH)
    await client.start()

    print(f"بدء سحب الفيديوهات. الترقيم يبدأ من: {counter}")

    async for message in client.iter_messages(source_channel, reverse=True, min_id=last_processed_id):
        
        is_video = False
        if message.video:
            is_video = True
        elif message.document:
            if any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
                is_video = True
            elif message.document.mime_type and message.document.mime_type.startswith('video/'):
                is_video = True
        
        if is_video:
            ext = '.mp4'
            if message.document and message.document.attributes:
                for attr in message.document.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name:
                        ext = os.path.splitext(attr.file_name)[1] or '.mp4'

            filename = f"{counter}{ext}"
            full_path = os.path.join(save_path, filename)
            
            try:
                print(f"جاري تحميل فيديو رقم {message.id}...")
                await client.download_media(message, file=full_path)
                
                with open(id_file, 'w') as f:
                    f.write(str(message.id))
                
                counter += 1
                await asyncio.sleep(1) 
            except Exception as e:
                print(f"خطأ في التحميل: {e}")
                break

    await client.disconnect()
    print("انتهت العملية.")

if __name__ == '__main__':
    asyncio.run(main())
