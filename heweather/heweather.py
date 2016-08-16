# -*- coding: utf-8 -*-
import sys, alfred, urllib2, json, re
from urllib import quote


def get_ip():
    url = "http://1212.ip138.com/ic.asp"
    opener = urllib2.urlopen(url)
    if url == opener.geturl():
        str = unicode(opener.read(), 'gb2312')
    str = str.split('<center>')[1].split('</center>')[0]  # a little tricky
    return re.search('\d+\.\d+\.\d+\.\d+', str).group(0)


def get_city():
    url = 'http://apis.baidu.com/apistore/iplookupservice/iplookup?ip=' + get_ip()
    req = urllib2.Request(url)
    req.add_header("apikey", "74c196f2485ed531620230e79d963b96")
    resp = urllib2.urlopen(req)
    content = resp.read()
    jo = json.loads(content)
    if jo['errNum'] == '1':
        feedback = alfred.Feedback()
        feedback.addItem(title=u'查询IP地址错误', subtitle=u'请稍后再尝试')
        feedback.output()
        exit(-1)
    city = jo['retData']['city']
    url = 'http://apis.baidu.com/xiaogg/changetopinyin/topinyin?str=' + quote(
        city.encode('utf-8')) + '&type=json&traditional=0&accent=0&letter=0&only_chinese=0'
    req = urllib2.Request(url)
    req.add_header("apikey", "74c196f2485ed531620230e79d963b96")
    resp = urllib2.urlopen(req)
    content = resp.read()
    jo = json.loads(content)
    return jo['pinyin'].replace(' ', '')


def set_cache():
    """
    获取天气并缓存
    """
    url = 'http://apis.baidu.com/heweather/weather/free?city=' + get_city()
    req = urllib2.Request(url)
    req.add_header("apikey", "74c196f2485ed531620230e79d963b96")
    resp = urllib2.urlopen(req)
    content = resp.read()
    test = json.loads(content)
    jo = json.loads(content)['HeWeather data service 3.0'][0]
    if not jo['status'] == 'ok':
        feedback = alfred.Feedback()
        feedback.addItem(title=u'查询天气信息错误', subtitle=u'请稍后再尝试')
        feedback.output()
        exit(-1)
    else:
        cache = {'hourly': jo['hourly_forecast'], 'basic': jo['basic'],
                 'suggestion': jo['suggestion'], 'daily': jo['daily_forecast'], 'aqi': jo['aqi']['city'],
                 'now': jo['now']}
        alfred.cache.set('heweather.list', cache, expire=600)


def get_cache():
    """
    获取缓存信息
    """
    if alfred.cache.timeout('heweather.list') == -1:
        set_cache()
    return alfred.cache.get('heweather.list')


def output(query):
    """
    返回结果给Alfred
    """
    if query == 'c':
        alfred.cache.delete('heweather.list')
        feedback = alfred.Feedback()
        feedback.addItem(title=u'缓存清理完成', subtitle=u'请尝试其他参数')
        feedback.output()
        exit(0)
    workflows = get_cache()
    feedback = alfred.Feedback()
    if query == 'h':
        for w in workflows['hourly']:
            feedback.addItem(
                title=u'气温:' + w['tmp'] + u'℃ 湿度:' + w['hum'] + u'% 降水概率:' + w['pop'] + u'% 气压:' + w['pres'] + u'KPa',
                subtitle=u'时间:' + w['date'] + u'    风力等级:' + w['wind']['sc'] + u' 风速:' + w['wind'][
                    'spd'] + u'Kmph 风向:' +
                         w['wind']['dir'])
    elif query == 'b':
        w = workflows['basic']
        feedback.addItem(title=w['cnty'] + u', ' + w['city'] + u'   经度:' + w['lon'] + u' 纬度:' + w['lat'],
                         subtitle=u'更新时间:' + w['update']['loc'])
    elif query == 's':
        workflows = workflows['suggestion']
        w = workflows['uv']
        feedback.addItem(title=u'紫外线指数:' + w['brf'], subtitle=w['txt'])
        w = workflows['flu']
        feedback.addItem(title=u'感冒指数:' + w['brf'], subtitle=w['txt'])
        w = workflows['trav']
        feedback.addItem(title=u'旅游指数:' + w['brf'], subtitle=w['txt'])
        w = workflows['drsg']
        feedback.addItem(title=u'穿衣指数:' + w['brf'], subtitle=w['txt'])
        w = workflows['sport']
        feedback.addItem(title=u'运动指数:' + w['brf'], subtitle=w['txt'])
        w = workflows['cw']
        feedback.addItem(title=u'洗车指数:' + w['brf'], subtitle=w['txt'])
        w = workflows['comf']
        feedback.addItem(title=u'舒适指数:' + w['brf'], subtitle=w['txt'])
    elif query == 'd':
        for w in workflows['daily']:
            feedback.addItem(
                title=w['tmp']['min'] + u'℃~' + w['tmp']['max'] + u'℃ 能见度:' + w['vis'] + u'km 湿度:' + w[
                    'hum'] + u'% 降水概率:' +
                      w['pop'] + u'%',
                subtitle=w['date'] + u' 白天' + w['cond']['txt_d'] + u' 夜间' + w['cond']['txt_n'] + u' 日出' + w['astro']['sr'] + u'日落' +
                         w['astro']['ss'] + u' ' + w['wind']['sc'] + u' ' + w['wind']['dir'] + u' 风速:' + w['wind'][
                             'spd'] + u'Kmph')
    elif query == 'a':
        w = workflows['aqi']
        feedback.addItem(title=w['qlty'] + u'  空气指数:' + w['aqi'],
                         subtitle='PM2.5:' + w['pm25'] + ' PM10:' + w['pm10'] + ' CO:' + w['co'] + ' SO2:' + w[
                             'so2'] + ' O3:' + w['o3'] + ' NO2:' + w['no2'])
    elif query == 'n':
        w = workflows['now']
        feedback.addItem(
            title=w['tmp'] + u' ' + w['cond']['txt'] + u'℃ 能见度' + w['vis'] + u' 湿度:' + w[
                'hum'] + '% ',
            subtitle=u'体感温度:' + w['fl'] + u' 气压:' + w['pres'] + '  ' + w['wind']['dir'] + u' 风力:' +
                     w['wind']['sc'] + u'级 风速:' + w['wind']['spd'] + u'Kmph')
    feedback.output()


if __name__ == '__main__':
    output(sys.argv[1])
