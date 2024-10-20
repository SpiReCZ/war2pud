# Application imports.
import json
import os

import war2pud

# 3rd party imports.
import numpy

from war2pud.util.utils import append_sitemap

puds_count = 0
puds_with_heroes_count = 0
puds_with_buildings_count = 0
puds_with_specials_count = 0
puds_without_goldmines_count = 0
puds_without_peasants_count = 0

sitemap = []
puds_with_heroes = []
puds_with_buildings = []
puds_with_specials = []
puds_without_goldmines = []
puds_without_peasants = []


def main():
    # traverse directories of ./puds and process all .pud files
    handle_dir('puds')

    puds_data = {
        'count': puds_count,
        'with-heroes-count': puds_with_heroes_count,
        'with-buildings-count': puds_with_buildings_count,
        'with-specials-count': puds_with_specials_count,
        'without-goldmines-count': puds_without_goldmines_count,
        'without-peasants-count': puds_without_peasants_count,
    }

    #print(json.dumps(pud_data, indent=4))
    with open("metadata/stats.json", 'w') as f:
        json.dump(puds_data, f, indent=4)
    with open("metadata/sitemap.json", 'w') as f:
        json.dump(sitemap, f, indent=4)
    with open("metadata/heroes.json", 'w') as f:
        json.dump(puds_with_heroes, f, indent=4)
    with open("metadata/buildings.json", 'w') as f:
        json.dump(puds_with_buildings, f, indent=4)
    with open("metadata/specials.json", 'w') as f:
        json.dump(puds_with_specials, f, indent=4)
    with open("metadata/goldmines.json", 'w') as f:
        json.dump(puds_without_goldmines, f, indent=4)
    with open("metadata/peasants.json", 'w') as f:
        json.dump(puds_without_peasants, f, indent=4)


def handle_dir(input_dir: str):
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            handle_file(root, file)


def handle_file(root: str, file: str):
    if file.endswith('.pud'):
        print('Processing:', os.path.join(root, file))
        handle_pud(os.path.join(root, file))


def handle_pud(file: str):
    reader = war2pud.PUDFileReader(file)
    reader.loadassets()

    pud = war2pud.model.PUD()

    global puds_count, puds_with_heroes_count, puds_with_buildings_count
    global puds_without_peasants_count, puds_with_specials_count, puds_without_goldmines_count
    puds_count += 1

    for section_name, data in reader.readsections():
        if section_name == 'TYPE':
            pud.type = data['type']
            pud.id = data['id']

        elif section_name == 'DESC':
            pud.description = data

        elif section_name == 'DIM ':
            pud.width, pud.height = data[0], data[1]

        elif section_name == 'VER ':
            pud.version = data

        elif section_name == 'OWNR':
            for index, type_ in enumerate(data):
                pud.players[index].id = type_
                pud.players[index].type = reader._allowedplayertypes[type_]
                pud.players[index].is_ai = pud.players[index].type != 'human'

        elif section_name == 'SIDE':
            for index, race in enumerate(data):
                pud.players[index].race = reader._allowedraces[race]['name']

        elif section_name == 'AIPL':
            for index, ai in enumerate(data):
                pud.players[index].ai_id = ai
                pud.players[index].ai_name = reader._allowedai[ai]['name']

        elif section_name == 'SGLD':
            for index, gold in enumerate(data):
                pud.players[index].gold = gold

        elif section_name == 'SLBR':
            for index, lumber in enumerate(data):
                pud.players[index].lumber = lumber

        elif section_name == 'SOIL':
            for index, oil in enumerate(data):
                pud.players[index].oil = oil

        elif section_name == 'UNIT':
            pud.units = data
            for unit in pud.units:
                unit.type = reader._units[unit.type_id]['name']
                unit.is_hero = unit.type in reader._hints_hero_units
                unit.is_building = (unit.type_id in reader._hints_building_units or
                                    unit.type_id == reader._hints_building_special_units)
                unit.is_special = (unit.type_id in reader._hints_building_special_units or
                                   unit.type_id == reader._hints_skeleton_unit or
                                   unit.type_id == reader._hints_daemon_unit)
                unit.is_goldmine = unit.type_id == reader._hints_goldmine_unit
                unit.is_peasant = unit.type_id in reader._hints_peasant_units

        elif section_name == 'ERA ':
            pud.terrain = reader._terrains[data]['name']

        elif section_name == 'ERAX ':
            pud.terrain_x = reader._terrains[data]['name']

        elif section_name == 'MTXM':
            tiles = numpy.zeros((pud.width, pud.height))

            for h in range(pud.height):
                for w in range(pud.width):
                    tiles[w, h] = data[w * h]

            pud.tiles = tiles

        elif section_name == 'UDTA':
            pud.unit_data = data

        # TODO (beau): Pud restrictions (Optional)
        elif section_name == 'ALOW':
            pass

        elif section_name == 'UGRD':
            pud.upgrade_data = data

    json_file = os.path.join('metadata', *file.split(os.sep)[1:]) + '.json'
    preview_file = os.path.join('preview', *file.split(os.sep)[1:]) + '.jpg'
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    os.makedirs(os.path.dirname(preview_file), exist_ok=True)


    append_sitemap(file, json_file, preview_file, sitemap)
    if any(u.is_hero for u in pud.units):
        puds_with_heroes_count += 1
        append_sitemap(file, json_file, preview_file, puds_with_heroes)
    if any(u.is_building for u in pud.units):
        puds_with_buildings_count += 1
        append_sitemap(file, json_file, preview_file, puds_with_buildings)
    if any(u.is_special for u in pud.units):
        puds_with_specials_count += 1
        append_sitemap(file, json_file, preview_file, puds_with_specials)
    if all(u.is_goldmine is False for u in pud.units):
        puds_without_goldmines_count += 1
        append_sitemap(file, json_file, preview_file, puds_without_goldmines)
    if all(u.is_peasant is False for u in pud.units):
        puds_without_peasants_count += 1
        append_sitemap(file, json_file, preview_file, puds_without_peasants)

    # print('Type:', pud.type)
    # print('ID:', hex(pud.id))
    # print('Version:', pud.version)
    # print('Size:', pud.width, 'x', pud.height)
    # print('Description:', pud.description)
    # print('Terrain:', pud.terrain)
    # print('Players:', sum([1 for p in pud.players if p.type != 'unused' and p.race != 'neutral']))
    #pud.export()

    pud_data = {
        'file': file,
        'picture': preview_file,
        'type': pud.type.decode('utf-8').rstrip('\x00'),
        'id': hex(pud.id),
        'version': pud.version,
        'size': f'{pud.width}x{pud.height}',
        'description': pud.description.decode('utf-8').rstrip('\x00'),
        'terrain': pud.terrain,
        'players-count': sum([1 for p in pud.players if p.type != 'unused' and p.race != 'neutral']),
        'units-count': len(pud.units),
        'heroes-count': sum(1 for u in pud.units if u.is_hero),
        'buildings-count': sum(1 for u in pud.units if u.is_building),
        'specials-count': sum(1 for u in pud.units if u.is_special),
        'goldmines-count': sum(1 for u in pud.units if u.is_goldmine),
        'players': [p.to_dict() for p in pud.players if p.type != 'unused' and p.race != 'neutral'],
        'units': [u.to_dict() for u in pud.units],
    }

    #print(json.dumps(pud_data, indent=4))
    with open(json_file, 'w') as f:
        json.dump(pud_data, f, indent=4)


if __name__ == '__main__':
    main()
