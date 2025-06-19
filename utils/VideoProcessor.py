import os
import shutil


class VideoProcessor:
    def __init__(self):
        self.temp_dir = "temp_processed"
        os.makedirs(self.temp_dir, exist_ok=True)

    def prepare_for_tiktok(self, video_path):
        output_path = os.path.join(self.temp_dir, f"tiktok_{os.path.basename(video_path)}")
        shutil.copy2(video_path, output_path)
        print(f"TikTok: Video copied to {output_path}")
        return output_path

    def prepare_for_instagram(self, video_path):
        output_path = os.path.join(self.temp_dir, f"instagram_{os.path.basename(video_path)}")
        shutil.copy2(video_path, output_path)
        print(f"Instagram: Video copied to {output_path}")
        return output_path

    def prepare_for_youtube(self, video_path):
        print(f"YouTube: Using original video {video_path}")
        return video_path

    def prepare_for_instagram_story(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension in ['.mp4', '.mov', '.avi']:
            output_path = os.path.join(self.temp_dir, f"instagram_story_{os.path.basename(file_path)}")
        else:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(self.temp_dir, f"instagram_story_{base_name}.jpg")

        shutil.copy2(file_path, output_path)
        print(f"Instagram Story: File copied to {output_path}")
        return output_path

    def cleanup_temp_files(self):
        try:
            for file in os.listdir(self.temp_dir):
                if file.startswith(('tiktok_', 'instagram_', 'instagram_story_')):
                    file_path = os.path.join(self.temp_dir, file)
                    os.remove(file_path)
                    print(f"Cleaned up: {file_path}")
        except Exception as e:
            print(f"Error cleaning up temp files: {e}")