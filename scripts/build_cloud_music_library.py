import os
import json
import csv

# 路径定义
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
PROJECTS_ROOT = os.path.join(LOCAL_APP_DATA, r"JianyingPro\User Data\Projects\com.lveditor.draft")

# Skill 根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_CSV = os.path.join(SKILL_ROOT, "data", "cloud_music_library.csv")
SFX_CSV = os.path.join(SKILL_ROOT, "data", "cloud_sound_effects.csv")

def load_existing_csv(path, id_key):
    library = {}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8', newline='') as f:
                lines = [l for l in f.readlines() if not l.startswith("#")]
                if lines:
                    reader = csv.DictReader(lines)
                    for row in reader:
                        m_id = row[id_key]
                        cats = set(row['categories'].split('|')) if row['categories'] else set()
                        library[m_id] = {
                            id_key: m_id,
                            "title": row['title'],
                            "duration_s": float(row['duration_s']) if row['duration_s'] else 0.0,
                            "categories": cats
                        }
        except Exception as e:
            print(f"⚠️ Reading existing CSV {path} failed: {e}")
    return library

def save_to_csv(path, library, id_key, title_prefix):
    sorted_ids = sorted(library.keys(), key=lambda x: library[x]['title'])
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(f"# JianYing Cloud {title_prefix} Library\n")
        f.write(f"# AI Guidance: Use '{id_key}' to reference. If not in cache, ask user to 'Sync Music' or use cloud API.\n")
        f.write("# Schema: identifier,title,duration_s,categories\n")
        
        writer = csv.DictWriter(f, fieldnames=[id_key, "title", "duration_s", "categories"])
        writer.writeheader()
        for m_id in sorted_ids:
            info = library[m_id]
            writer.writerow({
                id_key: m_id,
                "title": info["title"],
                "duration_s": info["duration_s"],
                "categories": "|".join(sorted(list(info["categories"])))
            })

def build_libraries():
    print(f"🔍 Scanning Jianying projects for cloud assets...")
    
    music_lib = load_existing_csv(MUSIC_CSV, "music_id")
    sfx_lib = load_existing_csv(SFX_CSV, "effect_id")

    if not os.path.exists(PROJECTS_ROOT):
        print("❌ Projects root not found.")
        return

    for project_name in os.listdir(PROJECTS_ROOT):
        project_path = os.path.join(PROJECTS_ROOT, project_name)
        if not os.path.isdir(project_path): continue
            
        content_path = os.path.join(project_path, "draft_content.json")
        if not os.path.exists(content_path): continue
            
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                audios = data.get('materials', {}).get('audios', [])
                for audio in audios:
                    m_type = audio.get('type')
                    title = audio.get('name', 'Unknown')
                    duration_ms = audio.get('duration', 0)
                    category = audio.get('category_name')
                    
                    if m_type == 'music':
                        m_id = audio.get('music_id') or audio.get('id')
                        if not m_id: continue
                        if m_id not in music_lib:
                            music_lib[m_id] = {"music_id": m_id, "title": title, "duration_s": round(duration_ms / 1000000, 2), "categories": set()}
                        if category: music_lib[m_id]["categories"].add(category)
                        
                    elif m_type == 'sound':
                        # 音效通常使用 effect_id
                        e_id = audio.get('effect_id')
                        if not e_id: continue
                        if e_id not in sfx_lib:
                            sfx_lib[e_id] = {"effect_id": e_id, "title": title, "duration_s": round(duration_ms / 1000000, 2), "categories": set()}
                        if category: sfx_lib[e_id]["categories"].add(category)
        except Exception as e:
            print(f"⚠ Skipping project '{project_name}': {e}")

    save_to_csv(MUSIC_CSV, music_lib, "music_id", "Music")
    save_to_csv(SFX_CSV, sfx_lib, "effect_id", "Sound Effects")

    print(f"✅ Success! Music: {len(music_lib)}, SFX: {len(sfx_lib)}")

if __name__ == "__main__":
    build_libraries()
