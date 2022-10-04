import colorsys
import color
import requests
# requests.get("https://tse3.explicit.bing.net/th?id=OIP-C.62RAWZHA5iHdqwZjLTHm-gHaFw&pid=Api")
colors, _ = color.str2color("chemical", "1751905ba35f4388ba6979749243cbcc",num=5)
print(colors)

# print(color.rgb2hsv((137,71,69)))