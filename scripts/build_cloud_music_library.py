import os
import json

# 路径定义
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
PROJECTS_ROOT = os.path.join(LOCAL_APP_DATA, r"JianyingPro\User Data\Projects\com.lveditor.draft")

# Skill 根目录
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY_FILE = os.path.join(SKILL_ROOT, "data", "cloud_music_library.json")

def build_pure_library():
    print(f"🔍 Scanning Jianying projects for music metadata...")
    
    # 1. 尝试读取现有库以进行增量更新
    music_library = {}
    if os.path.exists(LIBRARY_FILE):
        try:
            with open(LIBRARY_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                for m_id, info in existing_data.items():
                    # 将 categories 转回 set 方便合并
                    info["categories"] = set(info.get("categories", []))
                    music_library[m_id] = info
        except Exception as e:
            print(f"⚠️ Warning: Could not read existing library: {e}")

    if not os.path.exists(PROJECTS_ROOT):
        print("❌ Projects root not found.")
        return

    # 2. 遍历所有工程文件夹
    for project_name in os.listdir(PROJECTS_ROOT):
        project_path = os.path.join(PROJECTS_ROOT, project_name)
        if not os.path.isdir(project_path):
            continue
            
        content_path = os.path.join(project_path, "draft_content.json")
        if not os.path.exists(content_path):
            continue
            
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # 3. 提取素材库中的音频
                audios = data.get('materials', {}).get('audios', [])
                for audio in audios:
                    m_id = audio.get('music_id') or audio.get('id')
                    if not m_id: continue
                    
                    # 只有类型为 music 的才记录
                    if audio.get('type') != 'music': continue

                    title = audio.get('name', 'Unknown')
                    duration_ms = audio.get('duration', 0)
                    
                    # 提取分类标签
                    category = audio.get('category_name')
                    
                    if m_id not in music_library:
                        music_library[m_id] = {
                            "music_id": m_id,
                            "title": title,
                            "duration_s": round(duration_ms / 1000000, 2),
                            "categories": set()
                        }
                    
                    if category:
                        music_library[m_id]["categories"].add(category)
        except: pass

    # 4. 转换 categories 为 list 以便 JSON 序列化
    final_library = {}
    for m_id, info in music_library.items():
        # 这里需要确保 info 是字典且包含 categories
        info["categories"] = sorted(list(info["categories"]))
        final_library[m_id] = info

    # 5. 写入
    os.makedirs(os.path.dirname(LIBRARY_FILE), exist_ok=True)
    with open(LIBRARY_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_library, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Success! Cloud Music Library updated with {len(final_library)} entries.")
    print(f"📂 Saved to: {LIBRARY_FILE}")

if __name__ == "__main__":
    build_pure_library()
