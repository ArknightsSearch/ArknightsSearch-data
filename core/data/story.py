from copy import deepcopy

from core.name import story_name, story_code, month_squad_name, activity_id2code
from .error import InvalidData

"""
解析 story_table 中的数据
"""


class StoryData:
    id: str
    filename: str
    type: str
    name: dict[str, str]
    code: str | None
    zone: str
    zone_name: dict[str, str]
    data: dict | None
    lang: dict[str, dict[str, str]]

    def __init__(self, story_id: str):
        self.id = story_id
        self.filename = story_id.split('/')[-1]
        self.code = None

    def format_name(self, name: str | dict[str, str], _type: str):
        data = deepcopy(self.lang[_type])
        for key in data:
            if isinstance(name, dict):
                data[key] = data[key] % (name.get(key) or name['zh_CN'])
            else:
                data[key] = data[key] % name
        return data

    @property
    def dump(self) -> dict:
        return {
            'id': self.id,
            # 'filename': self.filename,
            'type': self.type,
            'name': self.name,
            'code': self.code,
            'zone': self.zone
        }


class MemoryData(StoryData):
    def __init__(self, story_id: str):
        super().__init__(story_id)
        self.type = 'Memory'
        self.name = story_name[self.id]
        self.code = None
        # 角色id
        group = self.filename.split('_', 3)
        self.zone = group[1]
        if group[3] != '1':
            for lang in self.name:
                self.name[lang] += ' ' + group[3]


class MainData(StoryData):
    lang = {
        'recap': {
            'zh_CN': '第%s章回顾'
        }
    }

    def __init__(self, story_id: str):
        super().__init__(story_id)
        self.type = 'Main'
        self.parse_name()
        self.parse_zone()

    def parse_name(self):
        group = self.filename.split('_')
        if group[0] == 'level':
            if group[-1] == 'recap':
                self.name = self.format_name(group[2], 'recap')
            elif group[1] in ['main', 'st', 'spst']:
                self.name = story_name[self.id]
                self.code = story_code[self.id]
            else:
                raise TypeError(f'Unknown story type {self.id}')
        elif group[0] == 'main':
            if '_'.join(group[-2:]) == 'zone_enter':
                # 已知剧情(10/11章)仅有视频资源，无文本
                raise InvalidData
        else:
            raise TypeError(f'Unknown story type {self.id}')

    def parse_zone(self):
        group = self.filename.split('_')
        if group[0] == 'level':
            if group[-1] == 'recap':
                self.zone = f'main_{group[2]}'
            elif group[1] in ['main', 'st', 'spst']:

                if not group[2].isdigit():
                    # TODO 临时补丁，17章主线更新引入
                    raise InvalidData
                
                self.zone = f'main_{int(group[2].split("-")[0])}'
            else:
                raise TypeError(f'Unknown zone {self.id}')
        elif group[-1] == 'enter':
            self.zone = f'main_{group[1]}'
        else:
            raise TypeError(f'Unknown zone {self.id}')


class RogueData(StoryData):
    def __init__(self, story_id: str):
        super().__init__(story_id)
        self.type = 'Rogue'
        self.parse_name()
        self.zone = 'rogue_' + self.filename.split('_')[3]

    def parse_name(self):
        group = self.filename.split('_')
        if group[1] == 'record' and int(group[3]) > 2:
            # 就你叫record是吧
            # 萨卡兹肉鸽更新：看来以后都叫record，但为什么details数据没变呢.jpg
            group[1] = 'chat'
        name = deepcopy(month_squad_name['_'.join(group[:-1])])
        for key in name:
            name[key] = f'{name[key]} Part.0{group[-1]}'
        self.name = name


class ActivityStory(StoryData):
    lang = {
        'entry': {
            'zh_CN': '%s进入活动'
        },
        'actfun': {
            'zh_CN': '愚人节剧情%s'
        },
        'lock': {
            'zh_CN': '连锁竞赛 %s'
        },
        'ending': {
            'zh_CN': '结局 %s'
        }
    }
    mini_story = {
        # zoneId里没有mini的坏id（
        'act4d0',
        'act7d5',
        'act10d5',
        'act13d0',
        'act15d5'
    }

    def __init__(self, story_id: str):
        super().__init__(story_id)
        self.type = 'Activity'
        self.parse_zone()
        self.parse_name()

    def parse_name(self):
        if self.id.split('/')[2] in ['guide', 'training', 'level']:
            # 教程关/关卡内剧情 无名称/不可再触发
            raise InvalidData
        group = self.filename.split('_')

        if self.filename == 'level_act12side_tr01_end':
            # 角你怎么训练关后塞剧情啊（
            self.code = 'DH-TR-1'
            self.name = {}

            from core.util import json
            from core.constant import stage_path, support_language

            for lang in support_language:
                for stage_id, stage_data in json.load(stage_path % lang)['stages'].items():
                    if stage_id == 'level_act12side_tr01':
                        self.name[lang] = stage_data['name']
            return

        if group[0] == 'level':
            if group[2] == 'hidden':
                # act13side_hidden
                # 长夜临光隐藏剧情，未发现入口
                raise InvalidData
            elif group[-1] == 'entry':
                self.name = self.format_name('', 'entry')
            elif group[1].endswith('fun') or group[1] == 'act17d7':
                # 愚人节剧情
                self.name = self.format_name(group[2], 'actfun')
            elif group[1].endswith('lock'):
                self.name = self.format_name(group[2].removeprefix('st'), 'lock')
            elif group[1].endswith('mini') or group[1] in self.mini_story:
                # 迷你故事集
                self.code = f'{activity_id2code[self.zone]}-{group[-1].upper().replace("0", "")}'
                self.name = story_name[self.id]
            elif group[2] == 'ending':
                # 目前仅在生稀盐酸发现，结局剧情
                self.name = self.format_name(group[3], 'ending')
            elif group[-1] in ['beg', 'end']:
                self.name = story_name[self.id]
                self.code = story_code[self.id]
            elif group[-1].startswith('st'):
                self.name = story_name[self.id]
                self.code = story_code[self.id]
            else:
                raise TypeError(f'Unknown story type {self.id}')
        elif group[0] in {'guide', 'tutorial', 'ui'}:
            raise InvalidData
        else:
            raise TypeError(f'Unknown story type {self.id}')

    def parse_zone(self):
        self.zone = self.id.split('/')[1]
        # 自由の角（
        if self.zone == 'a001':
            self.zone = '1stact'


Data = MemoryData | MainData | RogueData | ActivityStory


class StoryParser:
    @staticmethod
    def parse(story_id: str) -> Data:
        story_id = story_id.lower()
        group = story_id.split('/')
        if group[0] == 'obt':
            # TODO record(第10/11章note)？
            if group[1] == 'memory':
                return MemoryData(story_id)
            elif group[1] == 'main':
                return MainData(story_id)
            elif group[1] == 'rogue':
                return RogueData(story_id)
            elif group[1] in [
                'tutorial',  # 关卡内引导
                'legion',  # 保全派驻引导
                'rune',  # 危机合约引导，
                'guide',  # 操作引导
                'roguelike',  # 肉鸽剧情
                'record',  # 10/11章note
                'sandboxperm'  # TODO
                # 好懒，不想适配（
            ]:
                raise InvalidData

            else:
                raise TypeError(f'Unknown story type obt/* {group}')
        elif group[0] == 'activities':
            return ActivityStory(story_id)

        raise InvalidData
