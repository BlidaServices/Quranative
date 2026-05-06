import os
import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import DocumentAttributeVideo

# جلب البيانات من متغيرات البيئة
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')

# دالة لمراقبة تقدم التحميل (للفهم)
def progress_callback(current, total):
    percent = (current / total) * 100
    sys.stdout.write(f"\rجاري التحميل: {percent:.2f}% ({current}/{total} bytes)")
    sys.stdout.flush()

async def main():
    print("--- بدء تشغيل السكريبت ---")
    
    if not SESSION_STRING:
        print("خطأ: SESSION_STRING غير موجود في Secrets!")
        return

    save_path = 'videos'
    id_file = 'last_video_id.txt'
    source_channel = 'QuranGB'
    
    if not os.path.exists(save_path):
        print(f"إنشاء مجلد جديد: {save_path}")
        os.makedirs(save_path)

    # تحديد الترقيم
    existing_files = [f for f in os.listdir(save_path) if f.split('.')[0].isdigit()]
    counter = max([int(f.split('.')[0]) for f in existing_files]) + 1 if existing_files else 1
    print(f"الترقيم سيبدأ من الرقم: {counter}")

    # قراءة آخر ID
    last_processed_id = 0
    if os.path.exists(id_file):
        with open(id_file, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                last_processed_id = int(content)
    print(f"آخر رسالة معالجة كانت تحمل ID: {last_processed_id}")

    # إعداد العميل
    client = TelegramClient(StringSession(SESSION_STRING.strip()), int(API_ID), API_HASH)
    
    print("محاولة الاتصال بتلجرام...")
    await client.start()
    print("تم الاتصال بنجاح!")

    print(f"جاري فحص الرسائل في قناة: {source_channel}...")
    
    async for message in client.iter_messages(source_channel, reverse=True, min_id=last_processed_id):
        is_video = False
        if message.video:
            is_video = True
        elif message.document and any(isinstance(a, DocumentAttributeVideo) for a in message.document.attributes):
            is_video = True
        
        if is_video:
            ext = '.mp4'
            if message.document and message.document.attributes:
                for attr in message.document.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name:
                        ext = os.path.splitext(attr.file_name)[1] or '.mp4'

            filename = f"{counter}{ext}"
            full_path = os.path.join(save_path, filename)
            
            print(f"\n[+] تم العثور على فيديو (رسالة {message.id})")
            print(f"حجم الملف المتوقع: {message.file.size} bytes")
            
            try:
                # التحميل مع عرض التقدم
                await client.download_media(message, file=full_path, progress_callback=progress_callback)
                print(f"\nتم حفظ الفيديو بنجاح باسم: {filename}")
                
                with open(id_file, 'w') as f:
                    f.write(str(message.id))
                
                counter += 1
                await asyncio.sleep(2) # راحة بسيطة للسيرفر
            except Exception as e:
                print(f"\nخطأ أثناء التحميل: {e}")
                continue

    await client.disconnect()
    print("\n--- انتهت المهمة بنجاح وتم قطع الاتصال ---")

if __name__ == '__main__':
    asyncio.run(main())
