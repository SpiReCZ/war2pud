#!/usr/bin/env python
#
#  This file is part of war2pud.
#
#  Copyright (c) 2012 Beau Hastings. All rights reserved.
#  License: GNU GPL version 2, see LICENSE for more details.
#
#  Author: Beau Hastings <beausy@gmail.com>

# Standard Python imports.
import os

# Application imports.

# 3rd party imports.
import numpy
from PIL import Image

from war2pud import util, const


class Unit(object):
    """
  Represents a game unit.
  """

    x = 0
    y = 0
    type_id = None
    type = None
    owner_id = None
    owner = None
    resource = None
    is_hero = False
    is_peasant = False
    is_building = False
    is_goldmine = False
    is_special = False

    def __init__(self, data):
        """
    Create a new `Unit` instance.

    Args:
      data (tuple) Containing x, y, type, owner, and resource
    """

        self.x = data[0]
        self.y = data[1]
        self.type_id = data[2]
        self.owner_id = data[3]
        self.resource = data[4]

    def __repr__(self):
        return '<%s(%r, %r, %d, %d>' % (self.__class__.__name__,
                                        self.type_id,
                                        self.owner,
                                        self.x,
                                        self.y)
    def to_dict(self):
        return {
            'type-id': self.type_id,
            'type': self.type,
            'owner': self.owner,
            'owner-id': self.owner_id,
            'resource': self.resource,
            'is-hero': self.is_hero,
            'is-building': self.is_building,
            'is-goldmine': self.is_goldmine,
            'is-special': self.is_special,
            'is-peasant': self.is_peasant
        }

    def __str__(self):
        if self.type is None:
            return '(no type)'

        unit_type = util.lookup_unit_type(self.type)
        if unit_type:
            return unit_type

        return str(self.type)


# ---------------------------------------------------------------------------------------------------

class Player(object):
    """
  Represents a player.
  """

    id = None
    race = None
    type = None
    is_ai = False
    ai_id = None
    ai_name = None
    gold = 0
    lumber = 0
    oil = 0

    def __init__(self):
        """
    Create a new `Player` instance.
    """
        pass

    def __repr__(self):
        return '<%s(%r, %r, %r>' % (self.__class__.__name__, self.race, self.type, self.ai_name)

    def to_dict(self):
        return {
            'race': self.race,
            'type': self.type,
            'is-ai': self.is_ai,
            'ai-id': self.ai_id,
            'ai-name': self.ai_name,
            'gold': self.gold,
            'lumber': self.lumber,
            'oil': self.oil
        }

# ---------------------------------------------------------------------------------------------------

class PUD(object):
    """
  Represents a map.
  """

    """
  (str) PUD type.
  """
    type = ''

    """
  (int) ID tag (for consistence check in multiplayer).
  """
    id = 0

    """
  (int) Version.
  """
    version = 0

    """
  (str) Description.
  """
    description = ''

    """
  (int) Map width.
  """
    width = 0

    """
  (int) Map height.
  """
    height = 0

    """
  (list) Units.
  """
    units = []

    """
  (list) Players.
  """
    players = []

    """
  (list) Tiles.
  """
    tiles = []

    """
  (str) Terrain.
  """
    terrain = ''

    """
  (str) Terrain X.
  """
    terrain_x = ''

    """
  (dict) Unit Data.
  """
    unit_data = {}


    """
  (dict) Upgrade Data.
  """
    upgrade_data = {}

    def __init__(self):
        """
    Create a new `PUD` instance.
    """
        self.players = [Player() for i in range(const.MAX_PLAYERS)]

    # -------------------------------------------------------------------------------------------------

    def export(self, filename=None):
        """
    Exports the map as an image.

    Args:
      filename (str) The destination image filename.
    """

        basedir = os.path.abspath(os.path.dirname(__file__))
        datadir = os.path.join(basedir, '..', 'data')

        if self.terrain == 'forest':
            tilemap = 'FOREST.BMP'
        elif self.terrain == 'winter':
            tilemap = 'WINTER.BMP'
        elif self.terrain == 'wasteland':
            tilemap = 'WASTE.BMP'
        elif self.terrain == 'swamp':
            tilemap = 'SWAMP.BMP'
        else:
            tilemap = 'FOREST.BMP'

        tilemap_path = os.path.join(datadir, tilemap)

        # copy region: rect = (x, y, width, height); region = im.crop(rect)
        tilemap = Image.open(tilemap_path)
        #tile = int(self.tiles[0, 0])

        #print([int(self.tiles[i, 0]) for i in range(8)])

        #print(hex(int(self.tiles[0, 0])))
        #print(hex(int(self.tiles[0, 1])))
        #print(hex(int(self.tiles[0, 65])))

        # 4800px = (4800 / 32) = 150 forest trees
        # 4320px = (4320 / 32) = 135 - 104 = start of light water
        #          432 (B0 01) in .pud, 297 difference
        #
        # first 104 entries in tileset are units, not tiles
        #print(((tile * 10) / 32 - 104))

        #print(tile)

        #tile_offset = tile
        #region = tilemap.crop((tile_offset, 0, tile_offset + 32, 32))
        #im = Image.new("RGB", (32, 32))
        #im.paste(region, (0, 0, 32, 32))
        #im.save(os.path.join(datadir, 'test.bmp'))

        #region = tilemap.crop((4800, 0, 4800 + 32, 32))
        #im = Image.new("RGB", (1024, 1024))
        #im.paste(region, (0, 0, 32, 32))
        #im.save(os.path.join(datadir, 'test.bmp'))


        scale_factor = 4

        tile_size = 32  # Each tile is 32x32 pixels
        map_width = self.width * tile_size
        map_height = self.height * tile_size

        scaled_width = map_width // scale_factor
        scaled_height = map_height // scale_factor

        im = Image.new("RGB", (scaled_width, scaled_height))

        tiles_per_row = tilemap.width // tile_size

        for y in range(self.height):
            for x in range(self.width):
                tile = int(self.tiles[y, x])
                tile_offset_x = (tile % tiles_per_row) * tile_size
                tile_offset_y = (tile // tiles_per_row) * tile_size
                region = tilemap.crop((tile_offset_x, tile_offset_y, tile_offset_x + tile_size, tile_offset_y + tile_size))
                region = region.resize((tile_size // scale_factor, tile_size // scale_factor), Image.Resampling.LANCZOS)
                im.paste(region, (x * (tile_size // scale_factor), y * (tile_size // scale_factor)))


        if filename:
            im.save(os.path.join(datadir, filename))
        else:
            im.save(os.path.join(datadir, 'test.bmp'))












