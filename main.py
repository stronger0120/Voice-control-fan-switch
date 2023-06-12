import serial
import os
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import time
import requests
import urllib.parse
import urllib.request
from playsound import playsound

def fetch_token():  # 提交请求，拿到token
    api_key = '0rb6hPtEIM7xuwcxYZoldGV0'
    secret_key = '8uhIjTmSF0gyPIY09HacPLhf2pMvcmfq'
    token_url = "https://openapi.baidu.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": api_key, "client_secret": secret_key}
    r = requests.get(url=token_url, params=params)
    if r.status_code == 200:
        rstr = r.json()
        tok = rstr['access_token']
        return (tok)
    else:
        print(r.text)
        print('请求错误！')


def ConnectRelay(PORT="COM3"):
    try:
        master = modbus_rtu.RtuMaster(serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='E', stopbits=1))
        master.set_timeout(5.0)
        master.set_verbose(True)
        # 读输入寄存器
        # c2s03 设备默认 slave=2, 起始地址=0, 输入寄存器个数 2
        master.execute(2, cst.READ_INPUT_REGISTERS, 0, 2)
        # 读保持寄存器
        # c2s03 设备默认 slave=2, 起始地址=0, 保持寄存器个数 1
        master.execute(2, cst.READ_HOLDING_REGISTERS, 0, 1)
        # 这里可以修改
        # 需要读取的功能码
        # 没有报错，返回 1
        response_code = 1
    except Exception as exc:
        print(str(exc))
        # 报错，返回<0 并输出错误
        response_code = -1
        master = None
    return response_code, master


def Switch(master, ACTION):
    """
    此函数为控制继电器开合函数，如果 ACTION=ON 则闭合，如果如果 ACTION=OFF 则断开。
    :param master: 485 主机对象，由 ConnectRelay 产生
    :param ACTION: ON 继电器闭合，开启风扇；OFF 继电器断开，关闭风扇。
    :return: >0 操作成功，<0 操作失败
       # 写单个线圈，状态常量为 0xFF00，请求线圈接通
        # c2s03 设备默认 slave=2, 线圈地址=0, 请求线圈接通即 output_value 不22 等于 0
         # 写单个线圈，状态常量为 0x0000，请求线圈断开
    # c2s03 设备默认 slave=2, 线圈地址=0, 请求线圈断开即 output_value 等于 0
    # 没有报错，返回 1
     # 报错，返回<0 并输出错误
    """
    try:
        if "on" in ACTION.lower():
            master.execute(2, cst.WRITE_SINGLE_COIL, 0, output_value=1)
        else:
            master.execute(2, cst.WRITE_SINGLE_COIL, 0, output_value=0)
            response_code = 1
    except Exception as exc:
        print(str(exc))
    response_code = -1
    return response_code


import wave
import requests
import time
import base64
from pyaudio import PyAudio, paInt16
import webbrowser

framerate = 16000  # 采样率
num_samples = 2000  # 采样点
channels = 1  # 声道
sampwidth = 2  # 采样宽度2bytes
FILEPATH = 'speech.wav'
#wav格式的优点是能完整地记录所有单声道或立体声的声音信息，让声音不会发生失真等问题

base_url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"
APIKey = "1Rx8Vr0YDiZmANl05PPfGMrl"  # 填写自己的APIKey
SecretKey = "d77fI2h04j6A3EITtGD3Pu3ztyqtGpY9"  # 填写自己的SecretKey
HOST = base_url % (APIKey, SecretKey)

#获取token，根据创建应用得到的APIKey和SecreKey来组装URL获取token。
def getToken(host):
    res = requests.post(host)
    return res.json()['access_token']


def save_wave_file(filepath, data):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)
    wf.setframerate(framerate)
    wf.writeframes(b''.join(data))
    wf.close()


