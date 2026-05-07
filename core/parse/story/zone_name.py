__all__ = ['zone_name']

from core.constant import invalid_story_id
from core.name import zone_name as base_name, char_name

from .data import story_data

zone_set: set[str] = set()
char_set: set[str] = set()
for i in story_data.values():
    (char_set if i.type == 'Memory' else zone_set).add(i.zone)

zone_name: dict[str, dict[str, str]] = {k: base_name[k] for k in zone_set if k not in invalid_story_id}

char_dict: dict[str, str] = {k.split('_', 3)[-1]: k for k in char_name}

for char in char_set:
    zone_name[char] = char_name[char_dict[char]]
