from datetime import date, datetime, timedelta
import math,requests,os,random,re,json
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d") #今天的日期

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')
user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')
name = os.getenv('NAME')
city = os.getenv('CITY')
aim_date = os.getenv('AIM_DATE')
start_date = os.getenv('START_DATE')


# 每日一句
# def get_english():
#     url = "http://open.iciba.com/dsapi/"
#     r = requests.get(url, timeout=100)
#     note = r.json()['content'] + "\n" + r.json()['note']
#     return note

# 获取天气
def get_weather():
    #url = os.getenv('URL')
    res = requests.get(url, timeout=100).json()
    ls = res['hourly']
    # flag = ls.find('雨')
    # print(type(ls))
    # print(type(ls[0]))
    high = ls[0]["temp"]
    high_time = ls[0]["fxTime"][11:16]
    low = ls[0]["temp"]
    # 记录下雨标记
    weather = ls[0]["text"]
    wf_time = ls[0]["fxTime"][11:16]
    if weather.find("雨")<0:
        wf_flag = False
    else:
        wf_flag = True

    for i in ls:
        if i["temp"] > high:
            high = i["temp"]
            # high_time = i["fxTime"][11:16]
        if i["temp"] < low:
            low = i["temp"]
        if weather.find("雨")<0 and i["text"].find("雨")>=0:
            weather = i["text"]
            wf_time = i["fxTime"][11:16]
            wf_flag = True
    if(wf_flag):
        return (u"降雨警报！%s的时候会下%s."%(wf_time,weather))
    else:
        return (u"%s天(%s ~ %s°)。"%(weather,high,low))

# 获取当前日期为星期几
# def get_week_day():
#   week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期天"]
#   week_day = week_list[datetime.date(today).weekday()]
#   return week_day

# 推送天数
def get_memorial_days_count():
  delta = today - datetime.strptime(start_date, "%Y-%m-%d")
  return delta.days

# 生日倒计时
def get_counter_left(aim_date):
  if re.match(r'^\d{1,2}\-\d{1,2}$', aim_date):
    next = datetime.strptime(str(date.today().year) + "-" + aim_date, "%Y-%m-%d")
  elif re.match(r'^\d{2,4}\-\d{1,2}\-\d{1,2}$', aim_date):
    next = datetime.strptime(aim_date, "%Y-%m-%d")
    next = next.replace(nowtime.year)
  else: return '日期错乱掉了..'
  if next < nowtime:
    next = next.replace(year=next.year + 1)
  return name +'生日还有 ' + str((next - today).days) + ' 天。'

# 彩虹
def get_words():
  # OpenRefactory Warning: The 'requests.get' method does not use any 'timeout' threshold which may cause program to hang indefinitely.
  words = requests.get("https://api.shadiao.pro/chp", timeout=100)
  if words.status_code != 200:
    return get_words()
  return words.json()['data']['text']

def format_temperature(temperature):
  return math.floor(temperature)

# 随机颜色
def get_random_color():
  return "#%06x" % random.randint(0, 0xFFFFFF)

#aimtime = 
andtime = '。在一起'+ str(get_memorial_days_count()) + '天，' + get_counter_left(aim_date) 

data = {
  "date": {
    "value": '', # today.strftime('%Y年%m月%d日'),
    #"color": get_random_color()
  },
  "week_day": {
    "value": '', # get_week_day(),
    #"color": get_random_color()
  },
  "weather": {
    "value": get_weather(),
    #"color": get_random_color()
  },
  "note": {
    "value": '', # get_english(),
    #"color": get_random_color()
  },
  "love_days": {
    "value": andtime,
    #"color": get_random_color()
  },
  "words": {
    "value": get_words(),
    #"color": get_random_color()
  },
}

if __name__ == '__main__':
  try:
    client = WeChatClient(app_id, app_secret)
  except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

  wm = WeChatMessage(client)
  try:
    for user_id in user_ids:
      print('正在发送给 %s, 数据如下：%s' % (user_id, data))
      res = wm.send_template(user_id, template_id, data)
  except WeChatClientException as e:
    print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
    exit(502)
