from PIL import Image, ImageDraw

# 创建一个32x32的图像
img = Image.new('RGBA', (32, 32), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# 画一个简单的图形
draw.ellipse([4, 4, 28, 28], fill='blue')

# 保存为ico文件
img.save('icon.ico') 