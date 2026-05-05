import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo

API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')

async def main():
    if not SESSION_STRING:
        print("خطأ: SESSION_STRING غير موجود!")
        return

    # تم تغيير المصدر ليكون قناتك الخاصة
    source_channel = -1003999226216
    target_hashtags = ['#نبات', '#طبيعة']
    save_path = 'pictures'
    id_file = 'last_id.txt'
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # تحديد الترقيم بناءً على الملفات الموجودة في المجلد
    existing_files = [f for f in os.listdir(save_path) if f.split('.')[0].isdigit()]
    counter = max([int(f.split('.')[0]) for f in existing_files]) + 1 if existing_files else 1

    # قراءة آخر ID تم التوقف عنده
    last_processed_id = 0
    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                last_processed_id = int(content)

    client = TelegramClient(StringSession(SESSION_STRING.strip()), int(API_ID), API_HASH)
    
    try:
        await client.start()
    except Exception as e:
        print(f"فشل الاتصال: {e}")
        return

    print(f"بدء السحب من قناتك الخاصة. الترقيم يبدأ من: {counter}")

    # الجلب من الأقدم للأحدث من داخل قناتك
    async for message in client.iter_messages(source_channel, reverse=True, min_id=last_processed_id, limit=None):
        
        text = message.text or ""
        has_tag = any(tag in text for tag in target_hashtags)
        
        if has_tag:
            is_video = False
            if message.video:
                is_video = True
            elif message.document:
                if any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
                    is_video = True
                if message.document.mime_type and message.document.mime_type.startswith('video/'):
                    is_video = True
            
            if (message.photo or message.document) and not is_video:
                ext = '.jpg'
                if message.document and message.document.mime_type and 'png' in message.document.mime_type:
                    ext = '.png'
                
                filename = f"{counter}{ext}"
                full_path = os.path.join(save_path, filename)
                
                try:
                    print(f"جاري تحميل الصورة {filename} من رسالة رقم {message.id}...")
                    await client.download_media(message, file=full_path)
                    
                    with open(id_file, 'w') as f:
                        f.write(str(message.id))
                    
                    counter += 1
                    await asyncio.sleep(0.5) 
                except Exception as e:
                    print(f"خطأ: {e}")
                    break

    print("اكتملت المزامنة من قناتك الخاصة.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
