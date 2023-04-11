import sys
import yaml
import pprint
import math
from zabbix_api import ZabbixAPI


TRIGGERNAME_SEARCH_FORMAT = 'Interface {0}('

LINKDOWN_TRIGGER_FILTER = [
  ": リンクダウン"
]

PORTSTATE_TRIGGER_FILTER = [
  ": アウトバウンド",
  ": インバウンド"
]

def filterLinkdownTrigger(description):
  for str in LINKDOWN_TRIGGER_FILTER:
    if str in description:
      return True
    else:
      continue

  return False
def filterPortStateTrigger(description):
  for str in PORTSTATE_TRIGGER_FILTER:
    if str in description:
      return True
    else:
      continue

  return False

def findTriggerFromTriggerList(triggerList, filter):
  items = {
    'link_trigger': [],
    'port_trigger': []
  } 
  for item in triggerList:
    if filter in item['description'] and filterLinkdownTrigger(item['description']):
      items['link_trigger'].append({
        "trigger": item['description'],
        "triggerid": item['triggerid']
      })
    elif filter in item['description'] and filterPortStateTrigger(item['description']):
      items['port_trigger'].append({
        "trigger": item['description'],
        "triggerid": item['triggerid']
      })
    else:
      continue

  return items

templatePath = sys.argv[1]
with open(templatePath, 'r') as f:
  ifTemplate = yaml.safe_load(f)

configPath = './conf.yml'
with open(configPath, 'r') as f:
  conf = yaml.safe_load(f)

zapi = ZabbixAPI(server=conf.get('zabbix_server'))
zapi.login(conf.get('zabbix_user'), conf.get('zabbix_password'))
hostdata = zapi.host.get({
  "filter": {
    "host": [
      ifTemplate.get('hostname')
    ]
  }})
hostid = hostdata[0].get('hostid')
descriptionFilter = []
descriptionFilter.extend(LINKDOWN_TRIGGER_FILTER)
descriptionFilter.extend(PORTSTATE_TRIGGER_FILTER)
triggers = zapi.trigger.get({
  "output": "extend",
  "hostids": hostid,
  "search": {
    "description": descriptionFilter, 
  },
  "searchByAny": True,
  "sortfield": "description"
})
images = dict()
images_result = zapi.image.get({
  "output": "extend",
  "search": {
    "name": [
      'port_normal',
      'port_disable',
      'port_error',
      'link_normal',
      'link_disable',
      'link_error',
    ], 
  },
  "searchByAny": True,
})
for item in images_result:
  images[item['name']] = item['imageid']

interfaces={}
for cardIndex in range(ifTemplate.get('line_card')):
  interfaces[str(cardIndex+1)] = {
    "port": [],
    "uplink": [],
  }

  for portIndex in range(ifTemplate.get('interface_port')):
    search_name = TRIGGERNAME_SEARCH_FORMAT.format(
      ifTemplate['ifname_format'].format(
        cardnumber=cardIndex+1,
        ifnumber=portIndex+1,
      )
    )
    item = findTriggerFromTriggerList(triggers, search_name)
    interfaces[str(cardIndex+1)]['port'].append(item)

  for ulPortIndex in range(ifTemplate.get('uplink_port')):
    search_name = TRIGGERNAME_SEARCH_FORMAT.format(
      ifTemplate['ifname_format'].format(
        cardnumber=cardIndex+1,
        ifnumber=ifTemplate.get('interface_port') + ulPortIndex+1,
      )
    )
    item = findTriggerFromTriggerList(triggers, search_name)
    interfaces[str(cardIndex+1)]['uplink'].append(item)

mapSchema = {
  "name": 'PortMap: ' + ifTemplate.get('hostname'),
  "width": 1280,
  "height": 100 + (int(ifTemplate.get('line_card')) * 200),
  "highlight": 0,
  "label_format": 1,
  "label_type_trigger": 4,
  "selements": [],
  "links": [],
  "shapes": []
}

TOP_PORT_COORDINATE = {
  'x': 74,
  'y': 154 
}
TOP_LINK_COORDINATE = {
  'x': 85,
  'y': 125
}
TOP_LABEL_COORDINATE = {
  'x': 80,
  'y': 100
}
portCoordinate = TOP_PORT_COORDINATE
linkCoordinate = TOP_LINK_COORDINATE
labelCoordinate = TOP_LABEL_COORDINATE
cardCoordinate = {
  'x': 5,
  'y': 175
}

