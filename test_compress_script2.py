import fitz
from PIL import Image
import os
import io

pdf_path = 'test_compress2.pdf'

doc = fitz.open()
page = doc.new_page()

# create a small dummy image
img = Image.new('RGB', (100, 100), color='blue')
img.save('dummy_small.jpg', quality=95)
page.insert_image(page.rect, filename='dummy_small.jpg')
doc.save(pdf_path)
doc.close()

original_size = os.path.getsize(pdf_path)
print(f'Original size: {original_size}')

doc = fitz.open(pdf_path)
max_dim = 1200
jpeg_quality = 50

for page in doc:
    for img in page.get_images(full=True):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image['image']
        
        pil_img = Image.open(io.BytesIO(image_bytes))
        
        if pil_img.width > max_dim or pil_img.height > max_dim:
            pil_img.thumbnail((max_dim, max_dim), Image.LANCZOS)
            
        if pil_img.mode in ('RGBA', 'P', 'LA'):
            pil_img = pil_img.convert('RGB')
            
        buf = io.BytesIO()
        pil_img.save(buf, format='JPEG', quality=jpeg_quality, optimize=True)
        new_image_bytes = buf.getvalue()
        
        if len(new_image_bytes) < len(image_bytes):
            page.replace_image(xref, stream=new_image_bytes)

doc.save('compressed_test2.pdf', garbage=4, deflate=True, clean=True)
doc.close()

print(f'Compressed size: {os.path.getsize("compressed_test2.pdf")}')
