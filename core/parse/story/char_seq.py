__all__ = ['seq_data']

import re
import asyncio
import json

import aiohttp

r1 = re.compile(r'^\d')


def get_seq(char_id: str) -> str:
    group = char_id.split('_')
    for i, seq in enumerate(group):
        if r1.search(seq):
            break
    else:
        raise ValueError('Cannot get seq from %s' % group)
    return 'npc_' + seq if 'npc' in group else seq + ('_' + group[i + 1] if i + 1 < len(group) else '')


async def get_data():
    async with aiohttp.ClientSession() as client:
        async with client.get('https://raw.githubusercontent.com/Arkfans/ArknightsName/main/data/npc.json') as r:
            return json.loads(await r.text())


name_data: dict[str, dict[str, list[str]]] = asyncio.run(get_data())
pre_seq_data: dict[str, dict[str, set[str]]] = {}
seq_data: list[list[list[str]]] = []

for char_id, char_name in name_data.items():
    char_seq = get_seq(char_id)
    if char_seq not in pre_seq_data:
        pre_seq_data[char_seq] = {'id': {char_id}, 'name': set()}
    else:
        pre_seq_data[char_seq]['id'].add(char_id)

    for lang, names in char_name.items():
        for name in names:
            pre_seq_data[char_seq]['name'].add(name)

for _, char_data in sorted(pre_seq_data.items(), key=lambda x: x[0]):
    seq_data.append([(sorted(char_data['id'])), sorted(char_data['name'])])
