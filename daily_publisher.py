import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"🔄 Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"❌ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"🎲 All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Timeless Elegance — Style That Never Goes Out of Fashion",
        "European Style Secrets for Everyday Grace",
        "The Confidence to Wear What You Love",
        "Classic Wardrobe Pieces That Elevate Everything",
        "How to Look Effortlessly Sophisticated",
        "Elegant Outfits for Every Occasion",
        "Living Boldly With Grace and Style",
        "Timeless Beauty — It Starts From Within",
        "The Art of Dressing With Confidence",
        "Everyday Inspiration From European Fashion",
        "Quiet Luxury: Elegance Without the Noise",
        "Style Tips That Stand the Test of Time",
        "How to Build a Timeless Capsule Wardrobe",
        "Grace in Every Step — Fashion and Poise",
        "Your Daily Dose of Elegance and Inspiration",
    ]

    fallback_descriptions = [
        "Elegance isn't loud — it's the way you carry yourself, the pieces you choose, and the confidence you wear every day. Timeless style never chases trends; it creates its own. Whether it's a perfectly tailored blazer or a simple silk scarf, the details make the difference. Save this for your next style moment! ✨ #fashion #elegance #timelessbeauty #style #confidence #elvianeeklund",
        "European fashion teaches us that less is more. Invest in quality, embrace neutrals, and let your personality shine through the details. You don't need a full new wardrobe — just the right pieces worn with intention. Double tap if you love classic style! 🕊️ #europeanstyle #elegance #fashiontips #classicstyle #capsulewardrobe #elvianeeklund",
        "Confidence is the most elegant accessory you can wear. When you believe in yourself, it shows in your posture, your choices, and your smile. Dress for the woman you are becoming, and watch how everything shifts. Drop a 👑 if you're working on your confidence today! #confidence #selflove #fashion #elegance #empowerment #elvianeeklund",
        "Timeless beauty starts from within. Nourish your mind, move your body, and treat yourself with the same grace you show others. Outer style is a reflection of inner peace. This is your reminder to glow from the inside out. Like if this resonated with you! 🌸 #timelessbeauty #selfcare #wellness #elegance #confidence #elvianeeklund",
        "A capsule wardrobe is the secret to effortless style. A few quality pieces in neutral tones can be mixed and matched for endless elegant looks. Quality over quantity, always. Save this as your guide to building a timeless closet! 👗 #capsulewardrobe #fashiontips #elegance #minimalism #styleguide #elvianeeklund",
        "Quiet luxury is about wearing what makes you feel refined without needing to announce it. Soft fabrics, tailored fits, and understated accessories speak volumes. Let your presence do the talking. Share this with a friend who gets it! 💫 #quietluxury #elegance #fashion #sophistication #styleinspo #elvianeeklund",
        "Style is a form of self-expression — your outfit tells your story before you say a word. Whether you prefer classic tailoring or modern minimalism, wear what feels authentically you. There are no fashion rules, only choices. Comment what your style says about you! 🎀 #fashion #selfexpression #personalstyle #elegance #styleinspiration #elvianeeklund",
        "Grace is elegance in motion. Walk with intention, speak with kindness, and carry yourself with the quiet confidence of someone who knows their worth. Elegance is a mindset as much as an aesthetic. Save this for a moment of inspiration. 🕊️ #grace #elegance #confidence #poise #mindset #elvianeeklund",
        "Timeless pieces never disappoint — a crisp white shirt, well-fitted trousers, a classic trench. These are the foundations of an elegant wardrobe that works for any occasion. Invest in staples, and the rest becomes easy. Double tap if you love classic fashion! 🤍 #classicstyle #fashionstaples #elegance #wardrobeessentials #timelessfashion #elvianeeklund",
        "Inspiration is everywhere when you learn to see beauty in the everyday — the way light hits a fabric, the confidence in a stranger's stride, the simplicity of a well-made garment. Let the world inspire your style. Comment what inspired you today! ✨ #dailyinspiration #fashion #beauty #lifestyle #elegance #elvianeeklund",
        "Sophistication is the ability to look put-together without looking like you tried too hard. It's balance, restraint, and knowing when less is more. Cultivate it in your style and your life. Like if you're a fan of effortless chic! 🌹 #sophistication #elegance #effortlesschic #fashiontips #style #elvianeeklund",
        "Every day is an opportunity to show up as your most elegant self. Not for anyone else — for you. Dress well, speak kindly, move with purpose, and let your inner light guide you. This is your gentle reminder. Save this for later. 💛 #elegance #selfcare #confidence #dailyreminder #lifestyle #elvianeeklund",
        "Beauty and fashion are personal journeys. What works for one person may not work for another — and that's the magic of self-expression. Embrace your unique style without comparison. You are the only you there is. Drop a 💖 if you're embracing your uniqueness! #selflove #individuality #fashion #beauty #confidence #elvianeeklund",
        "The European approach to fashion: quality, comfort, and confidence. Choose pieces that make you feel good, not just look good. When you feel comfortable in what you wear, it shows. Double tap if you dress for yourself! 🥂 #europeanstyle #comfortableluxury #fashion #confidence #qualityoverquantity #elvianeeklund",
        "End your day the way you started it — with grace. Reflect on your wins, give yourself credit, and rest knowing you showed up as your best self. Tomorrow is a fresh canvas. Good night, elegant one. 🌙 #elegance #gratitude #selfcare #nightroutine #lifestyle #elvianeeklund",
    ]

    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "elegant and sophisticated — speak like a refined European fashion editor",
        "graceful and poised — inspire quiet confidence and timeless style",
        "warm and encouraging — speak like a close friend sharing style advice",
        "polished and aspirational — motivate viewers to elevate their everyday elegance",
        "calm and refined — emphasise grace, quality and inner beauty",
        "inspiring and empowering — help viewers feel confident in their own skin",
        "classic and timeless — celebrate enduring style over fleeting trends",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"for the social media page 'Elviane Eklund'. "
        f"The page covers elegant European fashion, lifestyle, and confidence. It's a European creator sharing timeless beauty, elegant style, and everyday inspiration - living boldly with grace and confidence. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and personal. "
        f"Include engagement calls-to-action such as: "
        f"Like if this inspired your style! Comment your fashion goal below! Share this with someone who loves timeless elegance! Follow Elviane Eklund for daily fashion and lifestyle inspiration!"
        f"Include relevant hashtags in ALL LOWERCASE such as #fashion #lifestyle #elegance #timelessbeauty #europeanstyle #confidence #style #grace #dailyinspiration #classicstyle #sophistication #selflove #fashioninspo #elvianeeklund. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )
    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("🚀 DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("✅ No new videos found to publish. Exiting.")
        return
        
    print(f"👉 Selected Video: {video_name}")
    print("🧠 Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"📝 Title: {title}")
    print(f"📝 Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"❌ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"❌ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"❌ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"❌ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"⚠️  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"❌ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["fashion", "lifestyle", "elegance", "europeanstyle", "confidence", "timelessbeauty", "style", "grace", "dailyinspiration", "sophistication", "classicstyle", "selflove", "fashioninspo", "elvianeeklund"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"❌ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\n✅ Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   🔄 This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"📦 Moved published video to {dest_path}")
    except Exception as e:
        print(f"❌ Failed to move published video: {e}")
    
    print("🎉 DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
