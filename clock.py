'''
Heroku 免費 dyno 所提供的規格：

dyno 會入睡。若 30 分鐘內無人使用，則進入睡眠狀態。喚醒需花約 20 秒。
每個月提供免費運作時間為 550 小時，通過信用卡認證後可增加至 1000 小時➁。
資料庫(database)免費可記錄 1 萬筆資料，最多同時提供 20 個連線服務。

由於 Heroku 的免費方案會讓 dyno 在 30 分鐘無人打擾之後陷入沉睡狀態，造成下次呼叫時需要較長的喚醒時間，而導致較差的使用者體驗。
為了能夠讓 Heroku 保持清醒狀態，我們用 APScheduler 讓我們的免費 dyno 在快要睡著的時候，呼叫 "https://你-APP-的名字.herokuapp.com/" ，自己喚醒自己。
另我讓他從星期一工作到星期五，六日放假休息
'''


from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('cron', day_of_week='mon-fri', minute='*/20')
def scheduled_job():
    url = "https://sunnystockdetect.herokuapp.com/"
    conn = urllib.request.urlopen(url)
        
    for key, value in conn.getheaders():
        print(key, value)

sched.start()


'''#測試
@sched.scheduled_job('interval', minutes=3)
def timed_job():
    print('This job is run every three minutes.')

@sched.scheduled_job('cron', day_of_week='mon-fri', hour=17)
def scheduled_job():
    print('This job is run every weekday at 5pm.')
'''
sched.start()