from PIL import Image,ImageDraw,ImageFont,ImageFilter
import random
from io import BytesIO
from django.http import HttpResponse

def check_code(width=120,height=30,char_length=5,font_file=r"../ARLRDBD.TTF",font_size=28):
    code = []   # 用来存生成的验证码字符串
    img = Image.new(mode='RGB',size=(width,height),color=(255,255,255))
    draw = ImageDraw.Draw(img,mode='RGB')
    def rndChar():
        # 随机生成大写字母 A-Z
        return chr(random.randint(65,90))
        # # 数字
        # return str(random.randint(0,9))
    def rndColor():
        # 生成随机颜色
        return (random.randint(0,255),random.randint(10,255),random.randint(64,255))
    font = ImageFont.truetype(font_file,font_size)
    # 写文字
    for i in range(char_length):
        char = rndChar()
        code.append(char)
        y = random.randint(0, height-font_size)
        # (i * 22, y)文字坐标
        draw.text((i * 22, y), char, font=font, fill=rndColor())
    # 写干扰点
    for i in range(40):
        draw.point([random.randint(0,width),random.randint(0,height)],fill=rndColor())
    # 写干扰圆圈
    for i in range(40):
        draw.point([random.randint(0,width),random.randint(0,height)],fill=rndColor())
        x = random.randint(0,width)
        y = random.randint(0,height)
        draw.arc((x,y,x+4,y+4),0,90,fill=rndColor())    # 就画一小段弧线

    # 画干扰线
    for i in range(5):
        x1 = random.randint(0,width)
        y1 = random.randint(0,height)
        x2 = random.randint(0,width)
        y2 = random.randint(0,height)

        draw.line((x1,y1,x2,y2),fill=rndColor())
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img, ''.join(code)


def image_code(request):
    #生成验证码图片并返回给前端，验证码文本存入 session
    img, code = check_code()
    request.session['check_code'] = code
    request.session.set_expiry(60*5)
    buf = BytesIO()
    img.save(buf, 'png')
    return HttpResponse(buf.getvalue(), content_type='image/png')