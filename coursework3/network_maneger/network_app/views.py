from django.shortcuts import render
from django.http import HttpResponse
from .forms import DeviceConfigForm
from coursework3_dev import connect_to_device, config_interface  # 导入之前的 Python 脚本

def index(request):
    return render(request, 'network_app/index.html')

def config_device(request):
    if request.method == 'POST':
        form = DeviceConfigForm(request.POST)
        if form.is_valid():
            # 获取表单数据
            ip = form.cleaned_data['ip']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            secret = form.cleaned_data['secret']
            interface = form.cleaned_data['interface']
            ip_addr = form.cleaned_data['ip_addr']
            mask = form.cleaned_data['mask']

            # 使用 Python 脚本配置设备
            connection = connect_to_device(username, ip, password, secret)
            if connection:
                result = config_interface(connection, interface, ip_addr, mask, {}, '')
                connection.disconnect()
                return HttpResponse(f"Configuration Result: {result}")
            else:
                return HttpResponse('[ERROR] Unable to connect to the device.')

    else:
        form = DeviceConfigForm()

    return render(request, 'network_app/config_device.html', {'form': form})