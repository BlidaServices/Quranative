import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo

# جلب البيانات من متغيرات البيئة
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')

async def main():
    if not SESSION_STRING:
        print("خطأ: SESSION_STRING غير موجود في Secrets!")
        return

    # إعداد المسارات والقناة
    source_channel = 'QuranGB'
    save_path = 'videos'
    id_file = 'last_video_id.txt'
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # حساب الترقيم بناءً على الملفات الموجودة في مجلد videos
    existing_files = [f for f in os.listdir(save_path) if f.split('.')[0].isdigit()]
    counter = max([int(f.split('.')[0]) for f in existing_files]) + 1 if existing_files else 1

    # قراءة آخر ID معالج من الملف
    last_processed_id = 0
    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                last_processed_id = int(content)

    # إنشاء العميل مع إعدادات إعادة الاتصال التلقائي
    client = TelegramClient(
        StringSession(SESSION_STRING.strip()), 
        int(API_ID), 
        API_HASH,
        connection_retries=10,
        retry_delay=5
    )
    
    await client.start()
    print(f"بدء المعالجة. الترقيم يبدأ من: {counter}")

    try:
        # جلب الرسائل من الأقدم للأحدث (reverse=True)
        async for message in client.iter_messages(source_channel, reverse=True, min_id=last_processed_id):
            
            # فحص هل الرسالة فيديو
            is_video = False
            if message.video:
                is_video = True
            elif message.document:
                if any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
                    is_video = True
                elif message.document.mime_type and message.document.mime_type.startswith('video/'):
                    is_video = True
            
            if is_video:
                # استخراج امتداد الملف
                ext = '.mp4'
                if message.document and message.document.attributes:
                    for attr in message.document.attributes:
                        if hasattr(attr, 'file_name') and attr.file_name:
                            ext = os.path.splitext(attr.file_name)[1] or '.mp4'

                filename = f"{counter}{ext}"
                full_path = os.path.join(save_path, filename)
                
                try:
                    print(f"تحميل فيديو رسالة {message.id} باسم {filename}...")
                    await client.download_media(message, file=full_path)
                    
                    # تحديث ملف الـ ID بعد كل عملية نجاح
                    with open(id_file, 'w') as f:
                        f.write(str(message.id))
                    
                    counter += 1
                    # تأخير بسيط لضمان استقرار الاتصال
                    await asyncio.sleep(1) 
                except Exception as e:
                    print(f"فشل تحميل الفيديو {message.id}: {e}")
                    # إذا حدث خطأ كبير، نحفظ الحالة ونخرج
                    break
    finally:
        await client.disconnect()
        print("انتهى السكريبت.")

if __name__ == '__main__':
    asyncio.run(main())