titleShape = {
  "type": 0,
  "x": 30,
  "y": 34,
  "width": 1000,
  "height": 32,
  "text": ifTemplate['hostname'] + ' Port Map',
  "font_size": 20,
  "text_halign": 1
} 
subtitle = "device: {0}({1} ports, {2} uplinks)".format(
  ifTemplate['devicename'],
  str(ifTemplate['interface_port']),
  str(ifTemplate['uplink_port']),
)
subTitleShape = {
  "type": 0,
  "x": 30,
  "y": 59,
  "width": 1000,
  "height": 22,
  "text": subtitle,
  "font_size": 14,
  "text_halign": 1
}
mapSchema['shapes'].append(titleShape)
mapSchema['shapes'].append(subTitleShape)

for cardIndex in interfaces.keys():
  cardShape = {
    "type": 0,
    "x": cardCoordinate['x'],
    "y": cardCoordinate['y'],
    "width": 50,
    "height": 30,
    "text": "Card-" + cardIndex
  } 
  mapSchema['shapes'].append(cardShape)

  i = 0
  for port in interfaces[cardIndex]['port']:
    i += 1
    xOffcet = (math.ceil(i/2) - 1) * 40
    yPortOffcet = 40 if i % 2 == 0 else 0
    yLinkOffcet = 120 if i % 2 == 0 else 0
    yLabelOffcet = 160 if i % 2 == 0 else 0
    mapSchema['selements'].append({
      "elements": [{"triggerid": item["triggerid"]} for item in port['port_trigger']],
      "elementtype": 2,
      "iconid_off": images['port_normal'],
      "iconid_on": images['port_error'],
      "iconid_disabled": images['port_disable'],
      "label": "",
      "x": portCoordinate['x'] + xOffcet,
      "y": portCoordinate['y'] + yPortOffcet,
    })
    mapSchema['selements'].append({
      "elements": [{"triggerid": item["triggerid"]} for item in port['link_trigger']],
      "elementtype": 2,
      "iconid_off": images['link_normal'],
      "iconid_on": images['link_error'],
      "iconid_disabled": images['link_disable'],
      "label": "",
      "x": linkCoordinate['x'] + xOffcet,
      "y": linkCoordinate['y'] + yLinkOffcet,
    })
    mapSchema['shapes'].append({
      "type": 0,
      "x": labelCoordinate['x'] + xOffcet,
      "y": labelCoordinate['y'] + yLabelOffcet,
      "width": 20,
      "height": 20,
      "text": str(i) 
    })

  for port in interfaces[cardIndex]['uplink']:
    i += 1
    xOffcet = (math.ceil(i/2) - 1) * 40 + 20
    yPortOffcet = 40 if i % 2 == 0 else 0
    yLinkOffcet = 120 if i % 2 == 0 else 0
    yLabelOffcet = 160 if i % 2 == 0 else 0
    mapSchema['selements'].append({
      "elements": [{"triggerid": item["triggerid"]} for item in port['port_trigger']],
      "elementtype": 2,
      "iconid_off": images['port_normal'],
      "iconid_on": images['port_error'],
      "iconid_disabled": images['port_disable'],
      "label": "",
      "x": portCoordinate['x'] + xOffcet,
      "y": portCoordinate['y'] + yPortOffcet,
    })
    mapSchema['selements'].append({
      "elements": [{"triggerid": item["triggerid"]} for item in port['link_trigger']],
      "elementtype": 2,
      "iconid_off": images['link_normal'],
      "iconid_on": images['link_error'],
      "iconid_disabled": images['link_disable'],
      "label": "",
      "x": linkCoordinate['x'] + xOffcet,
      "y": linkCoordinate['y'] + yLinkOffcet,
    })
    mapSchema['shapes'].append({
      "type": 0,
      "x": labelCoordinate['x'] + xOffcet,
      "y": labelCoordinate['y'] + yLabelOffcet,
      "width": 20,
      "height": 20,
      "text": str(i) 
    })

zapi.map.create(mapSchema)