def my_record():
    #录音函数中使用了PyAudio库，是Python下的一个音频处理模块，用于将音频流输送到计算机声卡上。在当前文件夹打开一个新的音频进行录音并存放录音数据。
    pa = PyAudio()
    stream = pa.open(format=paInt16, channels=channels,
                     rate=framerate, input=True, frames_per_buffer=num_samples) #打开一个新的音频stream
    my_buf = [] #存放录音数据
    # count = 0
    t = time.time()
    print('正在录音...')

    while time.time() < t + 4:  #设置录音时间
        string_audio_data = stream.read(num_samples)
        my_buf.append(string_audio_data)
    print('录音结束.')
    save_wave_file(FILEPATH, my_buf)
    stream.close()


def get_audio(file):
    with open(file, 'rb') as f:
        data = f.read()
    return data

# 传入语音二进制数据，token，在语音识别函数中调用获取的token和已经录制好的音频数据，按照要求的格式来写进JSON参数进行上传音频。
# dev_pid为百度语音识别提供的几种语言选择，默认1537为有标点普通话
def speech2text(speech_data, token, dev_pid=1537):
    FORMAT = 'wav'
    RATE = '16000'
    CHANNEL = 1
    CUID = '*******'
    SPEECH = base64.b64encode(speech_data).decode('utf-8')

    data = {
        'format': FORMAT,
        'rate': RATE,
        'channel': CHANNEL,
        'cuid': CUID,
        'len': len(speech_data),
        'speech': SPEECH,
        'token': token,
        'dev_pid': dev_pid
    }
    url = 'https://vop.baidu.com/server_api'     # 短语音识别请求地址
    headers = {'Content-Type': 'application/json'}
    print('正在识别...')
    r = requests.post(url, json=data, headers=headers)
    Result = r.json()
    if 'result' in Result:
        return Result['result'][0]
    else:
        return Result


def openbrowser(text):
    maps = {
        '开': ['开。', '想开风扇。', '请打开风扇。', '打开风扇。', '开风扇。','开开开。', '打开。', '热死了。'],
        '关': ['关。', '关掉风扇。', '请关掉风扇。', '关掉。', '好冷。', '想关掉风扇。','关风扇。'],
    }
    if text in maps['开']:
        print(1111111)
        # speech.say("现在为您开风扇")

        start = time.time()
        Switch(master, "on")

    elif text in maps['关']:
        start = time.time()
        Switch(master, "off")
    else:
        print(222222)
        start = time.time()



if __name__ == '__main__':
    flag = 'y'
    code, master = ConnectRelay("COM3")
    while flag.lower() == 'y':
        start = time.time()
        token = fetch_token()
        TTS_URL = "https://tsn.baidu.com/text2audio"
        text = u"请说出您的指令。".encode(
            'utf8')

        PER = 106  # 发音人,基础音库：0为度小美，1为度小宇，3为度逍遥，4为度丫丫;精品音库5为度小娇，103为度米朵，106为度博文，110为度小童，111为度小萌，默认为度小美

        SPD = 5  # 语速，取值0-15，默认为中语速(5)
        PIT = 5  # 音调，取值0-15，默认为中语调(5)
        VOL = 5  # 音量，取值0-9，默认为中音量(5)

        AUE = 3  # 文件格式, 3：mp3(default)  4：pcm-16k  5：pcm-8k  6.wav

        FORMATS = {3: "mp3", 4: "pcm", 5: "pcm", 6: "wav"}
        FORMAT = FORMATS[AUE]

        data = urllib.parse.urlencode(
            {'tex': text, 'per': PER, 'tok': token, 'cuid': '20009514', 'ctp': 1, 'lan': 'zh', 'aue': AUE})

        req = requests.post(TTS_URL, data)
        print(req.status_code)

        if req.status_code == 200:
            result_str = req.content
            save_file = r'F:\作业\IT创新项目实践\test.mp3'  # 文件保存路径
            with open(save_file, 'wb') as of:
                of.write(result_str)
            print('请说出您的指令!')
            playsound(save_file)
        else:
            print('has error!')

        my_record()
        TOKEN = getToken(HOST)
        speech = get_audio(FILEPATH)
        result = speech2text(speech, TOKEN, int(1537))
        print(result)
        if type(result) == str:
            openbrowser(result.strip('，'))
        flag = input('Continue?(y/n):')
