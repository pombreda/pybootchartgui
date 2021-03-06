#  This file is part of pybootchartgui.

#  pybootchartgui is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  pybootchartgui is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with pybootchartgui. If not, see <http://www.gnu.org/licenses/>.

import cairo

import draw

def render(writer, res, options, filename):
    handlers = {
        "png": (lambda w,h: cairo.ImageSurface(cairo.FORMAT_ARGB32,w,h), lambda sfc: sfc.write_to_png(filename)),
        "pdf": (lambda w,h: cairo.PDFSurface(filename, w, h), lambda sfc: 0),
        "svg": (lambda w,h: cairo.SVGSurface(filename, w, h), lambda sfc: 0)
    }

    if options.format is None:
        format = filename.rsplit('.',1)[1];
    else:
        format = options.format

    if not(format in handlers):
        writer.error("Unknown format '%s'." % format)
        return 10

    make_surface, write_surface = handlers[format]
    w,h = draw.extents(*res)
    w = max(w, draw.MIN_IMG_W)
    surface = make_surface(w,h)
    ctx = cairo.Context(surface)
    draw.render(ctx, options, *res)
    write_surface(surface)
    writer.status("bootchart written to '%s'" % filename)

