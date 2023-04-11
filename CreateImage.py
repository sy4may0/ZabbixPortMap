import yaml
import base64
from zabbix_api import ZabbixAPI

IMAGE_SET = [
  {
    'name': 'port_normal',
    'path': './icon/port_normal.png',
  },
  {
    'name': 'port_error',
    'path': './icon/port_error.png',
  },
  {
    'name': 'port_disable',
    'path': './icon/port_disable.png',
  },
  {
    'name': 'link_normal',
    'path': './icon/link_normal.png',
  },
  {
    'name': 'link_error',
    'path': './icon/link_error.png',
  },
  {
    'name': 'link_disable',
    'path': './icon/link_disable.png',
  },
]

configPath = './conf.yml'
with open(configPath, 'r') as f:
  conf = yaml.safe_load(f)

zapi = ZabbixAPI(server=conf.get('zabbix_server'))
zapi.login(conf.get('zabbix_user'), conf.get('zabbix_password'))

for item in IMAGE_SET:
  with open(item['path'], 'rb') as f:
    data = base64.b64encode(f.read())

    result = zapi.image.create({
      "imagetype": 1,
      "name": item['name'],
      "image": data.decode('utf-8')
    })

    print(result)

