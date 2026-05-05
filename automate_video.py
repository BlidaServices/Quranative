import os
import random
import subprocess
import requests
import json
import asyncio
import google.generativeai as genai

# --- الإعدادات الأساسية ---
API_KEY = os.environ.get("GEMINI_API_KEY")
PICTURES_DIR = "pictures"
OUTPUT_DIR = "shorts"
TEMP_DIR = "temp_work"

# إعداد نموذج Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_gemini_choice():
    """طلب اختيار سورة وآيات وقارئ من Gemini"""
    prompt = """
    Choose a beautiful and touching Quranic passage for a short social media video (9:16).
    The passage should be complete in meaning, emotional, and between 3 to 6 verses.
    Choose a reader randomly from this list: 
    [Yasser_Ad-Dussary_128kbps, Maher_AlMuaiqly_64kbps, Abdurrahmaan_As-Sudais_192kbps, Menshawi_16kbps]
    
    Return ONLY a JSON object: 
    {"surah": number, "start": number, "end": number, "reader": "string"}
    """
    try:
        response = model.generate_content(prompt)
        # تنظيف الرد من أي زوائد نصية
        clean_json = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_json)
    except Exception as e:
        print(f"⚠️ Gemini Error: {e}. Using fallback choice.")
        return {"surah": 67, "start": 1, "end": 5, "reader": "Yasser_Ad-Dussary_128kbps"}

def run_command(cmd):
    """تنفيذ أوامر النظام"""
    subprocess.run(cmd, shell=True, check=True)

async def generate_video():
    # 1. اختيار المحتوى
    choice = get_gemini_choice()
    surah, start, end, reader = choice['surah'], choice['start'], choice['end'], choice['reader']
    
    print(f"🎬 AI Selection: Surah {surah} | Verses {start}-{end} | Reader: {reader}")

    # 2. تجهيز المجلدات
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if os.path.exists(TEMP_DIR):
        run_command(f"rm -rf {TEMP_DIR}")
    os.makedirs(TEMP_DIR)

    # 3. اختيار صورة خلفية عشوائية من المجلد المحلي
    images = [f for f in os.listdir(PICTURES_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not images:
        raise Exception(f"❌ No images found in {PICTURES_DIR}")
    
    selected_bg = os.path.join(PICTURES_DIR, random.choice(images))
    dimmed_bg = os.path.join(TEMP_DIR, "dimmed_bg.jpg")
    
    # معالجة الخلفية: تغيير الحجم ليكون عمودياً 1080x1920 وتعتيمها بنسبة 80%
    print(f"🖼️ Processing background: {selected_bg}")
    run_command(f"convert '{selected_bg}' -resize 1080x1920^ -gravity center -extent 1080x1920 -brightness-contrast -80x0 '{dimmed_bg}'")

    audio_list_path = os.path.join(TEMP_DIR, "audio_list.txt")
    video_concat_path = os.path.join(TEMP_DIR, "video_list.txt")

    # 4. معالجة الآيات (تحميل الصوت والنصوص وتوليد الإطارات)
    with open(audio_list_path, "w") as af, open(video_concat_path, "w") as vf:
        for v in range(start, end + 1):
            s_str, v_str = str(surah).zfill(3), str(v).zfill(3)
            
            # روابط المصادر (الصوت وصورة الآية)
            audio_url = f"https://www.everyayah.com/data/{reader}/{s_str}{v_str}.mp3"
            text_url = f"https://legacy.quran.com/images/ayat_retina/{surah}_{v}.png"
            
            a_file = os.path.join(TEMP_DIR, f"{v}.mp3")
            t_file = os.path.join(TEMP_DIR, f"{v}.png")
            frame_file = os.path.join(TEMP_DIR, f"{v}.jpg")

            print(f"📥 Fetching Verse {v}...")
            with open(a_file, 'wb') as f: f.write(requests.get(audio_url).content)
            with open(t_file, 'wb') as f: f.write(requests.get(text_url).content)

            # دمج صورة الآية (تحويلها للأبيض) فوق الخلفية المعتمة
            run_command(f"convert '{dimmed_bg}' \( '{t_file}' -trim +repage -resize 950x -fill white -colorize 100% \) -gravity center -composite '{frame_file}'")

            # حساب مدة الصوت بدقة باستخدام ffprobe
            duration = subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 '{a_file}'", shell=True).decode().strip()
            
            af.write(f"file '{v}.mp3'\n")
            vf.write(f"file '{v}.jpg'\nduration {duration}\n")

        # إضافة السطر الأخير لضمان عدم توقف الفيديو قبل انتهاء الصوت
        vf.write(f"file '{end}.jpg'\n")

    # 5. الدمج النهائي للفيديو والصوت
    merged_audio = os.path.join(TEMP_DIR, "final_audio.mp3")
    output_filename = f"quran_s{surah}_{start}_{end}_{random.randint(100,999)}.mp4"
    final_video_path = os.path.join(OUTPUT_DIR, output_filename)

    print("🎥 Merging assets into final video...")
    # دمج ملفات الصوت
    run_command(f"ffmpeg -y -f concat -safe 0 -i {audio_list_path} -c copy {merged_audio}")
    
    # دمج الصور مع الصوت لإنتاج MP4
    run_command(f"ffmpeg -y -f concat -safe 0 -i {video_concat_path} -i {merged_audio} "
                f"-c:v libx264 -pix_fmt yuv420p -r 25 -c:a aac -b:a 192k -shortest '{final_video_path}'")

    print(f"✅ Success! Video saved: {final_video_path}")
    
    # تنظيف الملفات المؤقتة
    run_command(f"rm -rf {TEMP_DIR}")

if __name__ == "__main__":
    asyncio.run(generate_video())
