#!/usr/bin/env python
#
#  war2pud - Warcraft 2 PUD reader.
#
#  This script parses Blizzard Entertainment's Warcraft 2 PUD files.
#
#  Based on PUD file format revision 3 specification from:
#    http://cade.datamax.bg/war2x/pudspec.html
#
#  Copyright (c) 2012 Beau Hastings. All rights reserved.
#  License: GNU GPL version 2, see LICENSE for more details.
#
#  Author: Beau Hastings <beausy@gmail.com>

import os
import struct

import numpy

from war2pud import util, exception, const, model

def join_arrays(*arrays):
    result = []
    for array in arrays:
        if isinstance(array, list):
            result.extend(array)
        elif isinstance(array, int):
            result.append(array)
        else:
            raise TypeError('Expected list or int, got %s' % type(array))
    return result

class TerrainType(object):
    """
  """
    FOREST = 0
    WINTER = 1
    WASTELAND = 2
    SWAMP = 3


# ---------------------------------------------------------------------------------------------------

class PUDFileReader(object):
    """
  """

    """
  (dict) PUD file sections.
  """
    _sections = {}

    """
  (tuple) PUD versions.
  """
    _versions = (
        17,  # Maps without new heroes.
        19  # Maps with new heroes.
    )

    """
  (list) Allowable player types.
  """
    _allowedplayertypes = [
        'passive computer',
        'computer',
        'passive computer',
        'unused',
        'computer',
        'human',
        'rescue (passive)',
        'rescue (active)'
    ]

    """
  (dict) Terrain types.
  """
    _terrains = {}

    """
  (dict) Unit data.
  """
    _unitdata = {}

    """
  (dict) Missile weapons.
  """
    _missileweapons = {}

    """
  (dict) Update types.
  """
    _upgrades = {}

    """
  (list) Allowed player races.
  """
    _allowedraces = {}

    """
  (dict) Allowed player AI.
  """
    _allowedai = {}

    """
  (int) Map width.
  """
    _mapwidth = 0

    """
  (int) Map height.
  """
    _mapheight = 0

    _hints_peasant_units = [2, 3]

    _hints_animal_unit = 57

    _hints_infantry_units = [0, 1]
    _hints_peasant_attack_units = [16, 17]
    _hints_skeleton_unit = 55
    _hints_infantry_basic_units = join_arrays(
        _hints_infantry_units,
        _hints_peasant_attack_units,
        _hints_skeleton_unit
    )

    _hints_cavalry_units = [6, 7]
    _hints_cavalry_upgraded_units = [12, 13]
    _hints_cavalry_basic_units = join_arrays(
        _hints_cavalry_units,
        _hints_cavalry_upgraded_units
    )

    _hints_archer_units = [8, 9]
    _hints_archer_upgraded_units = [18, 19]
    _hints_archer_basic_units = join_arrays(
        _hints_archer_units,
        _hints_archer_upgraded_units
    )

    _hints_mage_units = [10, 11]

    _hints_demolition_units = [14, 15]

    _hints_siege_units = [4, 5]

    _hints_naval_tanker_units = [26, 27]
    _hints_naval_transport_units = [28, 29]
    _hints_naval_attack_light_units = [30, 31]
    _hints_naval_attack_heavy_units = [32, 33]
    _hints_naval_stealth_units = [38, 39]
    _hints_naval_basic_units = join_arrays(
        _hints_naval_tanker_units,
        _hints_naval_transport_units,
        _hints_naval_attack_light_units,
        _hints_naval_attack_heavy_units,
        _hints_naval_stealth_units
    )

    _hints_air_scout_units = [40, 41]
    _hints_air_attack_units = [42, 43]
    _hints_daemon_unit = 56
    _hints_air_basic_units = join_arrays(
        _hints_air_scout_units,
        _hints_air_attack_units,
        _hints_daemon_unit
    )

    _hints_hero_alleria_unit = 20
    _hints_hero_terongorenfiend_unit = 21
    _hints_hero_kurdanandskyree_unit = 22
    _hints_hero_dentarg_unit = 23
    _hints_hero_khadgar_unit = 24
    _hints_hero_gromhellscream_unit = 25
    _hints_hero_deathwing_unit = 35
    _hints_hero_turalyon_unit = 44
    _hints_hero_eyeofkillrog_unit = 45
    _hints_hero_danath_unit = 46
    _hints_hero_khorgathbladefist_unit = 47
    _hints_hero_chogall_unit = 49
    _hints_hero_lothar_unit = 50
    _hints_hero_guldan_unit = 51
    _hints_hero_utherlightbringer_unit = 52
    _hints_hero_zuljin_unit = 53
    _hints_hero_units = join_arrays(
        _hints_hero_alleria_unit,
        _hints_hero_terongorenfiend_unit,
        _hints_hero_kurdanandskyree_unit,
        _hints_hero_dentarg_unit,
        _hints_hero_khadgar_unit,
        _hints_hero_gromhellscream_unit,
        _hints_hero_deathwing_unit,
        _hints_hero_turalyon_unit,
        _hints_hero_eyeofkillrog_unit,
        _hints_hero_danath_unit,
        _hints_hero_khorgathbladefist_unit,
        _hints_hero_chogall_unit,
        _hints_hero_lothar_unit,
        _hints_hero_guldan_unit,
        _hints_hero_utherlightbringer_unit,
        _hints_hero_zuljin_unit
    )
    _hints_building_units = [
        58, 59, 60, 61, 62, 63, 64, 65, 66,
        67, 68, 69, 70, 71, 72, 73, 74, 75, 76,
        77, 78, 79, 80, 81, 82, 83, 84, 85, 86,
        87, 88, 89, 90, 91, 96, 97, 98, 99
    ]
    _hints_building_special_units = [100, 101, 102]
    _hints_building_walls_units = [103, 104]

    _hints_goldmine_unit = 92
    _hints_oil_patch_unit = 93
    _hints_resource_units = join_arrays(
        _hints_goldmine_unit,
        _hints_oil_patch_unit
    )

    _hints_start_location_units = [94, 95]

    # -------------------------------------------------------------------------------------------------

    def __init__(self, filename=None):
        """
    Create a new `PUDFileReader` instance.

    Args:
      filename (str) Path to a PUD file.
    """

        if filename:
            self.filename = filename

    # -------------------------------------------------------------------------------------------------

    def loadassets(self, datadir=None):
        """
    Load text file database assets.

    Args:
      datadir (str) Path to data directory. (default: current_directory/data)

    Returns:
      (bool) `True` if loading assets succeeded.
    """

        if datadir is None:
            basedir = os.path.abspath(os.path.dirname(__file__))
            datadir = os.path.join(basedir, '..', 'data')

        self._units = util.loadtextdb(os.path.join(datadir, 'units.txt'))
        self._missileweapons = util.loadtextdb(os.path.join(datadir, 'missile_weapons.txt'))
        self._terrains = util.loadtextdb(os.path.join(datadir, 'terrains.txt'))
        self._upgrades = util.loadtextdb(os.path.join(datadir, 'upgrade_types.txt'))
        self._allowedraces = util.loadtextdb(os.path.join(datadir, 'races.txt'))
        self._allowedai = util.loadtextdb(os.path.join(datadir, 'player_ai.txt'))

        return True

    # -------------------------------------------------------------------------------------------------

    def readsections(self):
        """
    Reads each section from the PUD file.

    Yields:
      (tuple) Containing the section name and (mixed) data.

    exception:
      (PudFileError) When end-of-file is unexpected.
    """

        with open(self.filename, 'rb') as f:
            while True:
                name = f.read(const.SECTIONNAME_LEN).decode("utf-8")
                if name == '':
                    break

                length = f.read(const.SECTIONDATA_LEN)
                if length == '':
                    raise exception.PudFileError('Unexpected end-of-file encountered at %d.' % f.tell())
                length = struct.unpack('i', length)[0]

                data = f.read(length)
                if data == '':
                    raise exception.PudFileError('Unexpected end-of-file encountered at %d.' % f.tell())

                yield name, self._parsesection(name, data, length)

    # -------------------------------------------------------------------------------------------------

    def _parsesection(self, name, data, length):
        """
    Parses a section node.

    Args:
      name   (str) Name of section.
      data   (str) Raw data to parse.
      length (int) Length of data.

    Returns:
      (dict) Containing section attribute and value pairs.

    exception:
      (SectionError) When `name` is unrecognized.
      (VersionError) When PUD version is unrecognized.
      (PlayerError)  When an unknown player type is encountered.
      (TerrainError) When an unknown terrain type is encountered.
      (MapError)     When map dimensions are out of bounds.
    """

        # Identifies as a PUD file
        if name == 'TYPE':
            pud_type, unused1, unused2, id = struct.unpack_from('=10s2BL', data)
            return dict(type=pud_type, unused1=unused1, unused2=unused2, id=id)

        # Identifies PUD version
        elif name == 'VER ':
            version = struct.unpack_from('=H', data)[0]
            if not version in self._versions:
                raise exception.VersionError('Unrecognized version `%i`' % version)
            return version

        # PUD description
        elif name == 'DESC':
            return struct.unpack_from('=32s', data)[0]

        # Identifies players
        elif name == 'OWNR':
            unpacked = struct.unpack_from('=16b', data)

            for player in unpacked:
                if not self._allowedplayertypes[player] in self._allowedplayertypes:
                    raise exception.PlayerError('Unknown player type `%i`' % player)

            return unpacked

        # Terrain type
        elif name == 'ERA ':
            terrain = struct.unpack_from('=H', data)[0]

            if not terrain in self._terrains:
                raise exception.TerrainError('Unknown terrain `%i`' % terrain)

            return terrain

        # Terrain type (Optional)
        elif name == 'ERAX':
            terrain = struct.unpack_from('=H', data)[0]

            if not terrain in self._terrains:
                raise exception.TerrainError('Unknown terrain `%i`' % terrain)

            return terrain

        # Map dimensions
        elif name == 'DIM ':
            width, height = struct.unpack_from('=HH', data)

            if width > const.MAX_MAP_WIDTH:
                raise exception.MapError('Map width is greater than the maximum of %d' % const.MAX_MAP_WIDTH)

            if height > const.MAX_MAP_HEIGHT:
                raise exception.MapError('Map height is greater than the maximum of %d' % const.MAX_MAP_HEIGHT)

            self._mapwidth, self._mapheight = width, height
            return width, height

        # Unit data
        elif name == 'UDTA':
            unpacked = struct.unpack_from('=H 110B 110B 127H 127H 127H 127H 110I 110H 110B 110B'
                                          '110B 110B 110B 110I 110I 110B 110B 110B 110B 110B'
                                          '110B 110B 110B 110B 110B 110B 110B 110B 110B 58B'
                                          '110H 110B 109I', data)

            use_default = unpacked[0]

            unitdata = dict(first_construction_frame=unpacked[1:111],
                            second_construction_frame=unpacked[111:221],
                            general_unit_gfx=unpacked[221:348],
                            summer_unit_gfx=unpacked[348:475],
                            winter_unit_gfx=unpacked[475:602],
                            wasteland_unit_gfx=unpacked[602:729],
                            sight_range=unpacked[729:839],
                            hit_points=unpacked[839:949],
                            magic=unpacked[949:1059],
                            build_time=unpacked[1059:1169],
                            gold_cost=unpacked[1169:1279],
                            lumber_cost=unpacked[1279:1389],
                            oil_cost=unpacked[1389:1499],
                            unit_size=unpacked[1499:1609],
                            box_size=unpacked[1609:1719],
                            attack_range=unpacked[1719:1829],
                            reaction_range_cpu=unpacked[1829:1939],
                            reaction_range_human=unpacked[1939:2049],
                            armor=unpacked[2049:2159],
                            selectable_by_rect=unpacked[2159:2269],
                            priority=unpacked[2269:2379],
                            basic_damage=unpacked[2379:2489],
                            piercing_damage=unpacked[2489:2599],
                            weapons_upgradeable=unpacked[2599:2709],
                            armor_upgradeable=unpacked[2709:2819],
                            missile_weapon=unpacked[2819:2929],
                            unit_type=unpacked[2929:3039],
                            decay_rate=unpacked[3039:3149],
                            annoy_cpu_factor=unpacked[3149:3259],
                            mouse_btn_2_action=unpacked[3259:3317],
                            point_value_for_kill_unit=unpacked[3317:3427],
                            can_target=unpacked[3427:3537],
                            flags=unpacked[3537:3647])

            for key in unitdata.keys():
                for index, value in enumerate(unitdata[key]):
                    if self._unitdata.get(index, {}):
                        self._unitdata[index][key] = value

            return unitdata

        # TODO (beau): Pud restrictions (Optional)
        elif name == 'ALOW':
            pass

        # Upgrade data
        elif name == 'UGRD':
            unpacked = struct.unpack_from('=H 52B 52H 52H 52H 52H 52H 52I', data)

            use_default = unpacked[0]

            updatedata = dict(upgrade_time=unpacked[1:53],
                              gold_cost=unpacked[53:105],
                              lumber_cost=unpacked[105:157],
                              oil_cost=unpacked[157:209],
                              upgrade_icon=unpacked[209:261],
                              group_applies_to=unpacked[261:313],
                              affect_flags=unpacked[313:365])

            return updatedata

        # Identifies race of each player
        elif name == 'SIDE':
            return struct.unpack_from('=8B 7B 1B', data)

        # Starting gold
        elif name == 'SGLD':
            return struct.unpack_from('=8H 7H 1H', data)

        # Starting lumber
        elif name == 'SLBR':
            return struct.unpack_from('=8H 7H 1H', data)

        # Starting oil
        elif name == 'SOIL':
            return struct.unpack_from('=8H 7H 1H', data)

        # Player AI
        elif name == 'AIPL':
            return struct.unpack_from('=8B 7B 1B', data)

        # Tiles map
        elif name == 'MTXM':
            fmt = '=' + str(self._mapwidth * self._mapheight) + 'H'
            return struct.unpack_from(fmt, data)

        # Movement map
        elif name == 'SQM ':
            fmt = '=' + str(self._mapwidth * self._mapheight) + 'H'
            unpacked = struct.unpack_from(fmt, data)
            return unpacked

        # Oil concentration map (obsolete)
        elif name == 'OILM':
            fmt = '=' + str(int((self._mapwidth * self._mapheight) / struct.calcsize('=H'))) + 'H'
            unpacked = struct.unpack_from(fmt, data)
            return unpacked

        # Action map
        elif name == 'REGM':
            fmt = '=' + str(self._mapwidth * self._mapheight) + 'H'
            unpacked = struct.unpack_from(fmt, data)
            return unpacked

        # Units
        elif name == 'UNIT':
            fmt = '=1H 1H 1B 1B 1H'
            unit_size = struct.calcsize(fmt)
            num_units = int(length / unit_size)

            start = 0
            end = start + unit_size

            units = []

            for i in range(num_units):
                unit = struct.unpack_from(fmt, data[start:end])
                units.append(model.Unit(unit))
                start += unit_size
                end = start + unit_size

            return units

        # Unknown (optional)
        elif name == 'SIGN':
            return struct.unpack_from('=1I', data)

        raise exception.SectionError('Unrecognized section `%s`' % name)

    # -------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------
