import os
import random
import subprocess
import requests
import json
import asyncio
import google.generativeai as genai

# --- الإعدادات ---
API_KEY = os.environ.get("GEMINI_API_KEY")
PICTURES_DIR = "pictures"
OUTPUT_DIR = "shorts"
TEMP_DIR = "temp_work"

# إعداد Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

def get_gemini_choice():
    prompt = """
    Give me a random touching Quranic passage for a short vertical video (TikTok/Reels).
    Return ONLY a JSON object: 
    {"surah": number, "start": number, "end": number, "reader": "string"}
    Choose a reader from: [Yasser_Ad-Dussary_128kbps, Maher_AlMuaiqly_64kbps, Abdurrahmaan_As-Sudais_192kbps, Menshawi_16kbps]
    The passage should be complete in meaning, emotional, and fits within 30-90 seconds.
    """
    try:
        response = model.generate_content(prompt)
        # تنظيف النص المستلم من أي علامات Markdown
        clean_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_text)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return {"surah": 1, "start": 1, "end": 7, "reader": "Yasser_Ad-Dussary_128kbps"}

def run_command(cmd):
    """وظيفة لتشغيل أوامر النظام (FFmpeg/ImageMagick)"""
    subprocess.run(cmd, shell=True, check=True)

async def create_video():
    # 1. الحصول على الاختيار من Gemini
    choice = get_gemini_choice()
    surah = choice['surah']
    start = choice['start']
    end = choice['end']
    reader = choice['reader']
    
    print(f"🎬 AI Choice: Surah {surah}, Verses {start}-{end}, Reader: {reader}")

    # 2. تجهيز المجلدات
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    # 3. اختيار صورة عشوائية وتعتيمها
    images = [f for f in os.listdir(PICTURES_DIR) if f.endswith(('.jpg', '.png'))]
    if not images:
        raise Exception("No images found in pictures directory!")
    
    bg_image = os.path.join(PICTURES_DIR, random.choice(images))
    dimmed_bg = os.path.join(TEMP_DIR, "dimmed.jpg")
    run_command(f"convert '{bg_image}' -brightness-contrast -80x0 '{dimmed_bg}'")

    audio_list = []
    concat_text = []

    # 4. معالجة كل آية
    for v in range(start, end + 1):
        s_str = str(surah).zfill(3)
        v_str = str(v).zfill(3)
        
        audio_url = f"https://www.everyayah.com/data/{reader}/{s_str}{v_str}.mp3"
        text_url = f"https://legacy.quran.com/images/ayat_retina/{surah}_{v}.png"
        
        audio_path = os.path.join(TEMP_DIR, f"{v}.mp3")
        text_path = os.path.join(TEMP_DIR, f"{v}_text.png")
        frame_path = os.path.join(TEMP_DIR, f"{v}_frame.jpg")

        # تحميل الملفات
        with open(audio_path, 'wb') as f:
            f.write(requests.get(audio_url).content)
        with open(text_path, 'wb') as f:
            f.write(requests.get(text_url).content)

        # دمج النص مع الخلفية باستخدام ImageMagick
        run_command(f"convert '{dimmed_bg}' \( '{text_path}' -trim +repage -resize 900x -fill white -colorize 100% \) -gravity center -composite '{frame_path}'")

        # حساب مدة الصوت
        duration_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{audio_path}'"
        duration = subprocess.check_output(duration_cmd, shell=True).decode().strip()
        
        concat_text.append(f"file '{v}_frame.jpg'\nduration {duration}")
        audio_list.append(f"file '{v}.mp3'")

    # كتابة ملفات التجميع لـ FFmpeg
    with open(os.path.join(TEMP_DIR, "concat.txt"), "w") as f:
        f.write("\n".join(concat_text))
        # تكرار السطر الأخير لتفادي مشكلة الفيديو القصير في FFmpeg
        f.write(f"\nfile '{end}_frame.jpg'")

    with open(os.path.join(TEMP_DIR, "audio.txt"), "w") as f:
        f.write("\n".join(audio_list))

    # 5. الدمج النهائي
    merged_audio = os.path.join(TEMP_DIR, "final.mp3")
    final_video = os.path.join(OUTPUT_DIR, f"quran_s{surah}_{start}_{end}.mp4")

    # دمج الأصوات أولاً
    run_command(f"ffmpeg -y -f concat -safe 0 -i {os.path.join(TEMP_DIR, 'audio.txt')} -c copy '{merged_audio}'")
    
    # إنتاج الفيديو
    run_command(f"ffmpeg -y -f concat -safe 0 -i {os.path.join(TEMP_DIR, 'concat.txt')} -i '{merged_audio}' -c:v libx264 -pix_fmt yuv420p -r 25 -c:a aac -b:a 192k -shortest '{final_video}'")

    print(f"✅ Video created: {final_video}")

if __name__ == "__main__":
    asyncio.run(create_video())
