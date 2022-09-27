from datetime import date, datetime, timedelta
import math
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage
import requests
import os
import random
import re,json
header = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36'
}

def get_english():
    """获取金山词霸每日一句，英文和翻译"""
    url = "http://open.iciba.com/dsapi/"
    r = requests.get(url,headers = header)
    note = r.json()['content'] + "  " + r.json()['note']
    return note

def get_weather():
    """获取天气预报"""
    url = "https://devapi.qweather.com/v7/weather/now?location=124.37,43.17&key=5b55e853fdc94f27839fa17527d13874"
    res = requests.get(url)
    res = res.json()['now']
    text =  "当前温度：" + res['temp'] + "℃，体感温度：" + res['feelsLike'] + "℃，" + res['windDir'] + res['windScale'] + "级。"
    if int(res['feelsLike']) < 15:
        a = "请崽崽注意防寒，外出及时添衣保暖，以免感冒。"
    elif int(res['feelsLike']) < 25:
        if int(res['windScale']) < 5:
            a = "今天天气不错喔，崽崽可以酌情外出散步。"
        else:
            a = "风太大了，请崽崽减少出门。"
    else:
        a = "高温徘徊暑气难消，请崽崽注意防暑。"
    return text + a

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d") #今天的日期

start_date = '2022-09-09'
city = '新乡' 
birthday = '01-22'

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')
user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')


if app_id is None or app_secret is None:
  print('请设置 APP_ID 和 APP_SECRET')
  exit(422)

if not user_ids:
  print('请设置 USER_ID，若存在多个 ID 用回车分开')
  exit(422)

if template_id is None:
  print('请设置 TEMPLATE_ID')
  exit(422)


# 获取当前日期为星期几
def get_week_day():
  week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
  week_day = week_list[datetime.date(today).weekday()]
  return week_day

# 纪念日正数
def get_memorial_days_count():
  if start_date is None:
    print('没有设置 START_DATE')
    return 0
  delta = today - datetime.strptime(start_date, "%Y-%m-%d")
  return delta.days

# 各种倒计时
def get_counter_left(aim_date):
  if aim_date is None:
    return 0

  # 为了经常填错日期的同学们
  if re.match(r'^\d{1,2}\-\d{1,2}$', aim_date):
    next = datetime.strptime(str(date.today().year) + "-" + aim_date, "%Y-%m-%d")
  elif re.match(r'^\d{2,4}\-\d{1,2}\-\d{1,2}$', aim_date):
    next = datetime.strptime(aim_date, "%Y-%m-%d")
    next = next.replace(nowtime.year)
  else:
    print('日期格式不符合要求')
    
  if next < nowtime:
    next = next.replace(year=next.year + 1)
  return '距离春节还有 ' + str((next - today).days) + ' 天。'

# 彩虹屁 接口不稳定，所以失败的话会重新调用，直到成功
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

# 返回一个数组，循环产生变量
def split_birthday():
  if birthday is None:
    return None
  return birthday.split('\n')

#aimtime = 
andtime = '今天是推送的第 '+ str(get_memorial_days_count()) + ' 天，'

data = {
  "city": {
    "value": city,
    "color": get_random_color()
  },
  "date": {
    "value": today.strftime('%Y年%m月%d日'),
    "color": get_random_color()
  },
  "week_day": {
    "value": get_week_day(),
    "color": get_random_color()
  },
  "weather": {
    "value": get_weather(),
    "color": get_random_color()
  },
  "note": {
    "value": get_english(),
    "color": get_random_color()
  },
  "love_days": {
    "value": andtime,
    "color": get_random_color()
  },
  "words": {
    "value": get_words(),
    "color": get_random_color()
  },
}

for index, aim_date in enumerate(split_birthday()):
  key_name = "birthday_left"
  if index != 0:
    key_name = key_name + "_%d" % index
  data[key_name] = {
    "value": get_counter_left(aim_date),
    "color": get_random_color()
  }

if __name__ == '__main__':
  try:
    client = WeChatClient(app_id, app_secret)
  except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

  wm = WeChatMessage(client)
  count = 0
  try:
    for user_id in user_ids:
      print('正在发送给 %s, 数据如下：%s' % (user_id, data))
      res = wm.send_template(user_id, template_id, data)
      count+=1
  except WeChatClientException as e:
    print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
    exit(502)

  print("发送了" + str(count) + "条消息")
