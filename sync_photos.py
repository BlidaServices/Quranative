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

    # معرف قناتك الخاصة
    source_channel = -1003999226216
    save_path = 'pictures'
    id_file = 'last_id.txt'
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # تحديد الترقيم بناءً على الملفات الموجودة
    existing_files = [f for f in os.listdir(save_path) if f.split('.')[0].isdigit()]
    counter = max([int(f.split('.')[0]) for f in existing_files]) + 1 if existing_files else 1

    # قراءة آخر ID معالج
    last_processed_id = 0
    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                last_processed_id = int(content)

    client = TelegramClient(StringSession(SESSION_STRING.strip()), int(API_ID), API_HASH)
    await client.start()

    print(f"بدء سحب كافة الصور والمجموعات. الترقيم يبدأ من: {counter}")

    # جلب كافة الرسائل التي تحتوي على ميديا من الأقدم للأحدث
    async for message in client.iter_messages(source_channel, reverse=True, min_id=last_processed_id, limit=None):
        
        # التحقق من وجود ميديا (صورة أو ملف)
        if message.photo or message.document:
            # فحص صارم لاستبعاد الفيديوهات
            is_video = False
            if message.video:
                is_video = True
            elif message.document:
                if any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
                    is_video = True
                if message.document.mime_type and message.document.mime_type.startswith('video/'):
                    is_video = True
            
            # إذا كانت ميديا وليست فيديو، يتم تحميلها
            if not is_video:
                # محاولة جلب الامتداد الأصلي أو استخدام jpg كافتراضي
                ext = '.jpg'
                if message.document and message.document.mime_type:
                    if 'png' in message.document.mime_type:
                        ext = '.png'
                    elif 'webp' in message.document.mime_type:
                        ext = '.webp'

                filename = f"{counter}{ext}"
                full_path = os.path.join(save_path, filename)
                
                try:
                    print(f"جاري تحميل رسالة رقم {message.id} إلى {filename}...")
                    await client.download_media(message, file=full_path)
                    
                    # حفظ الـ ID لضمان الاستمرارية
                    with open(id_file, 'w') as f:
                        f.write(str(message.id))
                    
                    counter += 1
                    # تأخير بسيط جداً لتجنب ضغط الطلبات
                    await asyncio.sleep(0.2)
                except Exception as e:
                    print(f"خطأ في تحميل الرسالة {message.id}: {e}")
                    # في حال حدوث خطأ FloodWait أو غيره يفضل التوقف وحفظ الحالة
                    break

    await client.disconnect()
    print(f"انتهت العملية. تم الوصول للرقم: {counter - 1}")

if __name__ == '__main__':
    asyncio.run(main())
