from ..gds_parser import GDSParser


class AreaGDSParser(GDSParser):
    def __init__(self):
        super(AreaGDSParser, self).__init__()
        self.command_name_table = {
            0x4a: ["init_board", "Init Board"],
            # params: (corner x, corner y, tiles w, tiles h, tile size w, tile size h,
            #          color r, color g, color b, color a)
            0x6e: ["remove_tiles", "Remove Tiles"],
            # params: (tile x, tile y, tile w, tile h)
            0x4b: ["set_solution", "Set Solution"],
            # params: (tile x, tile y, tile w, tile h)
        }
