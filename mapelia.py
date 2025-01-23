#!/usr/bin/env python3

import maps

def main():
    parser = maps.get_parser()
    args = parser.parse_args()
    output = maps.process(args)
    print('The output is in file %s' % output)



if __name__ == '__main__':
    main()

# Ideas for the future:
#
# * Add a decent GUI.
# * Progress bar while processing.
# * Make a preview of the map images when they are selected.
# * Show statistics about standard deviation, Fourier components and
#   so on, depending on the channel selected to extract the elevations.
# * Add an automatic channel selection mode, following what appears
#   more promising from the image statistics.
# * Let it open the result in meshlab or blender if they are available.
# * Document the algorithm I wrote to connect the points into triangles
#   on a sphere-like object.
