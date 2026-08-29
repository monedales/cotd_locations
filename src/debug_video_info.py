import yt_dlp

url = "https://www.youtube.com/watch?v=AnpeG8nb0Ek"

with yt_dlp.YoutubeDL() as ydl:
    info = ydl.extract_info(url, download=False)

print("--- Todas as chaves disponíveis ---")
print(sorted(info.keys()))

print("\n--- Campos que parecem relevantes ---")
print("title:", info.get("title"))
print("upload_date:", info.get("upload_date"))
print("id:", info.get("id"))
