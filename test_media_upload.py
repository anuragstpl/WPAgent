"""
Test script for WordPress media upload
"""
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from wordpress_publisher import WordPressPublisher

print("""
╔══════════════════════════════════════════════════════════╗
║         WORDPRESS MEDIA UPLOAD TEST                      ║
╚══════════════════════════════════════════════════════════╝
""")

# Initialize publisher
publisher = WordPressPublisher()

# Test image URL from Pexels
test_image_url = "https://images.pexels.com/photos/1181671/pexels-photo-1181671.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"

print("\nTest Details:")
print(f"Image URL: {test_image_url}")
print(f"WordPress Site: {publisher.base_url}")
print("\n" + "="*60)

# Try to upload the image
print("\nAttempting to upload image...")

media_id = publisher.upload_media(
    image_url=test_image_url,
    title="Test Image Upload",
    alt_text="Test image for media upload verification",
    caption="This is a test image uploaded via the news bot"
)

print("\n" + "="*60)

if media_id:
    print(f"\n✅ SUCCESS! Image uploaded successfully!")
    print(f"Media ID: {media_id}")
    print(f"View in WordPress: {publisher.base_url}/wp-admin/upload.php")
    print(f"\nYou can now use this media_id ({media_id}) in your posts!")
else:
    print(f"\n❌ FAILED! Image upload failed.")
    print(f"\nPlease check:")
    print(f"1. Bearer token has media upload permissions")
    print(f"2. WordPress file upload is enabled")
    print(f"3. File size is within limits")
    print(f"4. Check news_bot.log for detailed error messages")

print("\n" + "="*60)
